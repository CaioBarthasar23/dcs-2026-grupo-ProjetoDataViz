import hashlib
from datetime import datetime, timezone

from src.chaves import montar_chave
from src.gravacao import gravar_lote
from tests.fakes import ArmazenamentoFalso


def test_put_preserva_bytes_sha256_e_metadados(tmp_path) -> None:
    nome = "CAM-0451_20261017T0900.txt"
    conteudo = "linha 1\nlinha 2\r\nposição ç\n".encode("utf-8")
    arquivo = tmp_path / nome
    arquivo.write_bytes(conteudo)
    cliente = ArmazenamentoFalso()

    gravar_lote(
        cliente,
        bucket="raw",
        caminho=arquivo,
        chave=montar_chave(nome),
        versao_coletor="teste",
        recebido_em=datetime(2026, 11, 2, tzinfo=timezone.utc),
    )

    assert len(cliente.puts) == 1
    put = cliente.puts[0]
    assert put.bucket == "raw"
    assert put.chave == (
        "telemetria/data=2026-10-17/hora=12/"
        "caminhao=CAM-0451/lote_1200.txt"
    )
    assert put.body == conteudo
    assert len(put.body) == len(conteudo)
    assert hashlib.sha256(put.body).hexdigest() == hashlib.sha256(conteudo).hexdigest()
    assert put.metadata == {
        "fonte": "provedor-satelite",
        "recebido-em": "2026-11-02T00:00:00Z",
        "versao-coletor": "teste",
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "caminhao": "CAM-0451",
        "janela-inicio": "2026-10-17T12:00:00Z",
        "arquivo-origem": nome,
    }
