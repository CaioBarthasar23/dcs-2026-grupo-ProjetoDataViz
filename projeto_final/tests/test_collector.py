import json
from datetime import datetime

import pytest

from src import collector as c

TZ = c.TZ


class FakeResp:
    def __init__(self, body):
        self.content = json.dumps(body).encode()
        self._body = body

    def json(self):
        return self._body


def fake_get_factory(estado):
    def fake_get(url, tentativas=3):
        estado["chamadas"] += 1
        if "/products" in url:
            return FakeResp({"success": True, "results": [{"productId": 1}]})
        if "/prices" in url:
            return FakeResp({"success": True, "results": [{"productId": 1, "marketPrice": 2.5}]})
        if "olinda" in url:
            return FakeResp({"value": estado["ptax"]})
        if "bcdata" in url:
            return FakeResp([{"data": "30/10/2026", "valor": "0.050788"}])
        raise AssertionError(url)

    return fake_get


FECH = [{"tipoBoletim": "Fechamento", "cotacaoCompra": 5.01, "cotacaoVenda": 5.02}]


def test_grava_tudo_e_nao_duplica(tmp_path, monkeypatch):
    estado = {"chamadas": 0, "ptax": FECH}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    st = c.LocalStorage(tmp_path)
    agora = datetime(2026, 10, 30, 18, 0, tzinfo=TZ)

    r1 = c.coletar(st, agora)
    assert all(v == "gravado" for v in r1.values()), r1
    assert len(list((tmp_path / "raw").rglob("*.json"))) == 4

    chamadas = estado["chamadas"]
    r2 = c.coletar(st, agora)
    assert all(v == "ja existia" for v in r2.values()), r2
    assert estado["chamadas"] == chamadas  # nem chama a rede de novo


def test_tcgcsv_nao_coleta_antes_da_atualizacao(tmp_path, monkeypatch):
    estado = {"chamadas": 0, "ptax": FECH}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    st = c.LocalStorage(tmp_path)
    r = c.coletar(st, datetime(2026, 10, 31, 11, 0, tzinfo=TZ))
    d = datetime(2026, 10, 31).date()
    assert r[c.key_tcg(d, "products")].startswith("ignorado")
    assert r[c.key_tcg(d, "prices")].startswith("ignorado")
    assert not (tmp_path / c.key_tcg(d, "products")).exists()
    # e depois das 18h a coleta correta ainda e possivel (nao caiu em "ja existia")
    r2 = c.coletar(st, datetime(2026, 10, 31, 18, 30, tzinfo=TZ))
    assert r2[c.key_tcg(d, "products")] == "gravado"


def test_ptax_aceita_rotulo_fechamento_ptax(tmp_path, monkeypatch):
    rotulo = [
        {"tipoBoletim": "Abertura", "cotacaoCompra": 5.0, "cotacaoVenda": 5.01},
        {"tipoBoletim": "Fechamento PTAX", "cotacaoCompra": 5.01, "cotacaoVenda": 5.02},
    ]
    estado = {"chamadas": 0, "ptax": rotulo}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    r = c.coletar(c.LocalStorage(tmp_path), datetime(2026, 11, 3, 18, 30, tzinfo=TZ))
    assert r[c.key_ptax(datetime(2026, 11, 3).date())] == "gravado"


def test_ptax_sem_fechamento_informa_os_tipos(tmp_path, monkeypatch):
    estado = {"chamadas": 0, "ptax": [{"tipoBoletim": "Abertura"}]}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    r = c.coletar(c.LocalStorage(tmp_path), datetime(2026, 11, 3, 18, 30, tzinfo=TZ))
    msg = r[c.key_ptax(datetime(2026, 11, 3).date())]
    assert msg.startswith("ignorado") and "Abertura" in msg


def test_backfill_ptax_grava_e_nao_duplica(tmp_path, monkeypatch):
    from datetime import date

    estado = {"chamadas": 0, "ptax": FECH}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    st = c.LocalStorage(tmp_path)
    r1 = c.backfill_ptax(st, date(2026, 11, 3), date(2026, 11, 6))
    assert list(r1.values()) == ["gravado"] * 4
    r2 = c.backfill_ptax(st, date(2026, 11, 3), date(2026, 11, 6))
    assert list(r2.values()) == ["ja existia"] * 4


def test_nao_sobrescreve_objeto_existente(tmp_path):
    st = c.LocalStorage(tmp_path)
    st.put("raw/x.json", b"original")
    with pytest.raises(FileExistsError):
        st.put("raw/x.json", b"novo")
    assert (tmp_path / "raw/x.json").read_bytes() == b"original"


def test_ptax_sem_fechamento_de_manha_nao_grava(tmp_path, monkeypatch):
    estado = {"chamadas": 0, "ptax": []}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    st = c.LocalStorage(tmp_path)
    r = c.coletar(st, datetime(2026, 10, 30, 9, 0, tzinfo=TZ))
    assert r[c.key_ptax(datetime(2026, 10, 30).date())].startswith("ignorado")


def test_ptax_vazia_a_tarde_grava_como_sem_boletim(tmp_path, monkeypatch):
    estado = {"chamadas": 0, "ptax": []}
    monkeypatch.setattr(c, "http_get", fake_get_factory(estado))
    st = c.LocalStorage(tmp_path)
    r = c.coletar(st, datetime(2026, 10, 31, 18, 0, tzinfo=TZ))  # sabado
    assert "sem boletim" in r[c.key_ptax(datetime(2026, 10, 31).date())]


def test_falha_de_uma_fonte_nao_derruba_as_outras(tmp_path, monkeypatch):
    base = fake_get_factory({"chamadas": 0, "ptax": FECH})

    def get(url, tentativas=3):
        if "olinda" in url:
            raise RuntimeError("bcb fora do ar")
        return base(url)

    monkeypatch.setattr(c, "http_get", get)
    r = c.coletar(c.LocalStorage(tmp_path), datetime(2026, 10, 30, 18, 0, tzinfo=TZ))
    assert any(v.startswith("ERRO") for v in r.values())
    assert sum(v == "gravado" for v in r.values()) == 3


def test_upload_nao_sobrescreve(tmp_path):
    local = c.LocalStorage(tmp_path / "local")
    destino = c.LocalStorage(tmp_path / "destino")
    local.put("raw/a.json", b"1")
    local.put("raw/b.json", b"2")
    destino.put("raw/a.json", b"ja estava la")
    cont = c.subir_local(local, destino)
    assert cont == {"enviados": 1, "ja_existiam": 1}
    assert (tmp_path / "destino/raw/a.json").read_bytes() == b"ja estava la"
