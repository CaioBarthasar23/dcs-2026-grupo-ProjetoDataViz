from pathlib import Path

import pytest

from src.config import config
from src.contrato import CorpoNaoJson, EnvelopeInvalido, validar


EXEMPLOS = Path(__file__).parents[1] / "specs" / "exemplos"


def _codigo_esperado(arquivo: Path) -> int:
    if arquivo.name.startswith("valido_"):
        return 202
    return int(arquivo.name.split("_", maxsplit=2)[1])


@pytest.mark.parametrize("arquivo", sorted(EXEMPLOS.iterdir()), ids=lambda p: p.name)
def test_exemplo_corresponde_ao_codigo_e_motivo_do_nome(arquivo: Path) -> None:
    corpo = arquivo.read_bytes()
    esperado = _codigo_esperado(arquivo)

    if esperado == 202:
        data_tag, objetos = validar(corpo, config.dominios)
        assert data_tag in config.dominios
        assert objetos
        assert all(isinstance(objeto, dict) for objeto in objetos)
        return

    tipo_erro = CorpoNaoJson if esperado == 400 else EnvelopeInvalido
    with pytest.raises(tipo_erro) as erro:
        validar(corpo, config.dominios)

    assert erro.value.motivo
    assert erro.value.status_code == esperado
