"""Decompõe a variação de preço em BRL entre duas datas.

Os retornos são frações (por exemplo, 0.10 representa 10%). A taxa de câmbio
efetivamente usada em cada ponta é recuperada de market_price_brl /
market_price; data_ptax_usada identifica a PTAX resolvida previamente no fato.
"""
from __future__ import annotations

from datetime import date
from math import isfinite
from typing import Any, Mapping, Sequence


MOTIVOS_EXCLUSAO = (
    "abaixo_limiar_inicio",
    "sem_preco_inicio",
    "sem_preco_fim",
    "ptax_ausente",
    "preco_usd_zero",
)


def decompor_variacao(
    fato_preco_diario: Sequence[Mapping[str, Any]],
    dim_produto: Sequence[Mapping[str, Any]],
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    limite_usd: float = 1.0,
) -> dict[str, Any]:
    """Calcula variações elegíveis e contagens de exclusão por motivo.

    Sem datas, usa a primeira e a última data presentes no fato. As datas
    explícitas são inclusivas e devem ser fornecidas em conjunto. Cada
    combinação carta/acabamento observada no intervalo é comparada nas duas
    datas exatas; uma linha ausente não é substituída por outra data.
    """
    if not isfinite(limite_usd):
        raise ValueError("limite_usd deve ser finito")
    if (data_inicio is None) != (data_fim is None):
        raise ValueError("data_inicio e data_fim devem ser fornecidas juntas")

    fact_rows = list(fato_preco_diario)
    if data_inicio is None:
        if not fact_rows:
            raise ValueError("fato_preco_diario vazio: não há período para calcular")
        data_inicio = min(row["data"] for row in fact_rows)
        data_fim = max(row["data"] for row in fact_rows)
    if data_inicio > data_fim:
        raise ValueError("data_inicio deve ser anterior ou igual a data_fim")

    produtos = {
        row["product_id"]: row
        for row in dim_produto
        if row.get("tipo_produto") == "carta"
        and row.get("raridade") != "Code Card"
    }
    por_chave: dict[tuple[Any, Any, date], Mapping[str, Any]] = {}
    pares: set[tuple[Any, Any]] = set()
    for row in fact_rows:
        product_id = row.get("product_id")
        dia = row.get("data")
        if product_id not in produtos or not data_inicio <= dia <= data_fim:
            continue
        chave = (product_id, row.get("acabamento"), dia)
        if chave in por_chave:
            raise ValueError(
                "mais de uma linha de fato para product_id, acabamento e data: "
                f"{chave}"
            )
        por_chave[chave] = row
        pares.add((product_id, row.get("acabamento")))

    excluidas = {motivo: 0 for motivo in MOTIVOS_EXCLUSAO}
    resultados = []
    for product_id, acabamento in sorted(pares, key=lambda item: (item[0], str(item[1]))):
        inicio = por_chave.get((product_id, acabamento, data_inicio))
        fim = por_chave.get((product_id, acabamento, data_fim))

        preco_inicio = inicio.get("market_price") if inicio else None
        preco_fim = fim.get("market_price") if fim else None

        if (preco_inicio is not None and preco_inicio == 0) or (
            preco_fim is not None and preco_fim == 0
        ):
            excluidas["preco_usd_zero"] += 1
            continue
        if inicio is None or preco_inicio is None:
            excluidas["sem_preco_inicio"] += 1
            continue
        if preco_inicio <= limite_usd:
            excluidas["abaixo_limiar_inicio"] += 1
            continue
        if fim is None or preco_fim is None:
            excluidas["sem_preco_fim"] += 1
            continue

        brl_inicio = inicio.get("market_price_brl")
        brl_fim = fim.get("market_price_brl")
        ptax_inicio = inicio.get("data_ptax_usada")
        ptax_fim = fim.get("data_ptax_usada")
        if (
            brl_inicio is None
            or brl_fim is None
            or ptax_inicio is None
            or ptax_fim is None
        ):
            excluidas["ptax_ausente"] += 1
            continue

        r_usd = preco_fim / preco_inicio - 1
        cambio_inicio = brl_inicio / preco_inicio
        cambio_fim = brl_fim / preco_fim
        r_cambio = cambio_fim / cambio_inicio - 1
        r_brl = brl_fim / brl_inicio - 1
        efeito_cruzado = r_usd * r_cambio

        resultados.append(
            {
                "product_id": product_id,
                "acabamento": acabamento,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "data_ptax_inicio": ptax_inicio,
                "data_ptax_fim": ptax_fim,
                "market_price_inicio_usd": preco_inicio,
                "market_price_fim_usd": preco_fim,
                "market_price_inicio_brl": brl_inicio,
                "market_price_fim_brl": brl_fim,
                "r_usd": r_usd,
                "r_cambio": r_cambio,
                "r_brl": r_brl,
                "efeito_carta": r_usd,
                "efeito_cambio": r_cambio,
                "efeito_cruzado": efeito_cruzado,
            }
        )

    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "resultados": resultados,
        "excluidas": excluidas,
    }
