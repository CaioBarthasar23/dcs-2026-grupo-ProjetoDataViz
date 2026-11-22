from datetime import date
from decimal import Decimal

import pytest

from src.concentracao_valor import calcular_concentracao_valor


D1 = date(2026, 10, 9)
D2 = date(2026, 10, 10)
D3 = date(2026, 10, 11)


def preco(gid, pid, dia, acabamento, usd, brl):
    return {
        "group_id": gid,
        "product_id": pid,
        "data": dia,
        "acabamento": acabamento,
        "market_price": usd,
        "market_price_brl": brl,
    }


def produto(gid, pid, tipo="carta", raridade="Rare"):
    return {
        "group_id": gid,
        "product_id": pid,
        "nome": f"Produto {pid}",
        "tipo_produto": tipo,
        "raridade": raridade,
    }


def dados():
    fatos = [
        preco(23651, 1, D1, "Alpha", 1.0, 5.0),
        preco(23651, 1, D2, "Alpha", 2.0, 10.0),
        preco(23651, 1, D3, "Zeta", 5.0, 50.0),
        preco(23651, 1, D3, "Alpha", 4.0, 40.0),
        preco(23651, 2, D2, "Normal", 2.0, 10.0),
        preco(23651, 2, D3, "Normal", 3.0, 30.0),
        preco(23651, 3, D3, "Normal", 2.0, 20.0),
        preco(23651, 4, D3, "Normal", 1.0, 10.0),
        preco(23651, 5, D3, "Normal", None, None),
        preco(23651, 6, D3, "Normal", 6.0, 60.0),
        preco(23651, 7, D3, "Normal", 7.0, 70.0),
        preco(23651, 8, D3, "Normal", 8.0, 80.0),
        preco(23651, 9, D1, "Normal", 9.0, 90.0),
        preco(23651, 10, D3, "Normal", 100.0, 500.0),
        preco(23651, 11, D3, "Normal", 100.0, 600.0),
        preco(23651, 12, D3, "Normal", 100.0, 700.0),
    ]
    produtos = [
        produto(23651, 1, raridade="Ultra Rare"),
        produto(23651, 2, raridade="Rare"),
        produto(23651, 3, raridade="Ultra Rare"),
        produto(23651, 4, raridade="Rare"),
        produto(23651, 5, raridade="Rare"),
        produto(23651, 6, raridade="Code Card"),
        produto(23651, 7, tipo="selado", raridade="Rare"),
        produto(23651, 8, raridade=None),
        produto(23651, 9, raridade="Ultra Rare"),
        produto(23651, 10, raridade="Rare"),
        produto(23651, 11, raridade="Rare"),
        produto(23651, 12, raridade="Rare"),
    ]
    return fatos, produtos


def test_exclui_code_card_selado_nulo_ultimo_dia_exemplar_e_cobertura():
    fatos, produtos = dados()
    resultado = calcular_concentracao_valor(fatos, produtos)

    assert resultado["data_referencia"] == D3
    assert resultado["moeda"] == "brl"
    assert resultado["quantidade_cartas"] == 8
    assert resultado["quantidade_excluidas"] == 2
    assert resultado["valor_total"] == pytest.approx(40 + 30 + 20 + 10 + 80 + 500 + 600 + 700)
    assert resultado["cobertura"] == {
        "primeira_data": D1,
        "ultima_data": D3,
        "quantidade_datas": 3,
    }
    assert sum(row["participacao"] for row in resultado["participacao_por_raridade"]) == pytest.approx(1.0)
    participacoes = resultado["participacao_por_raridade"]
    assert [
        (row["raridade"], row["valor"], row["participacao"])
        for row in participacoes
    ] == [
        ("Rare", 1840.0, pytest.approx(1840 / 1980)),
        ("sem raridade", 80.0, pytest.approx(80 / 1980)),
        ("Ultra Rare", 60.0, pytest.approx(60 / 1980)),
    ]
    assert any(row["raridade"] == "sem raridade" for row in participacoes)


def test_ultimo_dia_nao_carrega_preco_anterior():
    fatos = [
        preco(23651, 1, D1, "A", 9.0, 90.0),
        preco(23651, 2, D3, "A", 1.0, 10.0),
    ]
    produtos = [produto(23651, 1), produto(23651, 2)]
    resultado = calcular_concentracao_valor(fatos, produtos)
    assert resultado["quantidade_cartas"] == 1
    assert resultado["quantidade_excluidas"] == 1
    assert resultado["valor_total"] == 10.0


def test_empate_acabamento_alfabetico():
    fatos = [
        preco(23651, 1, D3, "Zeta", 2.0, 20.0),
        preco(23651, 1, D3, "Alpha", 2.0, 20.0),
    ]
    resultado = calcular_concentracao_valor(fatos, [produto(23651, 1)])
    assert resultado["valor_total"] == 20.0
    assert resultado["quantidade_cartas"] == 1
    assert resultado["acabamentos_escolhidos"] == {1: "Alpha"}


def test_participacoes_desempate_raridade():
    fatos = [
        preco(23651, 1, D3, "A", 5.0, 50.0),
        preco(23651, 2, D3, "A", 5.0, 50.0),
    ]
    produtos = [
        produto(23651, 1, raridade="Zeta"),
        produto(23651, 2, raridade="Alpha"),
    ]
    resultado = calcular_concentracao_valor(fatos, produtos)
    assert [row["raridade"] for row in resultado["participacao_por_raridade"]] == ["Alpha", "Zeta"]


def test_fronteira_exata_80_inclusiva_e_desempate_product_id():
    fatos = [
        preco(23651, 20, D3, "A", 40.0, 40.0),
        preco(23651, 10, D3, "A", 40.0, 40.0),
        preco(23651, 30, D3, "A", 20.0, 20.0),
    ]
    produtos = [produto(23651, 10), produto(23651, 20), produto(23651, 30)]
    resultado = calcular_concentracao_valor(fatos, produtos, moeda="usd", limite=Decimal("0.8"))
    assert resultado["valor_total"] == 100.0
    assert resultado["quantidade_cartas_limite"] == 2
    assert resultado["limite"] == 0.8


def test_ordem_decrescente_valor_e_empate_product_id():
    fatos = [
        preco(23651, 2, D3, "A", 8.0, 80.0),
        preco(23651, 1, D3, "A", 8.0, 80.0),
        preco(23651, 3, D3, "A", 4.0, 40.0),
    ]
    resultado = calcular_concentracao_valor(
        fatos,
        [produto(23651, 1), produto(23651, 2), produto(23651, 3)],
        moeda="usd",
        limite=0.4,
    )
    assert resultado["quantidade_cartas_limite"] == 1


def test_moedas_diferentes_com_cambio_mudando():
    fatos = [
        preco(23651, 1, D3, "A", 10.0, 60.0),
        preco(23651, 2, D3, "A", 20.0, 100.0),
    ]
    produtos = [produto(23651, 1), produto(23651, 2)]
    brl = calcular_concentracao_valor(fatos, produtos, moeda="brl")
    usd = calcular_concentracao_valor(fatos, produtos, moeda="usd")
    assert brl["valor_total"] == 160.0
    assert usd["valor_total"] == 30.0


@pytest.mark.parametrize("limite", [0.0, -0.1, 1.01, float("inf"), float("nan")])
def test_limite_fora_do_intervalo_levanta_value_error(limite):
    fatos, produtos = dados()
    with pytest.raises(ValueError, match="limite|percentual"):
        calcular_concentracao_valor(fatos, produtos, limite=limite)


def test_moeda_invalida_levanta_value_error():
    fatos, produtos = dados()
    with pytest.raises(ValueError, match="moeda"):
        calcular_concentracao_valor(fatos, produtos, moeda="eur")


def test_multiplos_group_ids_levantam_value_error():
    fatos = [preco(23651, 1, D3, "A", 10.0, 50.0)]
    produtos = [produto(999, 1)]
    with pytest.raises(ValueError, match="group_id"):
        calcular_concentracao_valor(fatos, produtos)


def test_linha_duplicada_levanta_value_error():
    fatos = [
        preco(23651, 1, D3, "A", 10.0, 50.0),
        preco(23651, 1, D3, "A", 11.0, 55.0),
    ]
    with pytest.raises(ValueError, match="duplicad"):
        calcular_concentracao_valor(fatos, [produto(23651, 1)])


def test_nenhuma_carta_elegivel_levanta_value_error():
    fatos = [
        preco(23651, 1, D3, "A", None, None),
        preco(23651, 2, D3, "A", None, None),
    ]
    produtos = [produto(23651, 1), produto(23651, 2)]
    with pytest.raises(ValueError, match="nenhuma carta elegível"):
        calcular_concentracao_valor(fatos, produtos)


def test_valor_total_zero_levanta_value_error():
    fatos = [preco(23651, 1, D3, "A", 0.0, 0.0)]
    with pytest.raises(ValueError, match="zero"):
        calcular_concentracao_valor(fatos, [produto(23651, 1)])


def test_resultado_nao_depende_da_ordem():
    fatos, produtos = dados()
    a = calcular_concentracao_valor(fatos, produtos)
    b = calcular_concentracao_valor(list(reversed(fatos)), list(reversed(produtos)))
    assert a == b
