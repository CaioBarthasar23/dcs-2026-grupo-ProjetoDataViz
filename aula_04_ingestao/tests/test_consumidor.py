from types import SimpleNamespace
import threading
import time

import pytest

from src.consumidor import Consumidor, FalhaClickHouse
from src.config import config


class LakeFalso:
    def __init__(self, chamadas=None, falhar_raw=False):
        self.chamadas = chamadas if chamadas is not None else []
        self.falhar_raw = falhar_raw
        self.manifestos = []

    def gravar_raw(self, lote, data_tag, dia, mensagens):
        self.chamadas.append("raw")
        if self.falhar_raw:
            raise OSError("falha raw de teste")
        return {
            "bucket": "teste",
            "chave": f"raw/{lote}.jsonl",
            "bytes": 10,
            "sha256": "hash-raw",
            "data_tag": data_tag,
            "linhas": len(mensagens),
        }

    def gravar_bronze(self, lote, data_tag, dia, linhas):
        self.chamadas.append("bronze")
        return {
            "bucket": "teste",
            "chave": f"bronze/{lote}.parquet",
            "bytes": 20,
            "sha256": "hash-bronze",
            "data_tag": data_tag,
            "linhas": len(linhas),
        }

    def gravar_manifesto(self, lote, dia, manifesto):
        self.chamadas.append("manifesto")
        self.manifestos.append(manifesto)
        return {"chave": f"manifesto/{lote}.json", "bytes": 30, "sha256": "hash"}

    def rejeitar(self, recebido_em_ms, motivo, corpo):
        self.chamadas.append("rejeicao")
        return {"chave": "raw/ingestao_rejeitados/rejeitado.json", "bytes": len(corpo)}


class ClickHouseFalso:
    def __init__(self, chamadas=None, falhar=False):
        self.chamadas = chamadas if chamadas is not None else []
        self.falhar = falhar
        self.linhas = []

    def inserir(self, linhas, lote=None):
        self.chamadas.append("clickhouse")
        self.linhas.extend(linhas)
        if self.falhar:
            raise RuntimeError("falha clickhouse de teste")


class CanalFalso:
    def __init__(self, chamadas):
        self.chamadas = chamadas
        self.acks = []

    def basic_ack(self, **kwargs):
        self.chamadas.append("ack")
        self.acks.append(kwargs)


def _entrega(consumidor, canal, tag=7, corpo=None):
    recebido_em_ms = time.time_ns() // 1_000_000
    corpo = corpo or b'{"data_tag":"livros","data":{"upc":"x"}}'
    consumidor.receber(
        canal,
        SimpleNamespace(delivery_tag=tag),
        SimpleNamespace(headers={"recebido_em_ms": recebido_em_ms}),
        corpo,
    )


def test_flush_grava_raw_bronze_clickhouse_manifesto_e_ack_nessa_ordem() -> None:
    chamadas = []
    lake = LakeFalso(chamadas)
    clickhouse = ClickHouseFalso(chamadas)
    canal = CanalFalso(chamadas)
    consumidor = Consumidor(lake=lake, clickhouse=clickhouse)

    _entrega(consumidor, canal)
    consumidor.flush(canal)

    assert chamadas == ["raw", "bronze", "clickhouse", "manifesto", "ack"]
    assert lake.manifestos[0]["status"] == "ok"
    assert len(clickhouse.linhas) == 1
    assert canal.acks == [{"delivery_tag": 7, "multiple": True}]


def test_envelope_invalido_e_gravado_antes_do_ack() -> None:
    chamadas = []
    lake = LakeFalso(chamadas)
    canal = CanalFalso(chamadas)
    consumidor = Consumidor(lake=lake, clickhouse=ClickHouseFalso(chamadas))

    _entrega(consumidor, canal, corpo=b'{"data":{"upc":"x"}}')

    assert chamadas == ["rejeicao", "ack"]
    assert canal.acks == [{"delivery_tag": 7, "multiple": False}]
    assert consumidor.buffer == []


def test_falha_clickhouse_grava_manifesto_erro_e_nao_da_ack() -> None:
    chamadas = []
    lake = LakeFalso(chamadas)
    clickhouse = ClickHouseFalso(chamadas, falhar=True)
    canal = CanalFalso(chamadas)
    consumidor = Consumidor(lake=lake, clickhouse=clickhouse)
    _entrega(consumidor, canal)

    with pytest.raises(FalhaClickHouse):
        consumidor.flush(canal)

    assert chamadas == ["raw", "bronze", "clickhouse", "manifesto"]
    assert lake.manifestos[0]["status"] == "erro_clickhouse"
    assert canal.acks == []


def test_falha_lake_nao_grava_clickhouse_nem_confirma_mensagem() -> None:
    chamadas = []
    lake = LakeFalso(chamadas, falhar_raw=True)
    clickhouse = ClickHouseFalso(chamadas)
    canal = CanalFalso(chamadas)
    consumidor = Consumidor(lake=lake, clickhouse=clickhouse)
    _entrega(consumidor, canal)

    with pytest.raises(OSError, match="falha raw de teste"):
        consumidor.flush(canal)

    assert chamadas == ["raw"]
    assert clickhouse.linhas == []
    assert canal.acks == []


def test_falha_clickhouse_fecha_conexao_para_reentrega(monkeypatch) -> None:
    chamadas = []
    lake = LakeFalso(chamadas)
    clickhouse = ClickHouseFalso(chamadas, falhar=True)
    parar = threading.Event()
    consumidor = Consumidor(lake=lake, clickhouse=clickhouse)

    class CanalComConsumo(CanalFalso):
        is_open = True

        def basic_qos(self, prefetch_count):
            self.prefetch = prefetch_count

        def queue_declare(self, **kwargs):
            self.declaracao = kwargs

        def basic_consume(self, **kwargs):
            self.callback = kwargs["on_message_callback"]

        def start_consuming(self):
            method = SimpleNamespace(delivery_tag=11)
            props = SimpleNamespace(
                headers={"recebido_em_ms": time.time_ns() // 1_000_000}
            )
            self.callback(
                self,
                method,
                props,
                b'{"data_tag":"livros","data":{"upc":"x"}}',
            )
            consumidor.flush(self)

        def stop_consuming(self):
            pass

    canal_consumo = CanalComConsumo(chamadas)

    class ConexaoFalsa:
        is_open = True

        def channel(self):
            return canal_consumo

        def call_later(self, delay, callback):
            self.timer = delay

        def close(self):
            self.is_open = False
            parar.set()

    conexao = ConexaoFalsa()
    monkeypatch.setattr(
        "src.consumidor.pika.BlockingConnection", lambda parametros: conexao
    )

    consumidor.executar(stop_event=parar)

    assert conexao.is_open is False
    assert canal_consumo.prefetch >= config.flush_n
    assert lake.manifestos[0]["status"] == "erro_clickhouse"
    assert canal_consumo.acks == []
