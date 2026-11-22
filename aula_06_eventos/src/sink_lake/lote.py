from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable


def decidir_fechamento(
    minutos_desde_abertura: float,
    tamanho_bytes: int,
    fechar_lote_minutos: float = 10,
    fechar_lote_bytes: int = 5 * 1024 * 1024,
) -> bool:
    if minutos_desde_abertura < 0 or tamanho_bytes < 0:
        raise ValueError("tempos e tamanhos nao podem ser negativos")
    return (
        minutos_desde_abertura >= fechar_lote_minutos
        or tamanho_bytes >= fechar_lote_bytes
    )


deve_fechar_lote = decidir_fechamento


class Lote:
    def __init__(
        self,
        partition: int,
        primeiro_offset: int,
        regiao: str,
        instante_particao: datetime,
        abrir_em: datetime | None = None,
        fechar_tempo_minutos: float = 10,
        fechar_tamanho_bytes: int = 5 * 1024 * 1024,
    ) -> None:
        self.partition = partition
        self.primeiro_offset = primeiro_offset
        self.regiao = regiao
        self.instante_particao = instante_particao.astimezone(timezone.utc)
        self.abrir_em = abrir_em or datetime.now(timezone.utc)
        self.fechar_tempo_minutos = fechar_tempo_minutos
        self.fechar_tamanho_bytes = fechar_tamanho_bytes
        self.eventos: list[dict] = []
        self.linhas_raw: list[bytes] = []
        self.ultimo_offset = primeiro_offset

    @property
    def tamanho_bytes(self) -> int:
        import json
        return sum(
            len(json.dumps(evento, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
            + 1
            for evento in self.eventos
        )

    def adicionar(self, evento: dict) -> None:
        self.eventos.append(evento)

    def adicionar_raw(self, evento: dict, raw: bytes) -> None:
        self.eventos.append(evento)
        self.linhas_raw.append(raw)

    def fechar(
        self,
        agora: datetime | None = None,
    ) -> bool:
        agora = agora or datetime.now(timezone.utc)
        minutos = (agora - self.abrir_em).total_seconds() / 60
        return decidir_fechamento(
            minutos,
            self.tamanho_bytes,
            self.fechar_tempo_minutos,
            self.fechar_tamanho_bytes,
        )
