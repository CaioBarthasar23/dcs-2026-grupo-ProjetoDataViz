import pytest

from src.chaves import montar_chave


def test_chave_usa_inicio_da_janela_em_utc() -> None:
    assert montar_chave("CAM-0451_20261017T0900.txt") == (
        "telemetria/data=2026-10-17/hora=12/"
        "caminhao=CAM-0451/lote_1200.txt"
    )


def test_chave_avanca_data_no_limite_utc() -> None:
    assert montar_chave("CAM-0451_20261017T2200.txt") == (
        "telemetria/data=2026-10-18/hora=01/"
        "caminhao=CAM-0451/lote_0100.txt"
    )


@pytest.mark.parametrize(
    ("nome", "chave_esperada"),
    [
        (
            "CAM-0451_20261017T0915.txt",
            "telemetria/data=2026-10-17/hora=12/"
            "caminhao=CAM-0451/lote_1215.txt",
        ),
        (
            "CAM-0451_20261017T0945.txt",
            "telemetria/data=2026-10-17/hora=12/"
            "caminhao=CAM-0451/lote_1245.txt",
        ),
    ],
)
def test_chave_converte_janelas_de_15_minutos(
    nome: str, chave_esperada: str
) -> None:
    assert montar_chave(nome) == chave_esperada


def test_chave_e_deterministica() -> None:
    nome = "CAM-0451_20261017T0900.txt"

    assert montar_chave(nome) == montar_chave(nome)


@pytest.mark.parametrize(
    "nome",
    [
        "CAM-0451_20261017T0960.txt",
        "SENSOR-0451_20261017T0900.txt",
        "CAM-0451_20261017T0900.csv",
    ],
)
def test_nome_invalido_levanta_value_error(nome: str) -> None:
    with pytest.raises(ValueError):
        montar_chave(nome)
