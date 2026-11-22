import json
import tempfile
from pathlib import Path

from src.gerador.outbox import adicionar_eventos, ler_outbox, marcar_enviado


def test_outbox_pendente_e_busca_sem_nome():
    with tempfile.TemporaryDirectory() as diretorio:
        caminho = Path(diretorio) / "eventos.jsonl"
        evento = {
            "event_id": "7f3b1c9e-52a4-4d0e-9c1b-6a2f8e4d7b10",
            "tipo": "checkin",
            "aluno": "a8f3c1d9e2b47f60",
        }
        adicionar_eventos(caminho, [evento])
        linhas = ler_outbox(caminho)
        assert linhas[0]["estado"] == "pendente"
        conteudo = caminho.read_text(encoding="utf-8")
        assert "Maria Silva" not in conteudo
        marcar_enviado(caminho, evento["event_id"])
        assert ler_outbox(caminho)[0]["estado"] == "enviado"
