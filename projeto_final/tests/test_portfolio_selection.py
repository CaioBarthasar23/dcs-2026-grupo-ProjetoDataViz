from copy import deepcopy
from datetime import date
from decimal import Decimal

import pytest

from src.selecao_carteiras import selecionar_carteiras


D1 = date(2026, 10, 31)
D2 = date(2026, 11, 1)


def preco(product_id, market_price, dia=D1, acabamento="Normal"):
    return {
        "data": dia,
        "product_id": product_id,
        "group_id": 23651,
        "acabamento": acabamento,
        "market_price": market_price,
    }


def produto(product_id, tipo="carta", raridade="Rare"):
    return {
        "group_id": 23651,
        "product_id": product_id,
        "tipo_produto": tipo,
        "raridade": raridade,
        "nome": f"Produto {product_id}",
    }


def cambio(dia=D1, venda=Decimal("10"), compra=Decimal("9")):
    return {
        "data": dia,
        "cotacao_compra": float(compra),
        "cotacao_venda": float(venda),
    }


def posicao(result, carteira, indice=0):
    return result[carteira]["posicoes"][indice]


def test_round_half_up_real_10_005_vezes_1_resulta_10_01():
    result = selecionar_carteiras(
        [preco(1, 10.005)],
        [produto(1, "carta")],
        [cambio(venda=Decimal("1"))],
        capital_brl=Decimal("100"),
        limite_cesta_carta_brl=Decimal("100"),
    )
    assert posicao(result, "cesta_raras")["custo_brl"] == Decimal("10.01")
    assert result["cesta_raras"]["caixa_brl"] == Decimal("89.99")


def test_soma_custos_arredondados_na_cesta():
    result = selecionar_carteiras(
        [preco(1, 10.004), preco(2, 10.004)],
        [produto(1), produto(2)],
        [cambio(venda=Decimal("1"))],
        capital_brl=Decimal("1000"),
        limite_cesta_carta_brl=Decimal("100"),
    )
    assert [p["custo_brl"] for p in result["cesta_raras"]["posicoes"]] == [
        Decimal("10.00"),
        Decimal("10.00"),
    ]
    assert result["cesta_raras"]["caixa_brl"] == Decimal("980.00")


def test_igualdade_exata_na_fronteira_de_100_reais_e_elegivel():
    result = selecionar_carteiras(
        [preco(1, 10.0)],
        [produto(1, "carta")],
        [cambio(venda=Decimal("10"))],
    )
    assert posicao(result, "cesta_raras")["product_id"] == 1
    assert posicao(result, "cesta_raras")["custo_brl"] == Decimal("100.00")


def test_conversao_float_por_str_e_igualdade_exata():
    result = selecionar_carteiras(
        [preco(1, 1.1)],
        [produto(1, "carta")],
        [cambio(venda=Decimal("100"))],
        limite_cesta_carta_brl=Decimal("110"),
    )
    assert posicao(result, "cesta_raras")["market_price_usd"] == Decimal("1.1")
    assert posicao(result, "cesta_raras")["custo_brl"] == Decimal("110.00")


def test_fronteira_1000_e_desempate_por_menor_product_id():
    result = selecionar_carteiras(
        [preco(20, 100.0), preco(10, 100.0)],
        [produto(20, "selado"), produto(10, "selado")],
        [cambio(venda=Decimal("10"))],
    )
    assert posicao(result, "selado")["product_id"] == 10
    assert posicao(result, "selado")["unidades"] == 1


def test_fronteira_500_da_propria_e_carta_de_1_unidade():
    result = selecionar_carteiras(
        [preco(1, 50.0), preco(2, 49.0)],
        [produto(1, "selado"), produto(2, "carta", "Rare")],
        [cambio(venda=Decimal("10"))],
    )
    propria = result["propria"]
    assert any(p["product_id"] == 1 and p["unidades"] == 1 for p in propria["posicoes"])
    assert any(p["product_id"] == 2 and p["unidades"] == 1 for p in propria["posicoes"])
    assert propria["caixa_brl"] == Decimal("10.00")


def test_acima_do_limite_excluido_e_500_na_carta_propria_elegivel():
    ptax = Decimal("10")
    result = selecionar_carteiras(
        [
            preco(1, 100.01),
            preco(2, 50.001),
            preco(3, 50.0),
            preco(4, 50.001),
            preco(5, 100.001),
            preco(101, 10.001),
            preco(102, 10.0),
        ],
        [
            produto(1, "carta"),
            produto(2, "carta"),
            produto(3, "carta"),
            produto(4, "selado"),
            produto(5, "selado"),
            produto(101, "carta"),
            produto(102, "carta"),
        ],
        [cambio(venda=ptax)],
    )
    ids_cesta = [p["product_id"] for p in result["cesta_raras"]["posicoes"]]
    assert 1 not in ids_cesta
    assert 101 not in ids_cesta
    assert 102 in ids_cesta
    propria_carta = [
        p["product_id"]
        for p in result["propria"]["posicoes"]
        if p["tipo"] == "carta"
    ]
    assert propria_carta == [3]
    propria_selado = [
        p["product_id"]
        for p in result["propria"]["posicoes"]
        if p["tipo"] == "selado"
    ]
    assert propria_selado == []
    assert [p["product_id"] for p in result["selado"]["posicoes"]] == [4]


def test_nulo_e_zero_sao_ignorados():
    nulo_selado = selecionar_carteiras(
        [preco(1, None), preco(99, 10.0)],
        [produto(1, "selado"), produto(99, "carta")],
        [cambio(venda=Decimal("10"))],
        capital_brl=Decimal("777"),
    )
    zero_selado = selecionar_carteiras(
        [preco(2, 0.0), preco(98, 10.0)],
        [produto(2, "selado"), produto(98, "carta")],
        [cambio(venda=Decimal("10"))],
        capital_brl=Decimal("777"),
    )
    assert nulo_selado["selado"] == {
        "posicoes": [],
        "caixa_brl": Decimal("777"),
    }
    assert zero_selado["selado"] == {
        "posicoes": [],
        "caixa_brl": Decimal("777"),
    }


def test_todos_market_price_nulos_levanta_value_error():
    with pytest.raises(
        ValueError,
        match="não há primeiro dia com market_price não nulo",
    ):
        selecionar_carteiras(
            [preco(1, None), preco(2, None)],
            [produto(1, "selado"), produto(2, "carta")],
            [cambio(venda=Decimal("10"))],
        )


def test_tipo_produto_e_code_card_discriminantes():
    result = selecionar_carteiras(
        [preco(1, 8.0), preco(2, 60.0)],
        [
            produto(1, "selado"),
            produto(2, "carta", "Rare"),
        ],
        [cambio(venda=Decimal("10"))],
    )
    assert posicao(result, "selado")["product_id"] == 1
    assert [p["product_id"] for p in result["cesta_raras"]["posicoes"]] == []
    propria_carta = [
        p["product_id"]
        for p in result["propria"]["posicoes"]
        if p["tipo"] == "carta"
    ]
    assert propria_carta == []


def test_code_card_maior_nao_escolhida_na_propria_e_entrada_na_cesta():
    result = selecionar_carteiras(
        [preco(1, 9.0), preco(2, 9.5)],
        [
            produto(1, "carta", "Rare"),
            produto(2, "carta", "Code Card"),
        ],
        [cambio(venda=Decimal("10"))],
    )
    ids_cesta = [p["product_id"] for p in result["cesta_raras"]["posicoes"]]
    assert ids_cesta == [2, 1]
    ids_propria_carta = [
        p["product_id"]
        for p in result["propria"]["posicoes"]
        if p["tipo"] == "carta"
    ]
    assert ids_propria_carta == [1]


def test_unidades_inteiras_sobra_e_selado_mais_barato_compra_varias():
    result = selecionar_carteiras(
        [preco(1, 12.345), preco(2, 10.0)],
        [produto(1, "selado"), produto(2, "selado")],
        [cambio(venda=Decimal("10"))],
    )
    selected = posicao(result, "selado")
    assert selected["unidades"] == 8
    assert selected["custo_brl"] == Decimal("987.60")
    assert result["selado"]["caixa_brl"] == Decimal("12.40")


def test_propria_compra_varias_unidades_de_selado_e_uma_carta():
    result = selecionar_carteiras(
        [preco(1, 20.0), preco(2, 16.0), preco(3, 30.0)],
        [
            produto(1, "selado"),
            produto(2, "selado"),
            produto(3, "carta", "Rare"),
        ],
        [cambio(venda=Decimal("10"))],
    )
    posicoes = result["propria"]["posicoes"]
    selado = [p for p in posicoes if p["tipo"] == "selado"]
    carta = [p for p in posicoes if p["tipo"] == "carta"]
    assert selado == [{
        "tipo": "selado",
        "product_id": 1,
        "acabamento": "Normal",
        "unidades": 2,
        "market_price_usd": Decimal("20"),
        "ptax_venda": Decimal("10"),
        "custo_brl": Decimal("400.00"),
    }]
    assert len(carta) == 1
    assert carta[0]["product_id"] == 3
    assert carta[0]["unidades"] == 1
    assert result["propria"]["caixa_brl"] == Decimal("300.00")


def test_propria_metade_sem_candidato_fica_em_caixa():
    result = selecionar_carteiras(
        [preco(1, 60.0), preco(2, 60.0)],
        [produto(1, "selado"), produto(2, "carta", "Code Card")],
        [cambio(venda=Decimal("10"))],
    )
    assert result["propria"]["posicoes"] == []
    assert result["propria"]["caixa_brl"] == Decimal("1000.00")


def test_dolar_converte_capital_e_cdi_usam_capital_sem_fixo():
    result = selecionar_carteiras(
        [preco(1, 1.0)],
        [produto(1, "selado")],
        [cambio(venda=Decimal("5"))],
        capital_brl=Decimal("1234"),
    )
    assert result["dolar"]["dolar_parado_usd"] == Decimal("246.8")
    assert result["cdi"]["caixa_brl"] == Decimal("1234")


def test_menos_de_10_cartas_elegiveis_deixa_resto_em_caixa():
    result = selecionar_carteiras(
        [preco(1, 10.0), preco(2, 9.0), preco(3, 8.0)],
        [produto(1), produto(2), produto(3)],
        [cambio(venda=Decimal("10"))],
    )
    assert len(result["cesta_raras"]["posicoes"]) == 3
    assert result["cesta_raras"]["caixa_brl"] == Decimal("730.00")


def test_precos_posteriores_nao_alteram_selecao():
    result = selecionar_carteiras(
        [
            preco(1, 9.4, D1),
            preco(2, 9.5, D1),
            preco(1, 100.0, D2),
            preco(3, 200.0, D2),
        ],
        [produto(1), produto(2), produto(3)],
        [cambio(venda=Decimal("10"))],
    )
    ids = [p["product_id"] for p in result["cesta_raras"]["posicoes"]]
    assert ids == [2, 1]


def test_ptax_asof_nao_usa_cotacao_posterior():
    result = selecionar_carteiras(
        [preco(1, 20.0, D1)],
        [produto(1, "selado")],
        [
            cambio(date(2026, 10, 28), venda=Decimal("7")),
            cambio(date(2026, 10, 29), venda=Decimal("8")),
            cambio(date(2026, 11, 1), venda=Decimal("12")),
        ],
    )
    position = posicao(result, "selado")
    assert position["ptax_venda"] == Decimal("8")
    assert result["metadata"]["data_ptax_venda"] == date(2026, 10, 29)


def test_primeiro_dia_exige_market_price_nao_nulo():
    result = selecionar_carteiras(
        [
            preco(1, None, D1),
            preco(1, 20.0, D2),
            preco(2, 10.0, D2),
        ],
        [produto(1), produto(2)],
        [cambio(D1, venda=Decimal("10")), cambio(D2, venda=Decimal("5"))],
    )
    assert result["metadata"]["data_inicial"] == D2
    assert posicao(result, "cesta_raras")["product_id"] == 1


def test_str_float_nao_e_usado_para_elegibilidade():
    result = selecionar_carteiras(
        [preco(1, 1.1)],
        [produto(1)],
        [cambio(venda=Decimal("100"))],
        limite_cesta_carta_brl=Decimal("110"),
    )
    assert posicao(result, "cesta_raras")["custo_brl"] == Decimal("110.00")


def test_corte_em_dez_e_empate_na_decima_decima_primeira():
    precos = [preco(pid, 12 - pid * 0.1) for pid in range(1, 13)]
    produtos = [produto(pid) for pid in range(1, 13)]
    result = selecionar_carteiras(
        precos,
        produtos,
        [cambio(venda=Decimal("1"))],
    )
    ids = [p["product_id"] for p in result["cesta_raras"]["posicoes"]]
    assert len(ids) == 10
    assert ids == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    empates = [
        *[preco(pid, 9.0 - i * 0.1) for i, pid in enumerate(range(1, 10), start=1)],
        preco(10, 8.0),
        preco(11, 8.0),
    ]
    empate_result = selecionar_carteiras(
        empates,
        [produto(pid) for pid in [*range(1, 12)]],
        [cambio(venda=Decimal("10"))],
    )
    ids_empate = [
        p["product_id"] for p in empate_result["cesta_raras"]["posicoes"]
    ]
    assert len(ids_empate) == 10
    assert 10 in ids_empate
    assert 11 not in ids_empate


def test_piso_intenso_nao_arredonda_quociente_para_cima():
    result = selecionar_carteiras(
        [preco(1, 11.5)],
        [produto(1, "selado")],
        [cambio(venda=Decimal("10"))],
    )
    position = posicao(result, "selado")
    assert position["unidades"] == 8
    assert position["custo_brl"] == Decimal("920.00")
    assert result["selado"]["caixa_brl"] == Decimal("80.00")


def test_acabamento_caro_acima_limite_nao_impede_mais_barato():
    result = selecionar_carteiras(
        [
            preco(1, 100.001, acabamento="Caro"),
            preco(1, 9.0, acabamento="Barato"),
        ],
        [produto(1, "carta")],
        [cambio(venda=Decimal("10"))],
        limite_cesta_carta_brl=Decimal("100"),
    )
    assert posicao(result, "cesta_raras")["acabamento"] == "Barato"


def test_acabamentos_de_um_produto_reduzem_a_uma_posicao_maior_preco():
    result = selecionar_carteiras(
        [
            preco(1, 15.0, acabamento="Zeta"),
            preco(1, 12.0, acabamento="Alpha"),
        ],
        [produto(1, "carta")],
        [cambio(venda=Decimal("10"))],
        limite_cesta_carta_brl=Decimal("200"),
    )
    assert len(result["cesta_raras"]["posicoes"]) == 1
    assert posicao(result, "cesta_raras")["acabamento"] == "Zeta"


def test_mesmo_product_id_nunca_aparece_duas_vezes_na_cesta():
    result = selecionar_carteiras(
        [
            preco(1, 12.0, acabamento="Zeta"),
            preco(1, 15.0, acabamento="Alpha"),
            preco(2, 11.0),
        ],
        [produto(1), produto(2)],
        [cambio(venda=Decimal("1"))],
    )
    ids = [p["product_id"] for p in result["cesta_raras"]["posicoes"]]
    assert len(ids) == len(set(ids))
    positions1 = [
        p for p in result["cesta_raras"]["posicoes"] if p["product_id"] == 1
    ]
    assert len(positions1) == 1
    assert positions1[0]["acabamento"] == "Alpha"
    assert 2 in ids


def test_acabamentos_iguais_desempatam_por_menor_nome():
    result = selecionar_carteiras(
        [
            preco(1, 10.0, acabamento="Zeta"),
            preco(1, 10.0, acabamento="Alpha"),
        ],
        [produto(1, "carta")],
        [cambio(venda=Decimal("10"))],
    )
    assert posicao(result, "cesta_raras")["acabamento"] == "Alpha"


def test_group_id_misturado_levanta_value_error():
    with pytest.raises(ValueError, match="group_id"):
        selecionar_carteiras(
            [preco(1, 10.0)],
            [produto(1)],
            [dict(cambio(venda=Decimal("10")), group_id=999)],
        )


def test_product_id_duplicado_em_produto_levanta_value_error():
    with pytest.raises(ValueError, match="produto duplicado"):
        selecionar_carteiras(
            [preco(1, 10.0)],
            [produto(1), produto(1)],
            [cambio(venda=Decimal("10"))],
        )


def test_nao_altera_entrada_e_resultado_e_deterministico():
    preco_diario = [preco(2, 10.0), preco(1, 10.0)]
    produtos = [produto(2), produto(1)]
    cambios = [cambio(venda=Decimal("10"))]
    original = deepcopy((preco_diario, produtos, cambios))

    primeiro = selecionar_carteiras(preco_diario, produtos, cambios)
    segundo = selecionar_carteiras(list(reversed(preco_diario)), list(reversed(produtos)), cambios)

    assert (preco_diario, produtos, cambios) == original
    assert primeiro == segundo
