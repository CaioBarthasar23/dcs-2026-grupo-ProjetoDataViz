from __future__ import annotations

import json
import os
import signal
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from confluent_kafka import Consumer, KafkaError, TopicPartition

from .agregacao import AgregadorMinuto
from .escrita import EscritorInfluxDB


def principal() -> int:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092")
    tamanho = int(os.environ.get("INFLUXDB_LOTE_TAMANHO", "100"))
    intervalo = float(os.environ.get("INFLUXDB_LOTE_INTERVALO_SEG", "1"))

    consumer = Consumer({
        "bootstrap.servers": bootstrap,
        "group.id": "sink-influxdb",
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe(["tatame.eventos"])
    agregador = AgregadorMinuto(
        os.environ.get("INFLUXDB_ESTADO_PATH", "estado/influxdb.json"),
        timedelta(hours=int(os.environ.get("INFLUXDB_DEDUPLICACAO_HORAS", "24"))),
    )
    escritor = EscritorInfluxDB()
    encerrando = False
    pendentes = 0
    ultima_escrita = time.monotonic()
    offsets_confirmados: dict[tuple[str, int], int] = {}

    def parar(_sig, _frame):
        nonlocal encerrando
        encerrando = True

    signal.signal(signal.SIGINT, parar)
    signal.signal(signal.SIGTERM, parar)

    try:
        while not encerrando:
            mensagem = consumer.poll(1.0)
            if mensagem is not None:
                if mensagem.error():
                    if mensagem.error().code() != KafkaError._PARTITION_EOF:
                        print(mensagem.error())
                    continue
                evento = json.loads(mensagem.value().decode("utf-8"))
                if evento.get("ocorrido_em"):
                    agregador.adicionar(evento)
                pendentes += 1
                offsets_confirmados[
                    (mensagem.topic(), mensagem.partition())
                ] = mensagem.offset() + 1

            deve_escrever = (
                pendentes
                and (
                    pendentes >= tamanho
                    or time.monotonic() - ultima_escrita >= intervalo
                )
            )
            if deve_escrever:
                escritor.escrever(agregador.pontos_line_protocol())
                limite = datetime.now(timezone.utc) - agregador.deduplicacao
                agregador.expirar_deduplicacao(limite)
                agregador.persistir()
                consumer.commit(
                    offsets=[
                        TopicPartition(topic, partition, offset)
                        for (topic, partition), offset in offsets_confirmados.items()
                    ],
                    asynchronous=False,
                )
                pendentes = 0
                offsets_confirmados.clear()
                ultima_escrita = time.monotonic()
    finally:
        if pendentes:
            escritor.escrever(agregador.pontos_line_protocol())
            agregador.persistir()
            consumer.commit(
                offsets=[
                    TopicPartition(topic, partition, offset)
                    for (topic, partition), offset in offsets_confirmados.items()
                ],
                asynchronous=False,
            )
        consumer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
