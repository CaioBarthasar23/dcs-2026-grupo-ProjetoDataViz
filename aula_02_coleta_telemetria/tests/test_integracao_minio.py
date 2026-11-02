import hashlib
import ipaddress
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import boto3
import pytest
from botocore.config import Config
from botocore.client import BaseClient


pytestmark = pytest.mark.integracao

_RAIZ = Path(__file__).resolve().parents[1]
_PREFIXO_LOTES = "telemetria/data=2026-10-17/hora=12/"
_NOME_ACEITACAO = "CAM-0451_20261017T0900.txt"
_TAMANHO_ACEITACAO = 983
_SHA256_ACEITACAO = "6789b712602d1985d24df7b48370a1190da3db4e2576a74b07b5520d28601b12"


def _ambiente_local(pouso: Path) -> dict[str, str]:
    nomes = (
        "S3_ENDPOINT_URL",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "BUCKET_RAW",
        "S3_REGION",
        "COLETOR_VERSAO",
    )
    ausentes = [nome for nome in nomes if not os.environ.get(nome)]
    if ausentes:
        pytest.skip(f"MinIO local não configurado: {', '.join(ausentes)}")

    ambiente = os.environ.copy()
    endpoint = urlsplit(ambiente["S3_ENDPOINT_URL"])
    host = endpoint.hostname
    if host is None:
        pytest.skip("S3_ENDPOINT_URL não é uma URL válida")
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = host.lower() == "localhost"
    if not local:
        pytest.skip("o teste de integração aceita somente endpoint MinIO local")
    if ambiente["BUCKET_RAW"] != "raw":
        pytest.skip("BUCKET_RAW deve apontar para o bucket raw")

    ambiente["POUSO_DIR"] = str(pouso)
    ambiente["AWS_EC2_METADATA_DISABLED"] = "true"
    return ambiente


def _gerar_lotes(pouso: Path, ambiente: dict[str, str]) -> None:
    subprocess.run(
        [
            sys.executable,
            "gerar_lotes.py",
            "--inicio",
            "2026-10-17T09:00",
            "--saida",
            str(pouso),
        ],
        cwd=_RAIZ,
        env=ambiente,
        check=True,
        capture_output=True,
        text=True,
    )
    assert len(list(pouso.glob("*.txt"))) == 80


def _executar_coletor(ambiente: dict[str, str]) -> None:
    subprocess.run(
        [sys.executable, "-m", "src.coletor"],
        cwd=_RAIZ,
        env=ambiente,
        check=True,
        capture_output=True,
        text=True,
    )


def _cliente_s3(ambiente: dict[str, str]) -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=ambiente["S3_ENDPOINT_URL"],
        aws_access_key_id=ambiente["S3_ACCESS_KEY"],
        aws_secret_access_key=ambiente["S3_SECRET_KEY"],
        region_name=ambiente["S3_REGION"],
        config=Config(s3={"addressing_style": "path"}),
    )


def _listar_chaves(cliente: BaseClient, bucket: str, prefixo: str) -> set[str]:
    paginador = cliente.get_paginator("list_objects_v2")
    return {
        objeto["Key"]
        for pagina in paginador.paginate(Bucket=bucket, Prefix=prefixo)
        for objeto in pagina.get("Contents", [])
    }


def _manifesto_mais_recente(
    cliente: BaseClient, bucket: str
) -> list[dict[str, Any]]:
    paginador = cliente.get_paginator("list_objects_v2")
    objetos = [
        objeto
        for pagina in paginador.paginate(
            Bucket=bucket, Prefix="_manifestos/telemetria/"
        )
        for objeto in pagina.get("Contents", [])
    ]
    assert objetos, "o coletor não gravou manifesto"
    manifesto = max(objetos, key=lambda objeto: objeto["LastModified"])
    corpo = cliente.get_object(Bucket=bucket, Key=manifesto["Key"])["Body"].read()
    return [json.loads(linha) for linha in corpo.decode("utf-8").splitlines()]


def test_integracao_80_lotes_hash_de_aceitacao_e_segunda_execucao(
    tmp_path: Path,
) -> None:
    pouso = tmp_path / "pouso"
    pouso.mkdir()
    ambiente = _ambiente_local(pouso)
    cliente = _cliente_s3(ambiente)
    bucket = ambiente["BUCKET_RAW"]

    _gerar_lotes(pouso, ambiente)
    _executar_coletor(ambiente)

    assert list(pouso.iterdir()) == []
    chaves_lotes = _listar_chaves(cliente, bucket, _PREFIXO_LOTES)
    assert len(chaves_lotes) == 80

    chave_aceitacao = (
        f"{_PREFIXO_LOTES}caminhao=CAM-0451/lote_1200.txt"
    )
    objeto = cliente.get_object(Bucket=bucket, Key=chave_aceitacao)
    conteudo = objeto["Body"].read()
    assert len(conteudo) == _TAMANHO_ACEITACAO
    assert hashlib.sha256(conteudo).hexdigest() == _SHA256_ACEITACAO

    metadados = cliente.head_object(Bucket=bucket, Key=chave_aceitacao)["Metadata"]
    assert set(metadados) == {
        "fonte",
        "recebido-em",
        "versao-coletor",
        "sha256",
        "caminhao",
        "janela-inicio",
        "arquivo-origem",
    }
    assert metadados["fonte"] == "provedor-satelite"
    assert metadados["versao-coletor"] == ambiente["COLETOR_VERSAO"]
    assert metadados["sha256"] == _SHA256_ACEITACAO
    assert metadados["caminhao"] == "CAM-0451"
    assert metadados["janela-inicio"] == "2026-10-17T12:00:00Z"
    assert metadados["arquivo-origem"] == _NOME_ACEITACAO
    recebido_em = datetime.fromisoformat(
        metadados["recebido-em"].replace("Z", "+00:00")
    )
    assert recebido_em.utcoffset() == timedelta(0)

    manifesto_primeira_execucao = _manifesto_mais_recente(cliente, bucket)
    assert len(manifesto_primeira_execucao) == 80
    assert all(
        item["status"] in {"gravado", "ja_existia"}
        for item in manifesto_primeira_execucao
    )
    linha_aceitacao = next(
        item
        for item in manifesto_primeira_execucao
        if item["arquivo"] == _NOME_ACEITACAO
    )
    assert linha_aceitacao["bytes"] == _TAMANHO_ACEITACAO
    assert linha_aceitacao["sha256"] == _SHA256_ACEITACAO

    _gerar_lotes(pouso, ambiente)
    _executar_coletor(ambiente)

    assert list(pouso.iterdir()) == []
    assert _listar_chaves(cliente, bucket, _PREFIXO_LOTES) == chaves_lotes
    manifesto_segunda_execucao = _manifesto_mais_recente(cliente, bucket)
    assert len(manifesto_segunda_execucao) == 80
    assert all(item["status"] == "ja_existia" for item in manifesto_segunda_execucao)
