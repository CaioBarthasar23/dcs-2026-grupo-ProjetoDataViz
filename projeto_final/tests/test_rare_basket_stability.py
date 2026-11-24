from copy import deepcopy
from datetime import date
from decimal import Decimal

from src.selecao_carteiras import selecionar_carteiras


D1 = date(2026, 10, 31)
D2 = date(2026, 11, 1)
D3 = date(2026, 11, 2)
D4 = date(2026, 11, 3)


def preco(pid, market, dia=D1, acabamento="Normal"):
    return {
        "data": dia,
        "product_id": pid,
        "group_id": 23651,
        "acabamento": acabamento,
        "market_price": market,
    }


def produto(pid, tipo="carta", raridade="Rare"):
    return {
        "group_id": 23651,
        "product_id": pid,
        "tipo_produto": tipo,
        "raridade": raridade,
        "nome": f"Produto {pid}",
    }


def cambio(dia=D1, venda=10):
    return {
        "data": dia,
        "group_id": 23651,
        "cotacao_venda": venda,
        "cotacao_compra": venda,
    }


def snapshot(result):
    return {
        "selado": {
            "posicoes": [
                (p["product_id"], p["acabamento"], p["unidades"], p["custo_brl"])
                for p in result["selado"]["posicoes"]
            ],
            "caixa_brl": result["selado"]["caixa_brl"],
        },
        "cesta_raras": {
            "posicoes": [
                (p["product_id"], p["acabamento"], p["unidades"], p["custo_brl"])
                for p in result["cesta_raras"]["posicoes"]
            ],
            "caixa_brl": result["cesta_raras"]["caixa_brl"],
        },
    }


def test_composicao_identica_primeiro_dia_e_periodo_completo():
    only = [
        preco(1, 119.88, D1),
        preco(2, 13.33, D1),
        preco(3, 11.80, D1),
    ]
    complete = only + [
        preco(1, 300.0, D2),
        preco(2, 200.0, D2),
        preco(3, 5.0, D2),
    ]
    produtos = [
        produto(1, "selado"),
        produto(2),
        produto(3),
    ]
    first = selecionar_carteiras(only, produtos, [cambio(D1)])
    all_days = selecionar_carteiras(
        complete,
        produtos,
        [cambio(D1), cambio(D2)],
    )
    assert snapshot(first) == snapshot(all_days)


def test_precos_posteriores_que_mudariam_escolha_nao_afetam():
    initial = [
        preco(1, 100.0, D1),
        preco(2, 9.0, D1),
        preco(3, 8.0, D1),
    ]
    later = [
        preco(1, 500.0, D2),
        preco(2, 9.5, D2),
        preco(3, 60.0, D2),
        preco(4, 50.0, D2),
    ]
    produtos = [
        produto(1, "selado"),
        produto(2),
        produto(3),
        produto(4),
    ]
    first = selecionar_carteiras(initial, produtos, [cambio(D1)])
    all_days = selecionar_carteiras(
        initial + later,
        produtos,
        [cambio(D1), cambio(D2)],
    )
    assert snapshot(first) == snapshot(all_days)


def test_adicao_incremental_d1_d2_d3_mantem_composicao():
    initial = [preco(1, 100.0, D1), preco(2, 9.0, D1)]
    produtos = [produto(1, "selado"), produto(2)]
    current = list(initial)
    expected = selecionar_carteiras(
        current,
        produtos,
        [cambio(D1)],
    )
    for dia, linha in (
        (D2, preco(1, 300.0, D2)),
        (D3, preco(2, 50.0, D3)),
        (D4, preco(3, 200.0, D4)),
    ):
        current = current + [linha]
        produtos_locais = produtos + ([produto(3)] if dia == D4 else [])
        cambios = [
            cambio(D1),
            *([cambio(dia)] if dia != D1 else []),
        ]
        actual = selecionar_carteiras(
            current,
            produtos_locais,
            cambios,
        )
        assert snapshot(actual) == snapshot(expected)


def test_ordem_das_linhas_nao_altera_resultado():
    rows = [
        preco(2, 9.0, D1),
        preco(1, 100.0, D1),
        preco(3, 8.0, D1),
        preco(1, 300.0, D2),
        preco(3, 60.0, D2),
    ]
    produtos = [
        produto(3),
        produto(1, "selado"),
        produto(2),
    ]
    direct = selecionar_carteiras(
        rows,
        produtos,
        [cambio(D1), cambio(D2)],
    )
    reverse = selecionar_carteiras(
        list(reversed(rows)),
        list(reversed(produtos)),
        [cambio(D2), cambio(D1)],
    )
    assert snapshot(direct) == snapshot(reverse)
