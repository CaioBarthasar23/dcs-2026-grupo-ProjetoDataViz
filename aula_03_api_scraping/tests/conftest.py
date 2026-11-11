import os
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def inicio_html():
    return (FIXTURES / "inicio.html").read_bytes()


@pytest.fixture
def inicio_uma_categoria_html():
    return (FIXTURES / "inicio_uma_categoria.html").read_bytes()


@pytest.fixture
def inicio_duas_categorias_html():
    return (FIXTURES / "inicio_duas_categorias.html").read_bytes()


@pytest.fixture
def categoria_html():
    return (FIXTURES / "categoria_mystery_p1.html").read_bytes()


@pytest.fixture
def categoria_p2_html():
    return (FIXTURES / "categoria_mystery_p2.html").read_bytes()


@pytest.fixture
def detalhe_html():
    return (FIXTURES / "detalhe_sharp_objects.html").read_bytes()


@pytest.fixture
def ptax_fechamento():
    return (FIXTURES / "ptax_fechamento.json").read_bytes()


@pytest.fixture
def ptax_vazia():
    return b'{"value":[]}'


@pytest.fixture
def ptax_sem_fechamento_elegivel():
    return (
        b'{"value":[{"tipoBoletim":"Fechamento",'
        b'"dataHoraCotacao":"2026-11-03 13:00:00.000000",'
        b'"cotacaoCompra":7.2,"cotacaoVenda":7.3}]}'
    )


@pytest.fixture
def fake_get():
    responses = []
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        if not responses:
            raise AssertionError("A chamada HTTP simulada não tem resposta configurada")
        response = responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    get.responses = responses
    get.calls = calls
    get.queue_response = lambda status, content=b"", headers=None: responses.append(
        SimpleNamespace(status_code=status, content=content, headers=headers or {})
    )
    return get


@pytest.fixture
def minio_client():
    mode = os.environ.get("TEST_MINIO")
    if mode not in {"1", "railway"}:
        pytest.skip("Integração MinIO habilitada com TEST_MINIO=1 ou TEST_MINIO=railway")

    if mode == "1":
        from src.config import load_config

        config = load_config()
        endpoint = config.endpoint_minio
        access_key = config.access_key
        secret_key = config.secret_key
        region = "us-east-1"
    else:
        endpoint = os.environ.get("S3_ENDPOINT_URL", "")
        access_key = os.environ.get("S3_ACCESS_KEY", "")
        secret_key = os.environ.get("S3_SECRET_KEY", "")
        region = os.environ.get("S3_REGION", "us-east-1")

    parsed_endpoint = urlsplit(endpoint)
    if not parsed_endpoint.hostname:
        pytest.fail("S3_ENDPOINT_URL não configurado para a integração MinIO")
    if mode == "1" and parsed_endpoint.hostname not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("A integração MinIO exige endpoint local")
    if mode == "railway" and parsed_endpoint.hostname in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("A integração Railway exige o endpoint MinIO remoto")
    if not access_key or not secret_key:
        pytest.fail("Credenciais MinIO de teste não configuradas")

    import boto3
    from botocore.exceptions import ClientError

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    try:
        client.head_bucket(Bucket="teste")
    except ClientError:
        pytest.fail("Bucket MinIO de teste 'teste' indisponível")
    return client
