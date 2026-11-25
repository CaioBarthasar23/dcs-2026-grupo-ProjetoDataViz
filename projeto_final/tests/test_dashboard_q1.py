from copy import deepcopy
from datetime import date

import pytest

from dashboard.p1 import preparar_ranking_p1


INICIO = date(2026, 10, 1)
FIM = date(2026, 10, 3)


def produto(product_id, *, raridade="Rare", image_url=None, url=None):
    return {
        "product_id": product_id,
        "tipo_produto": "carta",
        "raridade": raridade,
        "image_url": image_url or f"imagem-{product_id}",
        "url": url or f"produto-{product_id}",
    }


def linha(product_id, dia, usd, brl, acabamento="Normal"):
    return {
        "product_id": product_id,
        "acabamento": acabamento,
        "data": dia,
        "market_price": usd,
        "market_price_brl": brl,
        "data_ptax_usada": dia if usd is not None else None,
    }


def dados():
    produtos = [
        produto(1),
        produto(2),
        produto(3),
        produto(4),
        produto(5),
        produto(6, raridade="Code Card"),
        produto(7),
        produto(8),
    ]
    fatos = [
        linha(1, INICIO, 10, 50), linha(1, FIM, 12, 72),
        linha(2, INICIO, 10, 50), linha(2, FIM, 11, 55),
        linha(3, INICIO, 10, 50), linha(3, FIM, 8, 40),
        linha(4, INICIO, 10, 50), linha(4, FIM, 8, 40),
        linha(5, INICIO, 1.00, 5), linha(5, FIM, 20, 100),
        linha(6, INICIO, 10, 50), linha(6, FIM, 100, 500),
        linha(7, INICIO, 1.01, 5.05), linha(7, FIM, 2, 10),
        linha(8, INICIO, None, None), linha(8, FIM, 4, 20),
    ]
    return fatos, produtos


def calcular(fatos=None, produtos=None, **kwargs):
    if fatos is None or produtos is None:
        fatos, produtos = dados()
    return preparar_ranking_p1(fatos, produtos, **kwargs)


def test_ranking_brl_ordena_variacao_decrescente_e_desempata_por_product_id():
    result = calcular()
    altas = result["maiores_altas"]
    quedas = result["maiores_quedas"]
    assert [row["product_id"] for row in altas[:3]] == [1, 2, 7]
    assert [row["product_id"] for row in quedas[:2]] == [3, 4]
    assert altas[0]["variacao_brl"] == pytest.approx(22)
    assert altas[0]["variacao_percentual"] == pytest.approx(0.44)


def test_empate_usa_product_id_e_depois_acabamento():
    fatos = [
        linha(9, INICIO, 5, 10, "Reverse Holo"), linha(9, FIM, 6, 20, "Reverse Holo"),
        linha(9, INICIO, 5, 10, "Normal"), linha(9, FIM, 6, 20, "Normal"),
        linha(2, INICIO, 5, 10), linha(2, FIM, 6, 20),
    ]
    result = calcular(fatos, [produto(9), produto(2)])
    assert [(r["product_id"], r["acabamento"]) for r in result["maiores_altas"]] == [
        (2, "Normal"), (9, "Normal"), (9, "Reverse Holo")
    ]


def test_soma_dos_tres_efeitos_fecha_variacao_total():
    result = calcular()
    for row in result["maiores_altas"] + result["maiores_quedas"]:
        assert row["variacao_percentual"] == pytest.approx(
            row["efeito_carta"] + row["efeito_cambio"] + row["efeito_cruzado"]
        )


def test_modo_usd_calcula_variacao_em_dolar_e_efeitos_nao_aplicaveis():
    result = calcular(moeda="usd")
    first = result["maiores_altas"][0]
    assert first["product_id"] == 1
    assert first["variacao_usd"] == pytest.approx(2)
    assert first["variacao_percentual"] == pytest.approx(0.2)
    assert first["efeito_cambio"] is None
    assert first["efeito_cruzado"] is None
    assert first["rotulo_efeito_cambio"] == "não se aplica"
    assert first["rotulo_efeito_cruzado"] == "não se aplica"


def test_limite_usd_estritamente_maior_que_um_e_nulos_nao_sao_zero():
    result = calcular()
    ids = {row["product_id"] for row in result["maiores_altas"] + result["maiores_quedas"]}
    assert 5 not in ids
    assert 7 in ids
    assert 8 not in ids
    assert result["excluidas"]["preco_inicial_nulo"] == 1
    assert result["excluidas"]["filtro_usd_1"] == 1


def test_code_card_com_maior_variacao_e_excluida_e_contada():
    result = calcular()
    ids = {row["product_id"] for row in result["maiores_altas"] + result["maiores_quedas"]}
    assert 6 not in ids
    assert result["excluidas"]["code_card"] == 1


def test_linhas_incluem_product_id_imagem_e_link_originais():
    result = calcular()
    for row in result["maiores_altas"] + result["maiores_quedas"]:
        assert row["product_id"] is not None
        assert row["image_url"] == f"imagem-{row['product_id']}"
        assert row["url"] == f"produto-{row['product_id']}"


def test_tamanho_e_parametro_e_datas_e_contagens_sao_devolvidos():
    result = calcular(tamanho=1)
    assert len(result["maiores_altas"]) == 1
    assert len(result["maiores_quedas"]) == 1
    assert result["data_inicio"] == INICIO
    assert result["data_fim"] == FIM
    assert result["quantidade_comparacoes"] == 5
    assert set(result["excluidas"]) == {
        "filtro_usd_1", "preco_inicial_nulo", "preco_final_nulo", "code_card"
    }


def test_nao_muta_entradas_e_repeticao_da_mesma_saida():
    fatos, produtos = dados()
    fatos_antes, produtos_antes = deepcopy(fatos), deepcopy(produtos)
    primeira = preparar_ranking_p1(fatos, produtos)
    segunda = preparar_ranking_p1(fatos, produtos)
    assert fatos == fatos_antes
    assert produtos == produtos_antes
    assert primeira == segunda


def test_modo_usd_ordena_pela_variacao_em_dolar_e_nao_pela_variacao_em_reais():
    fatos = [
        linha(21, INICIO, 10, 50), linha(21, FIM, 12, 51),
        linha(22, INICIO, 10, 50), linha(22, FIM, 11, 60),
    ]
    produtos = [produto(21), produto(22)]
    brl = calcular(fatos, produtos, moeda="brl")
    usd = calcular(fatos, produtos, moeda="usd")
    assert [r["product_id"] for r in brl["maiores_altas"]] == [22, 21]
    assert [r["product_id"] for r in usd["maiores_altas"]] == [21, 22]
    assert [r["product_id"] for r in usd["maiores_quedas"]] == [22, 21]


def test_preco_final_nulo_e_excluido_e_contado_e_nao_vira_queda_total():
    fatos = [
        linha(31, INICIO, 10, 50), linha(31, FIM, None, None),
        linha(32, INICIO, 10, 50), linha(32, FIM, 11, 55),
    ]
    for moeda in ("brl", "usd"):
        result = calcular(fatos, [produto(31), produto(32)], moeda=moeda)
        ids = [r["product_id"] for r in result["maiores_altas"] + result["maiores_quedas"]]
        assert 31 not in ids
        assert result["excluidas"]["preco_final_nulo"] == 1
        assert result["quantidade_comparacoes"] == 1
