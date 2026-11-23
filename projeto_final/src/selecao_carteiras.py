"""Seleção pura das carteiras usando somente dados do primeiro dia da silver."""
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _validar_grupos(
    preco_diario: Sequence[Mapping[str, Any]],
    produto: Sequence[Mapping[str, Any]],
    cambio_diario: Sequence[Mapping[str, Any]],
) -> None:
    grupos = {
        row["group_id"]
        for row in list(preco_diario) + list(produto) + list(cambio_diario)
        if row.get("group_id") is not None
    }
    if len(grupos) > 1:
        raise ValueError("as linhas misturam mais de um group_id")


def _ptax_asof(
    cambio_diario: Sequence[Mapping[str, Any]],
    data: Any,
) -> tuple[Decimal, Any]:
    candidatos = [
        row
        for row in cambio_diario
        if row.get("data") is not None
        and row["data"] <= data
        and row.get("cotacao_venda") is not None
    ]
    if not candidatos:
        raise ValueError("não há PTAX de venda anterior ou igual ao primeiro dia")
    escolhido = max(candidatos, key=lambda row: row["data"])
    ptax = _decimal(escolhido["cotacao_venda"])
    if ptax is None:
        raise ValueError("PTAX de venda nula")
    return ptax, escolhido["data"]


def _custo_brl(unidades: int, market_price: Decimal, ptax: Decimal) -> Decimal:
    return (Decimal(unidades) * market_price * ptax).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def selecionar_carteiras(
    preco_diario: Sequence[Mapping[str, Any]],
    produto: Sequence[Mapping[str, Any]],
    cambio_diario: Sequence[Mapping[str, Any]],
    *,
    capital_brl: Decimal = Decimal("1000"),
    limite_selado_brl: Decimal = Decimal("1000"),
    limite_cesta_carta_brl: Decimal = Decimal("100"),
    metade_propria_brl: Decimal = Decimal("500"),
    quantidade_cesta_raras: int = 10,
) -> dict[str, Any]:
    """Seleciona as carteiras sem rede ou alteração das entradas.

    preco_diario usa as colunas da silver: data, product_id, group_id,
    acabamento e market_price (USD). produto usa product_id, group_id,
    tipo_produto e raridade. cambio_diario usa data, cotacao_venda e
    cotacao_compra da silver. Os preços em USD são convertidos de float para
    Decimal por str(). A cotacao_venda é associada por ASOF. A propria usa
    2 × metade_propria_brl como base das duas metades, não capital_brl.
    Cada carteira considera todas as linhas elegíveis (product_id, acabamento)
    do primeiro dia; por product_id mantém o maior market_price elegível e,
    em empate, o menor nome de acabamento (hipótese, validação pendente).
    Menos de 10 cartas elegíveis na cesta deixa o resto em caixa (hipótese,
    validação pendente). A divisão 50/50 da propria também é hipótese,
    validação pendente. Exige pelo menos um market_price não nulo em
    preco_diario; sem ele, lança ValueError com essa causa.
    """
    precos = [dict(row) for row in preco_diario]
    produtos = [dict(row) for row in produto]
    cambios = [dict(row) for row in cambio_diario]
    _validar_grupos(precos, produtos, cambios)

    datas_com_preco = sorted({
        row["data"]
        for row in precos
        if row.get("data") is not None and row.get("market_price") is not None
    })
    if not datas_com_preco:
        raise ValueError("não há primeiro dia com market_price não nulo")
    data_inicial = datas_com_preco[0]
    ptax, data_ptax = _ptax_asof(cambios, data_inicial)

    produtos_por_id: dict[Any, Mapping[str, Any]] = {}
    for row in produtos:
        product_id = row.get("product_id")
        if product_id in produtos_por_id:
            raise ValueError(f"produto duplicado product_id={product_id}")
        produtos_por_id[product_id] = row

    def elegiveis(tipo: str, limite: Decimal, *, excluir_code_card: bool = False):
        elegiveis_por_produto: dict[Any, tuple[Decimal, Mapping[str, Any]]] = {}
        for row in precos:
            if row.get("data") != data_inicial:
                continue
            product_id = row.get("product_id")
            market = _decimal(row.get("market_price"))
            if market is None or market <= 0:
                continue
            info = produtos_por_id.get(product_id)
            if info is None or info.get("tipo_produto") != tipo:
                continue
            if excluir_code_card and info.get("raridade") == "Code Card":
                continue
            if market * ptax > limite:
                continue

            atual = elegiveis_por_produto.get(product_id)
            if atual is None:
                elegiveis_por_produto[product_id] = (market, row)
                continue
            market_atual, row_atual = atual
            acabamento = str(row.get("acabamento") or "")
            acabamento_atual = str(row_atual.get("acabamento") or "")
            if (
                market > market_atual
                or (
                    market == market_atual
                    and acabamento < acabamento_atual
                )
            ):
                elegiveis_por_produto[product_id] = (market, row)

        candidatos = []
        for product_id, (market, row) in elegiveis_por_produto.items():
            info = produtos_por_id[product_id]
            candidatos.append((product_id, row, market, info))
        candidatos.sort(
            key=lambda item: (
                -item[2],
                item[0] if isinstance(item[0], int) else 10**100,
                str(item[0]),
            )
        )
        return candidatos

    def posicao(
        tipo: str,
        product_id: Any,
        row: Mapping[str, Any],
        market: Decimal,
        unidades: int,
    ) -> dict[str, Any]:
        return {
            "tipo": tipo,
            "product_id": product_id,
            "acabamento": str(row.get("acabamento") or ""),
            "unidades": unidades,
            "market_price_usd": market,
            "ptax_venda": ptax,
            "custo_brl": _custo_brl(unidades, market, ptax),
        }

    selado_candidatos = elegiveis("selado", limite_selado_brl)
    selado_posicoes: list[dict[str, Any]] = []
    if selado_candidatos:
        product_id, row, market, _info = selado_candidatos[0]
        unidades = int(
            (limite_selado_brl / (market * ptax)).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        if unidades > 0:
            p = posicao("selado", product_id, row, market, unidades)
            selado_posicoes = [p]

    cesta_candidatos = elegiveis("carta", limite_cesta_carta_brl)
    cesta_posicoes: list[dict[str, Any]] = []
    cesta_custo = Decimal("0")
    for product_id, row, market, _info in cesta_candidatos[
        :quantidade_cesta_raras
    ]:
        p = posicao("carta", product_id, row, market, 1)
        cesta_posicoes.append(p)
        cesta_custo += p["custo_brl"]

    propria_posicoes: list[dict[str, Any]] = []
    propria_caixa = metade_propria_brl * 2

    propria_selado = elegiveis("selado", metade_propria_brl)
    if propria_selado:
        product_id, row, market, _info = propria_selado[0]
        unidades = int(
            (metade_propria_brl / (market * ptax)).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        if unidades > 0:
            p = posicao("selado", product_id, row, market, unidades)
            propria_posicoes.append(p)
            propria_caixa -= p["custo_brl"]

    propria_carta = elegiveis(
        "carta", metade_propria_brl, excluir_code_card=True
    )
    if propria_carta:
        product_id, row, market, _info = propria_carta[0]
        p = posicao("carta", product_id, row, market, 1)
        propria_posicoes.append(p)
        propria_caixa -= p["custo_brl"]

    capital_decimal = _decimal(capital_brl)
    if capital_decimal is None:
        raise ValueError("capital_brl nulo")

    if selado_posicoes:
        selado_caixa = capital_decimal - sum(
            (p["custo_brl"] for p in selado_posicoes),
            Decimal("0"),
        )
    else:
        selado_caixa = capital_decimal

    cesta_caixa = capital_decimal - cesta_custo

    dolar_usd = capital_decimal / ptax

    return {
        "metadata": {
            "data_inicial": data_inicial,
            "ptax_venda": ptax,
            "data_ptax_venda": data_ptax,
        },
        "selado": {
            "posicoes": selado_posicoes,
            "caixa_brl": selado_caixa,
        },
        "cesta_raras": {
            "posicoes": cesta_posicoes,
            "caixa_brl": cesta_caixa,
        },
        "propria": {
            "posicoes": propria_posicoes,
            "caixa_brl": propria_caixa,
        },
        "dolar": {
            "posicoes": [],
            "caixa_brl": Decimal("0"),
            "dolar_parado_usd": dolar_usd,
        },
        "cdi": {
            "posicoes": [],
            "caixa_brl": capital_decimal,
        },
    }
