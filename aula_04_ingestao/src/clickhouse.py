"""Persistência de lotes na tabela de ingestão do ClickHouse."""

import argparse
import json
import logging
from collections.abc import Iterable, Mapping
from datetime import date
from io import BytesIO
from typing import Any

import boto3
import clickhouse_connect

from src.config import config


logger = logging.getLogger(__name__)


class ClickHouse:
    def __init__(self, cliente: Any | None = None) -> None:
        self.cliente = cliente or clickhouse_connect.get_client(
            host=config.clickhouse_host,
            port=config.clickhouse_http_port,
            username=config.clickhouse_user,
            password=config.clickhouse_password,
            database=config.clickhouse_database,
            settings={"async_insert": config.clickhouse_async_insert},
        )

    def inserir(
        self,
        linhas: Iterable[Mapping[str, Any]],
        lote: str | None = None,
    ) -> int:
        linhas_lote = list(linhas)
        if not linhas_lote:
            return 0

        dados = []
        for linha in linhas_lote:
            valor_json = linha["data_json"]
            if not isinstance(valor_json, str):
                valor_json = json.dumps(
                    valor_json, ensure_ascii=False, separators=(",", ":")
                )
            dados.append(
                [int(linha["timestamp"]), valor_json, str(linha["data_tag"])]
            )

        self.cliente.insert(
            f"{config.clickhouse_database}.{config.clickhouse_tabela}",
            dados,
            column_names=["timestamp", "data_json", "data_tag"],
            settings={
                "async_insert": config.clickhouse_async_insert,
                "input_format_try_infer_dates": 0,
                "input_format_try_infer_datetimes": 0,
            },
        )
        logger.info(
            "lote=%s passo=clickhouse data_tag=%s tamanho=%d",
            lote or "sem_lote",
            ",".join(sorted({str(linha["data_tag"]) for linha in linhas_lote})),
            len(linhas_lote),
        )
        return len(linhas_lote)


def reprocessar(
    data_tag: str,
    dia: str,
    cliente_s3: Any | None = None,
    clickhouse: ClickHouse | None = None,
) -> int:
    """Reinsere no ClickHouse os Parquets da bronze de um domínio e dia."""
    if data_tag not in config.dominios:
        raise ValueError(f"data_tag fora de DOMINIOS: {data_tag}")
    try:
        dia_validado = date.fromisoformat(dia).isoformat()
    except ValueError as erro:
        raise ValueError("data deve estar no formato AAAA-MM-DD") from erro
    if dia_validado != dia:
        raise ValueError("data deve estar no formato AAAA-MM-DD")

    import pyarrow.parquet as parquet

    s3 = cliente_s3 or boto3.client(
        "s3",
        endpoint_url=config.s3_endpoint_url,
        region_name=config.s3_region,
        aws_access_key_id=config.s3_access_key,
        aws_secret_access_key=config.s3_secret_key,
    )
    destino = clickhouse or ClickHouse()
    prefixo = f"bronze/ingestao/data_tag={data_tag}/data={dia_validado}/"
    paginas = s3.get_paginator("list_objects_v2").paginate(
        Bucket=config.bucket_bronze,
        Prefix=prefixo,
    )
    total = 0
    try:
        for pagina in paginas:
            objetos = sorted(
                pagina.get("Contents", []), key=lambda item: item["Key"]
            )
            for objeto in objetos:
                chave = objeto["Key"]
                if not chave.endswith(".parquet"):
                    continue
                corpo = s3.get_object(Bucket=config.bucket_bronze, Key=chave)[
                    "Body"
                ].read()
                tabela = parquet.read_table(BytesIO(corpo))
                timestamps = tabela.column("timestamp").to_pylist()
                valores_json = tabela.column("data_json").to_pylist()
                linhas = [
                    {
                        "timestamp": int(timestamp),
                        "data_json": valor_json,
                        "data_tag": data_tag,
                    }
                    for timestamp, valor_json in zip(
                        timestamps, valores_json, strict=True
                    )
                ]
                nome_arquivo = chave.rsplit("/", 1)[-1]
                total += destino.inserir(
                    linhas, lote=f"reprocessamento:{nome_arquivo}"
                )
    finally:
        if clickhouse is None:
            destino.cliente.close()
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Operações na tabela de ingestão.")
    comandos = parser.add_subparsers(dest="comando", required=True)
    replay = comandos.add_parser(
        "reprocessar", help="reinsere no ClickHouse a bronze de um domínio e dia"
    )
    replay.add_argument("--data-tag", required=True)
    replay.add_argument("--data", required=True, help="dia no formato AAAA-MM-DD")
    argumentos = parser.parse_args()

    if argumentos.comando == "reprocessar":
        quantidade = reprocessar(argumentos.data_tag, argumentos.data)
        print(f"linhas_reprocessadas={quantidade}")


if __name__ == "__main__":
    main()
