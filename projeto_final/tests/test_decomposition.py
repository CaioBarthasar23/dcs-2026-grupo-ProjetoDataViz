from datetime import date

import pytest

from src.decomposicao import decompor_variacao


INICIO = date(2026, 10, 8)
FIM = date(2026, 10, 13)


def produto(product_id, tipo="carta", raridade="Rare"):
    return {
        "product_id": product_id,
        "tipo_produto": tipo,
        "raridade": raridade,
    }


def preco(product_id, acabamento, dia, usd, brl, ptax_dia):
    return {
        "product_id": product_id,
        "acabamento": acabamento,
        "data": dia,
        "market_price": usd,
        "market_price_brl": brl,
        "data_ptax_usada": ptax_dia,
    }


def calcular(rows, products, **kwargs):
    return decompor_variacao(
        rows,
        products,
        data_inicio=INICIO,
        data_fim=FIM,
        **kwargs,
    )


def test_identidade_e_soma_dos_tres_efeitos_com_tolerancia():
    rows = [
        preco(1, "Normal", INICIO, 10.0, 50.0, INICIO),
        preco(1, "Normal", FIM, 12.0, 72.0, FIM),
    ]

    result = calcular(rows, [produto(1)])
    row = result["resultados"][0]

    assert (1 + row["r_brl"]) == pytest.approx(
        (1 + row["r_usd"]) * (1 + row["r_cambio"]), abs=1e-12
    )
    assert row["r_brl"] == pytest.approx(
        row["efeito_carta"] + row["efeito_cambio"] + row["efeito_cruzado"],
        abs=1e-12,
    )
    assert row["efeito_carta"] == pytest.approx(0.2)
    assert row["efeito_cambio"] == pytest.approx(0.2)
    assert row["efeito_cruzado"] == pytest.approx(0.04)
    assert row["r_brl"] == pytest.approx(0.44)


def test_limite_padrao_exclui_preco_igual_ou_abaixo_de_um_dolar():
    rows = [
        preco(1, "Normal", INICIO, 1.0, 5.0, INICIO),
        preco(1, "Normal", FIM, 2.0, 10.0, FIM),
        preco(2, "Normal", INICIO, 0.99, 4.95, INICIO),
        preco(2, "Normal", FIM, 2.0, 10.0, FIM),
        preco(3, "Normal", INICIO, 1.01, 5.05, INICIO),
        preco(3, "Normal", FIM, 2.0, 10.0, FIM),
    ]

    result = calcular(rows, [produto(1), produto(2), produto(3)])

    assert [row["product_id"] for row in result["resultados"]] == [3]
    assert result["excluidas"]["abaixo_limiar_inicio"] == 2


def test_exclui_code_card_e_selado_sem_conta_los_como_excluidos():
    rows = [
        preco(1, "Normal", INICIO, 3.0, 15.0, INICIO),
        preco(1, "Normal", FIM, 4.0, 20.0, FIM),
        preco(2, "Normal", INICIO, 3.0, 15.0, INICIO),
        preco(2, "Normal", FIM, 4.0, 20.0, FIM),
    ]

    result = calcular(
        rows,
        [produto(1, raridade="Code Card"), produto(2, tipo="selado")],
    )

    assert result["resultados"] == []
    assert all(value == 0 for value in result["excluidas"].values())


def test_separa_contagens_de_linha_ou_preco_nulo_por_ponta():
    rows = [
        preco(1, "Normal", FIM, 2.0, 10.0, FIM),  # sem linha no início
        preco(2, "Normal", INICIO, None, None, None),
        preco(2, "Normal", FIM, 2.0, 10.0, FIM),
        preco(3, "Normal", INICIO, 2.0, 10.0, INICIO),
        preco(3, "Normal", FIM, None, None, None),
        preco(4, "Normal", INICIO, 2.0, 10.0, INICIO),  # sem linha no fim
    ]

    result = calcular(rows, [produto(i) for i in range(1, 5)])

    assert result["resultados"] == []
    assert result["excluidas"]["sem_preco_inicio"] == 2
    assert result["excluidas"]["sem_preco_fim"] == 2


def test_separa_ptax_ausente_e_preco_usd_zero():
    rows = [
        preco(1, "Normal", INICIO, 2.0, None, None),
        preco(1, "Normal", FIM, 3.0, 15.0, FIM),
        preco(2, "Normal", INICIO, 0.0, 0.0, INICIO),
        preco(2, "Normal", FIM, 3.0, 15.0, FIM),
        preco(3, "Normal", INICIO, 2.0, 10.0, INICIO),
        preco(3, "Normal", FIM, 0.0, 0.0, FIM),
    ]

    result = calcular(rows, [produto(1), produto(2), produto(3)])

    assert result["resultados"] == []
    assert result["excluidas"]["ptax_ausente"] == 1
    assert result["excluidas"]["preco_usd_zero"] == 2


def test_cambio_estavel_zera_efeito_cambio_e_cruzado():
    rows = [
        preco(1, "Normal", INICIO, 2.0, 10.0, INICIO),
        preco(1, "Normal", FIM, 3.0, 15.0, FIM),
    ]

    row = calcular(rows, [produto(1)])['resultados'][0]

    assert row["efeito_cambio"] == pytest.approx(0.0, abs=1e-12)
    assert row["efeito_cruzado"] == pytest.approx(0.0, abs=1e-12)
    assert row["r_usd"] == pytest.approx(row["r_brl"])


def test_carta_estavel_com_cambio_em_alta_tem_so_efeito_de_cambio():
    rows = [
        preco(1, "Normal", INICIO, 2.0, 10.0, INICIO),
        preco(1, "Normal", FIM, 2.0, 12.0, FIM),
    ]

    row = calcular(rows, [produto(1)])['resultados'][0]

    assert row["efeito_carta"] == pytest.approx(0.0, abs=1e-12)
    assert row["efeito_cambio"] == pytest.approx(0.2)
    assert row["efeito_cruzado"] == pytest.approx(0.0, abs=1e-12)
    assert row["r_brl"] == pytest.approx(row["efeito_cambio"])


def test_usa_datas_explicitas_e_limite_parametrizado():
    rows = [
        preco(1, "Normal", INICIO, 1.5, 7.5, INICIO),
        preco(1, "Normal", FIM, 2.0, 10.0, FIM),
    ]

    result = decompor_variacao(
        rows,
        [produto(1)],
        data_inicio=INICIO,
        data_fim=FIM,
        limite_usd=1.49,
    )

    assert result["resultados"][0]["product_id"] == 1


def test_datas_padrao_sao_primeira_e_ultima_presentes_no_fato():
    rows = [
        preco(1, "Normal", INICIO, 2.0, 10.0, INICIO),
        preco(1, "Normal", FIM, 3.0, 15.0, FIM),
    ]

    result = decompor_variacao(rows, [produto(1)])

    assert result["resultados"][0]["data_inicio"] == INICIO
    assert result["resultados"][0]["data_fim"] == FIM
