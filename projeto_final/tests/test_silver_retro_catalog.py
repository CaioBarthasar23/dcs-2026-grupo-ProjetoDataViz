import json
from datetime import date

from src import silver as s


GID = 23651


def prod(pid, name, number=None, rarity=None):
    ext = []
    if rarity:
        ext.append({"name": "Rarity", "displayName": "Rarity", "value": rarity})
    if number:
        ext.append({"name": "Number", "displayName": "Number", "value": number})
    return {
        "productId": pid,
        "name": name,
        "cleanName": name,
        "categoryId": 3,
        "groupId": GID,
        "imageUrl": f"https://img/{pid}.jpg",
        "url": f"https://tcg/{pid}",
        "modifiedOn": "2024-12-23T20:27:39.373",
        "extendedData": ext,
    }


def preco(pid, sub="Normal", market=1.5, low=1.0, mid=1.4, high=3.0):
    return {
        "productId": pid,
        "lowPrice": low,
        "midPrice": mid,
        "highPrice": high,
        "marketPrice": market,
        "directLowPrice": None,
        "subTypeName": sub,
    }


def ok(results):
    return {"success": True, "errors": [], "results": results}


def montar_lake(tmp_path, dias):
    for dia, (products, prices) in dias.items():
        base = tmp_path / f"raw/tcgplayer/group_id={GID}/data={dia.isoformat()}"
        base.mkdir(parents=True)
        if products is not None:
            (base / "products.json").write_text(json.dumps(products))
        if prices is not None:
            (base / "prices.json").write_text(json.dumps(prices))
    return s.LocalLake(tmp_path)


class FakeWriter:
    def __init__(self):
        self.saidas = {}

    def __call__(self, lake, key, tabela, registros):
        self.saidas[key] = (tabela, registros)


def _precos(w, dia):
    key = f"silver/preco_diario/group_id={GID}/data={dia.isoformat()}/preco.parquet"
    return w.saidas[key][1]


def test_datas_anteriores_usam_primeiro_cadastro_valido_com_marca(tmp_path):
    anterior = date(2026, 10, 31)
    primeiro = date(2026, 11, 12)
    catalogo = [prod(1, "Pikachu ex", "057/191", "Double Rare")]
    lake = montar_lake(tmp_path, {
        anterior: (None, ok([preco(1, market=1.75)])),
        primeiro: (ok(catalogo), ok([preco(1, market=1.75)])),
    })
    w = FakeWriter()

    r = s.rebuild(lake, lake, writer=w)

    linha_anterior = _precos(w, anterior)[0]
    linha_primeira = _precos(w, primeiro)[0]
    assert linha_anterior["cadastro_retroativo"] is True
    assert linha_primeira["cadastro_retroativo"] is False
    assert linha_anterior["market_price"] == 1.75
    assert r["preco_diario"]["validos"] == 2
    assert r["preco_diario"]["quarentena"] == 0


def test_product_id_fora_do_cadastro_retroativo_continua_quarentena(tmp_path):
    anterior = date(2026, 10, 31)
    primeiro = date(2026, 11, 12)
    lake = montar_lake(tmp_path, {
        anterior: (None, ok([preco(999)])),
        primeiro: (ok([prod(1, "Pikachu ex", "057/191", "Double Rare")]), ok([preco(1)])),
    })
    w = FakeWriter()

    r = s.rebuild(lake, lake, writer=w)

    q = tmp_path / f"quarentena/preco_diario/group_id={GID}/data={anterior.isoformat()}/registros.jsonl"
    motivos = [json.loads(x)["motivo"] for x in q.read_text().splitlines()]
    assert motivos == ["product_id sem produto correspondente"]
    assert r["preco_diario"]["validos"] == 1
    assert r["preco_diario"]["quarentena"] == 1


def test_nenhum_preco_e_criado_e_contagens_sao_consistentes(tmp_path):
    anterior = date(2026, 10, 31)
    primeiro = date(2026, 11, 12)
    raw = preco(1, "Holofoil", market=2.25, low=1.5, mid=2.0, high=4.0)
    lake = montar_lake(tmp_path, {
        anterior: (None, ok([raw, preco(999)])),
        primeiro: (ok([prod(1, "Pikachu ex", "057/191", "Double Rare")]), ok([raw])),
    })
    w = FakeWriter()

    r = s.rebuild(lake, lake, writer=w)
    linhas = _precos(w, anterior) + _precos(w, primeiro)

    assert len(linhas) == 2
    assert all({k: v for k, v in x.items() if k in (
        "market_price", "low_price", "mid_price", "high_price", "acabamento"
    )} == {
        "market_price": 2.25,
        "low_price": 1.5,
        "mid_price": 2.0,
        "high_price": 4.0,
        "acabamento": "Holofoil",
    } for x in linhas)
    assert r["preco_diario"]["lidos"] == (
        r["preco_diario"]["validos"] + r["preco_diario"]["quarentena"]
    )


def test_dia_sem_products_depois_do_primeiro_continua_nao_retroativo(tmp_path):
    primeiro = date(2026, 11, 12)
    seguinte = date(2026, 11, 13)
    lake = montar_lake(tmp_path, {
        primeiro: (ok([prod(1, "Pikachu ex", "057/191", "Double Rare")]), ok([preco(1)])),
        seguinte: (None, ok([preco(1)])),
    })
    w = FakeWriter()

    s.rebuild(lake, lake, writer=w)

    assert _precos(w, primeiro)[0]["cadastro_retroativo"] is False
    assert _precos(w, seguinte)[0]["cadastro_retroativo"] is False


def test_reconstrucao_duas_vezes_e_deterministica(tmp_path):
    anterior = date(2026, 10, 31)
    primeiro = date(2026, 11, 12)
    lake = montar_lake(tmp_path, {
        anterior: (None, ok([preco(1)])),
        primeiro: (ok([prod(1, "Pikachu ex", "057/191", "Double Rare")]), ok([preco(1)])),
    })
    w1 = FakeWriter()
    w2 = FakeWriter()

    s.rebuild(lake, lake, writer=w1)
    s.rebuild(lake, lake, writer=w2)

    assert w1.saidas == w2.saidas


def test_sem_nenhum_products_tudo_continua_quarentena(tmp_path):
    dia = date(2026, 10, 31)
    lake = montar_lake(tmp_path, {dia: (None, ok([preco(1), preco(2)]))})
    w = FakeWriter()

    r = s.rebuild(lake, lake, writer=w)

    assert r["preco_diario"]["validos"] == 0
    assert r["preco_diario"]["quarentena"] == 2
    assert not any(k.startswith("silver/preco_diario/") for k in w.saidas)


def test_coluna_extra_nao_altera_colunas_do_contrato(tmp_path):
    pytest = __import__("pytest")
    pa = pytest.importorskip("pyarrow")
    schema = s._schemas(pa)["preco_diario"]
    nomes = schema.names

    contrato = [
        "data", "product_id", "group_id", "acabamento",
        "market_price", "low_price", "mid_price", "high_price",
        "moeda", "fonte", "chave_raw",
    ]
    assert nomes[:-1] == contrato
    assert nomes[-1] == "cadastro_retroativo"
    assert schema.field("cadastro_retroativo").type == pa.bool_()


def test_primeiro_catalogo_valido_ignora_catalogos_invalidos_anteriores(tmp_path):
    invalido = date(2026, 10, 31)
    sem_produtos_validos = date(2026, 11, 1)
    primeiro_valido = date(2026, 11, 12)
    lake = montar_lake(tmp_path, {
        invalido: ({"success": False, "errors": [], "results": []}, ok([preco(1)])),
        sem_produtos_validos: (ok([]), ok([preco(1)])),
        primeiro_valido: (
            ok([prod(1, "Pikachu ex", "057/191", "Double Rare")]),
            ok([preco(1)]),
        ),
    })
    w = FakeWriter()

    r = s.rebuild(lake, lake, writer=w)

    for dia in (invalido, sem_produtos_validos):
        linhas = _precos(w, dia)
        assert len(linhas) == 1
        assert linhas[0]["cadastro_retroativo"] is True
    assert _precos(w, primeiro_valido)[0]["cadastro_retroativo"] is False
    assert r["preco_diario"]["validos"] == 3
    assert r["preco_diario"]["quarentena"] == 0


def test_catalogo_retroativo_fixo_e_produto_posterior(tmp_path):
    anterior = date(2026, 10, 31)
    primeiro = date(2026, 11, 12)
    posterior = date(2026, 11, 13)
    lake = montar_lake(tmp_path, {
        anterior: (None, ok([preco(1), preco(2)])),
        primeiro: (
            ok([prod(1, "Pikachu ex", "057/191", "Double Rare")]),
            ok([preco(1), preco(2)]),
        ),
        posterior: (
            ok([
                prod(1, "Pikachu ex", "057/191", "Double Rare"),
                prod(2, "Novo produto", "058/191", "Rare"),
            ]),
            ok([preco(1), preco(2)]),
        ),
    })
    w = FakeWriter()

    r = s.rebuild(lake, lake, writer=w)

    anterior_linhas = _precos(w, anterior)
    anterior_por_id = {linha["product_id"]: linha for linha in anterior_linhas}
    assert anterior_por_id[1]["cadastro_retroativo"] is True
    assert set(anterior_por_id) == {1}

    q = tmp_path / f"quarentena/preco_diario/group_id={GID}/data={anterior.isoformat()}/registros.jsonl"
    motivos = [json.loads(x)["motivo"] for x in q.read_text().splitlines()]
    assert motivos == ["product_id sem produto correspondente"]

    posterior_por_id = {linha["product_id"]: linha for linha in _precos(w, posterior)}
    assert posterior_por_id[1]["cadastro_retroativo"] is False
    assert posterior_por_id[2]["cadastro_retroativo"] is False
    assert r["preco_diario"]["validos"] == 4
    assert r["preco_diario"]["quarentena"] == 2
