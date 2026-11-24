from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest

from src.valor_carteiras import calcular_valor_carteiras


D1 = date(2026, 10, 31)
D2 = date(2026, 11, 1)
D3 = date(2026, 11, 2)


def preco(product_id, market_price, dia=D1, acabamento="Normal"):
    return {
        "data": dia,
        "product_id": product_id,
        "group_id": 23651,
        "acabamento": acabamento,
        "market_price": market_price,
    }


def cambio(dia=D1, compra=10, venda=10):
    return {
        "data": dia,
        "group_id": 23651,
        "cotacao_compra": compra,
        "cotacao_venda": venda,
    }


def cdi(dia, taxa):
    return {"data": dia, "group_id": 23651, "taxa_dia": taxa}


def composicao(
    data_inicial=D1,
    caixa_selado=900,
    caixa_cesta=900,
    caixa_propria=276,
    dolar_usd=100,
):
    return {
        "metadata": {
            "data_inicial": data_inicial,
            "ptax_venda": Decimal("10"),
            "data_ptax_venda": D1,
        },
        "selado": {
            "posicoes": [{
                "tipo": "selado",
                "product_id": 1,
                "acabamento": "Normal",
                "unidades": 1,
                "market_price_usd": Decimal("10"),
                "ptax_venda": Decimal("10"),
                "custo_brl": Decimal("100"),
            }],
            "caixa_brl": Decimal(str(caixa_selado)),
        },
        "cesta_raras": {
            "posicoes": [{
                "tipo": "carta",
                "product_id": 2,
                "acabamento": "Normal",
                "unidades": 1,
                "market_price_usd": Decimal("10"),
                "ptax_venda": Decimal("10"),
                "custo_brl": Decimal("100"),
            }],
            "caixa_brl": Decimal(str(caixa_cesta)),
        },
        "propria": {
            "posicoes": [{
                "tipo": "selado",
                "product_id": 3,
                "acabamento": "Normal",
                "unidades": 1,
                "market_price_usd": Decimal("10"),
                "ptax_venda": Decimal("10"),
                "custo_brl": Decimal("100"),
            }],
            "caixa_brl": Decimal(str(caixa_propria)),
        },
        "dolar": {
            "posicoes": [],
            "caixa_brl": Decimal("0"),
            "dolar_parado_usd": Decimal(str(dolar_usd)),
        },
        "cdi": {
            "posicoes": [],
            "caixa_brl": Decimal("1000"),
        },
    }


def linhas(result):
    return result["linhas"]


def linha(result, data, carteira, taxa):
    for row in linhas(result):
        if (
            row["data"] == data
            and row["carteira"] == carteira
            and row["taxa_venda"] == Decimal(str(taxa))
        ):
            return row
    raise AssertionError("linha não encontrada")


def test_ptax_compra_asof_nao_usa_cotacao_posterior():
    result = calcular_valor_carteiras(
        composicao(),
        [preco(1, 10), preco(1, 12, D2)],
        [
            cambio(D1, compra=2),
            cambio(D2, compra=3),
            cambio(D3, compra=99),
        ],
        [],
        taxas_venda=(Decimal("0"),),
    )
    assert linha(result, D1, "selado", 0)["valor_brl"] == Decimal("920.00")
    assert linha(result, D2, "selado", 0)["valor_brl"] == Decimal("936.00")


def test_cdi_taxa_porcentagem_e_sabado_sem_taxa():
    result = calcular_valor_carteiras(
        composicao(data_inicial=D1),
        [preco(1, 10), preco(1, 10, D2), preco(1, 10, D3)],
        [cambio(D1, compra=1), cambio(D2, compra=1), cambio(D3, compra=1)],
        [cdi(D1, 0.05), cdi(D2, 0.05)],
        taxas_venda=(Decimal("0"),),
    )
    assert linha(result, D1, "cdi", 0)["valor_brl"] == Decimal("1000.00")
    assert linha(result, D2, "cdi", 0)["valor_brl"] == Decimal("1000.50")
    assert linha(result, D3, "cdi", 0)["valor_brl"] == Decimal("1000.50")


def test_taxa_apenas_em_posicoes_e_dolar_cdi_iguais():
    result = calcular_valor_carteiras(
        composicao(),
        [preco(1, 10), preco(2, 10), preco(3, 10)],
        [cambio(D1, compra=10)],
        [],
        taxas_venda=(Decimal("0"), Decimal("0.15")),
    )
    assert linha(result, D1, "dolar", 0)["valor_brl"] == Decimal("1000.00")
    assert linha(result, D1, "dolar", 0.15)["valor_brl"] == Decimal("1000.00")
    assert linha(result, D1, "cdi", 0)["valor_brl"] == Decimal("1000.00")
    assert linha(result, D1, "cdi", 0.15)["valor_brl"] == Decimal("1000.00")
    assert linha(result, D1, "selado", 0.15)["valor_brl"] == Decimal("985.00")
    assert linha(result, D1, "cesta_raras", 0.15)["valor_brl"] == Decimal("985.00")
    assert linha(result, D1, "propria", 0.15)["valor_brl"] == Decimal("361.00")


def test_sobra_cdi_composta_em_dias_uteis():
    result = calcular_valor_carteiras(
        composicao(caixa_cesta=900),
        [preco(2, 10), preco(2, 10, D2), preco(2, 10, D3)],
        [cambio(D1, compra=1), cambio(D2, compra=1), cambio(D3, compra=1)],
        [cdi(D2, 0.05), cdi(D3, 0.10)],
        taxas_venda=(Decimal("0"),),
    )
    assert linha(result, D1, "cesta_raras", 0)["valor_brl"] == Decimal("910.00")
    assert linha(result, D2, "cesta_raras", 0)["valor_brl"] == Decimal("910.45")
    assert linha(result, D3, "cesta_raras", 0)["valor_brl"] == Decimal("911.35")


def test_dolar_valorizado_por_ptax_compra():
    result = calcular_valor_carteiras(
        composicao(dolar_usd=100),
        [preco(1, 10)],
        [cambio(D1, compra=12)],
        [],
        taxas_venda=(Decimal("0"),),
    )
    assert linha(result, D1, "dolar", 0)["valor_brl"] == Decimal("1200.00")


def test_preco_carregado_dia_sem_linha_e_nulo():
    result = calcular_valor_carteiras(
        composicao(),
        [
            preco(1, 10),
            preco(2, 9, D2),
            preco(1, 12, D3),
        ],
        [cambio(D1, compra=10), cambio(D2, compra=10), cambio(D3, compra=10)],
        [],
        taxas_venda=(Decimal("0"),),
    )
    assert linha(result, D2, "selado", 0)["preco_carregado"] is True
    assert linha(result, D2, "selado", 0)["valor_brl"] == Decimal("1000.00")


def test_preco_nulo_usa_ultimo_preco():
    result = calcular_valor_carteiras(
        composicao(),
        [preco(1, 10), preco(1, None, D2), preco(2, 9, D2)],
        [cambio(D1, compra=10), cambio(D2, compra=10)],
        [],
        taxas_venda=(Decimal("0"),),
    )
    assert linha(result, D2, "selado", 0)["preco_carregado"] is True
    assert linha(result, D2, "selado", 0)["valor_brl"] == Decimal("1000.00")


def test_grade_so_preco_diario_e_sem_datas_de_cambio_cdi():
    result = calcular_valor_carteiras(
        composicao(),
        [preco(1, 10), preco(1, 11, D2)],
        [cambio(D1, compra=10), cambio(D3, compra=20)],
        [cdi(D3, 0.05)],
        taxas_venda=(Decimal("0"),),
    )
    datas = sorted({row["data"] for row in linhas(result)})
    assert datas == [D1, D2]


def test_ptax_ausente_levanta_value_error():
    with pytest.raises(ValueError, match="PTAX de compra ASOF"):
        calcular_valor_carteiras(
            composicao(),
            [preco(1, 10)],
            [],
            [],
        )


def test_composicao_sem_metadata_data_inicial_levanta_value_error():
    composition = composicao()
    del composition["metadata"]
    with pytest.raises(ValueError, match="composição inicial sem data_inicial"):
        calcular_valor_carteiras(
            composition,
            [preco(1, 10)],
            [cambio(D1, compra=10)],
            [],
        )


def test_group_id_misto_levanta_value_error():
    with pytest.raises(ValueError, match="único group_id"):
        calcular_valor_carteiras(
            composicao(),
            [preco(1, 10)],
            [dict(cambio(D1, compra=10), group_id=999)],
            [],
        )


def test_linha_preco_duplicada_levanta_value_error():
    with pytest.raises(ValueError, match="linha duplicada de preço"):
        calcular_valor_carteiras(
            composicao(),
            [preco(1, 10), preco(1, 11)],
            [cambio(D1, compra=10)],
            [],
        )


def test_nenhum_preco_conhecido_levanta_value_error():
    composition = composicao()
    composition["selado"]["posicoes"][0]["market_price_usd"] = None
    with pytest.raises(ValueError, match="nenhum preço conhecido"):
        calcular_valor_carteiras(
            composition,
            [preco(1, None)],
            [cambio(D1, compra=10)],
            [],
        )


def test_retorno_excesso_cdi_e_perda_maxima_conferiveis():
    result = calcular_valor_carteiras(
        composicao(caixa_cesta=900),
        [preco(2, 10), preco(2, 12, D2), preco(2, 9, D3)],
        [cambio(D1, compra=10), cambio(D2, compra=10), cambio(D3, compra=10)],
        [cdi(D2, 0.05), cdi(D3, 0.05)],
        taxas_venda=(Decimal("0"),),
    )
    row_cdi = linha(result, D3, "cdi", 0)
    row_cesta = linha(result, D3, "cesta_raras", 0)
    assert row_cdi["retorno_acumulado"] == Decimal("0.001000")
    assert row_cesta["retorno_acumulado"] == Decimal("-0.009100")
    assert row_cesta["excesso_sobre_cdi"] == Decimal("-0.010100")
    assert result["metricas"]["cesta_raras"][Decimal("0")]["perda_maxima"] == Decimal("0.028958")


def test_composicao_nao_muda_e_entrada_nao_e_mutada():
    original = composicao()
    snapshot = deepcopy(original)
    precos = [preco(1, 10), preco(1, 12, D2), preco(1, 13, D3)]
    inputs = [precos, [cambio(D1, compra=10), cambio(D2, compra=10)], []]
    first = calcular_valor_carteiras(
        original, inputs[0], inputs[1], inputs[2], taxas_venda=(Decimal("0"),)
    )
    second = calcular_valor_carteiras(
        deepcopy(original),
        list(reversed(precos)),
        list(reversed(inputs[1])),
        [],
        taxas_venda=(Decimal("0"),),
    )
    assert original == snapshot
    assert first["linhas"] == second["linhas"]


def test_saida_contrato_tipos_sem_nulos():
    result = calcular_valor_carteiras(
        composicao(),
        [preco(1, 10)],
        [cambio(D1, compra=10)],
        [],
        taxas_venda=(Decimal("0"),),
    )
    required = {
        "data",
        "group_id",
        "carteira",
        "valor_brl",
        "retorno_acumulado",
        "taxa_venda",
        "excesso_sobre_cdi",
    }
    for row in linhas(result):
        assert required.issubset(row)
        assert row["valor_brl"] is not None
        assert isinstance(row["group_id"], int)
        assert isinstance(row["valor_brl"], Decimal)


def test_dias_preco_carregado_conta_carteira_e_dia_uma_vez():
    composition = composicao()
    composition["selado"]["posicoes"].append({
        "tipo": "selado",
        "product_id": 11,
        "acabamento": "Normal",
        "unidades": 1,
        "market_price_usd": Decimal("10"),
        "ptax_venda": Decimal("10"),
        "custo_brl": Decimal("100"),
    })
    result = calcular_valor_carteiras(
        composition,
        [
            preco(1, 10),
            preco(11, 10),
            preco(2, 9, D2),
            preco(1, None, D2),
            preco(11, None, D2),
            preco(1, 10, D3),
            preco(11, None, D3),
        ],
        [
            cambio(D1, compra=10),
            cambio(D2, compra=10),
            cambio(D3, compra=10),
        ],
        [],
        taxas_venda=(Decimal("0"),),
    )
    assert result["metricas"]["selado"][Decimal("0")]["dias_preco_carregado"] == 2
