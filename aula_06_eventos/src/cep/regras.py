from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4


def parse_utc(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def utc_iso(instante: datetime) -> str:
    from datetime import timezone
    return instante.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def evento_complexo(
    tipo: str,
    chave: str,
    evento: dict[str, Any],
    agora: datetime,
    janela: timedelta,
    origem_ids: list[str],
    atrasado: bool,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "tipo": tipo,
        "detectado_em": utc_iso(agora),
        "chave": chave,
        "regiao": evento.get("regiao"),
        "academia": evento.get("academia"),
        "janela": f"P{int(janela.total_seconds() // 86400)}D",
        "eventos_origem": origem_ids,
        "atrasado": atrasado,
    }
