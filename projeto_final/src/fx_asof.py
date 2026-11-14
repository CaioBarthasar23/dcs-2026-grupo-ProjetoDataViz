"""Converte preços da silver para BRL com ASOF JOIN do DuckDB.

A associação usa a última data de `cambio_diario` menor ou igual à data do
preço. Sem cotação anterior, `market_price_brl` e `data_ptax_usada` ficam nulos.

A cotação `compra` como padrão é decisão do aluno em 2026-11-14, hipótese com
validação pendente e ADR pendente. RF-08 e as demais seções da especificação
não definem se `cotacao_compra` ou `cotacao_venda` deve converter `market_price`.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Mapping, Sequence

import duckdb
import pyarrow as pa

Cotacao = Literal["compra", "venda"]

_PRECO_SCHEMA = pa.schema(
    [
        ("data", pa.date32()),
        ("product_id", pa.int32()),
        ("group_id", pa.int32()),
        ("acabamento", pa.string()),
        ("market_price", pa.float64()),
        ("low_price", pa.float64()),
        ("mid_price", pa.float64()),
        ("high_price", pa.float64()),
        ("moeda", pa.string()),
        ("fonte", pa.string()),
        ("chave_raw", pa.string()),
    ]
)
_CAMBIO_SCHEMA = pa.schema(
    [
        ("data", pa.date32()),
        ("cotacao_compra", pa.float64()),
        ("cotacao_venda", pa.float64()),
        ("data_hora_cotacao", pa.timestamp("us")),
        ("boletim", pa.string()),
        ("chave_raw", pa.string()),
    ]
)


def _arrow_table(rows: Sequence[Mapping[str, Any]], schema: pa.Schema) -> pa.Table:
    if not rows:
        return pa.Table.from_pylist([], schema=schema)
    # Deixe o Arrow preservar também colunas extras que possam existir no contrato.
    return pa.Table.from_pylist([dict(row) for row in rows])


def converter_precos(
    precos: Sequence[Mapping[str, Any]],
    cambios: Sequence[Mapping[str, Any]],
    cotacao: Cotacao = "compra",
) -> list[dict[str, Any]]:
    """Retorna linhas de preço com `market_price_brl` e `data_ptax_usada`.

    `precos` e `cambios` são registros nos contratos `preco_diario` e
    `cambio_diario` da silver. `cotacao` escolhe `cotacao_compra` (padrão) ou
    `cotacao_venda`; qualquer outro valor é recusado. A data da PTAX é inclusiva.

    A escolha de `compra` como padrão é decisão do aluno em 2026-11-14,
    hipótese com validação pendente e ADR pendente. RF-08 e as demais seções da
    especificação não definem qual cotação converterá `market_price`.
    """
    if cotacao not in ("compra", "venda"):
        raise ValueError("cotacao deve ser 'compra' ou 'venda'")

    tabela_precos = _arrow_table(precos, _PRECO_SCHEMA)
    tabela_cambios = _arrow_table(cambios, _CAMBIO_SCHEMA)
    coluna_cotacao = f"cotacao_{cotacao}"

    with duckdb.connect(database=":memory:") as con:
        con.register("precos", tabela_precos)
        con.register("cambios", tabela_cambios)
        rows = con.execute(
            f"""
            SELECT
                p.*,
                c.data AS data_ptax_usada,
                CASE
                    WHEN p.market_price IS NULL OR c.data IS NULL THEN NULL
                    ELSE p.market_price * c.{coluna_cotacao}
                END AS market_price_brl
            FROM precos AS p
            ASOF LEFT JOIN cambios AS c
                ON p.data >= c.data
            ORDER BY p.data, p.product_id, p.acabamento
            """
        ).to_arrow_table().to_pylist()
    return rows
