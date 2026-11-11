"""Escrita de raw, bronze e manifestos no lake S3 compatível."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4
from zoneinfo import ZoneInfo

import boto3

from src.config import config


logger = logging.getLogger(__name__)
FUSO_DADOS = ZoneInfo("America/Sao_Paulo")


@dataclass(frozen=True)
class MensagemRecebida:
    corpo: bytes
    recebido_em_ms: int


def dia_local(recebido_em_ms: int) -> str:
    instante = datetime.fromtimestamp(recebido_em_ms / 1000, tz=UTC)
    return instante.astimezone(FUSO_DADOS).date().isoformat()


def novo_lote(recebido_em_ms: int) -> str:
    instante = datetime.fromtimestamp(recebido_em_ms / 1000, tz=UTC).astimezone(
        FUSO_DADOS
    )
    return f"lote_{instante:%H%M%S}_{uuid4().hex}"


class Lake:
    def __init__(self, cliente_s3: Any | None = None) -> None:
        self.s3 = cliente_s3 or boto3.client(
            "s3",
            endpoint_url=config.s3_endpoint_url,
            region_name=config.s3_region,
            aws_access_key_id=config.s3_access_key,
            aws_secret_access_key=config.s3_secret_key,
        )

    @staticmethod
    def _sha256(conteudo: bytes) -> str:
        return hashlib.sha256(conteudo).hexdigest()

    def _put(
        self,
        bucket: str,
        chave: str,
        conteudo: bytes,
        lote: str,
        content_type: str,
    ) -> dict[str, Any]:
        sha256 = self._sha256(conteudo)
        self.s3.put_object(
            Bucket=bucket,
            Key=chave,
            Body=conteudo,
            ContentType=content_type,
            Metadata={"sha256": sha256, "lote": lote},
        )
        return {
            "bucket": bucket,
            "chave": chave,
            "bytes": len(conteudo),
            "sha256": sha256,
        }

    def gravar_raw(
        self,
        lote: str,
        data_tag: str,
        dia: str,
        mensagens: Iterable[MensagemRecebida],
    ) -> dict[str, Any]:
        inicio = datetime.now(UTC)
        linhas = []
        quantidade = 0
        for mensagem in mensagens:
            corpo_texto = mensagem.corpo.decode("utf-8", errors="replace")
            corpo_texto = corpo_texto.replace("\r", " ").replace("\n", " ")
            linha = {
                "recebido_em_ms": mensagem.recebido_em_ms,
                "envelope": corpo_texto,
            }
            linhas.append(
                json.dumps(linha, ensure_ascii=False, separators=(",", ":"))
            )
            quantidade += 1
        conteudo = ("\n".join(linhas) + "\n").encode("utf-8")
        chave = (
            f"raw/ingestao/data_tag={data_tag}/data={dia}/{lote}.jsonl"
        )
        arquivo = self._put(
            config.bucket_raw, chave, conteudo, lote, "application/x-ndjson"
        )
        arquivo.update({"data_tag": data_tag, "linhas": quantidade})
        logger.info(
            "lote=%s data_tag=%s passo=raw tamanho=%d duracao_ms=%d",
            lote,
            data_tag,
            arquivo["bytes"],
            int((datetime.now(UTC) - inicio).total_seconds() * 1000),
        )
        return arquivo

    def gravar_bronze(
        self,
        lote: str,
        data_tag: str,
        dia: str,
        linhas: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        import duckdb
        import pyarrow as pa

        inicio = datetime.now(UTC)
        valores_timestamp: list[int] = []
        valores_json: list[str] = []
        for linha in linhas:
            valores_timestamp.append(int(linha["timestamp"]))
            valor_json = linha["data_json"]
            valores_json.append(
                valor_json
                if isinstance(valor_json, str)
                else json.dumps(valor_json, ensure_ascii=False, separators=(",", ":"))
            )
        tabela_arrow = pa.table(
            {
                "timestamp": pa.array(valores_timestamp, type=pa.uint64()),
                "data_json": pa.array(valores_json, type=pa.string()),
            }
        )
        chave = (
            f"bronze/ingestao/data_tag={data_tag}/data={dia}/{lote}.parquet"
        )
        with tempfile.TemporaryDirectory(prefix="aula04-bronze-") as diretorio:
            caminho_local = Path(diretorio) / f"{lote}.parquet"
            caminho_sql = str(caminho_local).replace("'", "''")
            conexao = duckdb.connect(database=":memory:")
            try:
                conexao.register("lote_arrow", tabela_arrow)
                conexao.execute(
                    f"COPY lote_arrow TO '{caminho_sql}' "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)"
                )
            finally:
                conexao.close()
            conteudo = caminho_local.read_bytes()
        arquivo = self._put(
            config.bucket_bronze,
            chave,
            conteudo,
            lote,
            "application/vnd.apache.parquet",
        )
        arquivo.update({"data_tag": data_tag, "linhas": len(valores_timestamp)})
        logger.info(
            "lote=%s data_tag=%s passo=bronze tamanho=%d duracao_ms=%d",
            lote,
            data_tag,
            arquivo["bytes"],
            int((datetime.now(UTC) - inicio).total_seconds() * 1000),
        )
        return arquivo

    def gravar_manifesto(
        self,
        lote: str,
        dia: str,
        manifesto: Mapping[str, Any],
    ) -> dict[str, Any]:
        conteudo = json.dumps(
            manifesto, ensure_ascii=False, separators=(",", ":"), default=str
        ).encode("utf-8")
        chave = f"raw/_manifestos/ingestao/data={dia}/{lote}.json"
        return self._put(
            config.bucket_raw,
            chave,
            conteudo,
            lote,
            "application/json",
        )

    def rejeitar(
        self,
        recebido_em_ms: int,
        motivo: str,
        corpo: bytes,
    ) -> dict[str, Any]:
        instante = datetime.fromtimestamp(recebido_em_ms / 1000, tz=UTC).astimezone(
            FUSO_DADOS
        )
        dia = instante.date().isoformat()
        lote = f"rejeitado_{instante:%H%M%S}_{uuid4().hex}"
        corpo_texto = corpo.decode("utf-8", errors="replace")
        objeto = {
            "recebido_em_ms": recebido_em_ms,
            "motivo": motivo,
            "corpo": corpo_texto,
        }
        conteudo = json.dumps(
            objeto, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        chave = f"raw/ingestao_rejeitados/data={dia}/{lote}.json"
        return self._put(
            config.bucket_raw,
            chave,
            conteudo,
            lote,
            "application/json",
        )
