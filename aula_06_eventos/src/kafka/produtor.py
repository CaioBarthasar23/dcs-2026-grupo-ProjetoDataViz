from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

from confluent_kafka import Producer

from src.gerador.outbox import ler_outbox, marcar_enviado


TOPICO = "tatame.eventos"


def bootstrap_servers() -> str:
    valor = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "").strip()
    if not valor:
        raise RuntimeError(
            "KAFKA_BOOTSTRAP_SERVERS ausente: configure o endereco do broker"
        )
    return valor


def criar_produtor() -> Producer:
    return Producer({
        "bootstrap.servers": bootstrap_servers(),
        "acks": "all",
        "enable.idempotence": True,
    })


def publicar_pendentes(
    caminho_outbox: str | Path,
    produtor: Producer | None = None,
    maximo: int | None = None,
) -> int:
    cliente = produtor or criar_produtor()
    pendentes = [
        linha for linha in ler_outbox(caminho_outbox)
        if linha["estado"] == "pendente"
    ]
    if maximo is not None:
        pendentes = pendentes[:maximo]

    erros: list[str] = []
    confirmados: list[str] = []

    def entrega(error, mensagem) -> None:
        event_id = None
        try:
            event_id = json.loads(mensagem.value().decode("utf-8")).get("event_id")
        except Exception:
            pass
        if error is not None:
            erros.append(f"{event_id}: {error}")

    for linha in pendentes:
        evento = linha["evento"]
        try:
            cliente.produce(
                TOPICO,
                key=evento["academia"].encode("utf-8"),
                value=json.dumps(evento, ensure_ascii=False).encode("utf-8"),
                on_delivery=entrega,
            )
            confirmados.append(evento["event_id"])
        except BufferError:
            cliente.poll(0)
            cliente.produce(
                TOPICO,
                key=evento["academia"].encode("utf-8"),
                value=json.dumps(evento, ensure_ascii=False).encode("utf-8"),
                on_delivery=entrega,
            )
            confirmados.append(evento["event_id"])
        cliente.poll(0)

    restante = cliente.flush(30)
    if restante:
        raise RuntimeError(f"{restante} mensagem(ns) nao foram confirmadas pelo broker")
    if erros:
        raise RuntimeError("Falhas de entrega: " + "; ".join(erros))

    for event_id in confirmados:
        marcar_enviado(caminho_outbox, event_id)
    return len(confirmados)


def principal() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outbox", default="outbox/eventos.jsonl")
    parser.add_argument("--maximo", type=int)
    args = parser.parse_args()
    print(publicar_pendentes(args.outbox, maximo=args.maximo))
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
