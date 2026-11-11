import json
from datetime import date, datetime

import pytest

from src import silver as s

GID = 23651


# ---------- fixtures com a mesma forma dos arquivos reais ----------
def prod(pid, name, number=None, rarity=None, group=GID):
    ext = []
    if rarity:
        ext.append({"name": "Rarity", "displayName": "Rarity", "value": rarity})
    if number:
        ext.append({"name": "Number", "displayName": "Number", "value": number})
    return {
        "productId": pid, "name": name, "cleanName": name, "categoryId": 3, "groupId": group,
        "imageUrl": f"https://img/{pid}.jpg", "url": f"https://tcg/{pid}",
        "modifiedOn": "2024-12-23T20:27:39.373", "extendedData": ext,
    }


def preco(pid, sub="Normal", market=1.5, low=1.0, mid=1.4, high=3.0):
    return {"productId": pid, "lowPrice": low, "midPrice": mid, "highPrice": high,
            "marketPrice": market, "directLowPrice": None, "subTypeName": sub}


PRODUTOS = [
    prod(1, "Pikachu ex", "057/191", "Double Rare"),
    prod(2, "Charmander", "010/191", "Common"),
    prod(3, "Surging Sparks Booster Box"),
    prod(4, "Code Card - Surging Sparks Booster Pack", rarity="Code Card"),
]


class FakeWriter:
    def __init__(self):
        self.saidas = {}

    def __call__(self, lake, key, tabela, registros):
        self.saidas[key] = (tabela, registros)


def montar_lake(tmp_path, dias, ptax=None, cdi=None):
    """dias: {date: (products_payload, prices_payload)}"""
    for d, (pr, pc) in dias.items():
        base = tmp_path / f"raw/tcgplayer/group_id={GID}/data={d.isoformat()}"
        base.mkdir(parents=True)
        if pr is not None:
            (base / "products.json").write_text(json.dumps(pr))
        if pc is not None:
            (base / "prices.json").write_text(json.dumps(pc))
    for d, payload in (ptax or {}).items():
        b = tmp_path / f"raw/bcb_ptax/group_id={GID}/data={d.isoformat()}"
        b.mkdir(parents=True)
        (b / "cotacao.json").write_text(json.dumps(payload))
    for d, payload in (cdi or {}).items():
        b = tmp_path / f"raw/bcb_cdi/group_id={GID}/data={d.isoformat()}"
        b.mkdir(parents=True)
        (b / "cdi.json").write_text(json.dumps(payload))
    return s.LocalLake(tmp_path)


def ok(results):
    return {"success": True, "errors": [], "results": results}


# ---------- classificacao ----------
def test_classificacao():
    assert s.classificar(PRODUTOS[0]) == "carta"
    assert s.classificar(PRODUTOS[2]) == "selado"
    # Code Card nao tem numero, mas e carta (excluida por raridade nas perguntas)
    assert s.classificar(PRODUTOS[3]) == "carta"
    assert s.montar_produto(PRODUTOS[3])["raridade"] == "Code Card"


@pytest.mark.parametrize("nome,esperado", [
    ("Surging Sparks Booster Box", "booster_box"),
    ("Surging Sparks Booster Box Case", "booster_box_case"),
    ("Surging Sparks Half Booster Box", "half_booster_box"),
    ("Surging Sparks Elite Trainer Box", "elite_trainer_box"),
    ("Surging Sparks Pokemon Center Elite Trainer Box (Exclusive) Case", "elite_trainer_box_case"),
    ("Surging Sparks Booster Bundle (LGS)", "booster_bundle"),
    ("Surging Sparks Booster Bundle Case (LGS)", "booster_bundle_case"),
    ("Surging Sparks Booster Pack", "booster_pack"),
    ("Surging Sparks Sleeved Booster Pack Case", "booster_pack_case"),
    ("Surging Sparks Booster Pack Art Bundle [Set of 4]", "booster_pack_bundle"),
    ("Surging Sparks 3 Pack Blisters [Zapdos]", "blister"),
    ("Surging Sparks 3 Pack Blisters Case", "blister_case"),
    ("Surging Sparks Build & Battle Box", "build_and_battle_box"),
    ("Surging Sparks Build & Battle Box Display", "build_and_battle_box_display"),
    ("Surging Sparks Fun Pack", "fun_pack"),
])
def test_categoria_selado(nome, esperado):
    assert s.categoria_selado(nome) == esperado


# ---------- modelos ----------
def _preco_dados(**kw):
    base = s.montar_preco(preco(1), date(2026, 11, 3), GID, "k")
    base.update(kw)
    return base


def test_nulo_nao_e_zero():
    m = s.PrecoDiario(**_preco_dados(market_price=None))
    assert m.market_price is None


@pytest.mark.parametrize("valor", ["1.50", 0, -1.0, float("nan")])
def test_preco_invalido_nao_passa(valor):
    with pytest.raises(Exception):
        s.PrecoDiario(**_preco_dados(market_price=valor))


def test_preco_inteiro_do_json_e_aceito():
    assert s.PrecoDiario(**_preco_dados(low_price=1500)).low_price == 1500.0


# ---------- reconstrucao ----------
def test_rebuild_basico(tmp_path):
    d = date(2026, 11, 3)
    lake = montar_lake(tmp_path, {d: (ok(PRODUTOS), ok([
        preco(1, "Holofoil", 5.0), preco(1, "Normal", None), preco(2), preco(3)]))})
    w = FakeWriter()
    r = s.rebuild(lake, lake, writer=w)

    tab, regs = w.saidas[f"silver/preco_diario/group_id={GID}/data=2026-11-03/preco.parquet"]
    assert tab == "preco_diario" and len(regs) == 4
    assert [(x["product_id"], x["acabamento"]) for x in regs] == sorted(
        (x["product_id"], x["acabamento"]) for x in regs)  # ordem deterministica
    nulo = [x for x in regs if x["product_id"] == 1 and x["acabamento"] == "Normal"][0]
    assert nulo["market_price"] is None
    assert all(x["moeda"] == "USD" and x["fonte"] == "tcgplayer" for x in regs)
    assert r["preco_diario"] == {"lidos": 4, "validos": 4, "quarentena": 0}

    _, prods = w.saidas[f"silver/produto/group_id={GID}/produto.parquet"]
    tipos = {x["product_id"]: x["tipo_produto"] for x in prods}
    assert tipos == {1: "carta", 2: "carta", 3: "selado", 4: "carta"}
    assert [x for x in prods if x["product_id"] == 3][0]["categoria_selado"] == "booster_box"
    _, col = w.saidas[f"silver/colecao/group_id={GID}/colecao.parquet"]
    assert col[0]["group_id"] == GID and col[0]["responsavel"]


def test_quarentena_orfao_duplicado_e_texto(tmp_path):
    d = date(2026, 11, 3)
    lake = montar_lake(tmp_path, {d: (ok(PRODUTOS), ok([
        preco(1), preco(1),                  # duplicado
        preco(999),                          # produto inexistente
        preco(2, market="3.5"),              # preco como texto
        preco(3)]))})
    w = FakeWriter()
    r = s.rebuild(lake, lake, writer=w)
    assert r["preco_diario"]["validos"] == 2
    assert r["preco_diario"]["quarentena"] == 3
    q = (tmp_path / f"quarentena/preco_diario/group_id={GID}/data=2026-11-03/registros.jsonl")
    motivos = [json.loads(x)["motivo"] for x in q.read_text().splitlines()]
    assert any("duplicado" in m for m in motivos)
    assert any("sem produto" in m for m in motivos)
    assert any("market_price" in m for m in motivos)


def test_dia_sem_products_usa_os_produtos_ja_conhecidos(tmp_path):
    lake = montar_lake(tmp_path, {
        date(2026, 11, 3): (ok(PRODUTOS), ok([preco(1)])),
        date(2026, 11, 4): (None, ok([preco(1)])),
    })
    w = FakeWriter()
    s.rebuild(lake, lake, writer=w)
    assert f"silver/preco_diario/group_id={GID}/data=2026-11-04/preco.parquet" in w.saidas


def test_produto_mais_recente_prevalece(tmp_path):
    novo = [dict(PRODUTOS[0], name="Pikachu ex (novo nome)")]
    lake = montar_lake(tmp_path, {
        date(2026, 11, 3): (ok(PRODUTOS), ok([preco(1)])),
        date(2026, 11, 4): (ok(novo), ok([preco(1)])),
    })
    w = FakeWriter()
    s.rebuild(lake, lake, writer=w)
    _, prods = w.saidas[f"silver/produto/group_id={GID}/produto.parquet"]
    assert [x for x in prods if x["product_id"] == 1][0]["nome"] == "Pikachu ex (novo nome)"


def test_rebuild_e_reproduzivel(tmp_path):
    lake = montar_lake(tmp_path, {date(2026, 11, 3): (ok(PRODUTOS), ok([preco(2), preco(1)]))})
    w1, w2 = FakeWriter(), FakeWriter()
    s.rebuild(lake, lake, writer=w1)
    s.rebuild(lake, lake, writer=w2)
    assert w1.saidas == w2.saidas


# ---------- cambio e cdi ----------
BOLETINS = {"value": [
    {"cotacaoCompra": 5.4892, "cotacaoVenda": 5.4898, "dataHoraCotacao": "2026-11-03 10:08:11.1", "tipoBoletim": "Abertura"},
    {"cotacaoCompra": 5.4929, "cotacaoVenda": 5.4935, "dataHoraCotacao": "2026-11-03 13:03:09.514", "tipoBoletim": "Fechamento PTAX"},
]}


def test_cambio_normaliza_rotulo_e_ignora_dia_sem_boletim(tmp_path):
    lake = montar_lake(tmp_path, {}, ptax={
        date(2026, 11, 2): {"value": []},       # feriado: sem linha, sem quarentena
        date(2026, 11, 3): BOLETINS,
    })
    w = FakeWriter()
    r = s.rebuild(lake, lake, writer=w)
    _, regs = w.saidas[f"silver/cambio_diario/group_id={GID}/cambio.parquet"]
    assert len(regs) == 1
    assert regs[0]["data"] == date(2026, 11, 3) and regs[0]["boletim"] == "Fechamento"
    assert regs[0]["cotacao_venda"] == 5.4935
    assert regs[0]["data_hora_cotacao"] == datetime(2026, 11, 3, 13, 3, 9, 514000)
    assert r["cambio_diario"]["quarentena"] == 0


def test_cambio_sem_fechamento_vai_para_quarentena(tmp_path):
    lake = montar_lake(tmp_path, {}, ptax={date(2026, 11, 3): {"value": [BOLETINS["value"][0]]}})
    r = s.rebuild(lake, lake, writer=FakeWriter())
    assert r["cambio_diario"]["quarentena"] == 1


def test_cdi_janelas_sobrepostas_vale_a_primeira(tmp_path):
    lake = montar_lake(tmp_path, {}, cdi={
        date(2026, 11, 3): [{"data": "02/11/2026", "valor": "0.050788"}, {"data": "03/11/2026", "valor": "0,050788"}],
        date(2026, 11, 4): [{"data": "03/11/2026", "valor": "0.050788"}, {"data": "04/11/2026", "valor": "0.050788"}],
    })
    w = FakeWriter()
    s.rebuild(lake, lake, writer=w)
    _, regs = w.saidas[f"silver/cdi_diario/group_id={GID}/cdi.parquet"]
    assert [x["data"] for x in regs] == [date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4)]
    assert regs[1]["chave_raw"].endswith("data=2026-11-03/cdi.json")
    assert regs[1]["taxa_dia"] == pytest.approx(0.050788)


# ---------- Parquet de verdade (so roda onde ha pyarrow) ----------
def test_parquet_tipos_do_contrato(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    lake = montar_lake(tmp_path, {date(2026, 11, 3): (ok(PRODUTOS), ok([preco(1, market=None), preco(2)]))},
                       ptax={date(2026, 11, 3): BOLETINS})
    s.rebuild(lake, lake)  # escritor real
    t = pq.read_table(tmp_path / f"silver/preco_diario/group_id={GID}/data=2026-11-03/preco.parquet")
    assert t.schema.field("product_id").type == pa.int32()
    assert t.schema.field("data").type == pa.date32()
    assert t.schema.field("market_price").type == pa.float64()
    assert t.column("market_price").null_count == 1  # nulo continua nulo
    c = pq.read_table(tmp_path / f"silver/cambio_diario/group_id={GID}/cambio.parquet")
    assert c.schema.field("data_hora_cotacao").type == pa.timestamp("us")
