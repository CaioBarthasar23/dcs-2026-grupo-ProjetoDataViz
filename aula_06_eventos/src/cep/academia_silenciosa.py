from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .regras import evento_complexo, parse_utc


def avaliar(
    estado_da_chave: dict[str, Any] | None,
    evento: dict[str, Any],
    agora: datetime,
    silencio: timedelta = timedelta(minutes=5),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    instante = parse_utc(evento["ocorrido_em"])
    if evento["tipo"] == "heartbeat":
        return {"ultimo_heartbeat": evento["ocorrido_em"]}, []
    return estado_da_chave or {"ultimo_heartbeat": utc_ou_nulo(evento)}, []


def vencidos(
    estado_da_chave: dict[str, Any],
    chave: str,
    academia_evento: dict[str, Any],
    agora: datetime,
    silencio: timedelta = timedelta(minutes=5),
) -> list[dict[str, Any]]:
    if not estado_da_chave or "ultimo_heartbeat" not in estado_da_chave:
        return []
    ultimo = parse_utc(estado_da_chave["ultimo_heartbeat"])
    if agora - ultimo < silencio:
        return []
    complexo = evento_complexo(
        "academia_silenciosa",
        chave,
        academia_evento,
        agora,
        silencio,
        [],
        atrasado=False,
    )
    return [complexo]


def utc_ou_nulo(evento: dict[str, Any]) -> str:
    return evento["ocorrido_em"]
