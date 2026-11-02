from pathlib import Path

import pytest

from src.leitura import listar_arquivos, nome_valido


def test_lista_arquivos_visiveis_diretos_incluindo_nome_invalido(
    tmp_path: Path,
) -> None:
    valido = tmp_path / "CAM-0451_20261017T0900.txt"
    invalido = tmp_path / "nome-invalido.txt"
    oculto = tmp_path / ".CAM-0451_20261017T0900.txt"
    subpasta = tmp_path / "subpasta"

    valido.touch()
    invalido.touch()
    oculto.touch()
    subpasta.mkdir()
    (subpasta / "CAM-0451_20261017T0915.txt").touch()

    assert listar_arquivos(tmp_path) == [valido, invalido]
    assert invalido.exists()


@pytest.mark.parametrize(
    "arquivo",
    [
        "CAM-0451_20261017T0900.csv",
        "SENSOR-0451_20261017T0900.txt",
        "CAM-0451_20261017T0960.txt",
    ],
)
def test_nome_invalido_permanece_no_pouso(tmp_path: Path, arquivo: str) -> None:
    caminho = tmp_path / arquivo
    caminho.write_bytes(b"conteudo teste")

    assert not nome_valido(caminho.name)
    assert caminho.read_bytes() == b"conteudo teste"
