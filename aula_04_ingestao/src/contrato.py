"""Validação estrutural do envelope de ingestão."""

import json
from collections.abc import Iterable
from typing import Any

from src.config import config


class EnvelopeInvalido(ValueError):
    """Envelope ou corpo que não atende ao contrato HTTP de ingestão."""

    def __init__(self, motivo: str, status_code: int = 422) -> None:
        self.motivo = motivo
        self.status_code = status_code
        super().__init__(motivo)


class CorpoNaoJson(EnvelopeInvalido):
    """O corpo não pode ser interpretado como JSON."""

    def __init__(self, motivo: str = "corpo da requisição não é JSON") -> None:
        super().__init__(motivo, status_code=400)


def validar(
    corpo: bytes | bytearray | str,
    dominios: Iterable[str],
) -> tuple[str, list[dict[str, Any]]]:
    """Valida o envelope e retorna a tag e seus objetos de dados.

    A validação não interpreta os campos internos de cada objeto em `data`.
    """
    tamanho = len(corpo.encode("utf-8") if isinstance(corpo, str) else corpo)
    if tamanho > config.http_max_bytes:
        raise EnvelopeInvalido(
            f"corpo excede HTTP_MAX_BYTES ({config.http_max_bytes} bytes)",
            status_code=413,
        )

    try:
        envelope = json.loads(corpo)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as erro:
        raise CorpoNaoJson(f"corpo da requisição não é JSON: {erro}") from erro

    if not isinstance(envelope, dict):
        raise EnvelopeInvalido("envelope deve ser um objeto JSON")

    campos_extra = set(envelope) - {"data_tag", "data"}
    if campos_extra:
        nomes = ", ".join(sorted(str(campo) for campo in campos_extra))
        raise EnvelopeInvalido(f"campo(s) não permitido(s) no envelope: {nomes}")

    if "data_tag" not in envelope:
        raise EnvelopeInvalido("campo obrigatório ausente: data_tag")
    data_tag = envelope["data_tag"]
    if not isinstance(data_tag, str):
        raise EnvelopeInvalido("data_tag deve ser texto")
    dominios_permitidos = set(dominios)
    if data_tag not in dominios_permitidos:
        raise EnvelopeInvalido(
            f"data_tag {data_tag!r} fora de DOMINIOS"
        )

    if "data" not in envelope:
        raise EnvelopeInvalido("campo obrigatório ausente: data")
    data = envelope["data"]
    if isinstance(data, dict):
        objetos = [data]
    elif isinstance(data, list) and data:
        if not all(isinstance(item, dict) for item in data):
            raise EnvelopeInvalido("data deve conter somente objetos JSON")
        objetos = data
    else:
        raise EnvelopeInvalido("data deve ser objeto ou lista não vazia de objetos")

    return data_tag, objetos
