import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.config import Config
from botocore.exceptions import ClientError

import src.coletor as coletor
from src.config import Configuracao
from src.coletor import executar
from src.chaves import montar_chave
from tests.fakes import ArmazenamentoFalso, Put


_INICIO = datetime(2026, 10, 17, 12, 4, 5, tzinfo=timezone.utc)


def _configuracao(pouso: Path) -> Configuracao:
    return Configuracao(
        s3_endpoint_url="http://teste",
        s3_access_key="teste",
        s3_secret_key="teste",
        bucket_raw="raw",
        s3_region="teste",
        coletor_versao="teste",
        pouso_dir=pouso,
    )


def _linhas_manifesto(cliente: ArmazenamentoFalso) -> list[dict]:
    manifesto = next(
        objeto
        for objeto in cliente.puts
        if objeto.chave.startswith("_manifestos/")
    )
    return [
        json.loads(linha)
        for linha in manifesto.body.decode("utf-8").splitlines()
    ]


def test_falha_em_lote_nao_interrompe_demais(tmp_path: Path) -> None:
    primeiro = tmp_path / "CAM-0451_20261017T0900.txt"
    segundo = tmp_path / "CAM-0452_20261017T0900.txt"
    primeiro.write_bytes(b"primeiro")
    segundo.write_bytes(b"segundo")
    cliente = ArmazenamentoFalso()
    cliente.respostas_head = [
        ClientError(
            {"Error": {"Code": "403", "Message": "teste"}},
            "HeadObject",
        )
    ]

    codigo = executar(_configuracao(tmp_path), cliente, _INICIO)

    assert codigo == 1
    linhas = _linhas_manifesto(cliente)
    assert [linha["status"] for linha in linhas] == ["erro", "gravado"]
    assert primeiro.exists()
    assert not segundo.exists()
    assert any(objeto.chave == montar_chave(segundo.name) for objeto in cliente.puts)


def test_main_configura_cliente_s3_sem_retry_automatico(
    tmp_path: Path, monkeypatch
) -> None:
    configuracao = _configuracao(tmp_path)
    cliente = ArmazenamentoFalso()
    opcoes: dict[str, object] = {}

    def criar_cliente(servico: str, **kwargs: object) -> ArmazenamentoFalso:
        assert servico == "s3"
        opcoes.update(kwargs)
        return cliente

    monkeypatch.setattr(coletor, "carregar_configuracao", lambda: configuracao)
    monkeypatch.setattr(coletor.boto3, "client", criar_cliente)

    assert coletor.main() == 0
    assert opcoes["endpoint_url"] == "http://teste"
    assert opcoes["aws_access_key_id"] == "teste"
    assert opcoes["aws_secret_access_key"] == "teste"
    assert opcoes["region_name"] == "teste"
    config = opcoes["config"]
    assert isinstance(config, Config)
    assert config.s3 == {"addressing_style": "path"}
    assert config.retries == {"max_attempts": 0}


@pytest.mark.parametrize(
    ("situacao", "codigo_esperado"),
    [("erro", 1), ("conflito_hash", 1), ("gravado", 0)],
)
def test_codigo_de_saida_sinaliza_erro_ou_conflito(
    tmp_path: Path, situacao: str, codigo_esperado: int
) -> None:
    caminho = tmp_path / "CAM-0451_20261017T0900.txt"
    caminho.write_bytes(b"lote")
    cliente = ArmazenamentoFalso()
    if situacao == "erro":
        cliente.respostas_head = [
            ClientError(
                {"Error": {"Code": "403", "Message": "teste"}},
                "HeadObject",
            )
        ]
    elif situacao == "conflito_hash":
        chave = montar_chave(caminho.name)
        cliente.objetos[("raw", chave)] = Put(
            "raw",
            chave,
            b"outro lote",
            {"sha256": "hash-diferente"},
        )

    codigo = executar(_configuracao(tmp_path), cliente, _INICIO)

    assert codigo == codigo_esperado
    assert _linhas_manifesto(cliente)[0]["status"] == situacao
