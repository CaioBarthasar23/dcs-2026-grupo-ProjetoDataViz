"""Publica uma mensagem PTAX com a lista de cotações de cada arquivo."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.produtores._amqp import Publicador


def publicar_ptax(arquivos: list[Path] | None = None) -> int:
    fontes = arquivos if arquivos is not None else sorted(Path("entrada/ptax").glob("*.jsonl"))
    quantidade = 0
    with Publicador() as publicador:
        for arquivo in fontes:
            with arquivo.open(encoding="utf-8") as entrada:
                cotacoes = [json.loads(linha) for linha in entrada if linha.strip()]
            if not cotacoes:
                continue
            publicador.publicar({"data_tag": "ptax", "data": cotacoes})
            quantidade += 1
    return quantidade


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, action="append")
    args = parser.parse_args()
    print(f"arquivos PTAX publicados: {publicar_ptax(args.arquivo)}")


if __name__ == "__main__":
    main()
