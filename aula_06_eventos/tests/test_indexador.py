from pathlib import Path

import pytest

from src.indexador.mapping import MAPPING_TEMPLATE
from src.indexador.indexador import estado_processados, indice_de, salvar_processados
from src.indexador.contexto import montar_contexto


def test_mapping_resumo():
    mapping = MAPPING_TEMPLATE["template"]["mappings"]["properties"]
    assert MAPPING_TEMPLATE["template"]["settings"]["number_of_shards"] == 3
    assert mapping["event_id"] == {"type": "keyword"}
    assert mapping["motivo"]["type"] == "text"
    assert mapping["motivo"]["analyzer"] == "portuguese"
    assert mapping["ocorrido_em"] == {"type": "date"}


def test_objeto_processado_e_repetivel(tmp_path):
    arquivo = tmp_path / "indexador.json"
    salvar_processados(arquivo, {"a.jsonl.gz", "b.jsonl.gz"})
    assert estado_processados(arquivo) == {"a.jsonl.gz", "b.jsonl.gz"}
    salvar_processados(arquivo, {"a.jsonl.gz", "b.jsonl.gz"})
    assert estado_processados(arquivo) == {"a.jsonl.gz", "b.jsonl.gz"}


def test_indice_mensal():
    assert indice_de({"ocorrido_em": "2026-11-14T11:02:07.412Z"}) == "tatame-eventos-2026.11"


def test_contexto_rejeita_campo_fora_do_contrato(tmp_path):
    with pytest.raises(ValueError, match="fora do contrato"):
        montar_contexto(
            "Pergunta",
            [{"event_id": "1", "_score": 1.2, "academia": "A", "nome": "Joao"}],
            {},
            [],
            tmp_path / "contexto.md",
        )


def test_contexto_local_e_campos_permitidos(tmp_path):
    destino = tmp_path / "contexto.md"
    montar_contexto(
        "Cancelamentos com preço",
        [{"event_id": "1", "_score": 2.3, "academia": "SE-STO-014", "motivo": "preço alto"}],
        {
            "alunos": {
                "valor": 40,
                "tipo": "exato",
                "periodo": "2026-11",
            }
        },
        ['{"query":{"match":{"motivo":"preço"}}}'],
        destino,
    )
    texto = destino.read_text()
    assert "Pergunta:" in texto
    assert "event_id=1" in texto
    assert "exato" in texto
