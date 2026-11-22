from __future__ import annotations

import argparse
import json
import os
import signal

from confluent_kafka import Consumer, KafkaError


TOPICO = "tatame.eventos"


def bootstrap_servers() -> str:
    valor = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "").strip()
    if not valor:
        raise RuntimeError(
            "KAFKA_BOOTSTRAP_SERVERS ausente: configure o endereco do broker"
        )
    return valor


def principal() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maximo", type=int, default=0)
    args = parser.parse_args()

    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers(),
        "group.id": "verificacao",
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([TOPICO])
    lidos = 0
    encerrando = False

    def parar(_sig, _frame):
        nonlocal encerrando
        encerrando = True

    signal.signal(signal.SIGINT, parar)
    signal.signal(signal.SIGTERM, parar)

    try:
        while not encerrando:
            mensagem = consumer.poll(1.0)
            if mensagem is None:
                if args.maximo and lidos >= args.maximo:
                    break
                continue
            if mensagem.error():
                if mensagem.error().code() != KafkaError._PARTITION_EOF:
                    print(mensagem.error())
                continue

            evento = json.loads(mensagem.value().decode("utf-8"))
            chave = mensagem.key().decode("utf-8") if mensagem.key() else ""
            print(
                f"tatame.eventos p={mensagem.partition()} "
                f"offset={mensagem.offset()} chave={chave} "
                f"event_id={evento.get('event_id')}"
            )
            consumer.commit(message=mensagem, asynchronous=False)
            lidos += 1
            if args.maximo and lidos >= args.maximo:
                break
    finally:
        consumer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
