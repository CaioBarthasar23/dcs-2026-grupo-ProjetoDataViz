from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .regras import evento_complexo, parse_utc


def avaliar(
    estado_da_chave: dict[str, Any] | None,
    evento: dict[str, Any],
    agora: datetime,
    janela: timedelta = timedelta(days=7),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    estado = estado_da_chave or {
        "matricula": None,
        "experimental": None,
        "origem_ids": [],
    }
    tipo = evento["tipo"]
    event_id = evento["event_id"]

    if event_id in estado["origem_ids"]:
        return estado, []

    if tipo == "matricula":
        novo = dict(estado)
        novo["matricula"] = evento["ocorrido_em"]
        novo["origem_ids"] = list(estado["origem_ids"]) + [event_id]
        return novo, []

    novo = dict(estado)
    novo["experimental"] = evento["ocorrido_em"]
    novo["origem_ids"] = list(estado["origem_ids"]) + [event_id]
    return novo, []


def vencidos(
    estado_da_chave: dict[str, Any],
    chave: str,
    evento: dict[str, Any],
    agora: datetime,
    janela: timedelta = timedelta(days=7),
) -> list[dict[str, Any]]:
    if not estado_da_chave or not estado_da_chave.get("experimental"):
        return []
    experimental = parse_utc(estado_da_chave["experimental"])
    if agora - experimental < janela:
        return []
    if estado_da_chave.get("matricula"):
        matricula = parse_utc(estado_da_chave["matricula"])
        if matricula >= experimental:
            return []
    origem_ids = estado_da_chave["origem_ids"]
    return [evento_complexo(
        "experimental_sem_matricula",
        chave,
        evento,
        agora,
        janela,
        origem_ids,
        atrasado=False,
    )]
