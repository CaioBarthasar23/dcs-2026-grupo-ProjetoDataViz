import asyncio
import json
from pathlib import Path

from src import api


EXEMPLOS = Path(__file__).parents[1] / "specs" / "exemplos"


def _request(
    metodo: str,
    caminho: str,
    corpo: bytes = b"",
    content_type: str = "application/json",
) -> tuple[int, bytes]:
    mensagens = iter(
        [{"type": "http.request", "body": corpo, "more_body": False}]
    )
    respostas = []

    async def receive():
        return next(mensagens)

    async def send(mensagem):
        respostas.append(mensagem)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": metodo,
        "scheme": "http",
        "path": caminho,
        "raw_path": caminho.encode(),
        "query_string": b"",
        "headers": [
            (b"content-type", content_type.encode()),
            (b"content-length", str(len(corpo)).encode()),
        ],
        "server": ("test", 80),
        "client": ("test", 1234),
        "root_path": "",
        "state": {},
    }
    asyncio.run(api.app(scope, receive, send))
    status = next(m["status"] for m in respostas if m["type"] == "http.response.start")
    body = b"".join(
        m.get("body", b"") for m in respostas if m["type"] == "http.response.body"
    )
    return status, body


def _post(corpo: bytes, content_type: str = "application/json") -> tuple[int, bytes]:
    return _request("POST", "/ingest", corpo, content_type)


def test_health_responde_ok() -> None:
    status, corpo = _request("GET", "/health")

    assert status == 200
    assert json.loads(corpo) == {"status": "ok"}


def test_post_valido_responde_202_e_publica_na_fila(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(api, "publicar_na_fila", lambda envelope: chamadas.append(envelope))
    corpo = (EXEMPLOS / "valido_livros_objeto.json").read_bytes()

    status, _ = _post(corpo)

    assert status == 202
    assert len(chamadas) == 1


def test_post_envelope_invalido_responde_422_com_motivo_sem_publicar(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(api, "publicar_na_fila", lambda envelope: chamadas.append(envelope))
    corpo = (EXEMPLOS / "invalido_422_data_tag_desconhecida.json").read_bytes()

    status, corpo_resposta = _post(corpo)

    assert status == 422
    assert json.loads(corpo_resposta).get("motivo")
    assert chamadas == []


def test_post_corpo_nao_json_responde_400_sem_publicar(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(api, "publicar_na_fila", lambda envelope: chamadas.append(envelope))
    corpo = (EXEMPLOS / "invalido_400_nao_json.txt").read_bytes()

    status, _ = _post(corpo, content_type="text/plain")

    assert status == 400
    assert chamadas == []


def test_post_corpo_grande_responde_413_sem_publicar(monkeypatch) -> None:
    chamadas = []
    monkeypatch.setattr(api, "publicar_na_fila", lambda envelope: chamadas.append(envelope))
    corpo = (EXEMPLOS / "invalido_413_corpo_grande_demais.json").read_bytes()

    status, _ = _post(corpo)

    assert status == 413
    assert chamadas == []


def test_publicador_cria_fila_duravel_e_confirma_mensagem(monkeypatch) -> None:
    class CanalFalso:
        def __init__(self):
            self.confirmacao_ativada = False
            self.fila = None
            self.publicacao = None

        def queue_declare(self, **kwargs):
            self.fila = kwargs

        def confirm_delivery(self):
            self.confirmacao_ativada = True

        def basic_publish(self, **kwargs):
            self.publicacao = kwargs
            return True

    class ConexaoFalsa:
        def __init__(self):
            self.canal_falso = CanalFalso()
            self.fechada = False

        def channel(self):
            return self.canal_falso

        def close(self):
            self.fechada = True

    conexao = ConexaoFalsa()
    monkeypatch.setattr(api.pika, "BlockingConnection", lambda parametros: conexao)
    corpo = b'{"data_tag":"livros","data":{"upc":"x"}}'

    api.publicar_na_fila(corpo)

    assert conexao.canal_falso.fila == {
        "queue": api.config.fila_ingestao,
        "durable": True,
    }
    assert conexao.canal_falso.confirmacao_ativada
    publicacao = conexao.canal_falso.publicacao
    assert publicacao["body"] == corpo
    assert publicacao["routing_key"] == api.config.fila_ingestao
    assert publicacao["mandatory"] is True
    assert publicacao["properties"].delivery_mode == 2
    recebido_em_ms = publicacao["properties"].headers["recebido_em_ms"]
    assert isinstance(recebido_em_ms, int) and recebido_em_ms > 0
    assert conexao.fechada
