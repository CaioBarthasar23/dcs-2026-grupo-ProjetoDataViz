import subprocess
from pathlib import Path

from src.config import load_config
from src.manifest import create_manifest, finalize_manifest, record_item
from src.pipeline import compare_counts, rerun_daily, run_collection
from src.storage import StorageConfig, verify_destinations


def test_manifesto_registra_execucao_e_itens():
    # RF-13, RNF-05
    manifest = create_manifest(data_ref="2026-11-02")
    manifest.escopo = {
        "tipo": "filtrado",
        "categorias": ["mystery_3"],
    }
    item = record_item(
        manifest,
        url="https://books.toscrape.com/",
        status_http=200,
        attempts=1,
        bytes_received=1024,
        sha256="abc",
        state="gravado",
        key="raw/books_toscrape/data=2026-11-02/inicio.html",
    )
    manifest = finalize_manifest(
        manifest,
        finished_at="2026-11-02T04:00:00Z",
        state="completa",
        declared_total=1,
        extracted_total=1,
        sources=["books.toscrape.com", "PTAX"],
        robots={"url": "https://books.toscrape.com/robots.txt", "status_http": 404},
    )
    assert manifest.id
    assert manifest.data_ref == "2026-11-02"
    assert manifest.started_at
    assert manifest.finished_at == "2026-11-02T04:00:00Z"
    assert manifest.state == "completa"
    assert manifest.declared_total == manifest.extracted_total == 1
    assert manifest.sources == ["books.toscrape.com", "PTAX"]
    assert manifest.para_dict()["escopo"] == {
        "tipo": "filtrado",
        "categorias": ["mystery_3"],
    }
    assert manifest.robots["status_http"] == 404
    assert item.state == "gravado"
    assert item.url == "https://books.toscrape.com/"
    assert item.key == "raw/books_toscrape/data=2026-11-02/inicio.html"
    assert item.status_http == 200
    assert item.attempts == 1
    assert item.bytes == 1024
    assert item.sha256 == "abc"
    assert item.error is None


def test_item_falhou_permanece_no_manifesto_com_causa():
    # RF-13, RNF-05
    manifest = create_manifest(data_ref="2026-11-02")
    item = record_item(
        manifest,
        url="https://books.toscrape.com/",
        status_http=503,
        attempts=4,
        bytes_received=0,
        state="falhou",
        error="tentativas esgotadas",
    )
    assert item.state == "falhou"
    assert item.error
    assert item.status_http == 503
    assert item.attempts == 4
    assert item.bytes == 0
    assert item.key is None


def test_divergencia_contagem_completa_ou_filtrada_marca_falha():
    # RF-14, RNF-01
    complete = compare_counts(extracted=999, declared=1000, scope="completa")
    filtered = compare_counts(extracted=31, declared=32, scope="filtrada")
    assert complete.state == filtered.state == "falha"
    assert complete.difference == filtered.difference == -1


def test_reexecucao_substitui_bronze_sem_duplicar():
    # RF-15, RNF-07
    result = rerun_daily(data_ref="2026-11-02", previous_run="run-1", new_run="run-2")
    assert result.manifest_id == "run-2"
    assert result.duplicate_upcs == 0
    assert result.previous_manifest_preserved is True
    assert result.bronze_replaced is True


def test_configuracao_nao_expoe_segredos():
    # RNF-08
    config = load_config(
        {
            "S3_ENDPOINT_URL": "http://localhost:9000",
            "S3_ACCESS_KEY": "test-key",
            "S3_SECRET_KEY": "test-secret",
        }
    )
    assert "test-secret" not in repr(config)
    assert "test-secret" not in str(config)
    project_dir = Path(__file__).resolve().parents[1]
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", ".env"],
        cwd=project_dir,
        capture_output=True,
        check=False,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".env"],
        cwd=project_dir,
        capture_output=True,
        check=False,
    )
    assert ignored.returncode == 0
    assert tracked.returncode != 0


def test_variaveis_injetadas_sobrescrevem_valores_do_dotenv(monkeypatch):
    import src.config as config_module

    dotenv = {
        "S3_ENDPOINT_URL": "http://localhost:9000",
        "S3_ACCESS_KEY": "dotenv-user",
        "S3_SECRET_KEY": "dotenv-secret",
    }
    monkeypatch.setattr(config_module, "dotenv_values", lambda _: dotenv)
    monkeypatch.setenv("S3_ENDPOINT_URL", "https://railway.example.test")
    monkeypatch.setenv("S3_ACCESS_KEY", "railway-user")
    monkeypatch.setenv("S3_SECRET_KEY", "railway-secret")

    config = config_module.load_config()

    assert config.endpoint_minio == "https://railway.example.test"
    assert config.access_key == "railway-user"
    assert config.secret_key == "railway-secret"


def test_mesmo_codigo_usa_minio_local_ou_railway():
    # RNF-10
    local = StorageConfig(endpoint_url="http://localhost:9000", bucket="teste")
    railway = StorageConfig(endpoint_url="https://minio.example.test", bucket="teste")
    result = verify_destinations(local, railway)
    assert result.same_interface is True
    assert result.code_changes == 0


def test_duracao_coleta_completa_e_registrada():
    # RNF-03
    times = iter([0.0, 1799.0, 0.0, 1801.0])
    clock = lambda: next(times)
    within_limit = run_collection(collect=lambda: None, monotonic=clock)
    over_limit = run_collection(collect=lambda: None, monotonic=clock)
    assert within_limit.duration_seconds == 1799.0
    assert within_limit.execution_state == "completa"
    assert over_limit.duration_seconds == 1801.0
    assert over_limit.execution_state == "falha"


def test_pipeline_registra_totais_e_divergencia_no_manifesto():
    manifest = create_manifest(data_ref="2026-11-02")

    result = run_collection(
        collect=lambda: None,
        monotonic=iter([0.0, 5.0]).__next__,
        manifest=manifest,
        declared_total=100,
        extracted_total=99,
        scope="completa",
    )

    assert result.execution_state == "falha"
    assert manifest.estado == "falha"
    assert manifest.total_declarado == 100
    assert manifest.total_extraido == 99


def test_pipeline_registra_duracao_e_estado_no_manifesto():
    manifest = create_manifest(data_ref="2026-11-02")

    result = run_collection(
        collect=lambda: None,
        monotonic=iter([0.0, 1801.0]).__next__,
        manifest=manifest,
        declared_total=100,
        extracted_total=100,
        scope="completa",
    )

    assert result.duration_seconds == 1801.0
    assert result.execution_state == "falha"
    assert manifest.estado == "falha"
    assert manifest.total_declarado == manifest.total_extraido == 100
