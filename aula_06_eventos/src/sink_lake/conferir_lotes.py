from __future__ import annotations

import argparse
import gzip
import json
import os

from confluent_kafka import Consumer, TopicPartition

from .storage import S3Storage


def contar_topico(bootstrap: str, topico: str, inicio: int, fim: int) -> tuple[int, list[str]]:
    consumer = Consumer({
        "bootstrap.servers": bootstrap,
        "group.id": "conferencia-lake",
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
    })
    metadata = consumer.list_topics(topico, timeout=10)
    atribuicoes = [
        TopicPartition(topico, partition, inicio)
        for partition in metadata.topics[topico].partitions
    ]
    consumer.assign(atribuicoes)
    linhas = 0
    ids = []
    sem_nova_mensagem = 0
    while sem_nova_mensagem < 10:
        mensagem = consumer.poll(0.5)
        if mensagem is None:
            sem_nova_mensagem += 1
            continue
        sem_nova_mensagem = 0
        if mensagem.error():
            continue
        if mensagem.offset() >= fim:
            continue
        evento = json.loads(mensagem.value().decode("utf-8"))
        if not evento.get("regiao"):
            continue
        linhas += 1
        ids.append(evento["event_id"])
    consumer.close()
    return linhas, ids


def listar_objetos(storage: S3Storage) -> list[tuple[str, list[dict]]]:
    paginator = storage.client.get_paginator("list_objects_v2")
    objetos = []
    for pagina in paginator.paginate(Bucket=storage.bucket):
        for item in pagina.get("Contents", []):
            chave = item["Key"]
            payload = storage.conteudo(chave)
            if payload is None:
                continue
            with gzip.GzipFile(fileobj=__import__("io").BytesIO(payload)) as arquivo:
                texto = arquivo.read().decode("utf-8")
            eventos = [json.loads(linha) for linha in texto.splitlines() if linha]
            objetos.append((chave, eventos))
    return objetos


def principal() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inicio", type=int, required=True)
    parser.add_argument("--fim", type=int, required=True)
    parser.add_argument("--topico", default="tatame.eventos")
    args = parser.parse_args()

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092")
    storage = S3Storage()
    storage.criar_bucket()
    linhas_topico, ids_topico = contar_topico(
        bootstrap,
        args.topico,
        args.inicio,
        args.fim,
    )
    objetos = listar_objetos(storage)
    ids_topico_set = set(ids_topico)
    linhas_bucket = sum(
        1
        for _, eventos in objetos
        for evento in eventos
        if evento["event_id"] in ids_topico_set
    )
    ids_bucket = [
        evento["event_id"]
        for _, eventos in objetos
        for evento in eventos
        if evento["event_id"] in ids_topico_set
    ]
    duplicados = sorted({
        event_id
        for event_id in ids_bucket
        if ids_bucket.count(event_id) > 1
    })
    print(f"topico_linhas={linhas_topico}")
    print(f"bucket_linhas={linhas_bucket}")
    print(f"iguais={linhas_topico == linhas_bucket}")
    print(f"event_id_repetidos={len(duplicados)}")
    for event_id in duplicados[:20]:
        print(f"event_id_repetido={event_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
