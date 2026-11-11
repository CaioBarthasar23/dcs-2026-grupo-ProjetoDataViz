from datetime import date
from urllib.parse import parse_qs, urlsplit

import pytest

from src.collectors.books import (
    collect_robots,
    collect_category,
    discover_categories,
    extract_book,
    select_categories,
)
from src.collectors.ptax import build_ptax_url, collect_ptax, format_ptax_date
from src.http import get_with_retry, get_with_timeout, validate_politeness


@pytest.fixture
def robots_404(fake_get):
    fake_get.queue_response(404, b"not found")
    return fake_get


def test_descobre_categorias_sem_total_fixo(
    inicio_html, inicio_uma_categoria_html, inicio_duas_categorias_html, fake_get
):
    # RF-01
    categories = discover_categories(inicio_html, get=fake_get)
    assert categories
    assert all(category.name and category.url for category in categories)
    one = discover_categories(inicio_uma_categoria_html, get=fake_get)
    two = discover_categories(inicio_duas_categorias_html, get=fake_get)
    assert len(two) > len(one)
    assert len(fake_get.calls) == 0


def test_pagina_next_ate_fim(categoria_html, categoria_p2_html, fake_get):
    # RF-02
    fake_get.queue_response(200, categoria_p2_html)
    pages = collect_category(
        "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
        get=fake_get,
        first_html=categoria_html,
    )
    assert len(pages) == 2
    assert len(fake_get.calls) == 1
    assert fake_get.calls[0][0] == (
        "https://books.toscrape.com/catalogue/category/books/mystery_3/page-2.html"
    )
    assert len({book.url for page in pages for book in page.books}) == sum(
        len(page.books) for page in pages
    )


def test_filtro_categorias_configurado():
    # RF-03
    selected = select_categories(["mystery", "romance"], "mystery")
    assert [category.name for category in selected] == ["mystery"]
    assert len(select_categories(["mystery", "romance"], "")) == 2


def test_visita_detalhe_para_upc_estoque_categoria(detalhe_html, categoria_html, fake_get):
    # RF-04
    book = extract_book(categoria_html, detail_html=detalhe_html, get=fake_get)
    assert book.upc == "e00eb4fd7b871a48"
    assert book.em_estoque is True
    assert book.qtd_estoque == 20
    assert book.categoria == "Mystery"
    assert book.titulo == "Sharp Objects"
    assert book.preco_gbp == 47.82


def test_registra_robots_404_sem_inferir_permissao(robots_404):
    # RF-05
    result = collect_robots(get=robots_404)
    assert result.status_http == 404
    assert result.body == b"not found"
    assert result.url.endswith("/robots.txt")
    assert result.consultado_em
    assert result.allowed_paths is None


def test_user_agent_intervalo_e_sequencial(fake_get):
    # RF-06, RNF-03
    fake_get.queue_response(200, b"one")
    fake_get.queue_response(200, b"two")
    result = validate_politeness(
        urls=["https://books.toscrape.com/a", "https://books.toscrape.com/b"],
        get=fake_get,
        user_agent="aula_03_api_scraping",
        min_interval=1.0,
    )
    assert result.max_concurrent == 1
    assert result.user_agent_identifiable
    assert result.minimum_start_interval >= 1.0
    assert len(fake_get.calls) == 2
    assert all(
        call[1]["headers"]["User-Agent"] == "aula_03_api_scraping"
        for call in fake_get.calls
    )


def test_consulta_ptax_e_seleciona_fechamento(ptax_fechamento, fake_get):
    # RF-07
    quote = collect_ptax(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 10, 30),
        response_body=ptax_fechamento,
        get=fake_get,
    )
    assert quote.tipoBoletim == "Fechamento"
    assert quote.moeda == "GBP"
    assert quote.dataHoraCotacao.startswith("2026-10-30")


def test_ptax_sem_fechamento_marca_incompleta(ptax_vazia, fake_get):
    # RF-08
    result = collect_ptax(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 11, 2),
        response_body=ptax_vazia,
        get=fake_get,
    )
    assert result.quote is None
    assert result.response_body == ptax_vazia
    assert result.execution_state == "incompleta"


def test_ptax_sem_fechamento_elegivel_marca_incompleta(
    ptax_sem_fechamento_elegivel, fake_get
):
    # RF-08
    result = collect_ptax(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 10, 30),
        response_body=ptax_sem_fechamento_elegivel,
        get=fake_get,
    )
    assert result.quote is None
    assert result.response_body == ptax_sem_fechamento_elegivel
    assert result.execution_state == "incompleta"


def test_envia_data_ptax_no_formato_aceito():
    # RF-16
    assert format_ptax_date(date(2026, 10, 24)) == "10-24-2026"
    url = build_ptax_url(
        window_start=date(2026, 10, 24),
        window_end=date(2026, 11, 2),
    )
    query = parse_qs(urlsplit(url).query)
    assert query["@moeda"] == ["'GBP'"]
    assert query["@dataInicial"] == ["'10-24-2026'"]
    assert query["@dataFinalCotacao"] == ["'11-02-2026'"]
    assert query["$format"] == ["json"]


def test_ptax_http_500_registra_falha_de_consulta(fake_get):
    # RF-16
    for _ in range(4):
        fake_get.queue_response(500, b"invalid date")
    result = collect_ptax(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 10, 24),
        response_body=None,
        get=fake_get,
    )
    assert result.status_http == 500
    assert result.execution_state == "falha"
    assert "500" in result.error
    assert "incompleta" != result.execution_state
    assert len(fake_get.calls) == 4


def test_timeout_explicito_conexao_leitura():
    # RNF-02
    elapsed = [0.0]
    calls = []

    def unresponsive_get(url, *, timeout):
        calls.append((url, timeout))
        elapsed[0] += sum(timeout)
        raise TimeoutError("read timeout")

    with pytest.raises(TimeoutError):
        get_with_timeout(
            "https://books.toscrape.com/",
            get=unresponsive_get,
            timeout=(5.0, 10.0),
        )
    timeout = calls[-1][1]
    assert timeout == (5.0, 10.0)
    assert all(0 < part < float("inf") for part in timeout)
    assert elapsed[0] == 15.0
    assert elapsed[0] <= 15.0


def test_respeita_retry_after_em_429(fake_get):
    # RNF-06
    waits = []
    fake_get.queue_response(429, headers={"Retry-After": "2"})
    fake_get.queue_response(200, b"ok")
    response = get_with_retry(
        "https://books.toscrape.com/",
        get=fake_get,
        sleep=waits.append,
    )
    assert response.content == b"ok"
    assert len(fake_get.calls) == 2
    assert waits == [2.0]


def test_repete_read_timeout_e_5xx_com_limite(fake_get):
    # RNF-06
    transient_failures = [
        ConnectionError("connection failed"),
        TimeoutError("read timeout"),
        (408, b"request timeout"),
        (503, b"unavailable"),
    ]
    for failure in transient_failures:
        fake_get.responses.clear()
        fake_get.calls.clear()
        waits = []
        if isinstance(failure, tuple):
            fake_get.queue_response(*failure)
        else:
            fake_get.responses.append(failure)
        fake_get.queue_response(200, b"ok")
        response = get_with_retry(
            "https://books.toscrape.com/",
            get=fake_get,
            max_attempts=4,
            sleep=waits.append,
            random_uniform=lambda low, high: high,
        )
        assert response.status_code == 200
        assert len(fake_get.calls) == 2
        assert waits == [0.5]

    fake_get.responses.clear()
    fake_get.calls.clear()
    waits = []
    for _ in range(4):
        fake_get.queue_response(503, b"unavailable")
    response = get_with_retry(
        "https://books.toscrape.com/",
        get=fake_get,
        max_attempts=4,
        sleep=waits.append,
        random_uniform=lambda low, high: high,
    )
    assert response.status_code == 503
    assert len(fake_get.calls) == 4
    assert waits == [0.5, 1.0, 2.0]


def test_nao_repete_outros_4xx(fake_get):
    # RNF-06
    fake_get.queue_response(404, b"not found")
    response = get_with_retry("https://books.toscrape.com/", get=fake_get)
    assert response.status_code == 404
    assert len(fake_get.calls) == 1
