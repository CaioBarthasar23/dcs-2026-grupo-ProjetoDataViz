"""Calcula concentração do valor da coleção no último dia."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any, Mapping, Sequence


def _decimal(value: Any, nome: str) -> Decimal:
    if value is None:
        raise ValueError(f"{nome} nulo")
    try:
        if isinstance(value, float) and not isfinite(value):
            raise ValueError(f"{nome} deve ser finito")
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{nome} deve ser um número decimal válido")


def _product_id_sort(product_id: Any) -> tuple[int, Any]:
    if isinstance(product_id, int):
        return (0, product_id)
    try:
        return (0, int(product_id))
    except (TypeError, ValueError):
        return (1, str(product_id))


def calcular_concentracao_valor(
    fato_preco_diario: Sequence[Mapping[str, Any]],
    dim_produto: Sequence[Mapping[str, Any]],
    *,
    moeda: str = "brl",
    limite: float | Decimal | str | None = None,
    percentual: float | Decimal | str | None = None,
) -> dict[str, Any]:
    """Retorna valor total, concentração por raridade e cobertura no último dia."""
    if moeda not in ("brl", "usd"):
        raise ValueError("moeda deve ser 'brl' ou 'usd'")

    if limite is not None and percentual is not None:
        limite_decimal = _decimal(limite, "limite")
        percentual_decimal = _decimal(percentual, "percentual")
        if limite_decimal != percentual_decimal:
            raise ValueError("limite e percentual devem representar o mesmo valor")
    elif limite is not None:
        limite_decimal = _decimal(limite, "limite")
    elif percentual is not None:
        limite_decimal = _decimal(percentual, "percentual")
    else:
        limite_decimal = Decimal("0.8")

    if limite_decimal <= 0 or limite_decimal > 1:
        raise ValueError("limite/percentual deve estar no intervalo (0, 1]")

    fatos = [dict(row) for row in fato_preco_diario]
    produtos_linhas = [dict(row) for row in dim_produto]
    todas_linhas = fatos + produtos_linhas
    grupos = {
        row["group_id"]
        for row in todas_linhas
        if row.get("group_id") is not None
    }
    if len(grupos) > 1:
        raise ValueError("as linhas misturam mais de um group_id")

    vistos: set[tuple[Any, Any, Any]] = set()
    for row in fatos:
        chave = (
            row.get("product_id"),
            row.get("acabamento"),
            row.get("data"),
        )
        if chave in vistos:
            raise ValueError(
                "linha duplicada para (produto, acabamento, data): "
                f"{chave}"
            )
        vistos.add(chave)

    if not fatos:
        raise ValueError("não há datas no fato_preco_diario")

    datas = sorted({row["data"] for row in fatos if row.get("data") is not None})
    if not datas:
        raise ValueError("não há datas no fato_preco_diario")

    primeira_data = datas[0]
    ultima_data = datas[-1]
    data_referencia = max(row["data"] for row in fatos)
    coluna_preco = "market_price_brl" if moeda == "brl" else "market_price"

    produtos: dict[Any, Mapping[str, Any]] = {}
    for row in produtos_linhas:
        product_id = row.get("product_id")
        if product_id in produtos:
            raise ValueError(f"produto duplicado product_id={product_id}")
        produtos[product_id] = row

    valores_por_carta: list[tuple[Any, Decimal]] = []
    acabamentos_escolhidos: dict[Any, str] = {}
    quantity_excluded = 0

    for product_id in sorted(produtos, key=_product_id_sort):
        produto = produtos[product_id]
        if produto.get("tipo_produto") != "carta":
            continue
        if produto.get("raridade") == "Code Card":
            continue

        candidatos = []
        for row in fatos:
            if row.get("product_id") != product_id:
                continue
            if row.get("data") != data_referencia:
                continue
            preco = row.get(coluna_preco)
            if preco is None:
                continue
            valor = _decimal(preco, f"{coluna_preco} de product_id={product_id}")
            acabamento = row.get("acabamento")
            candidatos.append((valor, str(acabamento or ""), row))

        if not candidatos:
            quantity_excluded += 1
            continue

        _valor, _acabamento, escolhido = min(
            candidatos,
            key=lambda candidato: (candidato[0], candidato[1]),
        )
        valor_escolhido = _decimal(
            escolhido[coluna_preco],
            f"{coluna_preco} de product_id={product_id}",
        )
        valores_por_carta.append((product_id, valor_escolhido))
        acabamentos_escolhidos[product_id] = str(escolhido.get("acabamento") or "")

    if not valores_por_carta:
        raise ValueError("nenhuma carta elegível com preço no último dia")

    valor_total_decimal = sum(
        (valor for _product_id, valor in valores_por_carta),
        Decimal("0"),
    )
    if valor_total_decimal == 0:
        raise ValueError("valor total é zero")

    valores_por_raridade: dict[str, dict[str, Any]] = {}
    for product_id, valor in valores_por_carta:
        raridade = produtos[product_id].get("raridade")
        nome = "sem raridade" if raridade is None else str(raridade)
        agregacao = valores_por_raridade.setdefault(
            nome,
            {"valor": Decimal("0"), "quantidade": 0},
        )
        agregacao["valor"] += valor
        agregacao["quantidade"] += 1

    participacao_por_raridade = []
    for nome, agregacao in valores_por_raridade.items():
        valor = agregacao["valor"]
        participacao_decimal = valor / valor_total_decimal
        participacao_por_raridade.append(
            {
                "raridade": nome,
                "valor": float(valor),
                "participacao": float(participacao_decimal),
                "quantidade_cartas": agregacao["quantidade"],
                "_participacao_decimal": participacao_decimal,
            }
        )
    participacao_por_raridade.sort(
        key=lambda row: (-row["_participacao_decimal"], row["raridade"])
    )
    for row in participacao_por_raridade:
        del row["_participacao_decimal"]

    acumulado = Decimal("0")
    limite_decimal_total = valor_total_decimal * limite_decimal
    quantidade_cartas_limite = 0
    for _product_id, valor in sorted(
        valores_por_carta,
        key=lambda item: (-item[1], _product_id_sort(item[0]))
    ):
        acumulado += valor
        quantidade_cartas_limite += 1
        if acumulado >= limite_decimal_total:
            break

    return {
        "data_referencia": data_referencia,
        "moeda": moeda,
        "valor_total": float(valor_total_decimal),
        "quantidade_cartas": len(valores_por_carta),
        "quantidade_excluidas": quantity_excluded,
        "participacao_por_raridade": participacao_por_raridade,
        "acabamentos_escolhidos": dict(sorted(acabamentos_escolhidos.items())),
        "limite": float(limite_decimal),
        "quantidade_cartas_limite": quantidade_cartas_limite,
        "cobertura": {
            "primeira_data": primeira_data,
            "ultima_data": ultima_data,
            "quantidade_datas": len(datas),
        },
    }
