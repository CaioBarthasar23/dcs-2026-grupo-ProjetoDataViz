from datetime import date


def dados_semana():
    precos = [
        {
            "data": date(2026, 10, 8),
            "product_id": 1,
            "group_id": 23651,
            "acabamento": "Normal",
            "market_price": 2.0,
            "low_price": None,
            "mid_price": None,
            "high_price": None,
            "moeda": "USD",
            "fonte": "tcgplayer",
            "chave_raw": "raw/tcgplayer/group_id=23651/data=2026-10-08/prices.json",
        },
        *[
            {
                "data": date(2026, 10, dia),
                "product_id": 1,
                "group_id": 23651,
                "acabamento": "Normal",
                "market_price": 2.0,
                "low_price": None,
                "mid_price": None,
                "high_price": None,
                "moeda": "USD",
                "fonte": "tcgplayer",
                "chave_raw": f"raw/tcgplayer/group_id=23651/data=2026-10-{dia:02d}/prices.json",
            }
            for dia in range(9, 14)
        ],
    ]
    cambios = [
        {
            "data": date(2026, 10, 9),
            "cotacao_compra": 5.0,
            "cotacao_venda": 7.0,
            "data_hora_cotacao": date(2026, 10, 9),
            "boletim": "Fechamento",
            "chave_raw": "raw/bcb_ptax/group_id=23651/data=2026-10-09/cotacao.json",
        },
        {
            "data": date(2026, 10, 13),
            "cotacao_compra": 6.0,
            "cotacao_venda": 8.0,
            "data_hora_cotacao": date(2026, 10, 13),
            "boletim": "Fechamento",
            "chave_raw": "raw/bcb_ptax/group_id=23651/data=2026-10-13/cotacao.json",
        },
        {
            "data": date(2026, 10, 14),
            "cotacao_compra": 99.0,
            "cotacao_venda": 101.0,
            "data_hora_cotacao": date(2026, 10, 14),
            "boletim": "Fechamento",
            "chave_raw": "raw/bcb_ptax/group_id=23651/data=2026-10-14/cotacao.json",
        },
    ]
    return precos, cambios


def converter():
    from src.fx_asof import converter_precos

    return converter_precos


def test_asof_usa_ultima_ptax_ate_data_do_preco_e_audita_data():
    converter_precos = converter()
    precos, cambios = dados_semana()

    resultado = converter_precos(precos, cambios)

    por_data = {linha["data"]: linha for linha in resultado}
    assert por_data[date(2026, 10, 9)]["data_ptax_usada"] == date(2026, 10, 9)
    for dia in (10, 11, 12):
        linha = por_data[date(2026, 10, dia)]
        assert linha["data_ptax_usada"] == date(2026, 10, 9)
        assert linha["market_price_brl"] == 10.0
    assert por_data[date(2026, 10, 13)]["data_ptax_usada"] == date(2026, 10, 13)
    assert por_data[date(2026, 10, 13)]["market_price_brl"] == 12.0


def test_preco_anterior_a_primeira_ptax_fica_nulo():
    converter_precos = converter()
    precos, cambios = dados_semana()

    linha = next(
        linha
        for linha in converter_precos(precos, cambios)
        if linha["data"] == date(2026, 10, 8)
    )

    assert linha["data_ptax_usada"] is None
    assert linha["market_price_brl"] is None


def test_ptax_na_mesma_data_do_preco_e_inclusiva():
    converter_precos = converter()
    precos, cambios = dados_semana()

    linha = next(
        linha
        for linha in converter_precos(precos, cambios)
        if linha["data"] == date(2026, 10, 9)
    )

    assert linha["data_ptax_usada"] == date(2026, 10, 9)
    assert linha["market_price_brl"] == 10.0


def test_cotacao_compra_e_padrao_e_venda_e_parametrizavel():
    converter_precos = converter()
    precos, cambios = dados_semana()

    compra = converter_precos(precos, cambios)
    venda = converter_precos(precos, cambios, cotacao="venda")
    compra_10 = next(x for x in compra if x["data"] == date(2026, 10, 10))
    venda_10 = next(x for x in venda if x["data"] == date(2026, 10, 10))

    assert compra_10["market_price_brl"] == 10.0
    assert venda_10["market_price_brl"] == 14.0
    assert venda_10["data_ptax_usada"] == date(2026, 10, 9)


def test_preco_market_price_nulo_permanece_nulo():
    converter_precos = converter()
    precos, cambios = dados_semana()
    precos[1]["market_price"] = None

    linha = next(
        linha
        for linha in converter_precos(precos, cambios)
        if linha["data"] == date(2026, 10, 9)
    )

    assert linha["data_ptax_usada"] == date(2026, 10, 9)
    assert linha["market_price_brl"] is None
