"""Confere contagens de entrada, ClickHouse e lake sem consumir a fila."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import boto3
import clickhouse_connect
import pyarrow.parquet as pq
import pyarrow as pa
import requests

from src.config import config


def _linhas_jsonl(padrao: str) -> int:
    total = 0
    for arquivo in Path(".").glob(padrao):
        with arquivo.open(encoding="utf-8") as entrada:
            total += sum(bool(linha.strip()) for linha in entrada)
    return total


def contar_esperadas() -> dict[str, int]:
    esperadas = {"livros": _linhas_jsonl("entrada/livros/*.jsonl")}
    esperadas["ptax"] = 0
    for arquivo in Path("entrada/ptax").glob("*.jsonl"):
        with arquivo.open(encoding="utf-8") as entrada:
            esperadas["ptax"] += sum(bool(linha.strip()) for linha in entrada)
    esperadas["telemetria"] = _linhas_jsonl("entrada/telemetria/*.txt")
    return esperadas


def _cliente_s3() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=config.s3_endpoint_url,
        region_name=config.s3_region,
        aws_access_key_id=config.s3_access_key,
        aws_secret_access_key=config.s3_secret_key,
    )


def contar_lake(s3: Any, tags: list[str]) -> tuple[dict[str, int], dict[str, int]]:
    raw = dict.fromkeys(tags, 0)
    bronze = dict.fromkeys(tags, 0)
    for tag in tags:
        prefixo_raw = f"raw/ingestao/data_tag={tag}/"
        for pagina in s3.get_paginator("list_objects_v2").paginate(
            Bucket=config.bucket_raw, Prefix=prefixo_raw
        ):
            for objeto in pagina.get("Contents", []):
                resposta = s3.get_object(Bucket=config.bucket_raw, Key=objeto["Key"])
                corpo = resposta["Body"].read()
                raw[tag] += sum(1 for linha in corpo.splitlines() if linha.strip())

        prefixo_bronze = f"bronze/ingestao/data_tag={tag}/"
        for pagina in s3.get_paginator("list_objects_v2").paginate(
            Bucket=config.bucket_bronze, Prefix=prefixo_bronze
        ):
            for objeto in pagina.get("Contents", []):
                resposta = s3.get_object(
                    Bucket=config.bucket_bronze, Key=objeto["Key"]
                )
                parquet = pq.read_table(pa.BufferReader(resposta["Body"].read()))
                bronze[tag] += parquet.num_rows
    return raw, bronze


def contar_clickhouse(tags: list[str]) -> dict[str, tuple[int, int]]:
    cliente = clickhouse_connect.get_client(
        host=config.clickhouse_host,
        port=config.clickhouse_http_port,
        username=config.clickhouse_user,
        password=config.clickhouse_password,
        database=config.clickhouse_database,
    )
    tabela = f"{config.clickhouse_database}.{config.clickhouse_tabela}"
    resultados: dict[str, tuple[int, int]] = {}
    try:
        for tag in tags:
            tag_sql = tag.replace("'", "''")
            total, distintos = cliente.query(
                "SELECT count(), uniqExact(tuple(timestamp, toJSONString(data_json))) "
                f"FROM {tabela} WHERE data_tag = '{tag_sql}'"
            ).result_rows[0]
            resultados[tag] = (int(total), int(distintos))
    finally:
        cliente.close()
    return resultados


def contar_manifestos(s3: Any) -> dict[str, dict[str, int]]:
    por_status: dict[str, dict[str, int]] = defaultdict(
        lambda: {"manifestos": 0, "linhas": 0}
    )
    for pagina in s3.get_paginator("list_objects_v2").paginate(
        Bucket=config.bucket_raw, Prefix="raw/_manifestos/ingestao/"
    ):
        for objeto in pagina.get("Contents", []):
            resposta = s3.get_object(Bucket=config.bucket_raw, Key=objeto["Key"])
            manifesto = json.loads(resposta["Body"].read())
            status = str(manifesto.get("status", "sem_status"))
            agregado = por_status[status]
            agregado["manifestos"] += 1
            agregado["linhas"] += sum(
                int(valor)
                for valor in manifesto.get("linhas_por_data_tag", {}).values()
            )
    return dict(por_status)


def estado_fila() -> dict[str, int]:
    url = (
        f"http://{config.rabbitmq_host}:{config.rabbitmq_ui_port}/api/queues/%2F/"
        f"{quote(config.fila_ingestao, safe='')}"
    )
    resposta = requests.get(
        url,
        auth=(config.rabbitmq_user, config.rabbitmq_password or ""),
        timeout=10,
    )
    resposta.raise_for_status()
    fila = resposta.json()
    return {
        "mensagens": int(fila.get("messages", 0)),
        "prontas": int(fila.get("messages_ready", 0)),
        "sem_ack": int(fila.get("messages_unacknowledged", 0)),
    }


def conferir() -> None:
    esperadas = contar_esperadas()
    tags = list(esperadas)
    s3 = _cliente_s3()
    raw, bronze = contar_lake(s3, tags)
    clickhouse = contar_clickhouse(tags)

    print("data_tag       esperadas  clickhouse  bronze  raw_envelopes  distintas")
    for tag in tags:
        total_ch, distintas = clickhouse[tag]
        print(
            f"{tag:<14} {esperadas[tag]:>9} {total_ch:>11} {bronze[tag]:>7} "
            f"{raw[tag]:>14} {distintas:>11}"
        )

    print("manifestos por status:")
    for status, valores in sorted(contar_manifestos(s3).items()):
        print(
            f"  {status}: {valores['manifestos']} manifestos, "
            f"{valores['linhas']} linhas"
        )
    fila = estado_fila()
    print(
        "fila: mensagens={mensagens}, prontas={prontas}, sem_ack={sem_ack}".format(
            **fila
        )
    )


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    conferir()


if __name__ == "__main__":
    main()
