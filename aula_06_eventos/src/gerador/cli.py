"""Linha de comando do gerador de eventos."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .anonimizacao import obter_chave_anonimizacao
from .geracao import gerar_eventos
from .outbox import adicionar_eventos
from .validacao import exigir_evento_valido


def carregar_env(caminho: Path) -> None:
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = linha.split("=", 1)
        os.environ.setdefault(nome.strip(), valor.strip().strip('"').strip("'"))


def principal() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quantidade", type=int, default=1000)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument(
        "--taxa-eventos",
        type=float,
        default=1.0,
        help="hipotese, validacao pendente",
    )
    parser.add_argument(
        "--outbox",
        default="outbox/eventos.jsonl",
    )
    args = parser.parse_args()

    carregar_env(Path(".env"))
    chave = obter_chave_anonimizacao()
    eventos = gerar_eventos(
        quantidade=args.quantidade,
        semente=args.semente,
        chave=chave,
        taxa_eventos=args.taxa_eventos,
    )
    for evento in eventos:
        exigir_evento_valido(evento)
    adicionar_eventos(args.outbox, eventos)
    print(f"{len(eventos)} eventos gravados no outbox")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
