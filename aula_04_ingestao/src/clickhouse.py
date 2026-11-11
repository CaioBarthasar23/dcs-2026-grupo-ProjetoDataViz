"""Persistência de lotes na tabela de ingestão do ClickHouse."""

import json
import logging
from collections.abc import Iterable, Mapping
from typing import Any

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
