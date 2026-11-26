"""Preparação pura do ranking da pergunta 1."""
from __future__ import annotations

from datetime import date
from typing import Any, Literal, Mapping, Sequence

from src.decomposicao import decompor_variacao

from dashboard.common import RARIDADE_CODE_CARD


def _chave_product_id(value: Any) -> tuple[int, Any]:
    try:
        return (0, int(value))
    except (TypeError, ValueError):
        return (1, str(value))


def preparar_ranking_p1(
    fato_preco_diario: Sequence[Mapping[str, Any]],
    dim_produto: Sequence[Mapping[str, Any]],
    *,
    moeda: Literal["brl", "usd"] = "brl",
    limite_usd: float = 1.0,
    tamanho: int = 10,
) -> dict[str, Any]:
    """Prepara altas e quedas por variação percentual sem modificar as entradas."""
    if moeda not in ("brl", "usd"):
        raise ValueError("moeda deve ser 'brl' ou 'usd'")
    if tamanho < 1:
        raise ValueError("tamanho deve ser positivo")
    fatos = [dict(row) for row in fato_preco_diario]
    produtos = [dict(row) for row in dim_produto]
    if not fatos:
        return {
            "data_inicio": None, "data_fim": None, "maiores_altas": [],
            "maiores_quedas": [], "quantidade_comparacoes": 0, "excluidas": {
                "filtro_usd_1": 0, "preco_inicial_nulo": 0,
                "preco_final_nulo": 0, "code_card": 0,
            },
        }

    data_inicio = min(row["data"] for row in fatos)
    data_fim = max(row["data"] for row in fatos)
    produtos_por_id = {row["product_id"]: row for row in produtos}
    code_ids = {
        product_id for product_id, produto in produtos_por_id.items()
        if produto.get("raridade") == RARIDADE_CODE_CARD
    }
    cartas = {
        product_id: produto for product_id, produto in produtos_por_id.items()
        if produto.get("tipo_produto") == "carta" and product_id not in code_ids
    }

    pontos: dict[tuple[Any, Any, date], Mapping[str, Any]] = {}
    pares: set[tuple[Any, Any]] = set()
    for row in fatos:
        if row["data"] < data_inicio or row["data"] > data_fim:
            continue
        chave = (row["product_id"], row.get("acabamento"), row["data"])
        pontos[chave] = row
        pares.add(chave[:2])

    excluidas = {
        "filtro_usd_1": 0,
        "preco_inicial_nulo": 0,
        "preco_final_nulo": 0,
        "code_card": len({product_id for product_id in code_ids if any(p[0] == product_id for p in pares)}),
    }
    elegiveis_usd: list[dict[str, Any]] = []
    for product_id, acabamento in sorted(pares, key=lambda p: (_chave_product_id(p[0]), str(p[1] or ""))):
        if product_id in code_ids or product_id not in cartas:
            continue
        inicio = pontos.get((product_id, acabamento, data_inicio))
        fim = pontos.get((product_id, acabamento, data_fim))
        preco_inicio = inicio.get("market_price") if inicio else None
        preco_fim = fim.get("market_price") if fim else None
        if preco_inicio is None:
            excluidas["preco_inicial_nulo"] += 1
            continue
        if preco_inicio <= limite_usd:
            excluidas["filtro_usd_1"] += 1
            continue
        if preco_fim is None:
            excluidas["preco_final_nulo"] += 1
            continue
        variacao_usd = preco_fim - preco_inicio
        pct_usd = variacao_usd / preco_inicio
        produto = cartas[product_id]
        elegiveis_usd.append({
            "product_id": product_id, "acabamento": acabamento,
            "market_price_inicio_usd": preco_inicio, "market_price_fim_usd": preco_fim,
            "variacao_usd": variacao_usd, "variacao_brl": None,
            "variacao_percentual_usd": pct_usd, "variacao_percentual": pct_usd,
            "efeito_carta": pct_usd, "efeito_cambio": None, "efeito_cruzado": None,
            "rotulo_efeito_cambio": "não se aplica", "rotulo_efeito_cruzado": "não se aplica",
            "image_url": produto.get("image_url"), "url": produto.get("url"),
        })

    # RF-10 continua sendo a fonte do cálculo e da validação aditiva em BRL.
    decomposicao = decompor_variacao(
        fatos,
        list(cartas.values()),
        data_inicio=data_inicio,
        data_fim=data_fim,
        limite_usd=limite_usd,
    )
    brl_por_par = {
        (row["product_id"], row["acabamento"]): row
        for row in decomposicao["resultados"]
    }
    rows_brl: list[dict[str, Any]] = []
    for row_usd in elegiveis_usd:
        key = (row_usd["product_id"], row_usd["acabamento"])
        dec = brl_por_par.get(key)
        if dec is None:
            continue
        inicio = pontos[(key[0], key[1], data_inicio)]
        fim = pontos[(key[0], key[1], data_fim)]
        brl_inicio, brl_fim = inicio.get("market_price_brl"), fim.get("market_price_brl")
        if brl_inicio is None or brl_fim is None:
            continue
        rows_brl.append({
            **row_usd,
            "market_price_inicio_brl": brl_inicio,
            "market_price_fim_brl": brl_fim,
            "variacao_brl": brl_fim - brl_inicio,
            "variacao_percentual": dec["r_brl"],
            "r_brl": dec["r_brl"],
            "efeito_carta": dec["efeito_carta"],
            "efeito_cambio": dec["efeito_cambio"],
            "efeito_cruzado": dec["efeito_cruzado"],
            "rotulo_efeito_cambio": None,
            "rotulo_efeito_cruzado": None,
        })

    selected = elegiveis_usd if moeda == "usd" else rows_brl
    # RF-10/RF-11: o ranking usa a variação percentual; a absoluta segue no retorno.
    highs = sorted(selected, key=lambda row: (
        -row["variacao_percentual"],
        _chave_product_id(row["product_id"]), str(row["acabamento"] or ""),
    ))[:tamanho]
    lows = sorted(selected, key=lambda row: (
        row["variacao_percentual"],
        _chave_product_id(row["product_id"]), str(row["acabamento"] or ""),
    ))[:tamanho]
    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "maiores_altas": highs,
        "maiores_quedas": lows,
        "quantidade_comparacoes": len(selected),
        "excluidas": excluidas,
    }
