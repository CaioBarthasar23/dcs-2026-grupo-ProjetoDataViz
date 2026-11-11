import hashlib

import pytest

from src.storage import (
    GravadorS3,
    StorageConfig,
    make_raw_key,
    save_ptax_raw,
    save_raw,
    validate_ascii_metadata,
)


def test_cliente_s3_nao_multiplica_retry_da_gravacao(monkeypatch):
    import src.storage as storage_module

    captured = {}

    def create_client(*args, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(storage_module.boto3, "client", create_client)
    GravadorS3(StorageConfig(endpoint_url="http://minio.test", bucket="raw"))

    assert captured["config"].retries["total_max_attempts"] == 1


def test_grava_html_bruto_bytes_e_metadados(detalhe_html):
    # RF-09, RNF-04, RNF-07
    result = save_raw(
        source_url="https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
        data_ref="2026-11-02",
        resource="livro=sharp-objects_997/detalhe",
        body=detalhe_html,
        metadata={"source-url": "https://books.toscrape.com/"},
    )
    assert result.body == detalhe_html
    assert result.sha256
    assert result.sha256 == hashlib.sha256(detalhe_html).hexdigest()
    assert result.key
    assert result.metadata["source-url"] == "https://books.toscrape.com/"
    assert result.metadata["sha256"] == result.sha256
    assert result.metadata["collected-at"]
    assert all(
        value.encode("ascii").decode("ascii") == value
        for value in result.metadata.values()
    )
    assert result.key == make_raw_key(
        "books_toscrape",
        "2026-11-02",
        "livro=sharp-objects_997/detalhe",
        detalhe_html,
    )


def test_grava_resposta_ptax_bruta_vazia(ptax_vazia):
    # RF-10, RNF-07
    result = save_ptax_raw(
        source_url="https://api.bcb.gov.br/ptax",
        moeda="GBP",
        data_ref="2026-11-02",
        window_start="11-02-2026",
        window_end="11-02-2026",
        body=ptax_vazia,
    )
    assert result.body == ptax_vazia
    assert result.sha256
    assert result.sha256 == hashlib.sha256(ptax_vazia).hexdigest()
    assert "moeda=GBP" in result.key
    assert "data=2026-11-02" in result.key


def test_reexecucao_reutiliza_chave_mesmo_conteudo(detalhe_html):
    # RF-09, RNF-07
    first = make_raw_key(
        "books_toscrape", "2026-11-02", "livro=sharp-objects_997/detalhe", detalhe_html
    )
    second = make_raw_key(
        "books_toscrape", "2026-11-02", "livro=sharp-objects_997/detalhe", detalhe_html
    )
    assert first == second
    assert "2026-11-02" in first
    assert "run-" not in first


def test_metadados_ascii_estrito():
    # RNF-04
    validate_ascii_metadata({"source-url": "https://example.test/a", "sha256": "abc"})
    with pytest.raises(UnicodeEncodeError):
        validate_ascii_metadata({"source-url": "https://example.test/ação"})
