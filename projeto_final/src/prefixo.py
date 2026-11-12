"""Validação do prefixo de escrita exclusivo da coleção SSP."""

from __future__ import annotations

import re

PREFIXO_PROPRIO = "group_id=23651"
_SEGMENTO_GROUP_ID = re.compile(r"group_id=\d+\Z")


def validar_chave(chave: str) -> str:
    """Retorna a chave se ela pertence somente à coleção SSP; caso contrário, recusa."""
    segmentos = chave.split("/")
    segmentos_group_id = [s for s in segmentos if _SEGMENTO_GROUP_ID.fullmatch(s)]
    if PREFIXO_PROPRIO not in segmentos or any(
        segmento != PREFIXO_PROPRIO for segmento in segmentos_group_id
    ):
        raise ValueError(
            f"ERRO escrita recusada: {chave} fora do prefixo {PREFIXO_PROPRIO}"
        )
    return chave
