from __future__ import annotations

import os

from confluent_kafka.admin import AdminClient, NewTopic


TOPICO = "tatame.eventos"
TOPICO_ALERTAS = "tatame.alertas"
RETENCAO_MS = 604800000


def bootstrap_servers() -> str:
    valor = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "").strip()
    if not valor:
        raise RuntimeError("KAFKA_BOOTSTRAP_SERVERS ausente")
    return valor


def principal() -> int:
    admin = AdminClient({"bootstrap.servers": bootstrap_servers()})
    novos = [
        NewTopic(
            TOPICO,
            num_partitions=6,
            replication_factor=1,
            config={"retention.ms": str(RETENCAO_MS)},
        ),
        NewTopic(
            TOPICO_ALERTAS,
            num_partitions=6,
            replication_factor=1,
            config={"retention.ms": str(RETENCAO_MS)},
        ),
    ]
    futuros = admin.create_topics(novos)
    for topico in (TOPICO, TOPICO_ALERTAS):
        try:
            futuros[topico].result(timeout=30)
        except Exception as erro:
            if "TOPIC_ALREADY_EXISTS" not in str(erro).upper():
                raise
        print(f"{topico} particoes=6 retention.ms={RETENCAO_MS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
