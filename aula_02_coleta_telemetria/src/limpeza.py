from pathlib import Path


def remover_confirmado(caminho: Path, status: str) -> None:
    if status in {"gravado", "ja_existia"}:
        caminho.unlink()
