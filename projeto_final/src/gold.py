"""Constrói fatos e dimensões Gold em Parquet a partir da silver.

Tabelas persistidas sob `gold/group_id=23651/<tabela>.parquet`:
`fato_preco_diario`, `dim_produto`, `dim_colecao`, `dim_data`,
`dim_acabamento` e `fato_cambio_diario`. A camada escolhida para leitura e
escrita pode ser local ou S3. A reconstrução regrava as mesmas chaves, sem
apagar objetos.

A conversão USD/BRL reutiliza `src.fx_asof.converter_precos`; a taxa padrão é
`cotacao_compra` e valores sem PTAX anterior permanecem nulos.
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import sys
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from src import silver
from src.collector import GROUP_ID
from src.fx_asof import converter_precos
from src.prefixo import PREFIXO_PROPRIO, validar_chave

log = logging.getLogger("gold")

I32 = pa.int32()
F64 = pa.float64()
STR = pa.string()
DATE = pa.date32()
TIMESTAMP = pa.timestamp("us")

SCHEMAS = {
    "fato_preco_diario": pa.schema(
        [
            ("group_id", I32),
            ("product_id", I32),
            ("data", DATE),
            ("acabamento", STR),
            ("market_price", F64),
            ("low_price", F64),
            ("mid_price", F64),
            ("high_price", F64),
            ("moeda", STR),
            ("fonte", STR),
            ("chave_raw", STR),
            ("data_ptax_usada", DATE),
            ("market_price_brl", F64),
        ]
    ),
    "dim_produto": pa.schema(
        [
            ("group_id", I32),
            ("product_id", I32),
            ("nome", STR),
            ("tipo_produto", STR),
            ("raridade", STR),
            ("numero", STR),
            ("image_url", STR),
            ("url", STR),
            ("categoria_selado", STR),
        ]
    ),
    "dim_colecao": pa.schema(
        [
            ("group_id", I32),
            ("nome", STR),
            ("sigla", STR),
            ("data_lancamento", DATE),
            ("responsavel", STR),
        ]
    ),
    "dim_data": pa.schema([("data", DATE)]),
    "dim_acabamento": pa.schema([("acabamento", STR)]),
    "fato_cambio_diario": pa.schema(
        [
            ("data", DATE),
            ("cotacao_compra", F64),
            ("cotacao_venda", F64),
            ("data_hora_cotacao", TIMESTAMP),
            ("boletim", STR),
            ("chave_raw", STR),
        ]
    ),
}


def make_lake(tipo: str):
    """Reutiliza a implementação de armazenamento da silver."""
    return silver.make_lake(tipo)


def _ler_parquet(lake, key: str, *, obrigatorio: bool = True) -> list[dict[str, Any]]:
    validar_chave(key)
    payload = lake.get(key)
    if payload is None:
        if obrigatorio:
            raise FileNotFoundError(f"tabela silver ausente: {key}")
        return []
    return pq.read_table(io.BytesIO(payload)).to_pylist()


def _ler_silver(fonte, group_id: int) -> tuple[list, list, list, list]:
    colecoes = _ler_parquet(
        fonte, f"silver/colecao/group_id={group_id}/colecao.parquet"
    )
    produtos = _ler_parquet(
        fonte, f"silver/produto/group_id={group_id}/produto.parquet"
    )
    cambios = _ler_parquet(
        fonte,
        f"silver/cambio_diario/group_id={group_id}/cambio.parquet",
        obrigatorio=False,
    )

    precos = []
    prefix = f"silver/preco_diario/group_id={group_id}/"
    for dia in fonte.datas(prefix):
        key = f"{prefix}data={dia.isoformat()}/preco.parquet"
        precos.extend(_ler_parquet(fonte, key))
    return colecoes, produtos, precos, cambios


def _validar_group_id(colecoes, produtos, precos, group_id: int) -> None:
    for nome, registros in (
        ("colecao", colecoes),
        ("produto", produtos),
        ("preco_diario", precos),
    ):
        if any(row.get("group_id") != group_id for row in registros):
            raise ValueError(f"silver/{nome} contém registro fora de group_id={group_id}")


def _rows_to_bytes(tabela: str, rows: list[dict]) -> bytes:
    arrow = pa.Table.from_pylist(rows, schema=SCHEMAS[tabela])
    buf = io.BytesIO()
    pq.write_table(
        arrow,
        buf,
        compression="snappy",
        version="2.6",
        data_page_version="1.0",
        use_dictionary=False,
        write_statistics=False,
    )
    return buf.getvalue()


def _gold_key(tabela: str, group_id: int) -> str:
    """Monta a chave Gold no layout particionado por coleção."""
    return f"gold/group_id={group_id}/{tabela}.parquet"


def build(fonte, destino, group_id: int = GROUP_ID) -> dict[str, int]:
    """Lê a silver, monta o esquema estrela e grava as seis tabelas Parquet.

    `fonte` e `destino` implementam a interface de lake compartilhada com a
    silver. `group_id` é restrito à coleção SSP (23651). Todas as chaves de
    saída são validadas antes da leitura ou da primeira gravação.
    """
    if group_id != 23651:
        raise ValueError(
            f"ERRO escrita recusada: GROUP_ID={group_id} fora do prefixo {PREFIXO_PROPRIO}"
        )

    keys = {tabela: _gold_key(tabela, group_id) for tabela in SCHEMAS}
    for key in keys.values():
        validar_chave(key)

    colecoes, produtos, precos, cambios = _ler_silver(fonte, group_id)
    _validar_group_id(colecoes, produtos, precos, group_id)

    cambios = sorted(cambios, key=lambda row: row["data"])
    precos_convertidos = converter_precos(precos, cambios)

    dim_produto = sorted(
        ({key: row.get(key) for key in SCHEMAS["dim_produto"].names} for row in produtos),
        key=lambda row: (row["group_id"], row["product_id"]),
    )
    dim_colecao = sorted(
        ({key: row.get(key) for key in SCHEMAS["dim_colecao"].names} for row in colecoes),
        key=lambda row: row["group_id"],
    )
    fato_preco = [
        {key: row.get(key) for key in SCHEMAS["fato_preco_diario"].names}
        for row in precos_convertidos
    ]
    fato_cambio = [
        {key: row.get(key) for key in SCHEMAS["fato_cambio_diario"].names}
        for row in cambios
    ]
    datas = sorted(
        {row["data"] for row in precos}
        | {row["data"] for row in cambios}
        | {row["data_ptax_usada"] for row in precos_convertidos if row["data_ptax_usada"]}
    )
    acabamentos = sorted({row["acabamento"] for row in precos if row.get("acabamento") is not None})

    tables = {
        "fato_preco_diario": fato_preco,
        "dim_produto": dim_produto,
        "dim_colecao": dim_colecao,
        "dim_data": [{"data": dia} for dia in datas],
        "dim_acabamento": [{"acabamento": value} for value in acabamentos],
        "fato_cambio_diario": fato_cambio,
    }
    for tabela, rows in tables.items():
        validar_chave(keys[tabela])
        destino.put(keys[tabela], _rows_to_bytes(tabela, rows))
        log.info("gold %-22s linhas=%d", tabela, len(rows))
    return {tabela: len(rows) for tabela, rows in tables.items()}


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("comando", choices=["build"])
    ap.add_argument("--fonte", choices=["local", "s3"], default="local")
    ap.add_argument("--destino", choices=["local", "s3"], default="local")
    args = ap.parse_args(argv)

    group_id_configurado = os.getenv("GROUP_ID", "23651")
    try:
        group_id_numerico = int(group_id_configurado)
    except ValueError:
        log.error(
            "ERRO escrita recusada: GROUP_ID=%s inválido; prefixo permitido %s",
            group_id_configurado,
            PREFIXO_PROPRIO,
        )
        return 1
    if group_id_numerico != 23651 or GROUP_ID != 23651:
        log.error(
            "ERRO escrita recusada: GROUP_ID=%s fora do prefixo %s",
            group_id_configurado,
            PREFIXO_PROPRIO,
        )
        return 1

    build(make_lake(args.fonte), make_lake(args.destino), group_id=GROUP_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
