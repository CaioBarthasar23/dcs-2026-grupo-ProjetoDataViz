"""Validacao pura dos eventos sinteticos."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID


REGIOES = {
    "sa-saopaulo",
    "us-virginia",
    "eu-estocolmo",
    "ap-sydney",
}
ORIGENS = {"app", "catraca", "gestao", "dispositivo"}
TIPOS = {
    "app_aberto",
    "video_assistido",
    "reserva_aula",
    "checkin",
    "cobranca_aprovada",
    "cobranca_falhou",
    "aula_experimental",
    "matricula",
    "graduacao",
    "cancelamento",
    "heartbeat",
}
PROIBIDOS = {
    "nome",
    "documento",
    "email",
    "e-mail",
    "telefone",
}


def validar_evento(evento: Mapping[str, Any]) -> list[str]:
    erros: list[str] = []
    tipo = evento.get("tipo")
    if tipo not in TIPOS:
        erros.append("tipo invalido")

    obrigatorios = {"event_id", "tipo", "ocorrido_em", "regiao", "academia", "origem"}
    if tipo == "heartbeat":
        obrigatorios.add("dispositivo_id")
    else:
        obrigatorios.add("aluno")
    if tipo == "cancelamento":
        obrigatorios.add("motivo")

    faltantes = sorted(obrigatorios - set(evento))
    if faltantes:
        erros.append("campos obrigatorios ausentes: " + ", ".join(faltantes))

    for campo in PROIBIDOS:
        if campo in evento:
            erros.append(f"campo proibido presente: {campo}")

    try:
        UUID(str(evento.get("event_id")))
    except (TypeError, ValueError):
        erros.append("event_id nao e UUID")

    ocorrido_em = evento.get("ocorrido_em")
    if not isinstance(ocorrido_em, str):
        erros.append("ocorrido_em invalido")
    else:
        if not ocorrido_em.endswith("Z") or "." not in ocorrido_em:
            erros.append("ocorrido_em deve ser UTC ISO 8601 com milissegundos")
        else:
            try:
                datetime.strptime(ocorrido_em, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                erros.append("ocorrido_em invalido")

    if evento.get("regiao") not in REGIOES:
        erros.append("regiao invalida")
    if evento.get("origem") not in ORIGENS:
        erros.append("origem invalida")
    if "aluno" in evento and not re.fullmatch(
        r"[0-9a-f]{16}",
        str(evento["aluno"]),
    ):
        erros.append("aluno invalido")

    if tipo != "heartbeat" and not isinstance(evento.get("aluno"), str):
        erros.append("aluno ausente")
    if tipo == "cancelamento" and not isinstance(evento.get("motivo"), str):
        erros.append("motivo invalido")
    return erros


def exigir_evento_valido(evento: Mapping[str, Any]) -> None:
    erros = validar_evento(evento)
    if erros:
        raise ValueError("Evento invalido: " + "; ".join(erros))
