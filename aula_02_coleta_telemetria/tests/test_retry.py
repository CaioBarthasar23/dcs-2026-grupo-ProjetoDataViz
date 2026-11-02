import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

from src.chaves import montar_chave
from src.gravacao import gravar_lote
from tests.fakes import ArmazenamentoFalso, Put


def erro_s3(codigo: int) -> ClientError:
    return ClientError(
        {"Error": {"Code": str(codigo), "Message": "teste"}},
        "PutObject",
    )


def argumentos(caminho: Path) -> dict[str, object]:
    return {
        "bucket": "raw",
        "caminho": caminho,
        "chave": montar_chave(caminho.name),
        "versao_coletor": "teste",
        "recebido_em": datetime(2026, 11, 2, tzinfo=timezone.utc),
    }


def test_502_head_ausente_reenvia_put_apos_espera_crescente(
    tmp_path: Path,
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    cliente.resultados_put = [erro_s3(502), erro_s3(503), None]
    esperas: list[float] = []

    def dormir(atraso: float) -> None:
        esperas.append(atraso)
        cliente.chamadas.append("sleep")

    resultado = gravar_lote(
        cliente,
        **argumentos(caminho),
        atrasos=(0.1, 0.2),
        dormir=dormir,
    )

    assert resultado.status == "gravado"
    assert cliente.chamadas == [
        "head",
        "put",
        "head",
        "sleep",
        "put",
        "head",
        "sleep",
        "put",
    ]
    assert esperas == [0.1, 0.2]
    assert len(cliente.puts) == 1
    assert not caminho.exists()


def test_403_nao_faz_nova_tentativa_nem_reconciliacao(
    tmp_path: Path,
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    cliente.resultados_put = [erro_s3(403)]
    esperas: list[float] = []

    resultado = gravar_lote(
        cliente,
        **argumentos(caminho),
        atrasos=(0.1, 0.2),
        dormir=esperas.append,
    )

    assert resultado.status == "erro"
    assert cliente.chamadas == ["head", "put"]
    assert esperas == []
    assert caminho.read_bytes() == b"lote"


def _verificar_reconciliacao_com_objeto_existente(
    tmp_path: Path, *, hash_igual: bool, status: str
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    conteudo = b"lote retransmitido"
    caminho.write_bytes(conteudo)
    chave = montar_chave(caminho.name)
    cliente = ArmazenamentoFalso()
    sha_existente = (
        hashlib.sha256(conteudo).hexdigest()
        if hash_igual
        else hashlib.sha256(b"objeto diferente").hexdigest()
    )
    objeto_original = Put(
        "raw",
        chave,
        b"objeto original",
        {"sha256": sha_existente},
    )
    cliente.objetos[("raw", chave)] = objeto_original
    cliente.respostas_head = [
        ClientError(
            {"Error": {"Code": "404", "Message": "teste"}},
            "HeadObject",
        )
    ]
    cliente.resultados_put = [erro_s3(502)]

    resultado = gravar_lote(
        cliente,
        **argumentos(caminho),
        atrasos=(0.1,),
        dormir=lambda _: pytest.fail("não deve esperar"),
    )

    assert resultado.status == status
    assert cliente.chamadas == ["head", "put", "head"]
    assert cliente.objetos[("raw", chave)] == objeto_original
    if status == "ja_existia":
        assert not caminho.exists()
    else:
        assert caminho.read_bytes() == conteudo


def test_502_head_igual_registra_ja_existia_sem_repetir(tmp_path: Path) -> None:
    _verificar_reconciliacao_com_objeto_existente(
        tmp_path, hash_igual=True, status="ja_existia"
    )


def test_502_head_diferente_registra_conflito_sem_repetir(tmp_path: Path) -> None:
    _verificar_reconciliacao_com_objeto_existente(
        tmp_path, hash_igual=False, status="conflito_hash"
    )


def test_502_sem_politica_reconcilia_e_retorna_erro(tmp_path: Path) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    cliente.resultados_put = [erro_s3(502)]

    resultado = gravar_lote(cliente, **argumentos(caminho))

    assert resultado.status == "erro"
    assert cliente.chamadas == ["head", "put", "head"]
    assert caminho.read_bytes() == b"lote"


@pytest.mark.parametrize(
    "falha_head",
    [
        erro_s3(502),
        erro_s3(503),
        erro_s3(504),
        ReadTimeoutError(endpoint_url="teste"),
        ConnectTimeoutError(endpoint_url="teste"),
    ],
)
def test_primeiro_head_transitorio_retorna_erro_sem_put(
    tmp_path: Path, falha_head: Exception
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    conteudo = b"lote"
    caminho.write_bytes(conteudo)
    cliente = ArmazenamentoFalso()
    cliente.respostas_head = [falha_head]

    resultado = gravar_lote(cliente, **argumentos(caminho))

    assert resultado.status == "erro"
    assert cliente.chamadas == ["head"]
    assert cliente.puts == []
    assert caminho.read_bytes() == conteudo


def test_502_head_inconclusivo_retorna_erro_sem_repetir(tmp_path: Path) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    cliente.respostas_head = [
        ClientError(
            {"Error": {"Code": "404", "Message": "teste"}},
            "HeadObject",
        ),
        ClientError(
            {"Error": {"Code": "503", "Message": "teste"}},
            "HeadObject",
        ),
    ]
    cliente.resultados_put = [erro_s3(502)]
    esperas: list[float] = []

    resultado = gravar_lote(
        cliente,
        **argumentos(caminho),
        atrasos=(0.1,),
        dormir=esperas.append,
    )

    assert resultado.status == "erro"
    assert cliente.chamadas == ["head", "put", "head"]
    assert esperas == []
    assert caminho.read_bytes() == b"lote"


def test_retry_esgotado_apos_head_confirmar_ausencia(tmp_path: Path) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    cliente.resultados_put = [erro_s3(502), erro_s3(502)]
    esperas: list[float] = []

    resultado = gravar_lote(
        cliente,
        **argumentos(caminho),
        atrasos=(0.1,),
        dormir=esperas.append,
    )

    assert resultado.status == "erro"
    assert cliente.chamadas == ["head", "put", "head", "put", "head"]
    assert esperas == [0.1]
    assert caminho.read_bytes() == b"lote"


@pytest.mark.parametrize(
    "erro",
    [ReadTimeoutError(endpoint_url="teste"), ConnectTimeoutError(endpoint_url="teste")],
)
def test_timeout_e_reconciliado_por_tipo_de_excecao(
    tmp_path: Path, erro: Exception
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    cliente.resultados_put = [erro]

    resultado = gravar_lote(
        cliente,
        **argumentos(caminho),
    )

    assert resultado.status == "erro"
    assert cliente.chamadas == ["head", "put", "head"]
    assert caminho.read_bytes() == b"lote"
