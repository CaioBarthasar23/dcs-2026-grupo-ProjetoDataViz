from datetime import datetime, timedelta, timezone

import pytest
from src.metadados import montar_metadados


def test_metadados_em_ascii() -> None:
    metadados = montar_metadados(
        "CAM-0451_20261017T0900.txt",
        sha256="a" * 64,
        versao_coletor="1.0",
        recebido_em=datetime(
            2026,
            11,
            2,
            2,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    assert metadados == {
        "fonte": "provedor-satelite",
        "recebido-em": "2026-11-02T00:00:00Z",
        "versao-coletor": "1.0",
        "sha256": "a" * 64,
        "caminhao": "CAM-0451",
        "janela-inicio": "2026-10-17T12:00:00Z",
        "arquivo-origem": "CAM-0451_20261017T0900.txt",
    }
    for chave, valor in metadados.items():
        chave.encode("ascii")
        valor.encode("ascii")


def test_metadados_rejeitam_instante_sem_fuso() -> None:
    with pytest.raises(ValueError, match="recebido_em"):
        montar_metadados(
            "CAM-0451_20261017T0900.txt",
            sha256="a" * 64,
            versao_coletor="1.0",
            recebido_em=datetime(2026, 11, 2),
        )


def test_metadados_rejeitam_valores_nao_ascii() -> None:
    with pytest.raises(UnicodeEncodeError):
        montar_metadados(
            "CAM-0451_20261017T0900.txt",
            sha256="a" * 64,
            versao_coletor="versão",
            recebido_em=datetime(2026, 11, 2, tzinfo=timezone.utc),
        )
