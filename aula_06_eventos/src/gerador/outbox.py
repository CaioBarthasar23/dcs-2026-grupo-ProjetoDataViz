"""Outbox local JSONL com estado pendente/enviado."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Mapping


def adicionar_eventos(
    caminho: str | Path,
    eventos: Iterable[Mapping],
) -> int:
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    quantidade = 0
    with destino.open("a", encoding="utf-8") as arquivo:
        for evento in eventos:
            linha = {
                "estado": "pendente",
                "evento": dict(evento),
            }
            arquivo.write(
                json.dumps(linha, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            quantidade += 1
    return quantidade


def ler_outbox(caminho: str | Path) -> list[dict]:
    origem = Path(caminho)
    if not origem.exists():
        return []
    with origem.open("r", encoding="utf-8") as arquivo:
        return [
            json.loads(linha)
            for linha in arquivo
            if linha.strip()
        ]


def marcar_enviado(caminho: str | Path, event_id: str) -> None:
    destino = Path(caminho)
    linhas = ler_outbox(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as arquivo:
        for linha in linhas:
            if linha["evento"].get("event_id") == event_id:
                linha["estado"] = "enviado"
            arquivo.write(
                json.dumps(linha, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
