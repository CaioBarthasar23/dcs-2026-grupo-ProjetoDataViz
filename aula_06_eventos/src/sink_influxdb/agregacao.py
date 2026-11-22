from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


TAGS_VALIDAS = frozenset({"regiao", "academia", "tipo"})


def inicio_minuto(ocorrido_em: str) -> datetime:
    instante = datetime.fromisoformat(ocorrido_em.replace("Z", "+00:00"))
    return instante.astimezone(timezone.utc).replace(second=0, microsecond=0)


def timestamp_ns(instante: datetime) -> int:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return int((instante - epoch).total_seconds() * 1_000_000_000)


def escape_tag(valor: object) -> str:
    return str(valor).replace("\\", "\\\\").replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")


def tags_do_evento(evento: dict) -> dict[str, str]:
    tags = {
        "regiao": str(evento["regiao"]),
        "academia": str(evento["academia"]),
        "tipo": str(evento["tipo"]),
    }
    if set(tags) != TAGS_VALIDAS:
        raise ValueError("conjunto de tags invalido")
    return tags


class AgregadorMinuto:
    def __init__(
        self,
        estado_path: str | Path,
        deduplicacao: timedelta = timedelta(hours=24),
    ) -> None:
        self.caminho = Path(estado_path)
        self.deduplicacao = deduplicacao
        self.contagens: dict[tuple[str, str, str, str], int] = {}
        self.vistos: dict[str, str] = {}
        self._carregar()

    def _carregar(self) -> None:
        if not self.caminho.exists():
            return
        dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        self.contagens = {
            tuple(json.loads(chave)): valor
            for chave, valor in dados.get("contagens", {}).items()
        }
        self.vistos = dados.get("vistos", {})

    def persistir(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps({
                "contagens": {
                    json.dumps(list(chave)): valor
                    for chave, valor in self.contagens.items()
                },
                "vistos": self.vistos,
            }),
            encoding="utf-8",
        )
        temporario.replace(self.caminho)

    def adicionar(self, evento: dict) -> list[tuple[dict, int]]:
        event_id = evento["event_id"]
        if event_id in self.vistos:
            return []

        minuto = inicio_minuto(evento["ocorrido_em"]).isoformat()
        tags = tags_do_evento(evento)
        chave = (
            minuto,
            tags["regiao"],
            tags["academia"],
            tags["tipo"],
        )
        self.contagens[chave] = self.contagens.get(chave, 0) + 1
        self.vistos[event_id] = evento["ocorrido_em"]
        return [(tags | {"minuto": minuto}, self.contagens[chave])]

    def expirar_deduplicacao(self, limite: datetime) -> None:
        limite_iso = limite.isoformat()
        self.vistos = {
            event_id: minuto
            for event_id, minuto in self.vistos.items()
            if minuto >= limite_iso
        }

    def pontos_line_protocol(self) -> list[str]:
        linhas = []
        for (minuto, regiao, academia, tipo), contagem in sorted(
            self.contagens.items()
        ):
            instante = datetime.fromisoformat(minuto)
            linhas.append(
                f"eventos,"
                f"regiao={escape_tag(regiao)},"
                f"academia={escape_tag(academia)},"
                f"tipo={escape_tag(tipo)} "
                f"contagem={contagem}i "
                f"{timestamp_ns(instante)}"
            )
        return linhas
