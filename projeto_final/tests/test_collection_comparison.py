from datetime import date

import pytest

from src.comparacao_colecoes import calcular_comparacao_colecoes


D1 = date(2026, 10, 9)
D2 = date(2026, 10, 10)
D3 = date(2026, 10, 11)
D4 = date(2026, 10, 12)


def _preco(gid, pid, dia, acabamento, usd):
    return {
        "data": dia,
        "product_id": pid,
        "group_id": gid,
        "acabamento": acabamento,
        "market_price": usd,
        "moeda": "USD",
    }


def _produto(gid, pid, tipo="carta", raridade="Rare"):
    return {
        "group_id": gid,
        "product_id": pid,
        "nome": f"Produto {pid}",
        "tipo_produto": tipo,
        "raridade": raridade,
        "numero": str(pid),
        "image_url": "",
        "url": "",
        "categoria_selado": None,
    }


def _grupo(gid, precos, produtos):
    return {"preco_diario": precos, "produto": produtos}


def _cambios():
    return [
        {"data": D1, "cotacao_compra": 5.0, "cotacao_venda": 5.1},
        {"data": D3, "cotacao_compra": 6.0, "cotacao_venda": 6.1},
    ]


def _dados_tres_colecoes():
    # 101: acabamento Alpha (R$ 10) vence no início; Beta fica mais barato depois.
    g101 = _grupo(
        101,
        [
            _preco(101, 1, D1, "Beta", 3),
            _preco(101, 1, D1, "Alpha", 2),
            _preco(101, 1, D2, "Alpha", 2),
            _preco(101, 1, D2, "Beta", 1),
            _preco(101, 1, D3, "Alpha", 2),
            _preco(101, 2, D1, "Normal", 4),
            _preco(101, 2, D3, "Normal", None),
            _preco(101, 3, D1, "Code", 20),
            _preco(101, 4, D1, "Sealed", 8),
        ],
        [
            _produto(101, 1), _produto(101, 2),
            _produto(101, 3, raridade="Code Card"),
            _produto(101, 4, tipo="selado"),
        ],
    )
    # 202 tem datas D1-D3; 303 tem D1,D3,D4. Com 101 (D1-D3), comum D1,D3.
    g202 = _grupo(
        202,
        [_preco(202, 20, d, "Foil", usd) for d, usd in
         [(D1, 1), (D2, 2), (D3, 3)]],
        [_produto(202, 20)],
    )
    g303 = _grupo(
        303,
        [_preco(303, 30, d, "Normal", usd) for d, usd in
         [(D1, 2), (D3, 3), (D4, 4)]],
        [_produto(303, 30)],
    )
    return {101: g101, 202: g202, 303: g303}


def test_periodo_comum_intersecao_e_indices_base_100_inclusive_ptax():
    resultado = calcular_comparacao_colecoes(_dados_tres_colecoes(), _cambios())
    assert resultado["periodo_comum"] == [D1, D3]
    for gid in (101, 202, 303):
        assert resultado["series"][gid][0]["indice_colecao"] == 100
    assert resultado["indice_ptax"][0]["indice"] == 100
    assert resultado["indice_ptax"][-1]["indice"] == 120


def test_soma_exemplares_code_card_e_selado_ficam_fora_e_acabamento_fixo():
    resultado = calcular_comparacao_colecoes(_dados_tres_colecoes(), _cambios())
    serie = resultado["series"][101]
    assert serie[0]["valor"] == 30  # Alpha de 1 + Normal de 2
    assert serie[1]["valor"] == 32  # Alpha segue fixo; produto 2 carrega 20
    assert serie[1]["quantidade_carregados"] == 1
    assert resultado["disponiveis"][101]["acabamentos_escolhidos"] == {
        1: "Alpha", 2: "Normal"
    }


def test_empate_de_acabamento_desempata_alfabeticamente():
    grupos = {7: _grupo(7, [
        _preco(7, 1, D1, "Zeta", 1), _preco(7, 1, D1, "Alpha", 1),
    ], [_produto(7, 1)])}
    resultado = calcular_comparacao_colecoes(grupos, _cambios())
    assert resultado["disponiveis"][7]["acabamentos_escolhidos"][1] == "Alpha"


def test_colecao_sem_carta_elegivel_no_primeiro_dia_excluida_com_motivo():
    grupos = _dados_tres_colecoes()
    grupos[404] = _grupo(404, [_preco(404, 40, D1, "A", 2)], [_produto(404, 40, tipo="selado")])
    resultado = calcular_comparacao_colecoes(grupos, _cambios())
    assert 404 in resultado["excluidas"]
    assert "carta elegível" in resultado["excluidas"][404]["motivo"]


def test_cobertura_por_colecao_calculada_no_periodo_comum():
    resultado = calcular_comparacao_colecoes(_dados_tres_colecoes(), _cambios())
    assert resultado["cobertura"][303]["dias_com_preco"] == 2
    assert resultado["cobertura"][303]["dias_periodo_comum"] == 2
    assert resultado["cobertura"][303]["proporcao_dias"] == 1.0


def test_resultado_nao_depende_da_ordem_de_entrada():
    grupos = _dados_tres_colecoes()
    a = calcular_comparacao_colecoes(grupos, _cambios())
    b = calcular_comparacao_colecoes(dict(reversed(list(grupos.items()))), _cambios())
    assert a == b


def test_indices_usd_e_brl_diferem_quando_ptax_muda():
    grupos = _dados_tres_colecoes()
    brl = calcular_comparacao_colecoes(grupos, _cambios(), moeda="brl")
    usd = calcular_comparacao_colecoes(grupos, _cambios(), moeda="usd")
    assert brl["series"][303][-1]["indice_colecao"] != usd["series"][303][-1]["indice_colecao"]


def test_filtro_usd_e_estrito_e_aplicado_no_primeiro_dia():
    grupos = {1: _grupo(1, [
        _preco(1, 1, D1, "A", 1.0),
        _preco(1, 2, D1, "A", 1.01),
        _preco(1, 1, D2, "A", 3),
    ], [_produto(1, 1), _produto(1, 2)])}
    resultado = calcular_comparacao_colecoes(grupos, _cambios(), preco_minimo_usd=1.0)
    assert resultado["disponiveis"][1]["acabamentos_escolhidos"] == {2: "A"}


def test_linha_duplicada_por_colecao_produto_acabamento_data_levanta_value_error():
    grupo = _grupo(1, [
        _preco(1, 1, D1, "A", 1), _preco(1, 1, D1, "A", 2),
    ], [_produto(1, 1)])
    with pytest.raises(ValueError, match="duplicad"):
        calcular_comparacao_colecoes({1: grupo}, _cambios())


def test_acabamento_escolhido_no_inicio_permanece_no_periodo_comum():
    grupo = _grupo(1, [
        _preco(1, 1, D1, "Alpha", 2), _preco(1, 1, D1, "Beta", 3),
        _preco(1, 1, D2, "Alpha", 2), _preco(1, 1, D2, "Beta", 1),
    ], [_produto(1, 1)])
    resultado = calcular_comparacao_colecoes({1: grupo}, _cambios())
    assert resultado["periodo_comum"] == [D1, D2]
    assert resultado["disponiveis"][1]["acabamentos_escolhidos"] == {1: "Alpha"}
    assert resultado["series"][1][1]["valor_usd"] == 2


def test_carta_que_cai_abaixo_do_limite_usd_permanece_na_serie():
    grupo = _grupo(1, [
        _preco(1, 1, D1, "A", 2), _preco(1, 1, D2, "A", 0.5),
    ], [_produto(1, 1)])
    resultado = calcular_comparacao_colecoes(
        {1: grupo}, _cambios(), moeda="usd", preco_minimo_usd=1
    )
    assert resultado["series"][1][1]["quantidade_cartas"] == 1
    assert resultado["series"][1][1]["valor_usd"] == 0.5


def test_preco_nulo_nao_conta_como_dia_com_preco_nem_periodo():
    grupos = {
        1: _grupo(1, [_preco(1, 1, D1, "A", 2), _preco(1, 1, D2, "A", None)], [_produto(1, 1)]),
        2: _grupo(2, [_preco(2, 2, D1, "A", 2), _preco(2, 2, D2, "A", 3)], [_produto(2, 2)]),
    }
    resultado = calcular_comparacao_colecoes(grupos, _cambios())
    assert resultado["periodo_comum"] == [D1]
    assert resultado["cobertura"][1]["dias_com_preco"] == 1
    assert resultado["cobertura"][1]["linhas_preco_periodo"] == 1


def test_colecao_excluida_nao_restringe_periodo_comum():
    grupos = {
        1: _grupo(1, [_preco(1, 1, d, "A", 2) for d in (D1, D2, D3)], [_produto(1, 1)]),
        2: _grupo(2, [_preco(2, 2, d, "A", 3) for d in (D1, D2, D3)], [_produto(2, 2)]),
        3: _grupo(3, [_preco(3, 3, d, "A", 4) for d in (D1, D3)], [_produto(3, 3, tipo="selado")]),
    }
    resultado = calcular_comparacao_colecoes(grupos, _cambios())
    assert 3 in resultado["excluidas"]
    assert resultado["periodo_comum"] == [D1, D2, D3]
