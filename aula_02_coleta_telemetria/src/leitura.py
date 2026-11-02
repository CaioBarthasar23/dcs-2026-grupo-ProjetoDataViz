import re
from datetime import datetime
from pathlib import Path


_PADRAO_NOME = re.compile(
    r"CAM-\d{4}_(?P<inicio>\d{8}T\d{4})\.txt"
)


def listar_arquivos(pouso_dir: Path) -> list[Path]:
    return sorted(
        (
            caminho
            for caminho in pouso_dir.iterdir()
            if not caminho.name.startswith(".") and caminho.is_file()
        ),
        key=lambda caminho: caminho.name,
    )


def nome_valido(nome: str) -> bool:
    correspondencia = _PADRAO_NOME.fullmatch(nome)
    if correspondencia is None:
        return False

    try:
        datetime.strptime(correspondencia.group("inicio"), "%Y%m%dT%H%M")
    except ValueError:
        return False
    return True
