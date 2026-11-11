import json

from src.models import Cotacao, Livro


def test_livro_e_cotacao_serializam_campos_exatos():
    book = Livro(
        upc="123",
        url="https://example.test/book",
        titulo="Book",
        categoria="Mystery",
        avaliacao="Five",
        preco_gbp=12.5,
        em_estoque=True,
        qtd_estoque=3,
        coletado_em="2026-11-02T00:00:00Z",
    )
    quote = Cotacao(
        moeda="GBP",
        dataHoraCotacao="2026-11-02 13:00:00",
        tipoBoletim="Fechamento",
        cotacaoCompra=7.1,
        cotacaoVenda=7.2,
    )

    book_line = book.para_json()
    quote_line = quote.para_json()
    serialized_book = json.loads(book_line)
    serialized_quote = json.loads(quote_line)

    assert set(serialized_book) == {
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
    assert len(serialized_book) == 9
    assert isinstance(serialized_book["preco_gbp"], float)
    assert isinstance(serialized_book["em_estoque"], bool)
    assert isinstance(serialized_book["qtd_estoque"], int)
    assert set(serialized_quote) == {
        "moeda",
        "dataHoraCotacao",
        "tipoBoletim",
        "cotacaoCompra",
        "cotacaoVenda",
    }
    assert len(serialized_quote) == 5
    assert isinstance(serialized_quote["cotacaoCompra"], float)
    assert isinstance(serialized_quote["cotacaoVenda"], float)
