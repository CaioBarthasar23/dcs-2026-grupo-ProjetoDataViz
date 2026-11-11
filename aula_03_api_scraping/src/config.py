import os
from dataclasses import dataclass, field
from math import isfinite
from typing import Mapping
from urllib.parse import urlsplit

from dotenv import dotenv_values


DEFAULT_HTTP_TIMEOUT = (5.0, 10.0)


@dataclass(frozen=True)
class Config:
    endpoint_minio: str
    access_key: str = field(repr=False)
    secret_key: str = field(repr=False)
    bucket_raw: str = "raw"
    bucket_bronze: str = "bronze"
    categorias: list[str] = field(default_factory=list)
    timeout: tuple[float, float] = DEFAULT_HTTP_TIMEOUT
    max_tentativas: int = 4
    intervalo_minimo: float = 1.0
    user_agent: str = "aula_03_api_scraping"

    @classmethod
    def de_ambiente(cls) -> "Config":
        return load_config()


def load_config(environ: Mapping[str, str] | None = None) -> Config:
    if environ is None:
        values = {**dotenv_values(".env"), **os.environ}
    else:
        values = environ

    def required(name: str) -> str:
        value = values.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Configuração obrigatória ausente: {name}")
        return value.strip()

    def positive_float(name: str, default: float, *, allow_zero: bool = False) -> float:
        raw_value = values.get(name)
        if raw_value is None or not str(raw_value).strip():
            return default
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise ValueError(f"Configuração inválida: {name}") from None
        if not isfinite(value) or value < 0 or (value == 0 and not allow_zero):
            raise ValueError(f"Configuração inválida: {name}")
        return value

    endpoint = required("S3_ENDPOINT_URL")
    parsed_endpoint = urlsplit(endpoint)
    if parsed_endpoint.scheme not in {"http", "https"} or not parsed_endpoint.hostname:
        raise ValueError("Configuração inválida: S3_ENDPOINT_URL")

    timeout_connect = positive_float("HTTP_TIMEOUT_CONNECT", DEFAULT_HTTP_TIMEOUT[0])
    timeout_read = positive_float("HTTP_TIMEOUT_READ", DEFAULT_HTTP_TIMEOUT[1])
    raw_attempts = values.get("HTTP_MAX_TENTATIVAS")
    try:
        attempts = 4 if raw_attempts is None or not str(raw_attempts).strip() else int(raw_attempts)
    except (TypeError, ValueError):
        raise ValueError("Configuração inválida: HTTP_MAX_TENTATIVAS") from None
    if attempts < 1:
        raise ValueError("Configuração inválida: HTTP_MAX_TENTATIVAS")

    raw_categories = values.get("SCRAPER_CATEGORIAS", "")
    categories = [
        category.strip()
        for category in str(raw_categories).split(",")
        if category.strip()
    ]

    return Config(
        endpoint_minio=endpoint,
        access_key=required("S3_ACCESS_KEY"),
        secret_key=required("S3_SECRET_KEY"),
        bucket_raw=str(values.get("BUCKET_RAW") or "raw").strip(),
        bucket_bronze=str(values.get("BUCKET_BRONZE") or "bronze").strip(),
        categorias=categories,
        timeout=(timeout_connect, timeout_read),
        max_tentativas=attempts,
        intervalo_minimo=positive_float(
            "HTTP_INTERVALO_MINIMO", 1.0, allow_zero=True
        ),
        user_agent=str(values.get("HTTP_USER_AGENT") or "aula_03_api_scraping").strip(),
    )
