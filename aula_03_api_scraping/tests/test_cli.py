import json
from datetime import date
from io import StringIO
from types import SimpleNamespace

import pytest

import src.collectors.books as books_module
import src.collectors.ptax as ptax_module
import src.cli as cli_module
from src.collectors.books import Category, select_categories
from src.cli import _ptax_window_start, main
from src.config import Config


def test_cli_extrair_data_ref_e_propaga_falha_sem_segredos():
    calls = []

    def runner(command, data_ref):
        calls.append((command, data_ref))
        raise RuntimeError("Falha detalhada do armazenamento")

    stderr = StringIO()
    exit_code = main(
        ["extrair", "--data-ref", "2026-11-02"],
        command_runner=runner,
        stderr=stderr,
    )

    assert calls == [("extrair", "2026-11-02")]
    assert exit_code != 0
    assert "RuntimeError" in stderr.getvalue()
    assert "Falha detalhada" not in stderr.getvalue()
    assert "Traceback" not in stderr.getvalue()


def test_cli_coletar_aceita_data_e_encaminha_data_ref():
    calls = []

    def runner(command, data_ref):
        calls.append((command, data_ref))
        return "completa"

    assert main(
        ["coletar", "--data", "2026-10-24"],
        command_runner=runner,
        stderr=StringIO(),
    ) == 0
    assert calls == [("coletar", "2026-10-24")]


def test_ptax_window_start_covers_30_calendar_days_before_reference():
    assert _ptax_window_start(date(2026, 10, 24)) == date(2026, 9, 24)


def test_select_categories_aceita_slug_da_url():
    categories = [
        Category(
            name="mystery",
            url="https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
        ),
        Category(
            name="poetry",
            url="https://books.toscrape.com/catalogue/category/books/poetry_23/index.html",
        ),
    ]

    selected = select_categories(categories, "mystery_3,poetry_23")

    assert [category.name for category in selected] == ["mystery", "poetry"]


@pytest.mark.parametrize(
    ("categories", "expected_scope"),
    [
        (
            ["mystery_3"],
            {"tipo": "filtrado", "categorias": ["mystery_3"]},
        ),
        (
            [],
            {"tipo": "completo", "categorias": []},
        ),
    ],
)
def test_coleta_persiste_escopo_configurado_no_manifesto(
    monkeypatch, categories, expected_scope
):
    class RawStorage:
        def __init__(self):
            self.manifest = None

        def gravar_raw(self, key, body, metadata):
            if "/manifestos/" in key:
                self.manifest = json.loads(body)

    class BooksCollector:
        def __init__(self, *, manifesto, **kwargs):
            self.manifesto = manifesto
            self.paginas_coletadas = []
            self.livros_coletados = []

        def coletar(self, data_ref):
            self.manifesto.registrar_source("books.toscrape.com")
            return []

    class PtaxCollector:
        def __init__(self, *, manifesto, **kwargs):
            self.manifesto = manifesto

        def coletar(self, **kwargs):
            self.manifesto.registrar_source("PTAX")
            return SimpleNamespace(quote=None, execution_state="sucesso")

    raw = RawStorage()
    config = Config(
        endpoint_minio="http://minio.test",
        access_key="unused",
        secret_key="unused",
        categorias=categories,
    )
    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "_new_storage", lambda _: (raw, object()))
    monkeypatch.setattr(books_module, "ColetorBooks", BooksCollector)
    monkeypatch.setattr(ptax_module, "ColetorPtax", PtaxCollector)

    assert cli_module.run_command("coletar", "2026-11-02") == "completa"
    assert raw.manifest["sources"] == ["books.toscrape.com", "PTAX"]
    assert raw.manifest["escopo"] == expected_scope
