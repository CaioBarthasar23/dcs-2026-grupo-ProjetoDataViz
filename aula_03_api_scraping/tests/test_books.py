import pytest
from botocore.exceptions import ClientError

import src.collectors.books as books_module
from src.collectors.books import ColetorBooks
from src.manifest import create_manifest
from src.storage import GravadorS3, StorageConfig


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.events = []

    def gravar_raw(self, chave, corpo, metadados):
        assert isinstance(corpo, bytes)
        self.objects[chave] = (corpo, metadados)
        self.events.append(("raw", metadados["source-url"]))


def test_descobre_categorias_registra_robots_e_aplica_filtro(
    inicio_duas_categorias_html, fake_get
):
    fake_get.queue_response(404, b"not found")
    fake_get.queue_response(200, inicio_duas_categorias_html)
    fake_get.queue_response(200, b"<html><body></body></html>")
    fake_get.queue_response(200, b"<html><body></body></html>")
    storage = MemoryStorage()
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorBooks(
        get=fake_get,
        gravador=storage,
        manifesto=manifest,
        categorias="",
    )

    categories = collector.coletar("2026-11-02")

    assert len(fake_get.calls) == 4
    assert [category.name for category in categories]
    assert len(categories) == len(collector.categorias_descobertas)
    assert manifest.robots["status_http"] == 404
    assert manifest.robots["allowed_paths"] is None
    assert manifest.sources == ["books.toscrape.com"]
    assert storage.objects[manifest.robots["chave"]][0] == b"not found"
    assert len(storage.objects) == 4
    assert all(isinstance(body, bytes) for body, _ in storage.objects.values())
    assert all(item.estado == "gravado" for item in manifest.itens)


def test_percorre_next_ate_fim_sem_repetir_livro(
    inicio_uma_categoria_html, detalhe_html, fake_get
):
    first_page = (
        '<article class="product_pod"><h3><a href="../../../sharp_objects_997/index.html" '
        'title="Sharp Objects">Sharp Objects</a></h3>'
        '<p class="price_color">£47.82</p><p class="star-rating Five"></p></article>'
        '<li class="next"><a href="page-2.html">next</a></li>'
    ).encode()
    second_page = (
        '<article class="product_pod"><h3><a href="../../../sharp_objects_997/index.html" '
        'title="Sharp Objects">Sharp Objects</a></h3>'
        '<p class="price_color">£47.82</p><p class="star-rating Five"></p></article>'
    ).encode()
    fake_get.queue_response(404, b"not found")
    fake_get.queue_response(200, inicio_uma_categoria_html)
    fake_get.queue_response(200, first_page)
    fake_get.queue_response(200, detalhe_html)
    fake_get.queue_response(200, second_page)
    storage = MemoryStorage()
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorBooks(
        get=fake_get,
        gravador=storage,
        manifesto=manifest,
        categorias="",
    )

    collector.coletar("2026-11-02")

    assert len(fake_get.calls) == 5
    category_calls = [fake_get.calls[index][0] for index in (2, 4)]
    assert category_calls[0].endswith("/mystery_3/index.html")
    assert category_calls[1].endswith("/mystery_3/page-2.html")
    pages = collector.paginas_coletadas
    books = [book["url"] for page in pages for book in page.books]
    assert len(pages) == 2
    assert len(books) == len(set(books))
    assert len([item for item in manifest.itens if "/categoria=" in item.chave]) == 2
    assert all(storage.objects[item.chave][0] for item in manifest.itens if item.chave)


def test_detalhe_fornece_upc_estoque_categoria_e_raw_precede_parse(
    inicio_uma_categoria_html, detalhe_html, fake_get, monkeypatch
):
    listing_url = "https://books.toscrape.com/catalogue/sharp_objects_997/index.html"
    listing = (
        '<article class="product_pod"><h3><a href="../../../sharp_objects_997/index.html" '
        'title="Título da listagem">Título abreviado</a></h3>'
        '<p class="price_color">£12.34</p>'
        '<p class="star-rating Three"></p></article>'
    ).encode()
    fake_get.queue_response(404, b"not found")
    fake_get.queue_response(200, inicio_uma_categoria_html)
    fake_get.queue_response(200, listing)
    fake_get.queue_response(200, detalhe_html)
    storage = MemoryStorage()
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorBooks(
        get=fake_get,
        gravador=storage,
        manifesto=manifest,
        categorias="mystery",
    )
    parse_events = []
    parse_detail = books_module._detail_fields

    def tracked_parse(html, url=""):
        parse_events.append(("parse", url))
        storage.events.append(("parse", url))
        return parse_detail(html, url)

    monkeypatch.setattr(books_module, "_detail_fields", tracked_parse)

    collector.coletar("2026-11-02")

    assert len(collector.livros_coletados) == 1
    book = collector.livros_coletados[0]
    assert book.upc == "e00eb4fd7b871a48"
    assert book.em_estoque is True
    assert book.qtd_estoque == 20
    assert book.categoria == "Mystery"
    assert book.titulo == "Título da listagem"
    assert book.preco_gbp == 12.34
    assert book.url == listing_url
    detail_raw_index = storage.events.index(("raw", listing_url))
    parse_index = storage.events.index(("parse", listing_url))
    assert detail_raw_index < parse_index


def test_502_no_gravador_repite_put_na_mesma_chave_e_contabiliza_tentativa():
    class FlakyClient:
        def __init__(self):
            self.puts = []

        def put_object(self, **kwargs):
            self.puts.append(kwargs)
            if len(self.puts) == 1:
                raise ClientError(
                    {
                        "Error": {"Code": "502"},
                        "ResponseMetadata": {"HTTPStatusCode": 502},
                    },
                    "PutObject",
                )

    client = FlakyClient()
    gravador = GravadorS3(
        StorageConfig(endpoint_url="http://minio.test", bucket="raw"),
        client=client,
        max_attempts=3,
        sleep=lambda _: None,
        random_uniform=lambda low, high: low,
    )
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorBooks(
        get=lambda *_args, **_kwargs: None,
        gravador=gravador,
        manifesto=manifest,
    )
    body = b"<html>raw</html>"

    item = collector._gravar_resposta(
        url="https://books.toscrape.com/",
        data_ref="2026-11-02",
        resource="inicio.html",
        status_http=200,
        attempts=1,
        body=body,
    )

    assert len(client.puts) == 2
    assert [put["Key"] for put in client.puts] == [item.chave, item.chave]
    assert [put["Body"] for put in client.puts] == [body, body]
    assert item.tentativas == 2


def test_gravador_nao_repete_erro_s3_permanente():
    class RejectingClient:
        def __init__(self):
            self.puts = 0

        def put_object(self, **kwargs):
            self.puts += 1
            raise ClientError(
                {
                    "Error": {"Code": "400"},
                    "ResponseMetadata": {"HTTPStatusCode": 400},
                },
                "PutObject",
            )

    client = RejectingClient()
    gravador = GravadorS3(
        StorageConfig(endpoint_url="http://minio.test", bucket="raw"),
        client=client,
        sleep=lambda _: None,
    )

    with pytest.raises(ClientError):
        gravador.gravar_raw("raw/test.html", b"body", {})

    assert client.puts == 1


def test_gravador_limita_tentativas_transitorias():
    class UnavailableClient:
        def __init__(self):
            self.puts = 0

        def put_object(self, **kwargs):
            self.puts += 1
            raise ClientError(
                {
                    "Error": {"Code": "502"},
                    "ResponseMetadata": {"HTTPStatusCode": 502},
                },
                "PutObject",
            )

    client = UnavailableClient()
    gravador = GravadorS3(
        StorageConfig(endpoint_url="http://minio.test", bucket="raw"),
        client=client,
        max_attempts=2,
        sleep=lambda _: None,
    )

    with pytest.raises(ClientError):
        gravador.gravar_raw("raw/test.html", b"body", {})

    assert client.puts == 2


def test_coletor_detecta_mudanca_na_estrutura_html_da_listagem(fake_get):
    changed_html = b"""
    <main class="catalogue">
      <article class="book-card"><a href="/book/1">Book</a></article>
    </main>
    """
    fake_get.queue_response(404, b"not found")
    fake_get.queue_response(
        200,
        b"""
        <div class="side_categories">
          <a href="catalogue/category/books/mystery_3/index.html">Mystery</a>
        </div>
        """,
    )
    fake_get.queue_response(200, changed_html)
    storage = MemoryStorage()
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorBooks(
        get=fake_get,
        gravador=storage,
        manifesto=manifest,
        categorias="mystery",
    )

    with pytest.raises(ValueError, match="Estrutura HTML"):
        collector.coletar("2026-11-02")

    assert collector.paginas_coletadas == []
    assert manifest.itens[-1].estado == "gravado"
    assert storage.objects[manifest.itens[-1].chave][0] == changed_html
