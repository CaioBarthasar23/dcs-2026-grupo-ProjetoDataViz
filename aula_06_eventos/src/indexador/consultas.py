from __future__ import annotations

import json
import os
import base64
import urllib.request


def headers() -> dict[str, str]:
    usuario = os.environ.get("ELASTIC_USER", "elastic")
    senha = os.environ.get("ELASTIC_PASSWORD")
    if not senha:
        raise RuntimeError("ELASTIC_PASSWORD ausente")
    credencial = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
    return {
        "Authorization": f"Basic {credencial}",
        "Content-Type": "application/json",
    }


def buscar(termo: str = "preco") -> list[dict]:
    url = os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200")
    corpo = {
        "query": {
            "bool": {
                "filter": [{"term": {"tipo": "cancelamento"}}],
                "must": [{"match": {"motivo": termo}}],
            }
        },
        "_source": ["event_id", "academia", "motivo", "tipo"],
        "sort": ["_score"],
    }
    requisicao = urllib.request.Request(
        url + "/tatame-eventos-*/_search",
        data=json.dumps(corpo).encode(),
        headers=headers(),
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        dados = json.loads(resposta.read().decode())
    return [
        {
            "_score": item["_score"],
            "event_id": item["_source"]["event_id"],
            "academia": item["_source"]["academia"],
            "motivo": item["_source"]["motivo"],
        }
        for item in dados["hits"]["hits"]
    ]


def alunos_unicos_estatisticas() -> dict[str, object]:
    url = os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200")
    corpo = {
        "size": 0,
        "aggs": {
            "alunos_estimativa": {
                "cardinality": {
                    "field": "aluno",
                    "precision_threshold": 40000,
                }
            }
        },
    }
    requisicao = urllib.request.Request(
        url + "/tatame-eventos-*/_search",
        data=json.dumps(corpo).encode(),
        headers=headers(),
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        dados = json.loads(resposta.read().decode())

    estimativa = dados["aggregations"]["alunos_estimativa"]["value"]
    corpo_exato = {
        "size": 0,
        "aggs": {
            "alunos": {
                "terms": {
                    "field": "aluno",
                    "size": 100000,
                }
            }
        },
    }
    requisicao = urllib.request.Request(
        url + "/tatame-eventos-*/_search",
        data=json.dumps(corpo_exato).encode(),
        headers=headers(),
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        dados_exatos = json.loads(resposta.read().decode())
    exato = len(dados_exatos["aggregations"]["alunos"]["buckets"])
    diferenca = (
        0.0
        if exato == 0
        else 100.0 * abs(exato - estimativa) / exato
    )
    return {
        "exato": exato,
        "estimativa": int(estimativa),
        "diferenca_percentual": round(diferenca, 2),
    }


def por_mes() -> list[dict]:
    url = os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200")
    corpo = {
        "size": 0,
        "aggs": {
            "meses": {
                "date_histogram": {
                    "field": "ocorrido_em",
                    "calendar_interval": "month",
                    "format": "yyyy.MM",
                },
                "aggs": {
                    "por_tipo": {"terms": {"field": "tipo", "size": 20}}
                },
            }
        },
    }
    requisicao = urllib.request.Request(
        url + "/tatame-eventos-*/_search",
        data=json.dumps(corpo).encode(),
        headers=headers(),
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        dados = json.loads(resposta.read().decode())
    return [
        {
            "mes": bucket["key_as_string"],
            "documentos": bucket["doc_count"],
            "tipos": {
                tipo["key"]: tipo["doc_count"]
                for tipo in bucket["por_tipo"]["buckets"]
            },
        }
        for bucket in dados["aggregations"]["meses"]["buckets"]
    ]
