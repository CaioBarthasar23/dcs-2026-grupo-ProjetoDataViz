from datetime import date
from decimal import Decimal

import pytest

from src.retorno_risco import calcular_retorno_risco


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
        "tipo_produto": tipo,
        "raridade": raridade,
    }


def test_fronteira_exata_usd_5_fica_fora():
    fatos = [
        preco(23651, 1, D1, "Normal", 5.0, 50.0),
        preco(23651, 1, D2, "Normal", 6.0, 60.0),
        preco(23651, 1, D3, "Normal", 7.0, 70.0),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D2, "Normal", 7.0, 70.0),
        preco(23651, 2, D3, "Normal", 8.0, 80.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1), produto(23651, 2)], moeda="usd"
    )
    assert resultado["quantidade_series_elegiveis"] == 1
    assert resultado["exclusoes_por_motivo"] == {
        "preco_inicial_nao_maior_que_minimo": 1,
        "sem_preco_no_primeiro_dia": 0,
        "sem_preco_no_ultimo_dia": 0,
    }


def test_sem_preco_no_primeiro_dia_excluido_e_contado():
    fatos = [
        preco(23651, 1, D1, "Normal", None, None),
        preco(23651, 1, D2, "Normal", 6.0, 60.0),
        preco(23651, 1, D3, "Normal", 7.0, 70.0),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1), produto(23651, 2)]
    )
    assert resultado["quantidade_series_elegiveis"] == 1
    assert resultado["exclusoes_por_motivo"]["sem_preco_no_primeiro_dia"] == 1


def test_sem_preco_no_ultimo_dia_excluido_e_contado():
    fatos = [
        preco(23651, 1, D1, "Normal", 6.0, 60.0),
        preco(23651, 1, D2, "Normal", 7.0, 70.0),
        preco(23651, 1, D3, "Normal", None, None),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1), produto(23651, 2)]
    )
    assert resultado["quantidade_series_elegiveis"] == 1
    assert resultado["exclusoes_por_motivo"]["sem_preco_no_ultimo_dia"] == 1


def test_preco_inicial_igual_ou_menor_que_minimo_excluido():
    fatos = [
        preco(23651, 1, D1, "Normal", 5.0, 50.0),
        preco(23651, 1, D3, "Normal", 7.0, 70.0),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1), produto(23651, 2)]
    )
    assert resultado["exclusoes_por_motivo"]["preco_inicial_nao_maior_que_minimo"] == 1


def test_nulo_no_meio_nao_cria_retorno():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 100.0),
        preco(23651, 1, D2, "Normal", None, None),
        preco(23651, 1, D3, "Normal", 12.0, 120.0),
    ]
    resultado = calcular_retorno_risco(fatos, [produto(23651, 1)])
    serie = resultado["series"][0]
    assert serie["quantidade_retornos"] == 0
    assert serie["desvio_padrao_retornos_diarios"] is None
    assert serie["retorno_no_periodo"] == pytest.approx(0.2)


def test_menos_retornos_que_minimo_da_desvio_nulo():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 100.0),
        preco(23651, 1, D2, "Normal", 11.0, 110.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1)], minimo_observacoes=2
    )
    serie = resultado["series"][0]
    assert serie["quantidade_retornos"] == 1
    assert serie["desvio_padrao_retornos_diarios"] is None


def test_minimo_observacoes_altera_desvio():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 100.0),
        preco(23651, 1, D2, "Normal", 12.0, 120.0),
        preco(23651, 1, D3, "Normal", 14.4, 144.0),
    ]
    dois = calcular_retorno_risco(
        fatos, [produto(23651, 1)], minimo_observacoes=2
    )
    tres = calcular_retorno_risco(
        fatos, [produto(23651, 1)], minimo_observacoes=3
    )
    assert dois["series"][0]["quantidade_retornos"] == 2
    assert dois["series"][0]["desvio_padrao_retornos_diarios"] == 0.0
    assert tres["series"][0]["desvio_padrao_retornos_diarios"] is None


def test_retorno_constante_tem_desvio_zero_legitimo():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 100.0),
        preco(23651, 1, D2, "Normal", 12.0, 120.0),
        preco(23651, 1, D3, "Normal", 14.4, 144.0),
    ]
    resultado = calcular_retorno_risco(fatos, [produto(23651, 1)])
    serie = resultado["series"][0]
    assert serie["quantidade_retornos"] == 2
    assert serie["desvio_padrao_retornos_diarios"] == 0.0


def test_brl_e_usd_diferem_com_cambio_mudando():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 50.0),
        preco(23651, 1, D2, "Normal", 12.0, 72.0),
        preco(23651, 1, D3, "Normal", 9.0, 63.0),
    ]
    usd = calcular_retorno_risco(fatos, [produto(23651, 1)], moeda="usd")
    brl = calcular_retorno_risco(fatos, [produto(23651, 1)], moeda="brl")
    assert usd["series"][0]["retorno_no_periodo"] == pytest.approx(-0.1)
    assert brl["series"][0]["retorno_no_periodo"] == pytest.approx(0.26)
    assert usd["series"][0]["desvio_padrao_retornos_diarios"] == pytest.approx(
        0.31819805153394637
    )
    assert brl["series"][0]["desvio_padrao_retornos_diarios"] == pytest.approx(
        0.3995156676634783
    )


def test_selado_fora_da_saida():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 100.0),
        preco(23651, 1, D3, "Normal", 12.0, 120.0),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D3, "Normal", 8.0, 80.0),
    ]
    resultado = calcular_retorno_risco(
        fatos,
        [produto(23651, 1, tipo="selado"), produto(23651, 2)],
    )
    assert resultado["quantidade_series_elegiveis"] == 1
    assert [serie["product_id"] for serie in resultado["series"]] == [2]


def test_code_card_incluida_com_code_card_true():
    fatos = [
        preco(23651, 1, D1, "Normal", 6.0, 60.0),
        preco(23651, 1, D3, "Normal", 8.0, 80.0),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D3, "Normal", 8.0, 80.0),
    ]
    resultado = calcular_retorno_risco(
        fatos,
        [
            produto(23651, 1, raridade="Rare"),
            produto(23651, 2, raridade="Code Card"),
        ],
    )
    assert resultado["quantidade_series_elegiveis"] == 2
    assert {
        serie["product_id"]: serie["code_card"] for serie in resultado["series"]
    } == {1: False, 2: True}


def test_precedencia_motivos_e_soma_excluidas():
    fatos = [
        preco(23651, 1, D1, "Normal", 4.0, 40.0),
        preco(23651, 1, D3, "Normal", None, None),
        preco(23651, 2, D1, "Normal", None, None),
        preco(23651, 2, D3, "Normal", None, None),
        preco(23651, 3, D1, "Normal", 6.0, 60.0),
        preco(23651, 3, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(
        fatos,
        [
            produto(23651, 1),
            produto(23651, 2),
            produto(23651, 3),
        ],
    )
    assert resultado["exclusoes_por_motivo"] == {
        "sem_preco_no_primeiro_dia": 1,
        "sem_preco_no_ultimo_dia": 1,
        "preco_inicial_nao_maior_que_minimo": 0,
    }
    assert sum(resultado["exclusoes_por_motivo"].values()) == resultado[
        "quantidade_series_excluidas"
    ]


def test_sem_linha_no_primeiro_dia_exclui_com_motivo():
    fatos = [
        preco(23651, 1, D2, "Normal", 6.0, 60.0),
        preco(23651, 1, D3, "Normal", 7.0, 70.0),
        preco(23651, 2, D1, "Normal", 6.0, 60.0),
        preco(23651, 2, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1), produto(23651, 2)]
    )
    assert resultado["exclusoes_por_motivo"]["sem_preco_no_primeiro_dia"] == 1


def test_preco_cai_a_zero_e_retorna_menos_100_porcento():
    fatos = [
        preco(23651, 1, D1, "Normal", 6.0, 60.0),
        preco(23651, 1, D2, "Normal", 0.0, 0.0),
        preco(23651, 1, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(fatos, [produto(23651, 1)])
    serie = resultado["series"][0]
    assert serie["quantidade_retornos"] == 1
    assert serie["desvio_padrao_retornos_diarios"] is None
    assert serie["retorno_no_periodo"] == pytest.approx(7 / 6 - 1)

    fatos = [
        preco(23651, 1, D1, "Normal", 6.0, 60.0),
        preco(23651, 1, D2, "Normal", 7.0, 70.0),
        preco(23651, 1, D3, "Normal", 0.0, 0.0),
    ]
    resultado = calcular_retorno_risco(fatos, [produto(23651, 1)])
    serie = resultado["series"][0]
    assert serie["quantidade_retornos"] == 2
    assert serie["retorno_no_periodo"] == pytest.approx(-1.0)
    assert serie["desvio_padrao_retornos_diarios"] == pytest.approx(
        0.8249579113843057
    )


def test_parametro_preco_minimo_renomeado_e_resultado_sem_acento():
    fatos = [
        preco(23651, 1, D1, "Normal", 7.0, 70.0),
        preco(23651, 1, D3, "Normal", 8.0, 80.0),
    ]
    resultado = calcular_retorno_risco(
        fatos,
        [produto(23651, 1)],
        preco_minimo_usd=Decimal("6"),
    )
    assert resultado["quantidade_series_elegiveis"] == 1


def test_cobertura_e_contagens_corretas():
    fatos = [
        preco(23651, 1, D1, "Normal", 6.0, 60.0),
        preco(23651, 1, D3, "Normal", 8.0, 80.0),
        preco(23651, 2, D1, "Normal", 5.0, 50.0),
        preco(23651, 2, D3, "Normal", 7.0, 70.0),
    ]
    resultado = calcular_retorno_risco(
        fatos, [produto(23651, 1), produto(23651, 2)]
    )
    assert resultado["cobertura"] == {
        "primeira_data": D1,
        "ultima_data": D3,
        "quantidade_datas": 2,
    }
    assert resultado["quantidade_series_elegiveis"] == 1
    assert resultado["quantidade_series_excluidas"] == 1


def test_resultado_independe_da_ordem():
    fatos = [
        preco(23651, 2, D1, "Zeta", 10.0, 100.0),
        preco(23651, 2, D3, "Zeta", 12.0, 144.0),
        preco(23651, 1, D1, "Normal", 6.0, 60.0),
        preco(23651, 1, D3, "Normal", 9.0, 99.0),
    ]
    produtos = [produto(23651, 2), produto(23651, 1)]
    direto = calcular_retorno_risco(fatos, produtos)
    reverso = calcular_retorno_risco(list(reversed(fatos)), list(reversed(produtos)))
    assert direto == reverso


@pytest.mark.parametrize("moeda", ["eur", "", None])
def test_moeda_invalida_levanta_value_error(moeda):
    with pytest.raises(ValueError, match="moeda"):
        calcular_retorno_risco([], [], moeda=moeda)


def test_group_misto_levanta_value_error():
    fatos = [preco(23651, 1, D1, "Normal", 10.0, 100.0)]
    produtos = [produto(999, 1)]
    with pytest.raises(ValueError, match="group_id"):
        calcular_retorno_risco(fatos, produtos)


def test_linha_duplicada_levanta_value_error():
    fatos = [
        preco(23651, 1, D1, "Normal", 10.0, 100.0),
        preco(23651, 1, D1, "Normal", 11.0, 110.0),
    ]
    with pytest.raises(ValueError, match="duplicad"):
        calcular_retorno_risco(fatos, [produto(23651, 1)])


def test_ausencia_de_datas_levanta_value_error():
    with pytest.raises(ValueError, match="datas"):
        calcular_retorno_risco([], [produto(23651, 1)])


def test_nenhuma_serie_elegivel_levanta_value_error():
    fatos = [
        preco(23651, 1, D1, "Normal", None, None),
        preco(23651, 1, D3, "Normal", None, None),
    ]
    with pytest.raises(ValueError, match="nenhuma série elegível"):
        calcular_retorno_risco(fatos, [produto(23651, 1)])
