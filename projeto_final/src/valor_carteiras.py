"""Calcula o valor diário das carteiras a partir da composição inicial da T-17."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


ZERO = Decimal("0")
ONE = Decimal("1")
CENT = Decimal("0.01")
RATE = Decimal("0.000001")


def _decimal(value: Any, nome: str) -> Decimal:
    if value is None:
        raise ValueError(f"{nome} nulo")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"{nome} deve ser finito")
        return value
    try:
        converted = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{nome} deve ser decimal válido") from exc
    if not converted.is_finite():
        raise ValueError(f"{nome} deve ser finito")
    return converted


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(RATE, rounding=ROUND_HALF_UP)


def _ptax_compra_asof(cambio_diario: Sequence[Mapping[str, Any]], data: Any) -> Decimal:
    candidatas = [
        row
        for row in cambio_diario
        if row.get("data") is not None
        and row["data"] <= data
        and row.get("cotacao_compra") is not None
    ]
    if not candidatas:
        raise ValueError(f"não há PTAX de compra ASOF para a data {data}")
    escolhida = max(candidatas, key=lambda row: row["data"])
    return _decimal(escolhida["cotacao_compra"], "cotacao_compra")


def _perda_maxima(valores: Sequence[Decimal]) -> Decimal:
    """Maior queda percentual de pico anterior para vale seguinte.

    A fórmula é hipótese, validação pendente: para cada valor da série,
    compara-se o valor ao maior pico anterior e calcula-se
    (pico - vale) / pico. Retorna o máximo; queda positiva em fração,
    zero quando não ocorre queda.
    """
    if not valores:
        return ZERO
    pico = valores[0]
    maior_queda = ZERO
    for valor in valores:
        if valor > pico:
            pico = valor
        elif pico > ZERO:
            queda = (pico - valor) / pico
            if queda > maior_queda:
                maior_queda = queda
    return _rate(maior_queda)


def calcular_valor_carteiras(
    composicao_inicial: Mapping[str, Any],
    preco_diario: Sequence[Mapping[str, Any]],
    cambio_diario: Sequence[Mapping[str, Any]],
    cdi_diario: Sequence[Mapping[str, Any]],
    *,
    taxas_venda: Sequence[Decimal] = (
        Decimal("0"),
        Decimal("0.15"),
    ),
    capital_brl: Decimal = Decimal("1000"),
) -> dict[str, Any]:
    """Calcula valor diário, retorno e perda máxima sem alterar a composição.

    preco_diario usa data, product_id, group_id, acabamento e market_price.
    cambio_diario usa data, group_id, cotacao_compra e cotacao_venda.
    cdi_diario usa data, group_id e taxa_dia em percentagem ao dia.

    Somente preço None é ausente: zero não é convertido nem tratado como nulo.
    Apenas datas distintas de preco_diario >= data_inicial geram linhas.
    A taxa de venda incide somente em posições carta/selado; dólar e CDI
    não recebem taxa. A fórmula da perda máxima é hipótese, validação pendente.
    """
    precos = [dict(row) for row in preco_diario]
    cambios = [dict(row) for row in cambio_diario]
    cditems = [dict(row) for row in cdi_diario]
    composicao = {
        carteira: (
            dict(bloco)
            if isinstance(bloco, Mapping)
            else bloco
        )
        for carteira, bloco in composicao_inicial.items()
    }
    capital = _decimal(capital_brl, "capital_brl")

    grupos = {
        row["group_id"]
        for row in precos + cambios + cditems
        if row.get("group_id") is not None
    }
    if len(grupos) != 1:
        raise ValueError("preco_diario, cambio_diario e cdi_diario devem ter um único group_id")
    group_id = next(iter(grupos))

    metadata = composicao_inicial.get("metadata")
    if not isinstance(metadata, Mapping) or metadata.get("data_inicial") is None:
        raise ValueError("composição inicial sem data_inicial")
    data_inicial = metadata["data_inicial"]

    datas = sorted({
        row["data"]
        for row in precos
        if row.get("data") is not None and row["data"] >= data_inicial
    })
    if not datas:
        raise ValueError("não há datas de preco_diario a partir da data inicial")

    positions_by_cart = {}
    for carteira in ("selado", "cesta_raras", "propria"):
        bloco = composicao_inicial.get(carteira)
        if not isinstance(bloco, Mapping):
            continue
        positions_by_cart[carteira] = [
            dict(posicao)
            for posicao in bloco.get("posicoes", [])
        ]

    taxas = tuple(dict.fromkeys(_decimal(taxa, "taxa_venda") for taxa in taxas_venda))

    linhas: list[dict[str, Any]] = []
    series: dict[tuple[str, Decimal], list[Decimal]] = {
        (carteira, taxa): []
        for carteira in ("selado", "cesta_raras", "propria", "dolar", "cdi")
        for taxa in taxas
    }
    carregados: dict[tuple[str, Decimal], int] = {
        key: 0 for key in series
    }

    caixa_inicial = {}
    for carteira in ("selado", "cesta_raras", "propria"):
        bloco = composicao_inicial.get(carteira)
        caixa_inicial[carteira] = (
            _decimal(bloco["caixa_brl"], f"caixa_brl de {carteira}")
            if isinstance(bloco, Mapping)
            else ZERO
        )

    for taxa in taxas:
        caixa_por_carteira = dict(caixa_inicial)
        caixa_cdi = (
            _decimal(
                composicao_inicial["cdi"]["caixa_brl"],
                "caixa_brl da carteira cdi",
            )
            if isinstance(composicao_inicial.get("cdi"), Mapping)
            else capital
        )
        dolar_usd = (
            _decimal(
                composicao_inicial["dolar"]["dolar_parado_usd"],
                "dolar_parado_usd",
            )
            if isinstance(composicao_inicial.get("dolar"), Mapping)
            else ZERO
        )
        ultimo_preco: dict[tuple[Any, Any], Decimal] = {}

        for position_carteira in ("selado", "cesta_raras", "propria"):
            for posicao in positions_by_cart.get(position_carteira, []):
                key = (
                    posicao["product_id"],
                    str(posicao.get("acabamento") or ""),
                )
                market_initial = posicao.get("market_price_usd")
                if market_initial is not None:
                    ultimo_preco[key] = _decimal(
                        market_initial,
                        f"market_price_usd de {key}",
                    )

        last_cdi = data_inicial
        for data in datas:
            ptax = _ptax_compra_asof(cambios, data)
            carregado_nesta_data = {
                carteira: False
                for carteira in ("selado", "cesta_raras", "propria")
            }

            for position_carteira in ("selado", "cesta_raras", "propria"):
                for posicao in positions_by_cart.get(position_carteira, []):
                    key = (
                        posicao["product_id"],
                        str(posicao.get("acabamento") or ""),
                    )
                    linhas_preco = [
                        row
                        for row in precos
                        if row.get("data") == data
                        and row.get("product_id") == key[0]
                        and str(row.get("acabamento") or "") == key[1]
                    ]
                    market_row = (
                        linhas_preco[0]
                        if len(linhas_preco) == 1
                        else None
                    )
                    if len(linhas_preco) > 1:
                        raise ValueError(
                            f"linha duplicada de preço em {data} para {key}"
                        )
                    if market_row is not None:
                        market = market_row.get("market_price")
                        if market is not None:
                            ultimo_preco[key] = _decimal(
                                market,
                                f"market_price de {key}",
                            )
                        else:
                            if key not in ultimo_preco:
                                raise ValueError(
                                    f"nenhum preço conhecido para product_id "
                                    f"{key[0]} acabamento {key[1]}"
                                )
                            carregado_nesta_data[position_carteira] = True
                    elif key not in ultimo_preco:
                        raise ValueError(
                            f"nenhum preço conhecido para product_id "
                            f"{key[0]} acabamento {key[1]}"
                        )
                    else:
                        carregado_nesta_data[position_carteira] = True

            for position_carteira, esta_carregado in carregado_nesta_data.items():
                if esta_carregado:
                    carregados[(position_carteira, taxa)] += 1

            # Compõe a caixa com taxas CDI em (last_cdi, data], sem retroagir.
            for row in sorted(
                (
                    row for row in cditems
                    if row.get("data") is not None
                    and row["data"] > last_cdi
                    and row["data"] <= data
                ),
                key=lambda item: item["data"],
            ):
                taxa_cdi = _decimal(row["taxa_dia"], "taxa_dia")
                fator = ONE + taxa_cdi / Decimal("100")
                for carteira in ("selado", "cesta_raras", "propria"):
                    caixa_por_carteira[carteira] = caixa_por_carteira[carteira] * fator
                caixa_cdi = caixa_cdi * fator
            last_cdi = data

            valores = {}
            for carteira in ("selado", "cesta_raras", "propria"):
                valor_posicoes = ZERO
                for posicao in positions_by_cart.get(carteira, []):
                    key = (
                        posicao["product_id"],
                        str(posicao.get("acabamento") or ""),
                    )
                    market = ultimo_preco[key]
                    unidades = int(posicao["unidades"])
                    bruto = Decimal(unidades) * market * ptax
                    liquido = bruto * (ONE - taxa)
                    valor_posicoes += liquido
                valores[carteira] = _money(
                    valor_posicoes + caixa_por_carteira[carteira]
                )

            valores["dolar"] = _money(dolar_usd * ptax)
            valores["cdi"] = _money(caixa_cdi)

            cdi_retorno = valores["cdi"] / capital - ONE
            cdi_retorno = _rate(cdi_retorno)

            for carteira in ("selado", "cesta_raras", "propria", "dolar", "cdi"):
                valor = valores[carteira]
                retorno = _rate(valor / capital - ONE)
                excesso = _rate(retorno - cdi_retorno)
                series[(carteira, taxa)].append(valor)
                linhas.append({
                    "data": data,
                    "group_id": group_id,
                    "carteira": carteira,
                    "valor_brl": valor,
                    "retorno_acumulado": retorno,
                    "taxa_venda": taxa,
                    "excesso_sobre_cdi": excesso,
                    "preco_carregado": carregado_nesta_data.get(carteira, False),
                })

    return {
        "linhas": linhas,
        "metricas": {
            carteira: {
                taxa: {
                    "perda_maxima": _perda_maxima(series[(carteira, taxa)]),
                    "dias_preco_carregado": carregados[(carteira, taxa)],
                }
                for taxa in taxas
            }
            for carteira in ("selado", "cesta_raras", "propria", "dolar", "cdi")
        },
    }
