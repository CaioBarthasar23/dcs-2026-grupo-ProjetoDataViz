"""Envia cada livro por HTTP, em série, para a API de ingestão."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

from src.config import config


def enviar_livros(
    arquivos: list[Path] | None = None,
    url: str | None = None,
    sessao: requests.Session | None = None,
) -> int:
    fontes = arquivos if arquivos is not None else sorted(Path("entrada/livros").glob("*.jsonl"))
    destino = url or f"http://localhost:{config.api_port}/ingest"
    cliente = sessao or requests.Session()
    enviados = 0
    for arquivo in fontes:
        with arquivo.open(encoding="utf-8") as entrada:
            for numero, linha in enumerate(entrada, start=1):
                if not linha.strip():
                    continue
                envelope = {"data_tag": "livros", "data": json.loads(linha)}
                resposta = cliente.post(destino, json=envelope, timeout=30)
                if resposta.status_code != 202:
                    raise RuntimeError(
                        f"{arquivo}:{numero}: API respondeu {resposta.status_code}"
                    )
                enviados += 1
    return enviados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, action="append")
    parser.add_argument("--url")
    args = parser.parse_args()
    print(f"livros enviados: {enviar_livros(args.arquivo, args.url)}")


if __name__ == "__main__":
    main()
