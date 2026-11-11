"""Configuração carregada do ambiente e do arquivo local .env."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv(override=False)


def _int_env(nome: str, padrao: int) -> int:
    valor = os.getenv(nome)
    return padrao if valor is None else int(valor)


@dataclass(frozen=True)
class Config:
    dominios: tuple[str, ...]

    rabbitmq_host: str
    rabbitmq_port: int
    rabbitmq_ui_port: int
    rabbitmq_user: str
    rabbitmq_password: str | None
    fila_ingestao: str

    clickhouse_host: str
    clickhouse_http_port: int
    clickhouse_user: str
    clickhouse_password: str | None
    clickhouse_database: str
    clickhouse_tabela: str
    clickhouse_async_insert: bool

    s3_endpoint_url: str
    s3_region: str
    s3_access_key: str | None
    s3_secret_key: str | None
    bucket_raw: str
    bucket_bronze: str
    bucket_silver: str
    bucket_teste: str

    flush_n: int
    flush_segundos: float
    http_max_bytes: int
    api_port: int


def carregar_config() -> Config:
    """Lê as configurações sem imprimir nem persistir credenciais."""
    dominios = tuple(
        dominio.strip()
        for dominio in os.getenv("DOMINIOS", "telemetria,livros,ptax").split(",")
        if dominio.strip()
    )
    return Config(
        dominios=dominios,
        rabbitmq_host=os.getenv("RABBITMQ_HOST", "localhost"),
        rabbitmq_port=_int_env("RABBITMQ_PORT", 5672),
        rabbitmq_ui_port=_int_env("RABBITMQ_UI_PORT", 15672),
        rabbitmq_user=os.getenv("RABBITMQ_USER", "ingestao"),
        rabbitmq_password=os.getenv("RABBITMQ_PASSWORD"),
        fila_ingestao=os.getenv("FILA_INGESTAO", "ingestao"),
        clickhouse_host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        clickhouse_http_port=_int_env("CLICKHOUSE_HTTP_PORT", 8123),
        clickhouse_user=os.getenv("CLICKHOUSE_USER", "ingestao"),
        clickhouse_password=os.getenv("CLICKHOUSE_PASSWORD"),
        clickhouse_database=os.getenv("CLICKHOUSE_DATABASE", "ingestao"),
        clickhouse_tabela=os.getenv("CLICKHOUSE_TABELA", "db_ingestion"),
        clickhouse_async_insert=os.getenv("CLICKHOUSE_ASYNC_INSERT", "0").strip()
        in {"1", "true", "yes"},
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"),
        s3_region=os.getenv("S3_REGION", "us-east-1"),
        s3_access_key=os.getenv("S3_ACCESS_KEY"),
        s3_secret_key=os.getenv("S3_SECRET_KEY"),
        bucket_raw=os.getenv("BUCKET_RAW", "raw"),
        bucket_bronze=os.getenv("BUCKET_BRONZE", "bronze"),
        bucket_silver=os.getenv("BUCKET_SILVER", "silver"),
        bucket_teste=os.getenv("BUCKET_TESTE", "teste"),
        flush_n=_int_env("FLUSH_N", 500),
        flush_segundos=float(os.getenv("FLUSH_SEGUNDOS", "2")),
        http_max_bytes=_int_env("HTTP_MAX_BYTES", 1_048_576),
        api_port=_int_env("API_PORT", 8000),
    )


config = carregar_config()
