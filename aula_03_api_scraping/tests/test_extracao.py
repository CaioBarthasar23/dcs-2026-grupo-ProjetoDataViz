from unittest.mock import Mock

from src.extractor import (
    extract_books,
    extract_quotes,
    validate_extraction,
)
from src.models import serialize_book, serialize_quote


def test_le_so_minio_sem_chamada_http(detalhe_html):
    # RF-11, RNF-09
    storage = Mock(read_raw=Mock(return_value=detalhe_html))
    http_get = Mock(side_effect=AssertionError("Extrator não deve usar HTTP"))
    rows = extract_books(storage=storage, keys=["raw/book.html"], http_get=http_get)
    assert rows
    http_get.assert_not_called()
    storage.read_raw.assert_called_once_with("raw/book.html")


def test_extrai_upc_estoque_e_preco_das_fixtures(detalhe_html, categoria_html):
    # RF-11, RNF-01
    rows = extract_books(
        storage=Mock(read_raw=Mock(side_effect=[categoria_html, detalhe_html])),
        keys=["raw/listing.html", "raw/detail.html"],
    )
    assert rows[0].upc == "e00eb4fd7b871a48"
    assert rows[0].preco_gbp == 47.82
    assert rows[0].qtd_estoque == 20


def test_decodifica_charset_sem_alterar_raw(detalhe_html):
    # RF-11, RNF-01
    original = bytes(detalhe_html)
    extract_books(storage=Mock(read_raw=Mock(return_value=original)), keys=["raw/detail.html"])
    assert original == detalhe_html


def test_avaliacao_preserva_rotulo(detalhe_html, categoria_html):
    # RF-11, RNF-01
    rows = extract_books(
        storage=Mock(read_raw=Mock(side_effect=[categoria_html, detalhe_html])),
        keys=["raw/listing.html", "raw/detail.html"],
    )
    assert rows[0].avaliacao in {"One", "Two", "Three", "Four", "Five"}
    assert isinstance(rows[0].avaliacao, str)


def test_cotacao_emite_campos_exatos(ptax_fechamento):
    # RF-12, RNF-01
    rows = extract_quotes(storage=Mock(read_raw=Mock(return_value=ptax_fechamento)), keys=["raw/ptax.json"])
    serialized = serialize_quote(rows[0])
    assert set(serialized) == {
        "moeda",
        "dataHoraCotacao",
        "tipoBoletim",
        "cotacaoCompra",
        "cotacaoVenda",
    }
    assert serialized["moeda"] == "GBP"
    assert serialized["dataHoraCotacao"].startswith("2026-10-30")


def test_divergencia_contagem_bloqueia_publicacao():
    # RF-14, RNF-01
    result = validate_extraction(extracted=999, declared=1000)
    assert result.state == "falha"
    assert result.difference == -1
    assert result.publishable is False


def test_livro_serializa_exatamente_nove_campos():
    # RF-11
    serialized = serialize_book(
        {
            "upc": "e00eb4fd7b871a48",
            "url": "https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
            "titulo": "Sharp Objects",
            "categoria": "Mystery",
            "avaliacao": "Four",
            "preco_gbp": 47.82,
            "em_estoque": True,
            "qtd_estoque": 20,
            "coletado_em": "2026-11-02T03:56:00Z",
        }
    )
    assert len(serialized) == 9
    assert set(serialized) == {
        "upc",
        "url",
        "titulo",
        "categoria",
        "avaliacao",
        "preco_gbp",
        "em_estoque",
        "qtd_estoque",
        "coletado_em",
    }
