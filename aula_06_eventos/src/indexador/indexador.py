from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
import urllib.request
import base64

import boto3
from botocore.config import Config


def autenticacao() -> dict[str, str]:
    usuario = os.environ.get("ELASTIC_USER", "elastic")
    senha = os.environ.get("ELASTIC_PASSWORD")
    if not senha:
        raise RuntimeError("ELASTIC_PASSWORD ausente")
    credencial = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
    return {"Authorization": f"Basic {credencial}"}


def requisicao(metodo: str, caminho: str, payload: dict | None = None):
    url = os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200").rstrip("/")
    dados = None
    headers = autenticacao()
    headers["Content-Type"] = "application/json"
    if payload is not None:
        dados = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        urljoin(url + "/", caminho.lstrip("/")),
        data=dados,
        headers=headers,
        method=metodo,
    )
    with urllib.request.urlopen(req, timeout=30) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def criar_template() -> dict:
    from .mapping import MAPPING_TEMPLATE
    return requisicao(
        "PUT",
        "_index_template/tatame-eventos-template",
        MAPPING_TEMPLATE,
    )


def s3_client():
    endpoint = os.environ.get("S3_ENDPOINT")
    access_key = os.environ.get("S3_ACCESS_KEY")
    secret_key = os.environ.get("S3_SECRET_KEY")
    if not all((endpoint, access_key, secret_key)):
        raise RuntimeError("credenciais S3 ausentes")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=Config(
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "path"},
            signature_version="s3v4",
        ),
    )


def indice_de(evento: dict) -> str:
    mes = evento["ocorrido_em"][:7].replace("-", ".")
    return f"tatame-eventos-{mes}"


def estado_processados(caminho: str | Path) -> set[str]:
    arquivo = Path(caminho)
    if not arquivo.exists():
        return set()
    return set(json.loads(arquivo.read_text(encoding="utf-8")).get("objetos", []))


def salvar_processados(caminho: str | Path, objetos: set[str]) -> None:
    arquivo = Path(caminho)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_suffix(".tmp")
    temporario.write_text(
        json.dumps({"objetos": sorted(objetos)}, ensure_ascii=False),
        encoding="utf-8",
    )
    temporario.replace(arquivo)


def eventos_do_bucket(
    bucket: str,
    prefixo: str = "regiao=",
) -> Iterable[dict]:
    s3 = s3_client()
    for pagina in s3.get_paginator("list_objects_v2").paginate(
        Bucket=bucket,
        Prefix=prefixo,
    ):
        for item in pagina.get("Contents", []):
            chave = item["Key"]
            if not chave.endswith(".jsonl.gz"):
                continue
            payload = s3.get_object(Bucket=bucket, Key=chave)["Body"].read()
            with gzip.GzipFile(fileobj=__import__("io").BytesIO(payload)) as gz:
                texto = gz.read().decode("utf-8")
            for linha in texto.splitlines():
                if linha:
                    yield chave, json.loads(linha)


def bulk_indexar(documentos: Iterable[tuple[str, dict]]) -> dict:
    partes = []
    for chave, evento in documentos:
        indice = indice_de(evento)
        partes.append(
            json.dumps({"index": {"_index": indice, "_id": evento["event_id"]}})
        )
        partes.append(json.dumps(evento, ensure_ascii=False))
    if not partes:
        return {"items": []}
    dados = ("\n".join(partes) + "\n").encode("utf-8")
    url = os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200").rstrip("/")
    headers = autenticacao()
    headers["Content-Type"] = "application/x-ndjson"
    req = urllib.request.Request(
        url + "/_bulk",
        data=dados,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resposta:
        resposta_json = json.loads(resposta.read().decode("utf-8"))
    rejeitados = [
        item
        for item in resposta_json.get("items", [])
        if item.get("index", {}).get("error")
    ]
    if rejeitados:
        print(json.dumps({"rejeitados": rejeitados}, ensure_ascii=False))
    return resposta_json


def principal() -> int:
    criar_template()
    bucket = os.environ.get("S3_BUCKET", "tatame-bruto")
    estado = os.environ.get(
        "INDEXADOR_ESTADO_PATH",
        "estado/indexador.json",
    )
    processados = estado_processados(estado)
    novos = []
    vistos_nesta_execucao = set(processados)
    for chave, evento in eventos_do_bucket(bucket):
        if chave in vistos_nesta_execucao:
            continue
        novos.append((chave, evento))
        vistos_nesta_execucao.add(chave)
    resposta = bulk_indexar(novos)
    if not resposta.get("errors"):
        salvar_processados(estado, vistos_nesta_execucao)
    else:
        for chave, evento in novos:
            vistos_nesta_execucao.discard(chave)
        salvar_processados(estado, vistos_nesta_execucao)
    print(f"objetos_indexados={len(novos)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
