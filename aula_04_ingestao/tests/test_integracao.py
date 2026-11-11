import json
import os
import socket
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from io import BytesIO
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo

import boto3
import clickhouse_connect
import pika
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


def _servicos_disponiveis_para_recuperacao() -> tuple[str, str, int] | None:
    load_dotenv()
    endpoint = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    url_s3 = urlparse(endpoint)
    s3_host = url_s3.hostname or "localhost"
    s3_port = url_s3.port or (443 if url_s3.scheme == "https" else 80)
    rabbit_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbit_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbit_ui_port = int(os.getenv("RABBITMQ_UI_PORT", "15672"))
    clickhouse_host = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
    if not all(
        (
            _servico_disponivel(s3_host, s3_port),
            _servico_disponivel(rabbit_host, rabbit_port),
            _servico_disponivel(rabbit_host, rabbit_ui_port),
            _servico_disponivel(clickhouse_host, clickhouse_port),
        )
    ):
        return None
    return endpoint, rabbit_host, rabbit_port


def _ambiente_isolado(fila: str, flush_n: int, flush_segundos: int) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "API_PORT": str(_porta_local_livre()),
            "FILA_INGESTAO": fila,
            "BUCKET_TESTE": "teste",
            "BUCKET_RAW": "teste",
            "BUCKET_BRONZE": "teste",
            "FLUSH_N": str(flush_n),
            "FLUSH_SEGUNDOS": str(flush_segundos),
        }
    )
    return env


def _iniciar_servidor(env: dict[str, str]) -> subprocess.Popen:
    processo = subprocess.Popen(
        [sys.executable, "-m", "src.servidor"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{env['API_PORT']}"
    limite = float(os.getenv("TESTE_TIMEOUT_INTEGRACAO_SEGUNDOS", "60"))
    prazo = time.monotonic() + limite
    while time.monotonic() < prazo:
        if processo.poll() is not None:
            pytest.fail("src.servidor encerrou antes de disponibilizar a API")
        try:
            if requests.get(f"{base_url}/health", timeout=1).status_code == 200:
                return processo
        except requests.RequestException:
            time.sleep(0.2)
    processo.kill()
    processo.wait()
    pytest.fail("API não ficou disponível dentro do limite da integração")


def _estado_fila(env: dict[str, str], fila: str) -> dict:
    host = env.get("RABBITMQ_HOST", "localhost")
    porta = env.get("RABBITMQ_UI_PORT", "15672")
    auth = (env.get("RABBITMQ_USER", "ingestao"), env["RABBITMQ_PASSWORD"])
    resposta = requests.get(
        f"http://{host}:{porta}/api/queues/%2F/{quote(fila, safe='')}",
        auth=auth,
        timeout=2,
    )
    resposta.raise_for_status()
    return resposta.json()


def _cliente_clickhouse(env: dict[str, str]):
    return clickhouse_connect.get_client(
        host=env.get("CLICKHOUSE_HOST", "localhost"),
        port=int(env.get("CLICKHOUSE_HTTP_PORT", "8123")),
        username=env.get("CLICKHOUSE_USER", "ingestao"),
        password=env["CLICKHOUSE_PASSWORD"],
        database=env.get("CLICKHOUSE_DATABASE", "ingestao"),
    )


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


def test_morte_com_kill_9_recupera_10000_mensagens_sem_perda() -> None:
    servicos = _servicos_disponiveis_para_recuperacao()
    if servicos is None:
        pytest.skip("RustFS, RabbitMQ, management API e ClickHouse precisam estar disponíveis")
    _, rabbit_host, rabbit_port = servicos
    identificador = str(uuid.uuid4())
    fila = f"ingestao_recuperacao_{identificador.replace('-', '')}"
    quantidade = 10_000
    env = _ambiente_isolado(fila, quantidade + 1, 600)
    processo = None
    ch = None
    try:
        processo = _iniciar_servidor(env)
        credenciais = pika.PlainCredentials(
            env.get("RABBITMQ_USER", "ingestao"), env["RABBITMQ_PASSWORD"]
        )
        conexao = pika.BlockingConnection(
            pika.ConnectionParameters(rabbit_host, rabbit_port, credentials=credenciais)
        )
        canal = conexao.channel()
        canal.queue_declare(queue=fila, durable=True)
        canal.confirm_delivery()
        for indice in range(quantidade):
            envelope = {
                "data_tag": "telemetria",
                "data": {"integracao_id": identificador, "indice": indice},
            }
            canal.basic_publish(
                exchange="",
                routing_key=fila,
                body=json.dumps(envelope).encode(),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent,
                    content_type="application/json",
                ),
            )
        conexao.close()

        limite = float(os.getenv("TESTE_TIMEOUT_INTEGRACAO_SEGUNDOS", "180"))
        prazo = time.monotonic() + limite
        while time.monotonic() < prazo:
            if _estado_fila(env, fila).get("messages_unacknowledged") == quantidade:
                break
            time.sleep(0.1)
        else:
            pytest.fail("o consumidor não recebeu as 10.000 mensagens antes da interrupção")

        processo.kill()  # SIGKILL: encerra sem shutdown gracioso nem ack
        processo.wait(timeout=10)
        processo = _iniciar_servidor(_ambiente_isolado(fila, 500, 1))

        prazo = time.monotonic() + limite
        while time.monotonic() < prazo:
            estado = _estado_fila(env, fila)
            if estado.get("messages_ready") == 0 and estado.get("messages_unacknowledged") == 0:
                break
            time.sleep(0.2)
        else:
            pytest.fail("a fila não foi drenada após reiniciar o consumidor")

        ch = _cliente_clickhouse(env)
        total, distintas = ch.query(
            "SELECT count(), uniqExact(data_json.indice::UInt64) "
            "FROM db_ingestion WHERE data_json.integracao_id::String = {id:String}",
            parameters={"id": identificador},
        ).result_rows[0]
        duplicatas = total - distintas
        print(f"T-13 recuperação: distintas={distintas}, duplicatas={duplicatas}")
        assert distintas == quantidade
        assert duplicatas >= 0
    finally:
        if processo is not None and processo.poll() is None:
            processo.kill()
            processo.wait(timeout=10)
        if ch is not None:
            ch.close()


def test_reprocessar_bronze_reinsere_linhas_no_clickhouse() -> None:
    servicos = _servicos_disponiveis_para_recuperacao()
    if servicos is None:
        pytest.skip("RustFS, RabbitMQ, management API e ClickHouse precisam estar disponíveis")
    endpoint, _, _ = servicos
    identificador = str(uuid.uuid4())
    fila = f"ingestao_replay_{identificador.replace('-', '')}"
    env = _ambiente_isolado(fila, 20, 1)
    processo = None
    ch = None
    try:
        processo = _iniciar_servidor(env)
        base_url = f"http://127.0.0.1:{env['API_PORT']}"
        for indice in range(20):
            resposta = requests.post(
                f"{base_url}/ingest",
                json={
                    "data_tag": "telemetria",
                    "data": {"integracao_id": identificador, "indice": indice},
                },
                timeout=30,
            )
            assert resposta.status_code == 202

        ch = _cliente_clickhouse(env)
        limite = float(os.getenv("TESTE_TIMEOUT_INTEGRACAO_SEGUNDOS", "60"))
        prazo = time.monotonic() + limite
        inicial = 0
        while time.monotonic() < prazo:
            inicial = ch.query(
                "SELECT count() FROM db_ingestion "
                "WHERE data_json.integracao_id::String = {id:String}",
                parameters={"id": identificador},
            ).result_rows[0][0]
            if inicial == 20:
                break
            time.sleep(0.2)
        assert inicial == 20

        menor_timestamp = ch.query(
            "SELECT min(timestamp) FROM db_ingestion "
            "WHERE data_json.integracao_id::String = {id:String}",
            parameters={"id": identificador},
        ).result_rows[0][0]
        dia = datetime.fromtimestamp(menor_timestamp / 1000, tz=UTC).astimezone(
            ZoneInfo("America/Sao_Paulo")
        ).date().isoformat()
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=env.get("S3_REGION", "us-east-1"),
            aws_access_key_id=env["S3_ACCESS_KEY"],
            aws_secret_access_key=env["S3_SECRET_KEY"],
        )
        prefixo = f"bronze/ingestao/data_tag=telemetria/data={dia}/"
        paginas = s3.get_paginator("list_objects_v2").paginate(
            Bucket="teste", Prefix=prefixo
        )
        objetos = [objeto for pagina in paginas for objeto in pagina.get("Contents", [])]
        bronze_linhas = 0
        for objeto in objetos:
            corpo = s3.get_object(Bucket="teste", Key=objeto["Key"])["Body"].read()
            bronze_linhas += parquet.read_table(BytesIO(corpo)).num_rows
        assert bronze_linhas >= 20

        antes = ch.query(
            "SELECT count() FROM db_ingestion WHERE data_tag = 'telemetria'"
        ).result_rows[0][0]
        resultado = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.clickhouse",
                "reprocessar",
                "--data-tag",
                "telemetria",
                "--data",
                dia,
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=limite,
            check=False,
        )
        assert resultado.returncode == 0, resultado.stderr
        assert f"linhas_reprocessadas={bronze_linhas}" in resultado.stdout
        depois, teste_total, teste_distintas = ch.query(
            "SELECT count(), "
            "countIf(data_json.integracao_id::String = {id:String}), "
            "uniqExactIf(data_json.indice::UInt64, data_json.integracao_id::String = {id:String}) "
            "FROM db_ingestion WHERE data_tag = 'telemetria'",
            parameters={"id": identificador},
        ).result_rows[0]
        assert depois - antes == bronze_linhas
        duplicatas = teste_total - teste_distintas
        print(
            "T-13 replay: "
            f"bronze_linhas={bronze_linhas}, novas_linhas={depois - antes}, "
            f"duplicatas_da_amostra={duplicatas}"
        )
        assert teste_total == 40
        assert teste_distintas == 20
    finally:
        if processo is not None and processo.poll() is None:
            processo.terminate()
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait()
        if ch is not None:
            ch.close()
