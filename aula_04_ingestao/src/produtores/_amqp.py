"""Publicação persistente na fila de ingestão."""

from __future__ import annotations

import json
import time
from typing import Any

import pika

from src.config import config


class Publicador:
    """Mantém uma conexão por execução e publica uma mensagem por chamada."""

    def __enter__(self) -> "Publicador":
        credenciais = pika.PlainCredentials(
            config.rabbitmq_user, config.rabbitmq_password or ""
        )
        self.conexao = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=config.rabbitmq_host,
                port=config.rabbitmq_port,
                credentials=credenciais,
            )
        )
        self.canal = self.conexao.channel()
        self.canal.queue_declare(queue=config.fila_ingestao, durable=True)
        self.canal.confirm_delivery()
        return self

    def publicar(self, envelope: dict[str, Any]) -> None:
        confirmado = self.canal.basic_publish(
            exchange="",
            routing_key=config.fila_ingestao,
            body=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers={"recebido_em_ms": time.time_ns() // 1_000_000},
                content_type="application/json",
            ),
            mandatory=True,
        )
        if confirmado is False:
            raise RuntimeError("broker não confirmou a publicação")

    def __exit__(self, *_: object) -> None:
        self.conexao.close()


def publicar(envelope: dict[str, Any]) -> None:
    with Publicador() as publicador:
        publicador.publicar(envelope)
