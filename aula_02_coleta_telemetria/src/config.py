import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Configuracao:
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    bucket_raw: str
    s3_region: str
    coletor_versao: str
    pouso_dir: Path


def carregar_configuracao() -> Configuracao:
    valores: dict[str, str] = {}
    for nome in (
        "S3_ENDPOINT_URL",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "BUCKET_RAW",
        "S3_REGION",
        "COLETOR_VERSAO",
        "POUSO_DIR",
    ):
        try:
            valores[nome] = os.environ[nome]
        except KeyError:
            raise ValueError(nome) from None

    return Configuracao(
        s3_endpoint_url=valores["S3_ENDPOINT_URL"],
        s3_access_key=valores["S3_ACCESS_KEY"],
        s3_secret_key=valores["S3_SECRET_KEY"],
        bucket_raw=valores["BUCKET_RAW"],
        s3_region=valores["S3_REGION"],
        coletor_versao=valores["COLETOR_VERSAO"],
        pouso_dir=Path(valores["POUSO_DIR"]),
    )
