import hashlib
from datetime import datetime, timezone
from pathlib import Path

from src.chaves import montar_chave
from src.gravacao import gravar_lote
from tests.fakes import ArmazenamentoFalso


def test_mesma_chave_conteudo_diferente_registra_conflito_sem_put_e_mantem_pouso(
    tmp_path: Path,
) -> None:
    nome = "CAM-0451_20261017T0900.txt"
    conteudo_original = b"lote original\n"
    conteudo_retransmitido = b"lote alterado\r\n"
    caminho = tmp_path / nome
    chave = montar_chave(nome)
    cliente = ArmazenamentoFalso()
    argumentos = {
        "bucket": "raw",
        "caminho": caminho,
        "chave": chave,
        "versao_coletor": "teste",
        "recebido_em": datetime(2026, 11, 2, tzinfo=timezone.utc),
    }

    caminho.write_bytes(conteudo_original)
    primeiro = gravar_lote(cliente, **argumentos)
    caminho.write_bytes(conteudo_retransmitido)

    resultado = gravar_lote(cliente, **argumentos)

    objeto = cliente.objetos[("raw", chave)]
    assert primeiro.status == "gravado"
    assert resultado.status == "conflito_hash"
    assert resultado.sha256 == hashlib.sha256(conteudo_retransmitido).hexdigest()
    assert len(cliente.puts) == 1
    assert objeto.body == conteudo_original
    assert objeto.metadata["sha256"] == hashlib.sha256(conteudo_original).hexdigest()
    assert caminho.read_bytes() == conteudo_retransmitido
