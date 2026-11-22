from __future__ import annotations

import json
import os
import signal
from pathlib import Path

from confluent_kafka import Consumer, KafkaError, Producer

from .config import ConfiguracaoCEP
from .estado import EstadoPersistente
from .motor import MotorCEP


def bootstrap_servers() -> str:
    valor = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "").strip()
    if not valor:
        raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS ausente")
    return valor


def principal() -> int:
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers(),
        "group.id": "cep",
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
    })
    producer = Producer({
        "bootstrap.servers": bootstrap_servers(),
        "acks": "all",
        "enable.idempotence": True,
    })
    consumer.subscribe(["tatame.eventos"])

    estado = EstadoPersistente(
        os.environ.get("CEP_ESTADO_PATH", "estado/cep.json")
    )
    motor = MotorCEP(estado, ConfiguracaoCEP.ambiente())
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
                complexos = motor.processar_temporizadores()
                for complexo in complexos:
                    producer.produce(
                        "tatame.alertas",
                        key=complexo["chave"].encode("utf-8"),
                        value=json.dumps(complexo, ensure_ascii=False).encode("utf-8"),
                    )
                if complexos:
                    restante = producer.flush(30)
                    if restante:
                        raise RuntimeError("alerta CEP nao confirmado pelo broker")
                continue
            if mensagem.error():
                if mensagem.error().code() != KafkaError._PARTITION_EOF:
                    print(mensagem.error())
                continue

            evento = json.loads(mensagem.value().decode("utf-8"))
            complexos = motor.processar(evento)
            for complexo in complexos:
                producer.produce(
                    "tatame.alertas",
                    key=complexo["chave"].encode("utf-8"),
                    value=json.dumps(complexo, ensure_ascii=False).encode("utf-8"),
                )
            if complexos:
                restante = producer.flush(30)
                if restante:
                    raise RuntimeError("alerta CEP nao confirmado pelo broker")
            estado.persistir()
            consumer.commit(message=mensagem, asynchronous=False)
    finally:
        estado.persistir()
        consumer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
