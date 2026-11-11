import pytest

from src.extractor import Extrator
from src.manifest import create_manifest, record_item


class MemoryStorage:
    def __init__(self, objects):
        self.objects = objects
        self.read_keys = []
        self.bronze = {}

    def ler_raw(self, key):
        self.read_keys.append(key)
        return self.objects[key]

    def gravar_bronze(self, key, lines):
        self.bronze[key] = list(lines)


def test_extrator_le_raw_sem_cliente_http_e_produz_registros(
    categoria_html, detalhe_html, ptax_fechamento, monkeypatch
):
    listing_key = "raw/books/listing.html"
    detail_key = "raw/books/detail.html"
    quote_key = "raw/ptax/moeda=GBP/janela=2026-10-29_a_2026-11-02.json"
    storage = MemoryStorage(
        {
            listing_key: categoria_html,
            detail_key: detalhe_html,
            quote_key: ptax_fechamento,
        }
    )
    manifest = create_manifest(data_ref="2026-11-02")
    record_item(
        manifest,
        url="https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
        status_http=200,
        attempts=1,
        bytes_received=len(categoria_html),
        state="gravado",
        key=listing_key,
        sha256="listing-hash",
    )
    record_item(
        manifest,
        url="https://books.toscrape.com/catalogue/sharp-objects_997/index.html",
        status_http=200,
        attempts=1,
        bytes_received=len(detalhe_html),
        state="gravado",
        key=detail_key,
        sha256="detail-hash",
    )
    record_item(
        manifest,
        url="https://olinda.bcb.gov.br/ptax",
        status_http=200,
        attempts=1,
        bytes_received=len(ptax_fechamento),
        state="gravado",
        key=quote_key,
        sha256="quote-hash",
    )
    import requests

    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("extrator não pode consultar HTTP")
        ),
    )
    extractor = Extrator(gravador=storage, manifesto=manifest)

    result = extractor.extrair()

    assert len(result.livros) == 1
    assert result.livros[0].upc == "e00eb4fd7b871a48"
    assert len(result.cotacoes) == 1
    assert result.cotacoes[0].dataHoraCotacao.startswith("2026-10-30")
    assert set(storage.read_keys) == {listing_key, detail_key, quote_key}


def test_publica_jsonl_apos_validacao_e_nao_publica_contagem_invalida(
    categoria_html, detalhe_html
):
    from src.extractor import ExtractionResult
    from src.models import Livro

    storage = MemoryStorage({})
    manifest = create_manifest(data_ref="2026-11-02")
    extractor = Extrator(gravador=storage, manifesto=manifest)
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
    result = ExtractionResult(livros=[book], cotacoes=[])

    outcome = extractor.publicar(
        result,
        livros_declarados=1,
        cotacoes_declaradas=0,
    )

    assert outcome.execution_state == "sucesso"
    assert set(storage.bronze) == {
        "bronze/livros/data=2026-11-02/livros.jsonl",
        "bronze/cotacoes/data=2026-11-02/cotacoes.jsonl",
    }
    assert len(storage.bronze["bronze/livros/data=2026-11-02/livros.jsonl"]) == 1
    assert manifest.estado == "sucesso"
    assert manifest.total_extraido == 1

    invalid_storage = MemoryStorage({})
    invalid_manifest = create_manifest(data_ref="2026-11-02")
    invalid_extractor = Extrator(
        gravador=invalid_storage,
        manifesto=invalid_manifest,
    )

    try:
        invalid_extractor.publicar(
            result,
            livros_declarados=2,
            cotacoes_declaradas=0,
        )
    except ValueError as error:
        assert "contagem" in str(error).lower()
    else:
        raise AssertionError("divergência de contagem deveria bloquear publicação")
    assert invalid_storage.bronze == {}
    assert invalid_manifest.estado == "falha"
    assert invalid_manifest.itens[-1].estado == "falhou"


def test_falha_ao_gravar_bronze_fica_registrada_no_manifesto():
    from src.extractor import ExtractionResult

    storage = MemoryStorage({})
    storage.gravar_bronze = lambda key, lines: (_ for _ in ()).throw(
        RuntimeError("armazenamento indisponível")
    )
    manifest = create_manifest(data_ref="2026-11-02")
    extractor = Extrator(gravador=storage, manifesto=manifest)

    with pytest.raises(RuntimeError, match="armazenamento indisponível"):
        extractor.publicar(
            ExtractionResult(livros=[], cotacoes=[]),
            livros_declarados=0,
            cotacoes_declaradas=0,
        )

    assert manifest.estado == "falha"
    assert manifest.itens[-1].estado == "falhou"
    assert manifest.itens[-1].erro == "armazenamento indisponível"
