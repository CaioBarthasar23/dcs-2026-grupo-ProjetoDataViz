"""API HTTP de entrada para envelopes de ingestão."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

import pika
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from src.config import config
from src.contrato import CorpoNaoJson, EnvelopeInvalido, validar


app = FastAPI(title="API de ingestão")
_PUBLISH_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="api-amqp")


def publicar_na_fila(corpo: bytes) -> None:
    """Publica o corpo original com persistência e publisher confirmation."""
    credenciais = pika.PlainCredentials(
        config.rabbitmq_user,
        config.rabbitmq_password or "",
    )
    conexao = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=config.rabbitmq_host,
            port=config.rabbitmq_port,
            credentials=credenciais,
        )
    )
    try:
        canal = conexao.channel()
        canal.queue_declare(queue=config.fila_ingestao, durable=True)
        canal.confirm_delivery()
        confirmado = canal.basic_publish(
            exchange="",
            routing_key=config.fila_ingestao,
            body=corpo,
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers={"recebido_em_ms": time.time_ns() // 1_000_000},
            ),
            mandatory=True,
        )
        if confirmado is False:
            raise RuntimeError("broker não confirmou a publicação")
    finally:
        conexao.close()


@app.post("/ingest", status_code=202)
async def ingest(request: Request) -> Response:
    # O limite é aplicado antes de acumular um corpo arbitrariamente grande.
    partes: list[bytes] = []
    tamanho = 0
    async for parte in request.stream():
        tamanho += len(parte)
        if tamanho > config.http_max_bytes:
            return JSONResponse(
                status_code=413,
                content={"motivo": f"corpo excede HTTP_MAX_BYTES ({config.http_max_bytes} bytes)"},
            )
        partes.append(parte)
    corpo_bytes = b"".join(partes)

    try:
        validar(corpo_bytes, config.dominios)
    except CorpoNaoJson as erro:
        return JSONResponse(status_code=400, content={"motivo": erro.motivo})
    except EnvelopeInvalido as erro:
        return JSONResponse(
            status_code=erro.status_code,
            content={"motivo": erro.motivo},
        )

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_PUBLISH_EXECUTOR, publicar_na_fila, corpo_bytes)
    return Response(status_code=202)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
