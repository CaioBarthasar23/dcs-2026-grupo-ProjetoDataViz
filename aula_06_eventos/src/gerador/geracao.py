"""Geracao deterministica de eventos sinteticos."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Iterable, Mapping
from uuid import NAMESPACE_URL, uuid5

from .anonimizacao import anonimizar_aluno


TAMANHO_REGIOES = (
    ("sa-saopaulo", 96, "BR"),
    ("us-virginia", 72, "US"),
    ("eu-estocolmo", 48, "SE"),
    ("ap-sydney", 24, "AU"),
)
TIPOS_ALUNO = (
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
)
TURMAS = ("adulto-fundamentos", "adulto-avancado", "kids")
FAIXAS = ("branca", "azul", "roxa", "marrom", "preta")
MOTIVOS_CANCELAMENTO = (
    "mudanca de horario",
    "distancia",
    "pausa temporaria",
)


def criar_academias() -> list[dict[str, str]]:
    academias = []
    contadores = {regiao: 0 for regiao, _, _ in TAMANHO_REGIOES}
    cidades = {"BR": "SAO", "US": "VA", "SE": "STO", "AU": "SYD"}
    for regiao, quantidade, pais in TAMANHO_REGIOES:
        prefixo = cidades[pais]
        for _ in range(quantidade):
            contadores[regiao] += 1
            academias.append({
                "regiao": regiao,
                "academia": f"{pais}-{prefixo}-{contadores[regiao]:03d}",
            })
    return academias


def criar_proporcoes() -> dict[str, float]:
    tipos = TIPOS_ALUNO + ("heartbeat",)
    peso = 1.0 / len(tipos)
    return {tipo: peso for tipo in tipos}


def utc_iso_milisegundos(instante: datetime) -> str:
    return instante.astimezone(timezone.utc).isoformat(
        timespec="milliseconds",
    ).replace("+00:00", "Z")


def gerar_eventos(
    quantidade: int,
    semente: int,
    chave: str,
    taxa_eventos: float = 1.0,
    proporcoes: Mapping[str, float] | None = None,
) -> list[dict]:
    if quantidade < 1:
        raise ValueError("quantidade deve ser maior que zero")
    if taxa_eventos <= 0:
        raise ValueError("taxa_eventos deve ser maior que zero")

    pesos = dict(proporcoes or criar_proporcoes())
    faltantes = set(TIPOS_ALUNO + ("heartbeat",)) - set(pesos)
    if faltantes:
        raise ValueError("proporcoes faltantes: " + ", ".join(sorted(faltantes)))
    if any(valor < 0 for valor in pesos.values()) or sum(pesos.values()) <= 0:
        raise ValueError("proporcoes devem ser nao negativas e somar acima de zero")

    rng = random.Random(semente)
    academias = criar_academias()
    tipos = list(pesos)
    pesos_lista = [pesos[tipo] for tipo in tipos]
    # Hipotese, validacao pendente: a taxa controla o intervalo inicial.
    intervalo = timedelta(milliseconds=max(1, int(1000.0 / taxa_eventos)))
    base = datetime(2026, 11, 14, 11, 0, tzinfo=timezone.utc)

    eventos = []
    for indice in range(quantidade):
        academia = rng.choice(academias)
        tipo = rng.choices(tipos, weights=pesos_lista, k=1)[0]
        instante = base + indice * intervalo
        origem = "dispositivo" if tipo == "heartbeat" else rng.choice(
            ("app", "catraca", "gestao")
        )
        evento = {
            "event_id": str(uuid5(
                NAMESPACE_URL,
                f"rede-tatame:{semente}:{indice}:{academia['academia']}:{tipo}",
            )),
            "tipo": tipo,
            "ocorrido_em": utc_iso_milisegundos(instante),
            "regiao": academia["regiao"],
            "academia": academia["academia"],
            "origem": origem,
        }

        if tipo == "heartbeat":
            evento["dispositivo_id"] = (
                f"dispositivo-{rng.randint(1, 240):03d}"
            )
        else:
            numero_aluno = rng.randint(1, 150)
            interno = (
                f"{academia['academia']}:{numero_aluno:03d}"
            )
            evento["aluno"] = anonimizar_aluno(interno, chave)
            if tipo not in ("cobranca_aprovada", "cobranca_falhou"):
                evento["turma"] = rng.choice(TURMAS)
            if tipo in (
                "checkin",
                "matricula",
                "graduacao",
                "aula_experimental",
                "app_aberto",
                "video_assistido",
                "reserva_aula",
            ):
                evento["faixa"] = rng.choice(FAIXAS)
            if tipo == "cobranca_falhou":
                evento["motivo"] = "cartao recusado"
            if tipo == "cancelamento":
                evento["motivo"] = rng.choice(MOTIVOS_CANCELAMENTO)
        eventos.append(evento)
    return eventos
