"""Anonimizacao HMAC-SHA-256 aplicada na borda."""
from __future__ import annotations

import hashlib
import hmac
import os


def obter_chave_anonimizacao() -> str:
    chave = os.environ.get("ANON_CHAVE")
    if chave is None or not chave.strip():
        raise RuntimeError(
            "ANON_CHAVE ausente: defina a chave secreta no ambiente"
        )
    return chave


def anonimizar_aluno(
    identificador_interno: str,
    chave: str | None = None,
) -> str:
    chave_efetiva = chave if chave is not None else obter_chave_anonimizacao()
    if not chave_efetiva:
        raise RuntimeError("ANON_CHAVE ausente: a chave nao pode ser vazia")
    digest = hmac.new(
        chave_efetiva.encode("utf-8"),
        identificador_interno.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:16]
