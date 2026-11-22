from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _instante(valor: Any) -> datetime:
    if isinstance(valor, datetime):
        return valor.astimezone(timezone.utc)
    return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).astimezone(timezone.utc)


def numero_lote(partition: int, primeiro_offset: int) -> int:
    if partition < 0 or primeiro_offset < 0:
        raise ValueError("partition e primeiro_offset devem ser nao negativos")
    return partition * 10_000_000 + primeiro_offset


def montar_chave(
    regiao: str,
    instante: Any,
    particionar_por: str = "evento",
    partition: int = 0,
    primeiro_offset: int = 0,
    numero: int | None = None,
    modo: str | None = None,
    chegada_em: Any | None = None,
) -> str:
    if modo is not None:
        particionar_por = modo
    if particionar_por == "chegada" and chegada_em is not None:
        instante = chegada_em
    if isinstance(instante, dict):
        campo = "ocorrido_em" if particionar_por == "evento" else "chegada_em"
        instante = instante.get(campo, instante)
    if particionar_por not in ("evento", "chegada"):
        raise ValueError("particionar_por deve ser 'evento' ou 'chegada'")
    instante_utc = _instante(instante)
    lote = numero if numero is not None else numero_lote(partition, primeiro_offset)
    return (
        f"regiao={regiao}/data={instante_utc:%Y-%m-%d}/"
        f"hora={instante_utc:%H}/lote-{lote:04d}.jsonl.gz"
    )


montar_chave_lote = montar_chave
