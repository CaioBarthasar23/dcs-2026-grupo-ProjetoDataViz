import pytest

from src.config import carregar_configuracao


VARIAVEIS = {
    "S3_ENDPOINT_URL": "https://teste.invalid",
    "S3_ACCESS_KEY": "teste",
    "S3_SECRET_KEY": "teste",
    "BUCKET_RAW": "teste",
    "S3_REGION": "teste",
    "COLETOR_VERSAO": "teste",
    "POUSO_DIR": "/tmp/teste",
}


def test_config_carrega_variaveis_de_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    for nome, valor in VARIAVEIS.items():
        monkeypatch.setenv(nome, valor)

    config = carregar_configuracao()

    assert config.s3_endpoint_url == VARIAVEIS["S3_ENDPOINT_URL"]
    assert config.s3_access_key == VARIAVEIS["S3_ACCESS_KEY"]
    assert config.s3_secret_key == VARIAVEIS["S3_SECRET_KEY"]
    assert config.bucket_raw == VARIAVEIS["BUCKET_RAW"]
    assert config.s3_region == VARIAVEIS["S3_REGION"]
    assert config.coletor_versao == VARIAVEIS["COLETOR_VERSAO"]
    assert str(config.pouso_dir) == VARIAVEIS["POUSO_DIR"]


def test_config_variavel_ausente_cita_somente_o_nome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for nome, valor in VARIAVEIS.items():
        monkeypatch.setenv(nome, valor)
    monkeypatch.delenv("S3_SECRET_KEY")

    with pytest.raises(ValueError) as erro:
        carregar_configuracao()

    assert str(erro.value) == "S3_SECRET_KEY"
