from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from src.chaves import montar_chave
from src.gravacao import gravar_lote
from src.limpeza import remover_confirmado
from tests.fakes import ArmazenamentoFalso, Put


class ArmazenamentoQueObservaPouso(ArmazenamentoFalso):
    def __init__(self, caminho: Path) -> None:
        super().__init__()
        self.caminho = caminho
        self.existia_durante_put: list[bool] = []

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        Metadata: dict[str, str],
    ) -> None:
        self.existia_durante_put.append(self.caminho.is_file())
        super().put_object(
            Bucket=Bucket,
            Key=Key,
            Body=Body,
            Metadata=Metadata,
        )


def _argumentos(caminho: Path) -> dict[str, object]:
    return {
        "bucket": "raw",
        "caminho": caminho,
        "chave": montar_chave(caminho.name),
        "versao_coletor": "teste",
        "recebido_em": datetime(2026, 11, 2, tzinfo=timezone.utc),
    }


def _erro_s3(codigo: int) -> ClientError:
    return ClientError(
        {"Error": {"Code": str(codigo), "Message": "teste"}},
        "PutObject",
    )


@pytest.mark.parametrize("codigo", [502, 403])
def test_put_falha_mantem_arquivo_no_pouso_e_presente_durante_put(
    tmp_path: Path, codigo: int
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    conteudo = b"lote de teste"
    caminho.write_bytes(conteudo)
    cliente = ArmazenamentoQueObservaPouso(caminho)
    cliente.resultados_put = [_erro_s3(codigo)]

    resultado = gravar_lote(cliente, **_argumentos(caminho))

    assert resultado.status == "erro"
    assert cliente.existia_durante_put == [True]
    assert caminho.read_bytes() == conteudo


def test_put_confirmado_remove_arquivo_apos_put(tmp_path: Path) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote de teste")
    cliente = ArmazenamentoQueObservaPouso(caminho)

    resultado = gravar_lote(cliente, **_argumentos(caminho))

    assert resultado.status == "gravado"
    assert cliente.existia_durante_put == [True]
    assert not caminho.exists()


def test_ja_existia_remove_arquivo_apos_confirmacao(tmp_path: Path) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    conteudo = b"lote de teste"
    caminho.write_bytes(conteudo)
    cliente = ArmazenamentoQueObservaPouso(caminho)
    argumentos = _argumentos(caminho)

    primeiro = gravar_lote(cliente, **argumentos)
    caminho.write_bytes(conteudo)
    segundo = gravar_lote(cliente, **argumentos)

    assert primeiro.status == "gravado"
    assert segundo.status == "ja_existia"
    assert cliente.existia_durante_put == [True]
    assert len(cliente.puts) == 1
    assert not caminho.exists()


def test_conflito_hash_mantem_arquivo_no_pouso(tmp_path: Path) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    chave = montar_chave(caminho.name)
    caminho.write_bytes(b"conteudo retransmitido")
    cliente = ArmazenamentoQueObservaPouso(caminho)
    cliente.objetos[("raw", chave)] = Put(
        "raw",
        chave,
        b"conteudo original",
        {"sha256": "hash-original"},
    )

    resultado = gravar_lote(cliente, **_argumentos(caminho))

    assert resultado.status == "conflito_hash"
    assert cliente.existia_durante_put == []
    assert caminho.read_bytes() == b"conteudo retransmitido"


@pytest.mark.parametrize("status", ["conflito_hash", "erro"])
def test_status_nao_confirmado_nao_remove_arquivo(
    tmp_path: Path, status: str
) -> None:
    caminho = tmp_path / "lote.txt"
    caminho.write_bytes(b"lote")

    remover_confirmado(caminho, status)

    assert caminho.read_bytes() == b"lote"
