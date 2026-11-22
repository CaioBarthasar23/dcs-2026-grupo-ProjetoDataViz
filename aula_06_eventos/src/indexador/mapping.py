MAPPING_TEMPLATE = {
    "index_patterns": ["tatame-eventos-*"],
    "template": {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 0,
        },
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "event_id": {"type": "keyword"},
                "tipo": {"type": "keyword"},
                "ocorrido_em": {"type": "date"},
                "regiao": {"type": "keyword"},
                "academia": {"type": "keyword"},
                "aluno": {"type": "keyword"},
                "turma": {"type": "keyword"},
                "faixa": {"type": "keyword"},
                "origem": {"type": "keyword"},
                "motivo": {
                    "type": "text",
                    "analyzer": "portuguese",
                },
                "dispositivo_id": {"type": "keyword"},
            },
        },
    },
}
