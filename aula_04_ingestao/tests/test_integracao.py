import os
import socket
import subprocess
import sys
import time
import uuid
from io import BytesIO
from urllib.parse import urlparse

import boto3
import clickhouse_connect
import pytest
import requests
from dotenv import load_dotenv
from pyarrow import parquet


pytestmark = pytest.mark.integracao


def _servico_disponivel(host: str, porta: int) -> bool:
    try:
        with socket.create_connection((host, porta), timeout=1):
            return True
    except OSError:
        return False


def _porta_local_livre() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_vinte_envelopes_aparecem_no_clickhouse_e_no_lake() -> None:
    load_dotenv()
    endpoint = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    s3_url = urlparse(endpoint)
    s3_host = s3_url.hostname or "localhost"
    s3_port = s3_url.port or (443 if s3_url.scheme == "https" else 80)
    ch_host = os.getenv("CLICKHOUSE_HOST", "localhost")
    ch_port = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
    rabbit_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbit_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    if not all(
        (
            _servico_disponivel(s3_host, s3_port),
            _servico_disponivel(rabbit_host, rabbit_port),
            _servico_disponivel(ch_host, ch_port),
        )
    ):
        pytest.skip("RustFS, RabbitMQ e ClickHouse do compose precisam estar disponíveis")

    identificador = str(uuid.uuid4())
    env = os.environ.copy()
    env.update(
        {
            "API_PORT": str(_porta_local_livre()),
            "FILA_INGESTAO": f"ingestao_teste_{identificador.replace('-', '')}",
            "BUCKET_TESTE": "teste",
            "BUCKET_RAW": "teste",
            "BUCKET_BRONZE": "teste",
        }
    )
    base_url = f"http://127.0.0.1:{env['API_PORT']}"
    limite = float(os.getenv("TESTE_TIMEOUT_INTEGRACAO_SEGUNDOS", "30"))
    processo = subprocess.Popen(
        [sys.executable, "-m", "src.servidor"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        prazo_inicio = time.monotonic() + limite
        while time.monotonic() < prazo_inicio:
            if processo.poll() is not None:
                pytest.fail("src.servidor encerrou antes de disponibilizar a API")
            try:
                if requests.get(f"{base_url}/health", timeout=1).status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.2)
        else:
            pytest.fail("API não ficou disponível dentro do limite da integração")

        for indice in range(20):
            resposta = requests.post(
                f"{base_url}/ingest",
                json={
                    "data_tag": "telemetria",
                    "data": {"integracao_id": identificador, "indice": indice},
                },
                timeout=limite,
            )
            assert resposta.status_code == 202

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=os.getenv("S3_REGION", "us-east-1"),
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        )
        ch = clickhouse_connect.get_client(
            host=ch_host,
            port=ch_port,
            username=os.getenv("CLICKHOUSE_USER", "ingestao"),
            password=os.environ["CLICKHOUSE_PASSWORD"],
            database=os.getenv("CLICKHOUSE_DATABASE", "ingestao"),
        )

        prazo = time.monotonic() + limite
        linhas_ch = linhas_raw = linhas_bronze = 0
        while time.monotonic() < prazo:
            linhas_ch = ch.query(
                "SELECT count() FROM db_ingestion "
                "WHERE data_json.integracao_id::String = {id:String}",
                parameters={"id": identificador},
            ).result_rows[0][0]

            prefixo_raw = "raw/ingestao/data_tag=telemetria/"
            prefixo_bronze = "bronze/ingestao/data_tag=telemetria/"
            objetos_raw = s3.list_objects_v2(Bucket="teste", Prefix=prefixo_raw).get(
                "Contents", []
            )
            objetos_bronze = s3.list_objects_v2(
                Bucket="teste", Prefix=prefixo_bronze
            ).get("Contents", [])
            linhas_raw = 0
            for objeto in objetos_raw:
                corpo = s3.get_object(Bucket="teste", Key=objeto["Key"])["Body"].read()
                linhas_raw += sum(
                    identificador.encode() in linha for linha in corpo.splitlines()
                )
            linhas_bronze = 0
            for objeto in objetos_bronze:
                corpo = s3.get_object(Bucket="teste", Key=objeto["Key"])["Body"].read()
                tabela = parquet.read_table(BytesIO(corpo))
                coluna = tabela.column("data_json").to_pylist()
                linhas_bronze += sum(identificador in valor for valor in coluna)
            if linhas_ch == linhas_raw == linhas_bronze == 20:
                break
            time.sleep(0.2)

        assert linhas_ch == 20
        assert linhas_raw == 20
        assert linhas_bronze == 20
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=5)
        except subprocess.TimeoutExpired:
            processo.kill()
            processo.wait()
