import logging

import pytest

from src import silver


class FakeS3Client:
    def __init__(self):
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(kwargs)
        return {}


def fake_s3_lake(client):
    storage = type("FakeStorage", (), {"bucket": "fake-bucket", "client": client})()
    return silver.S3Lake(storage)


def test_local_lake_grava_chave_da_colecao(tmp_path):
    lake = silver.LocalLake(tmp_path)
    key = "silver/produto/group_id=23651/produto.parquet"

    lake.put(key, b"dados")

    assert (tmp_path / key).read_bytes() == b"dados"


@pytest.mark.parametrize(
    "key",
    [
        "silver/produto/group_id=24269/produto.parquet",
        "silver/produto/produto.parquet",
    ],
)
def test_local_lake_recusa_chave_antes_de_criar_arquivos(tmp_path, key):
    lake = silver.LocalLake(tmp_path)

    with pytest.raises(ValueError, match="ERRO escrita recusada"):
        lake.put(key, b"dados")

    assert list(tmp_path.iterdir()) == []


def test_s3_lake_grava_chave_da_colecao():
    client = FakeS3Client()
    lake = fake_s3_lake(client)
    key = "quarentena/produto/group_id=23651/data=2026-11-14/registros.jsonl"

    lake.put(key, b"dados")

    assert [call["Key"] for call in client.calls] == [key]


@pytest.mark.parametrize(
    "key",
    [
        "silver/produto/group_id=24269/produto.parquet",
        "silver/produto/produto.parquet",
    ],
)
def test_s3_lake_recusa_chave_antes_de_chamar_cliente(key):
    client = FakeS3Client()
    lake = fake_s3_lake(client)

    with pytest.raises(ValueError, match="ERRO escrita recusada"):
        lake.put(key, b"dados")

    assert client.calls == []


def test_rebuild_recusa_group_id_alheio_antes_de_invocar_writer():
    class FonteVazia:
        def datas(self, prefix):
            return []

    escritas = []

    def writer(lake, key, tabela, registros):
        escritas.append(key)

    with pytest.raises(ValueError, match="ERRO escrita recusada"):
        silver.rebuild(FonteVazia(), object(), writer=writer, group_id=24269)

    assert escritas == []


def test_main_recusa_group_id_diferente_antes_de_criar_lakes(monkeypatch, caplog):
    monkeypatch.setenv("GROUP_ID", "24269")

    def lake_nao_deve_ser_criado(tipo):
        pytest.fail(f"main criou lake {tipo!r} antes de recusar GROUP_ID")

    monkeypatch.setattr(silver, "make_lake", lake_nao_deve_ser_criado)
    with caplog.at_level(logging.ERROR, logger="silver"):
        status = silver.main(["rebuild", "--fonte", "local", "--destino", "local"])

    assert status != 0
    assert "GROUP_ID=24269" in caplog.text
    assert "group_id=23651" in caplog.text
