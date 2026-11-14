import json
import logging
from datetime import date

import pytest

from src import collector as c, silver


class FakeResp:
    def __init__(self, body):
        self.content = json.dumps(body).encode("utf-8")
        self._body = body

    def json(self):
        return self._body


FECHAMENTO = {
    "value": [
        {
            "tipoBoletim": "Fechamento PTAX",
            "cotacaoCompra": 5.01,
            "cotacaoVenda": 5.02,
        }
    ]
}


def test_backfill_grava_data_ptax_ausente_no_prefixo_proprio(tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(c, "http_get", lambda url: (chamadas.append(url), FakeResp(FECHAMENTO))[1])
    storage = c.LocalStorage(tmp_path)
    dia = date(2026, 10, 29)

    resultado = c.backfill_ptax(storage, dia, dia)

    key = c.key_ptax(dia)
    assert resultado == {key: "gravado"}
    assert (tmp_path / key).read_bytes() == json.dumps(FECHAMENTO).encode("utf-8")
    assert len(chamadas) == 1
    assert "group_id=23651" in key.split("/")


def test_backfill_nao_altera_bytes_da_chave_que_ja_existia(tmp_path, monkeypatch):
    storage = c.LocalStorage(tmp_path)
    dia = date(2026, 10, 30)
    key = c.key_ptax(dia)
    original = b'{"objeto":"bruto-original"}\n'
    storage.put(key, original)
    antes = (tmp_path / key).read_bytes()
    monkeypatch.setattr(c, "http_get", lambda url: pytest.fail("nao deveria consultar o BCB"))

    resultado = c.backfill_ptax(storage, dia, dia)

    depois = (tmp_path / key).read_bytes()
    assert resultado == {key: "ja existia"}
    assert depois == antes == original


def test_resposta_vazia_historica_grava_objeto_vazio_com_marca_de_lacuna(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(c, "http_get", lambda url: FakeResp({"value": []}))
    storage = c.LocalStorage(tmp_path)
    dia = date(2026, 10, 31)

    resultado = c.backfill_ptax(storage, dia, dia)

    key = c.key_ptax(dia)
    assert resultado == {key: "gravado (sem boletim no dia)"}
    payload = json.loads((tmp_path / key).read_bytes())
    assert payload == {"value": []}
    assert not any("cotacaoCompra" in row or "cotacaoVenda" in row for row in payload["value"])


def test_resposta_nao_vazia_sem_fechamento_e_ignorada(tmp_path, monkeypatch):
    monkeypatch.setattr(
        c,
        "http_get",
        lambda url: FakeResp({"value": [{"tipoBoletim": "Abertura"}]}),
    )
    storage = c.LocalStorage(tmp_path)
    dia = date(2026, 10, 28)

    resultado = c.backfill_ptax(storage, dia, dia)

    key = c.key_ptax(dia)
    assert "ignorado" in resultado[key]
    assert "Abertura" in resultado[key]
    assert not (tmp_path / key).exists()


def test_backfill_grava_todas_as_chaves_no_group_id_proprio(tmp_path, monkeypatch):
    chaves_gravadas = []
    original_put = c.LocalStorage.put

    def put_com_registro(storage, key, data):
        chaves_gravadas.append(key)
        original_put(storage, key, data)

    monkeypatch.setattr(c.LocalStorage, "put", put_com_registro)
    monkeypatch.setattr(c, "http_get", lambda url: FakeResp(FECHAMENTO))
    storage = c.LocalStorage(tmp_path)

    c.backfill_ptax(storage, date(2026, 10, 27), date(2026, 10, 29))

    assert chaves_gravadas
    assert all("group_id=23651" in key.split("/") for key in chaves_gravadas)


def test_main_recusa_group_id_alheio_antes_de_obter_storage(monkeypatch, caplog):
    monkeypatch.setenv("GROUP_ID", "24269")
    monkeypatch.setattr(
        c,
        "get_storage",
        lambda: pytest.fail("nao deveria obter storage com GROUP_ID alheio"),
    )

    with caplog.at_level(logging.ERROR, logger="coletor"):
        status = c.main(["backfill-ptax", "--de", "2026-10-24", "--ate", "2026-10-30"])

    assert status != 0
    assert "GROUP_ID=24269" in caplog.text
    assert "group_id=23651" in caplog.text


def test_silver_ignora_objeto_ptax_vazio_sem_criar_cambio_ou_zero(tmp_path):
    raw = silver.LocalLake(tmp_path / "raw")
    raw.put(
        "raw/bcb_ptax/group_id=23651/data=2026-10-31/cotacao.json",
        b'{"value": []}',
    )
    escritas = []

    def writer(destino, key, tabela, registros):
        escritas.append((key, tabela, registros))

    silver.rebuild(raw, object(), writer=writer, group_id=23651)

    cambios = [registro for _, tabela, registros in escritas if tabela == "cambio_diario" for registro in registros]
    assert not cambios
    assert not any(tabela == "cambio_diario" for _, tabela, _ in escritas)
    assert all(
        registro.get("cotacao_compra") != 0 and registro.get("cotacao_venda") != 0
        for registro in cambios
    )
