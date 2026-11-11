"""Consumidor RabbitMQ e coordenador do flush de micro-lotes."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import logging
import threading
import time
from typing import Any

import pika

from src.clickhouse import ClickHouse
from src.config import config
from src.contrato import EnvelopeInvalido, validar
from src.lake import Lake, MensagemRecebida, dia_local, novo_lote


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EntregaValida:
    delivery_tag: int
    data_tag: str
    timestamp: int
    corpo: bytes
    objetos: list[dict[str, Any]]


class FalhaClickHouse(RuntimeError):
    """Sinaliza falha após tentativa registrada no manifesto."""


class Consumidor:
    def __init__(
        self,
        lake: Lake | None = None,
        clickhouse: ClickHouse | None = None,
    ) -> None:
        self.lake = lake or Lake()
        self.clickhouse = clickhouse or ClickHouse()
        self.buffer: list[EntregaValida] = []
        self.buffer_inicio: float | None = None
        self.conexao: pika.BlockingConnection | None = None
        self.canal: Any | None = None
        self._stop_event = threading.Event()

    @staticmethod
    def _timestamp_recebimento(properties: Any) -> int:
        headers = getattr(properties, "headers", None) or {}
        valor = headers.get("recebido_em_ms")
        if valor is None:
            return time.time_ns() // 1_000_000
        if isinstance(valor, bytes):
            valor = valor.decode("ascii", errors="strict")
        return int(valor)

    def _ack_rejeicao(
        self,
        canal: Any,
        delivery_tag: int,
        recebido_em_ms: int,
        motivo: str,
        corpo: bytes,
    ) -> None:
        inicio = time.perf_counter()
        arquivo = self.lake.rejeitar(recebido_em_ms, motivo, corpo)
        canal.basic_ack(delivery_tag=delivery_tag, multiple=False)
        logger.info(
            "lote=%s data_tag=desconhecida passo=rejeicao tamanho=%d tempo_ms=%d",
            arquivo["chave"].rsplit("/", 1)[-1],
            arquivo["bytes"],
            int((time.perf_counter() - inicio) * 1000),
        )

    def receber(
        self,
        canal: Any,
        method: Any,
        properties: Any,
        corpo: bytes,
    ) -> None:
        recebido_em_ms = self._timestamp_recebimento(properties)
        inicio_validacao = time.perf_counter()
        try:
            data_tag, objetos = validar(corpo, config.dominios)
        except EnvelopeInvalido as erro:
            self._ack_rejeicao(
                canal,
                method.delivery_tag,
                recebido_em_ms,
                erro.motivo,
                corpo,
            )
            return
        logger.info(
            "lote=buffer data_tag=%s passo=validacao tamanho=%d tempo_ms=%d",
            data_tag,
            len(corpo),
            int((time.perf_counter() - inicio_validacao) * 1000),
        )

        entrega = EntregaValida(
            delivery_tag=method.delivery_tag,
            data_tag=data_tag,
            timestamp=recebido_em_ms,
            corpo=corpo,
            objetos=objetos,
        )
        if not self.buffer:
            self.buffer_inicio = time.monotonic()
        self.buffer.append(entrega)
        logger.info("lote=buffer data_tag=%s tamanho=%d", data_tag, len(self.buffer))
        if len(self.buffer) >= config.flush_n:
            self.flush(canal)

    def _novo_manifesto(self, lote: str, entregas: list[EntregaValida]) -> dict[str, Any]:
        mensagens = Counter(entrega.data_tag for entrega in entregas)
        linhas = Counter(
            entrega.data_tag
            for entrega in entregas
            for _ in entrega.objetos
        )
        return {
            "lote": lote,
            "mensagens_por_data_tag": dict(mensagens),
            "linhas_por_data_tag": dict(linhas),
            "mensagens": len(entregas),
            "arquivos": [],
            "chaves_gravadas": [],
            "tempos_ms": {},
            "status": "ok",
        }

    def _registrar_arquivos(
        self,
        manifesto: dict[str, Any],
        camada: str,
        arquivos: list[dict[str, Any]],
    ) -> None:
        for arquivo in arquivos:
            registro = {"camada": camada, **arquivo}
            manifesto["arquivos"].append(registro)
            manifesto["chaves_gravadas"].append(arquivo["chave"])

    def _passo(
        self,
        manifesto: dict[str, Any],
        nome: str,
        funcao: Any,
        lote: str,
        data_tag: str,
        tamanho: int,
    ) -> Any:
        inicio = time.perf_counter()
        try:
            resultado = funcao()
        except Exception as erro:
            duracao_ms = int((time.perf_counter() - inicio) * 1000)
            manifesto["tempos_ms"][nome] = (
                manifesto["tempos_ms"].get(nome, 0) + duracao_ms
            )
            logger.error(
                "lote=%s data_tag=%s passo=%s tamanho=%d tempo_ms=%d erro_tipo=%s",
                lote,
                data_tag,
                nome,
                tamanho,
                duracao_ms,
                type(erro).__name__,
            )
            raise
        duracao_ms = int((time.perf_counter() - inicio) * 1000)
        manifesto["tempos_ms"][nome] = (
            manifesto["tempos_ms"].get(nome, 0) + duracao_ms
        )
        logger.info(
            "lote=%s data_tag=%s passo=%s tamanho=%d tempo_ms=%d",
            lote,
            data_tag,
            nome,
            tamanho,
            duracao_ms,
        )
        return resultado

    def flush(self, canal: Any) -> None:
        if not self.buffer:
            return

        entregas = self.buffer
        self.buffer = []
        self.buffer_inicio = None
        lote = novo_lote(entregas[0].timestamp)
        dia_manifesto = dia_local(entregas[0].timestamp)
        manifesto = self._novo_manifesto(lote, entregas)
        mensagens_por_chave: dict[tuple[str, str], list[MensagemRecebida]] = defaultdict(list)
        linhas_por_chave: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for entrega in entregas:
            dia = dia_local(entrega.timestamp)
            mensagens_por_chave[(entrega.data_tag, dia)].append(
                MensagemRecebida(entrega.corpo, entrega.timestamp)
            )
            for objeto in entrega.objetos:
                linhas_por_chave[(entrega.data_tag, dia)].append(
                    {
                        "timestamp": entrega.timestamp,
                        "data_json": objeto,
                        "data_tag": entrega.data_tag,
                    }
                )

        arquivos_raw = []
        for (data_tag, dia), mensagens in sorted(mensagens_por_chave.items()):
            arquivo = self._passo(
                manifesto,
                "raw",
                lambda tag=data_tag, data=dia, msgs=mensagens: self.lake.gravar_raw(
                    lote, tag, data, msgs
                ),
                lote,
                data_tag,
                len(mensagens),
            )
            arquivos_raw.append(arquivo)
        self._registrar_arquivos(manifesto, "raw", arquivos_raw)

        arquivos_bronze = []
        for (data_tag, dia), linhas in sorted(linhas_por_chave.items()):
            arquivo = self._passo(
                manifesto,
                "bronze",
                lambda tag=data_tag, data=dia, lote_linhas=linhas: self.lake.gravar_bronze(
                    lote, tag, data, lote_linhas
                ),
                lote,
                data_tag,
                len(linhas),
            )
            arquivos_bronze.append(arquivo)
        self._registrar_arquivos(manifesto, "bronze", arquivos_bronze)

        todas_linhas = [
            linha
            for chave in sorted(linhas_por_chave)
            for linha in linhas_por_chave[chave]
        ]
        data_tags = sorted({entrega.data_tag for entrega in entregas})
        inicio_clickhouse = time.perf_counter()
        try:
            self._passo(
                manifesto,
                "clickhouse",
                lambda: self.clickhouse.inserir(todas_linhas, lote=lote),
                lote,
                ",".join(data_tags),
                len(todas_linhas),
            )
        except Exception as erro:
            logger.error(
                "lote=%s data_tag=%s passo=clickhouse tamanho=%d tempo_ms=%d "
                "erro_tipo=%s",
                lote,
                ",".join(data_tags),
                len(todas_linhas),
                int((time.perf_counter() - inicio_clickhouse) * 1000),
                type(erro).__name__,
            )
            manifesto["status"] = "erro_clickhouse"
            manifesto["motivo"] = "falha na gravação do ClickHouse"
            manifesto["erro_tipo"] = type(erro).__name__
            self._passo(
                manifesto,
                "manifesto_erro",
                lambda: self.lake.gravar_manifesto(lote, dia_manifesto, manifesto),
                lote,
                ",".join(data_tags),
                len(todas_linhas),
            )
            raise FalhaClickHouse("INSERT do ClickHouse falhou") from None

        manifesto["chaves_gravadas"].append(
            f"{config.clickhouse_database}.{config.clickhouse_tabela}"
        )
        self._passo(
            manifesto,
            "manifesto",
            lambda: self.lake.gravar_manifesto(lote, dia_manifesto, manifesto),
            lote,
            ",".join(data_tags),
            len(todas_linhas),
        )
        inicio_ack = time.perf_counter()
        canal.basic_ack(delivery_tag=entregas[-1].delivery_tag, multiple=True)
        logger.info(
            "lote=%s data_tag=%s passo=ack tamanho=%d tempo_ms=%d",
            lote,
            ",".join(data_tags),
            len(entregas),
            int((time.perf_counter() - inicio_ack) * 1000),
        )

    def _agendar_flush_temporizado(self) -> None:
        if self.conexao is None or self._stop_event.is_set():
            return
        self.conexao.call_later(config.flush_segundos, self._flush_temporizado)

    def _flush_temporizado(self) -> None:
        if self._stop_event.is_set():
            if self.canal is not None and self.canal.is_open:
                self.canal.stop_consuming()
            return
        if self.buffer:
            self.flush(self.canal)
        self._agendar_flush_temporizado()

    def _consumir_conexao(self) -> None:
        credenciais = pika.PlainCredentials(
            config.rabbitmq_user, config.rabbitmq_password or ""
        )
        self.conexao = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=config.rabbitmq_host,
                port=config.rabbitmq_port,
                credentials=credenciais,
            )
        )
        self.canal = self.conexao.channel()
        self.canal.queue_declare(queue=config.fila_ingestao, durable=True)
        self.canal.basic_qos(prefetch_count=max(config.flush_n, 1))
        self.canal.basic_consume(
            queue=config.fila_ingestao,
            on_message_callback=self.receber,
            auto_ack=False,
        )
        self._agendar_flush_temporizado()
        self.canal.start_consuming()

    def executar(self, stop_event: threading.Event | None = None) -> None:
        if config.flush_n < 1 or config.flush_segundos <= 0:
            raise ValueError("FLUSH_N e FLUSH_SEGUNDOS devem ser positivos")
        self._stop_event = stop_event or threading.Event()
        while not self._stop_event.is_set():
            try:
                self._consumir_conexao()
            except Exception as erro:
                logger.error(
                    "consumidor desconectado tipo_erro=%s",
                    type(erro).__name__,
                )
            finally:
                if self.conexao is not None and self.conexao.is_open:
                    self.conexao.close()
                self.conexao = None
                self.canal = None
            if not self._stop_event.is_set():
                self._stop_event.wait(config.flush_segundos)


def consumir(stop_event: threading.Event | None = None) -> None:
    Consumidor().executar(stop_event=stop_event)
