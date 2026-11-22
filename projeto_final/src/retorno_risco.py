"""Calcula retorno no período e risco diário das séries de preço."""
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


def _desvio_amostral(retornos: list[Decimal]) -> float | None:
    if len(retornos) < 2:
        return None
    media = sum(retornos, Decimal("0")) / Decimal(len(retornos))
    soma_quadrados = sum(
        ((retorno - media) ** 2 for retorno in retornos),
        Decimal("0"),
    )
    variancia = soma_quadrados / Decimal(len(retornos) - 1)
    return float(variancia.sqrt())


def calcular_retorno_risco(
    fato_preco_diario: Sequence[Mapping[str, Any]],
    dim_produto: Sequence[Mapping[str, Any]],
    *,
    moeda: str = "brl",
    preco_minimo_usd: float | Decimal | str = 5,
    minimo_observacoes: int = 2,
) -> dict[str, Any]:
    """Retorna retorno no período e desvio amostral dos retornos consecutivos."""
    if moeda not in ("brl", "usd"):
        raise ValueError("moeda deve ser 'brl' ou 'usd'")
    if not isinstance(minimo_observacoes, int) or minimo_observacoes < 1:
        raise ValueError("minimo_observacoes deve ser um inteiro maior ou igual a 1")

    limite_decimal = _decimal(preco_minimo_usd, "preco_minimo_usd")
    if not limite_decimal.is_finite():
        raise ValueError("preco_minimo_usd deve ser finito")

    fatos = [dict(row) for row in fato_preco_diario]
    produtos_linhas = [dict(row) for row in dim_produto]
    grupos = {
        row["group_id"]
        for row in fatos + produtos_linhas
        if row.get("group_id") is not None
    }
    if len(grupos) > 1:
        raise ValueError("as linhas misturam mais de um group_id")

    vistos: set[tuple[Any, Any, Any]] = set()
    for row in fatos:
        chave = (row.get("product_id"), row.get("acabamento"), row.get("data"))
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
    coluna_preco = "market_price_brl" if moeda == "brl" else "market_price"

    produtos: dict[Any, Mapping[str, Any]] = {}
    for row in produtos_linhas:
        product_id = row.get("product_id")
        if product_id in produtos:
            raise ValueError(f"produto duplicado product_id={product_id}")
        produtos[product_id] = row

    exclusoes_por_motivo = {
        "sem_preco_no_primeiro_dia": 0,
        "sem_preco_no_ultimo_dia": 0,
        "preco_inicial_nao_maior_que_minimo": 0,
    }
    series_excluidas: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []

    pares = sorted(
        {
            (row["product_id"], row["acabamento"])
            for row in fatos
            if row.get("product_id") is not None
            and row.get("acabamento") is not None
        },
        key=lambda par: (_product_id_sort(par[0]), str(par[1]))
    )

    for product_id, acabamento in pares:
        produto = produtos.get(product_id)
        if produto is None or produto.get("tipo_produto") != "carta":
            continue

        linhas_por_data = {
            row["data"]: row
            for row in fatos
            if row.get("product_id") == product_id
            and row.get("acabamento") == acabamento
            and row.get("data") is not None
        }

        linha_inicial = linhas_por_data.get(primeira_data)
        linha_final = linhas_por_data.get(ultima_data)
        preco_usd_inicial = (
            linha_inicial.get("market_price")
            if linha_inicial is not None
            else None
        )
        preco_escolhido_inicial = (
            linha_inicial.get(coluna_preco)
            if linha_inicial is not None
            else None
        )
        preco_escolhido_final = (
            linha_final.get(coluna_preco)
            if linha_final is not None
            else None
        )

        motivo: str | None = None
        if preco_usd_inicial is not None:
            usd_inicial = _decimal(
                preco_usd_inicial,
                f"market_price de product_id={product_id}",
            )
            elegivel_por_minimo = usd_inicial > limite_decimal
        else:
            elegivel_por_minimo = False

        if preco_escolhido_inicial is None:
            motivo = "sem_preco_no_primeiro_dia"
        elif preco_escolhido_final is None:
            motivo = "sem_preco_no_ultimo_dia"
        elif not elegivel_por_minimo:
            motivo = "preco_inicial_nao_maior_que_minimo"

        if motivo is not None:
            exclusoes_por_motivo[motivo] += 1
            series_excluidas.append(
                {
                    "product_id": product_id,
                    "acabamento": acabamento,
                    "motivo": motivo,
                }
            )
            continue

        inicial = _decimal(
            preco_escolhido_inicial,
            f"{coluna_preco} inicial de product_id={product_id}",
        )
        final = _decimal(
            preco_escolhido_final,
            f"{coluna_preco} final de product_id={product_id}",
        )
        retorno_periodo = final / inicial - Decimal("1")

        retornos: list[Decimal] = []
        for anterior, atual in zip(datas, datas[1:]):
            linha_anterior = linhas_por_data.get(anterior)
            linha_atual = linhas_por_data.get(atual)
            if linha_anterior is None or linha_atual is None:
                continue
            valor_anterior = linha_anterior.get(coluna_preco)
            valor_atual = linha_atual.get(coluna_preco)
            if valor_anterior is None or valor_atual is None:
                continue
            anterior_decimal = _decimal(
                valor_anterior,
                f"{coluna_preco} de product_id={product_id}",
            )
            atual_decimal = _decimal(
                valor_atual,
                f"{coluna_preco} de product_id={product_id}",
            )
            if anterior_decimal == 0:
                continue
            retornos.append(atual_decimal / anterior_decimal - Decimal("1"))

        desvio = (
            _desvio_amostral(retornos)
            if len(retornos) >= minimo_observacoes
            else None
        )
        raridade = produto.get("raridade")
        series.append(
            {
                "product_id": product_id,
                "acabamento": acabamento,
                "raridade": None if raridade is None else str(raridade),
                "code_card": raridade == "Code Card",
                "preco_inicial": float(inicial),
                "preco_final": float(final),
                "retorno_no_periodo": float(retorno_periodo),
                "desvio_padrao_retornos_diarios": desvio,
                "quantidade_retornos": len(retornos),
            }
        )

    if not series:
        raise ValueError("nenhuma série elegível")

    return {
        "data_inicial": primeira_data,
        "data_final": ultima_data,
        "moeda": moeda,
        "preco_minimo_usado": float(limite_decimal),
        "quantidade_series_elegiveis": len(series),
        "quantidade_series_excluidas": len(series_excluidas),
        "exclusoes_por_motivo": exclusoes_por_motivo,
        "series_excluidas": series_excluidas,
        "series": series,
        "cobertura": {
            "primeira_data": primeira_data,
            "ultima_data": ultima_data,
            "quantidade_datas": len(datas),
        },
    }
