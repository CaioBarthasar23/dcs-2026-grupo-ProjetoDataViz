import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from src.chaves import montar_chave
from src.gravacao import gravar_lote
from src.limpeza import remover_confirmado
from tests.fakes import ArmazenamentoFalso


def test_duas_execucoes_identicas_fazem_um_put_e_status_ja_existia(
    tmp_path: Path,
) -> None:
    nome = "CAM-0451_20261017T0900.txt"
    conteudo = b"lote de teste\n"
    caminho = tmp_path / nome
    caminho.write_bytes(conteudo)
    cliente = ArmazenamentoFalso()
    argumentos = {
        "bucket": "raw",
        "caminho": caminho,
        "chave": montar_chave(nome),
        "versao_coletor": "teste",
        "recebido_em": datetime(2026, 11, 2, tzinfo=timezone.utc),
    }

    primeiro = gravar_lote(cliente, **argumentos)

    assert primeiro.status == "gravado"
    assert primeiro.chave == argumentos["chave"]
    assert primeiro.sha256 == hashlib.sha256(conteudo).hexdigest()
    assert primeiro.bytes == len(conteudo)
    assert not caminho.exists()

    caminho.write_bytes(conteudo)
    segundo = gravar_lote(cliente, **argumentos)

    assert segundo.status == "ja_existia"
    assert segundo.chave == primeiro.chave
    assert segundo.sha256 == primeiro.sha256
    assert segundo.bytes == primeiro.bytes
    assert len(cliente.puts) == 1
    assert not caminho.exists()


@pytest.mark.parametrize("status", ["gravado", "ja_existia"])
def test_remover_confirmado_remove_status_confirmados(
    tmp_path: Path, status: str
) -> None:
    caminho = tmp_path / "lote.txt"
    caminho.write_bytes(b"lote")

    remover_confirmado(caminho, status)

    assert not caminho.exists()


def test_remover_confirmado_preserva_status_nao_confirmado(tmp_path: Path) -> None:
    caminho = tmp_path / "lote.txt"
    caminho.write_bytes(b"lote")

    remover_confirmado(caminho, "erro")

    assert caminho.read_bytes() == b"lote"


def test_objeto_sem_sha256_levanta_erro_e_nao_faz_put(tmp_path: Path) -> None:
    nome = "CAM-0451_20261017T0900.txt"
    caminho = tmp_path / nome
    caminho.write_bytes(b"lote de teste")
    cliente = ArmazenamentoFalso()
    cliente.put_object(
        Bucket="raw",
        Key=montar_chave(nome),
        Body=b"conteudo existente",
        Metadata={"outra-chave": "valor"},
    )
    caminho.write_bytes(b"lote de teste")

    with pytest.raises(ValueError, match="sha256"):
        gravar_lote(
            cliente,
            bucket="raw",
            caminho=caminho,
            chave=montar_chave(nome),
            versao_coletor="teste",
            recebido_em=datetime(2026, 11, 2, tzinfo=timezone.utc),
        )

    assert len(cliente.puts) == 1
    assert caminho.exists()


def test_erro_head_que_nao_seja_ausencia_propaga(tmp_path: Path) -> None:
    class ErroHead(ArmazenamentoFalso):
        def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
            raise ClientError(
                {"Error": {"Code": "403", "Message": "teste"}},
                "HeadObject",
            )

    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")

    with pytest.raises(ClientError):
        gravar_lote(
            ErroHead(),
            bucket="raw",
            caminho=caminho,
            chave=montar_chave(caminho.name),
            versao_coletor="teste",
            recebido_em=datetime(2026, 11, 2, tzinfo=timezone.utc),
        )

    assert caminho.exists()
