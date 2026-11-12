import logging

import pytest

from src import collector as c
from src.prefixo import PREFIXO_PROPRIO, validar_chave


class FakeS3Client:
    def __init__(self):
        self.calls = []

    def head_object(self, **kwargs):
        self.calls.append(("head_object", kwargs))
        return {}

    def put_object(self, **kwargs):
        self.calls.append(("put_object", kwargs))
        return {}


def fake_s3(client):
    storage = object.__new__(c.S3Storage)
    storage.bucket = "fake-bucket"
    storage.client = client
    return storage


def test_chave_do_prefixo_proprio_e_aceita():
    key = "raw/tcgplayer/group_id=23651/data=2026-11-11/prices.json"
    assert PREFIXO_PROPRIO == "group_id=23651"
    assert validar_chave(key) == key


@pytest.mark.parametrize(
    "key",
    [
        "raw/tcgplayer/group_id=24269/data=2026-11-11/prices.json",
        "raw/tcgplayer/data=2026-11-11/prices.json",
        "raw/group_id=23651/tcgplayer/group_id=24269/prices.json",
    ],
)
def test_local_storage_recusa_chave_fora_do_prefixo(key, tmp_path):
    storage = c.LocalStorage(tmp_path)
    with pytest.raises(ValueError, match="ERRO escrita recusada"):
        storage.put(key, b"payload")
    assert not list(tmp_path.rglob("*"))


def test_s3_storage_recusa_chave_e_nao_chama_cliente():
    client = FakeS3Client()
    storage = fake_s3(client)

    with pytest.raises(ValueError, match="group_id=24269.*group_id=23651"):
        storage.put(
            "raw/tcgplayer/group_id=24269/data=2026-11-11/prices.json", b"payload"
        )

    assert client.calls == []


def test_subir_local_recusa_chave_de_outra_colecao_antes_do_cliente(tmp_path):
    local = c.LocalStorage(tmp_path / "local")
    key = "raw/tcgplayer/group_id=24269/data=2026-11-11/prices.json"
    path = local.root / key
    path.parent.mkdir(parents=True)
    path.write_bytes(b"payload")
    client = FakeS3Client()

    with pytest.raises(ValueError, match="fora do prefixo group_id=23651"):
        c.subir_local(local, fake_s3(client))

    assert client.calls == []


def test_group_id_de_outra_colecao_faz_coletor_recusar(monkeypatch, caplog):
    monkeypatch.setenv("GROUP_ID", "24269")

    def storage_nao_deve_ser_criado():
        pytest.fail("o coletor tentou obter storage antes de recusar GROUP_ID")

    monkeypatch.setattr(c, "get_storage", storage_nao_deve_ser_criado)
    with caplog.at_level(logging.ERROR, logger="coletor"):
        status = c.main(["collect"])

    assert status != 0
    assert "GROUP_ID=24269" in caplog.text
    assert "group_id=23651" in caplog.text
