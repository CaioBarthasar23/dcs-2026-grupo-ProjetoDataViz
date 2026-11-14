from datetime import date

import pytest

from src.selado_vs_cartas import RARIDADES_CARTAS_PADRAO, calcular_comparacao


D1 = date(2026, 10, 1)
D2 = date(2026, 10, 2)
D3 = date(2026, 10, 3)
BRL_OMITIDO = object()


def produto(product_id, tipo, raridade=None):
    return {
        "product_id": product_id,
        "tipo_produto": tipo,
        "raridade": raridade,
    }


def fato(product_id, acabamento, dia, usd, brl=BRL_OMITIDO):
    if brl is BRL_OMITIDO:
        brl = usd
    return {
        "product_id": product_id,
        "acabamento": acabamento,
        "data": dia,
        "market_price": usd,
        "market_price_brl": brl,
    }


def calcular(rows, products, **kwargs):
    return calcular_comparacao(
        rows,
        products,
        data_inicio=D1,
        data_fim=D3,
        **kwargs,
    )


def test_indices_base_100_media_selados_e_soma_cartas_conferidas_a_mao():
    rows = [
        fato(1, "Box", D1, 10),
        fato(2, "Bundle", D1, 30),
        fato(3, "Normal", D1, 10),
        fato(4, "Holofoil", D1, 20),
        fato(1, "Box", D2, 20),
        fato(2, "Bundle", D2, 40),
        fato(3, "Normal", D2, 15),
        fato(4, "Holofoil", D2, 25),
        fato(1, "Box", D3, 20),
        fato(2, "Bundle", D3, 40),
        fato(3, "Normal", D3, 15),
        fato(4, "Holofoil", D3, 25),
    ]
    products = [
        produto(1, "selado"),
        produto(2, "selado"),
        produto(3, "carta", "Double Rare"),
        produto(4, "carta", "Hyper Rare"),
    ]

    series = calcular(rows, products)

    assert series[0]["media_selados"] == pytest.approx(20)
    assert series[0]["soma_cartas"] == pytest.approx(30)
    assert series[0]["indice_selados"] == pytest.approx(100)
    assert series[0]["indice_cartas"] == pytest.approx(100)
    assert series[1]["media_selados"] == pytest.approx(30)
    assert series[1]["soma_cartas"] == pytest.approx(40)
    assert series[1]["indice_selados"] == pytest.approx(150)
    assert series[1]["indice_cartas"] == pytest.approx(100 * 40 / 30)
    assert series[1]["quantidade_selados"] == 2
    assert series[1]["quantidade_cartas"] == 2


def test_lista_padrao_exclui_ace_spec_rare_e_lista_configurada_pode_incluir():
    rows = [
        fato(1, "Normal", D1, 10),
        fato(2, "Normal", D1, 20),
        fato(3, "Normal", D1, 30),
        fato(4, "Normal", D1, 40),
        fato(1, "Normal", D2, 10),
        fato(2, "Normal", D2, 20),
        fato(3, "Normal", D2, 30),
        fato(4, "Normal", D2, 40),
    ]
    products = [
        produto(1, "carta", "Double Rare"),
        produto(2, "carta", "ACE SPEC Rare"),
        produto(3, "carta", "Rare"),
        produto(4, "carta", "Code Card"),
        produto(9, "selado"),
    ]
    rows.extend([fato(9, "Pack", D1, 5), fato(9, "Pack", D2, 5)])

    padrao = calcular(rows, products)
    com_ace = calcular(
        rows,
        products,
        raridades_cartas=[*RARIDADES_CARTAS_PADRAO, "ACE SPEC Rare"],
    )

    assert padrao[0]["quantidade_cartas"] == 1
    assert padrao[0]["soma_cartas"] == pytest.approx(10)
    assert com_ace[0]["quantidade_cartas"] == 2
    assert com_ace[0]["soma_cartas"] == pytest.approx(30)


def test_cesta_fixa_nao_adiciona_item_que_aparece_depois_do_primeiro_dia():
    rows = [
        fato(1, "Box", D1, 10),
        fato(2, "Normal", D1, 10),
        fato(1, "Box", D2, 12),
        fato(2, "Normal", D2, 11),
        fato(1, "Box", D3, 13),
        fato(2, "Normal", D3, 12),
        fato(3, "Normal", D2, 100),
        fato(3, "Normal", D3, 200),
    ]
    products = [
        produto(1, "selado"),
        produto(2, "carta", "Double Rare"),
        produto(3, "carta", "Hyper Rare"),
    ]

    series = calcular(rows, products)

    assert all(row["quantidade_cartas"] == 1 for row in series)
    assert [row["soma_cartas"] for row in series] == [10, 11, 12]


def test_item_sem_preco_ou_com_nulo_usa_ultimo_e_e_contado_como_carregado():
    rows = [
        fato(1, "Box", D1, 10),
        fato(2, "Normal", D1, 10, 10),
        fato(3, "Normal", D1, 20, 20),
        fato(1, "Box", D2, 12),
        fato(2, "Normal", D2, None, None),
        # O produto 3 não tem linha em D2.
        fato(1, "Box", D3, 14),
        fato(2, "Normal", D3, 12, 12),
        fato(3, "Normal", D3, 22, 22),
    ]
    products = [
        produto(1, "selado"),
        produto(2, "carta", "Double Rare"),
        produto(3, "carta", "Ultra Rare"),
    ]

    series = calcular(rows, products, moeda="brl")

    assert series[1]["soma_cartas"] == pytest.approx(30)
    assert series[1]["quantidade_cartas_carregadas"] == 2
    assert series[1]["quantidade_selados_carregados"] == 0
    assert series[1]["quantidade_cartas"] == 2


def test_preco_nulo_na_moeda_escolhida_no_inicio_nao_entra_na_cesta():
    rows = [
        fato(1, "Box", D1, 10, 10),
        fato(2, "Normal", D1, 10, 10),
        fato(3, "Normal", D1, 20, None),
        fato(1, "Box", D2, 12, 12),
        fato(2, "Normal", D2, 11, 11),
        fato(3, "Normal", D2, 25, 25),
    ]
    products = [
        produto(1, "selado"),
        produto(2, "carta", "Double Rare"),
        produto(3, "carta", "Ultra Rare"),
    ]

    series = calcular(rows, products, moeda="brl")

    assert series[0]["quantidade_cartas"] == 1
    assert series[0]["soma_cartas"] == pytest.approx(10)
    assert series[1]["soma_cartas"] == pytest.approx(11)


def test_moeda_usd_e_brl_produz_indices_diferentes_com_variacao_cambial():
    rows = [
        fato(1, "Box", D1, 20, 100),
        fato(2, "Normal", D1, 10, 50),
        fato(1, "Box", D2, 20, 120),
        fato(2, "Normal", D2, 20, 120),
    ]
    products = [produto(1, "selado"), produto(2, "carta", "Double Rare")]

    usd = calcular(rows, products, moeda="usd")
    brl = calcular(rows, products, moeda="brl")

    assert usd[1]["indice_cartas"] == pytest.approx(200)
    assert brl[1]["indice_cartas"] == pytest.approx(240)
    assert usd[1]["indice_selados"] == pytest.approx(100)
    assert brl[1]["indice_selados"] == pytest.approx(120)


def test_filtro_usd_estrito_aplica_separadamente_as_duas_cestas_no_inicio():
    rows = [
        fato(1, "Selado igual", D1, 5),
        fato(2, "Selado acima", D1, 6),
        fato(3, "Carta igual", D1, 5),
        fato(4, "Carta acima", D1, 7),
        fato(1, "Selado igual", D2, 100),
        fato(2, "Selado acima", D2, 8),
        fato(3, "Carta igual", D2, 100),
        fato(4, "Carta acima", D2, 9),
    ]
    products = [
        produto(1, "selado"),
        produto(2, "selado"),
        produto(3, "carta", "Double Rare"),
        produto(4, "carta", "Hyper Rare"),
    ]

    series = calcular(rows, products, preco_minimo_usd=5)

    assert series[0]["quantidade_selados"] == 1
    assert series[0]["quantidade_cartas"] == 1
    assert series[1]["media_selados"] == pytest.approx(8)
    assert series[1]["soma_cartas"] == pytest.approx(9)


def test_usa_somente_datas_presentes_no_fato():
    rows = [
        fato(1, "Box", D1, 10),
        fato(2, "Normal", D1, 10),
        fato(1, "Box", D3, 12),
        fato(2, "Normal", D3, 12),
    ]
    products = [produto(1, "selado"), produto(2, "carta", "Double Rare")]

    series = calcular(rows, products)

    assert [row["data"] for row in series] == [D1, D3]


def test_periodo_padrao_usa_primeira_e_ultima_data_do_fato():
    rows = [
        fato(1, "Box", D1, 10),
        fato(2, "Normal", D1, 10),
        fato(1, "Box", D3, 12),
        fato(2, "Normal", D3, 12),
    ]
    products = [produto(1, "selado"), produto(2, "carta", "Double Rare")]

    series = calcular_comparacao(rows, products)

    assert [row["data"] for row in series] == [D1, D3]


def test_cesta_vazia_ou_valor_inicial_zero_levanta_value_error():
    rows = [fato(1, "Box", D1, 10), fato(1, "Box", D2, 11)]

    with pytest.raises(ValueError, match="cesta.*cartas"):
        calcular(rows, [produto(1, "selado")])

    rows_zero = [
        fato(1, "Box", D1, 0),
        fato(2, "Normal", D1, 1),
        fato(1, "Box", D2, 1),
        fato(2, "Normal", D2, 1),
    ]
    with pytest.raises(ValueError, match="valor inicial.*selados"):
        calcular(rows_zero, [produto(1, "selado"), produto(2, "carta", "Double Rare")])


def test_linha_duplicada_para_item_e_data_levanta_value_error():
    rows = [
        fato(1, "Box", D1, 10),
        fato(1, "Box", D1, 11),
        fato(2, "Normal", D1, 10),
        fato(1, "Box", D2, 12),
        fato(2, "Normal", D2, 12),
    ]
    products = [produto(1, "selado"), produto(2, "carta", "Double Rare")]

    with pytest.raises(ValueError, match="mais de uma linha"):
        calcular(rows, products)
