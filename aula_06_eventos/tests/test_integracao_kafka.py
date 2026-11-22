from __future__ import annotations

import json
import os
import time
from uuid import uuid4

import pytest
from confluent_kafka import Consumer, Producer


TOPICO = "tatame.eventos"


def entrega_sucesso(error, mensagem):
    assert error is None


def test_dez_eventos_mesma_academia_mesma_particao_offsets_crescentes():
    bootstrap = os.environ.get(
        "KAFKA_BOOTSTRAP_SERVERS",
        "127.0.0.1:29092",
    )

    producer = Producer({
        "bootstrap.servers": bootstrap,
        "acks": "all",
        "enable.idempotence": True,
    })
    eventos = []
    offsets_por_academia: dict[str, list[int]] = {
        "SE-STO-014": [],
        "US-VA-003": [],
    }
    particoes_por_academia: dict[str, set[int]] = {
        "SE-STO-014": set(),
        "US-VA-003": set(),
    }

    def entrega(error, mensagem):
        assert error is None
        evento = json.loads(mensagem.value().decode("utf-8"))
        academia = evento["academia"]
        offsets_por_academia[academia].append(mensagem.offset())
        particoes_por_academia[academia].add(mensagem.partition())

    for indice in range(10):
        academia = "SE-STO-014" if indice < 5 else "US-VA-003"
        evento = {
            "event_id": str(uuid4()),
            "tipo": "checkin",
            "academia": academia,
        }
        eventos.append(evento)
        producer.produce(
            TOPICO,
            key=academia.encode("utf-8"),
            value=json.dumps(evento).encode("utf-8"),
            on_delivery=entrega,
        )
    assert producer.flush(30) == 0

    assert len(particoes_por_academia["SE-STO-014"]) == 1
    assert len(particoes_por_academia["US-VA-003"]) == 1
    for offsets in offsets_por_academia.values():
        assert offsets == sorted(offsets)
        assert len(offsets) == 5
