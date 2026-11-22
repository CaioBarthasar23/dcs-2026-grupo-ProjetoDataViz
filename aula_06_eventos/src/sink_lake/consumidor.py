from __future__ import annotations

import gzip
import json
import os
import signal
from datetime import datetime, timezone
from pathlib import Path

from confluent_kafka import Consumer, KafkaError, TopicPartition

from .chave import montar_chave
from .lote import Lote
from .storage import S3Storage


TOPICO = "tatame.eventos"


def principal() -> int:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092")
    particionar_por = os.environ.get("PARTICIONAR_POR", "evento")
    if particionar_por not in ("evento", "chegada"):
        raise RuntimeError("PARTICIONAR_POR deve ser 'evento' ou 'chegada'")
    minutos = float(os.environ.get("FECHAR_LOTE_MINUTOS", "10"))
    bytes_limite = int(os.environ.get("FECHAR_LOTE_BYTES", "5242880"))

    consumer = Consumer({
        "bootstrap.servers": bootstrap,
        "group.id": "sink-lake",
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([TOPICO])
    storage = S3Storage()
    storage.criar_bucket()
    lotes: dict[tuple[str, str, str, int], Lote] = {}
    offsets: dict[tuple[str, int], int] = {}
    estado_path = Path(os.environ.get("LAKE_ESTADO_PATH", "estado/lake_sink.json"))
    vistos: set[str] = set()
    if estado_path.exists():
        try:
            vistos = set(json.loads(estado_path.read_text(encoding="utf-8")).get("event_ids", []))
        except json.JSONDecodeError:
            vistos = set()
    encerrando = False

    def parar(_sig, _frame):
        nonlocal encerrando
        encerrando = True

    def persistir_vistos() -> None:
        estado_path.parent.mkdir(parents=True, exist_ok=True)
        temporario = estado_path.with_suffix(".tmp")
        temporario.write_text(
            json.dumps({"event_ids": sorted(vistos)}),
            encoding="utf-8",
        )
        temporario.replace(estado_path)

    signal.signal(signal.SIGINT, parar)
    signal.signal(signal.SIGTERM, parar)

    def fechar_lotes(forcar: bool = False) -> None:
        agora = datetime.now(timezone.utc)
        nao_vazio = False
        for identificador, lote in list(lotes.items()):
            if not forcar and not lote.fechar(agora):
                continue
            jsonl = b"".join(linha + b"\n" for linha in lote.linhas_raw)
            gz = gzip.compress(jsonl, mtime=0)
            chave = montar_chave(
                lote.regiao,
                lote.instante_particao,
                particionar_por,
                lote.partition,
                lote.primeiro_offset,
            )
            storage.gravar(chave, gz)
            offsets[(TOPICO, lote.partition)] = max(
                offsets.get((TOPICO, lote.partition), lote.primeiro_offset),
                lote.ultimo_offset + 1,
            )
            lotes.pop(identificador)
            nao_vazio = True
        if nao_vazio and offsets:
            consumer.commit(
                offsets=[
                    TopicPartition(topic, partition, offset)
                    for (topic, partition), offset in offsets.items()
                ],
                asynchronous=False,
            )

    try:
        while not encerrando:
            mensagem = consumer.poll(1.0)
            agora = datetime.now(timezone.utc)
            fechar_lotes(False)

            if mensagem is None:
                continue
            if mensagem.error():
                if mensagem.error().code() != KafkaError._PARTITION_EOF:
                    print(mensagem.error())
                continue

            raw = mensagem.value()
            evento = json.loads(raw.decode("utf-8"))
            event_id = evento.get("event_id")
            if event_id and event_id in vistos:
                offsets[(mensagem.topic(), mensagem.partition())] = mensagem.offset() + 1
                consumer.commit(
                    offsets=[
                        TopicPartition(topic, partition, offset)
                        for (topic, partition), offset in offsets.items()
                    ],
                    asynchronous=False,
                )
                continue
            if event_id:
                vistos.add(event_id)
                persistir_vistos()
            if not evento.get("regiao"):
                offsets[(mensagem.topic(), mensagem.partition())] = mensagem.offset() + 1
                consumer.commit(
                    offsets=[
                        TopicPartition(topic, partition, offset)
                        for (topic, partition), offset in offsets.items()
                    ],
                    asynchronous=False,
                )
                continue
            if particionar_por == "evento":
                ocorrido_em = evento.get("ocorrido_em")
                if ocorrido_em:
                    instante = datetime.fromisoformat(
                        ocorrido_em.replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                else:
                    instante = agora
            else:
                instante = agora

            regiao = evento["regiao"]
            instante_particao = instante.replace(minute=0, second=0, microsecond=0)
            identificador = (
                regiao,
                instante_particao.strftime("%Y-%m-%d"),
                instante_particao.strftime("%H"),
                mensagem.partition(),
            )
            lote = lotes.get(identificador)
            if lote is None:
                lote = Lote(
                    mensagem.partition(),
                    mensagem.offset(),
                    regiao,
                    instante_particao,
                    abrir_em=agora,
                    fechar_tempo_minutos=minutos,
                    fechar_tamanho_bytes=bytes_limite,
                )
                lotes[identificador] = lote
            lote.adicionar_raw(evento, raw)
            lote.ultimo_offset = mensagem.offset()

            if lote.fechar(agora):
                fechar_lotes(True)
    finally:
        fechar_lotes(True)
        if offsets:
            consumer.commit(
                offsets=[
                    TopicPartition(topic, partition, offset)
                    for (topic, partition), offset in offsets.items()
                ],
                asynchronous=False,
            )
        consumer.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
