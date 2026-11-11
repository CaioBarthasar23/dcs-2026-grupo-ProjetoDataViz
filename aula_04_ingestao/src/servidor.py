"""Inicializa a API HTTP e o consumidor RabbitMQ no mesmo processo."""

import logging
import threading

import uvicorn

from src.api import app
from src.config import config
from src.consumidor import consumir


logger = logging.getLogger(__name__)


def iniciar_consumidor(
    stop_event: threading.Event | None = None,
) -> tuple[threading.Thread, threading.Event]:
    parar = stop_event or threading.Event()
    thread = threading.Thread(
        target=consumir,
        kwargs={"stop_event": parar},
        name="consumidor-ingestao",
        daemon=True,
    )
    thread.start()
    return thread, parar


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _, parar = iniciar_consumidor()
    try:
        uvicorn.run(app, host="0.0.0.0", port=config.api_port)
    finally:
        parar.set()


if __name__ == "__main__":
    main()
