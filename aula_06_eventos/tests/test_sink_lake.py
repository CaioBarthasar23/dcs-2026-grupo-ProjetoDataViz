from datetime import datetime, timedelta, timezone

import pytest

from src.sink_lake.chave import montar_chave, numero_lote
from src.sink_lake.lote import decidir_fechamento
from src.sink_lake.gzip_lote import comprimir, montar_jsonl
from src.sink_lake.storage import S3Storage


def test_chave_evento():
    instante = datetime(2026, 11, 14, 11, 42, tzinfo=timezone.utc)
    chave = montar_chave(
        "eu-estocolmo",
        instante,
        "evento",
        partition=3,
        primeiro_offset=42,
    )
    assert chave.startswith("regiao=eu-estocolmo/data=2026-11-14/hora=11/")
    assert chave.endswith(".jsonl.gz")
    assert "lote-" in chave


def test_chave_chegada_usa_instante_separado():
    evento = datetime(2026, 11, 14, 23, 59, tzinfo=timezone.utc)
    chegada = datetime(2026, 11, 15, 0, 1, tzinfo=timezone.utc)
    chave = montar_chave(
        "eu-estocolmo",
        evento,
        "chegada",
        partition=1,
        primeiro_offset=7,
        chegada_em=chegada,
    )
    assert "/data=2026-11-15/hora=00/" in chave


def test_numero_lote_depende_particao_e_offset():
    um = numero_lote(0, 42)
    outro = numero_lote(1, 42)
    assert um != outro
    assert um == 42
    assert outro == 10_000_042


def test_mesma_particao_e_offset_regrava_mesma_chave():
    instante = datetime(2026, 11, 14, 11, tzinfo=timezone.utc)
    uma = montar_chave("eu-estocolmo", instante, "evento", 2, 42)
    duas = montar_chave("eu-estocolmo", instante, "evento", 2, 42)
    assert uma == duas


def test_fechamento_por_tempo():
    assert decidir_fechamento(10, 10, 10, 5242880)


def test_fechamento_por_tamanho():
    assert decidir_fechamento(1, 5242880, 10, 5242880)


def test_lote_nao_fecha_antes_dos_limites():
    assert not decidir_fechamento(9.9, 5242879, 10, 5242880)


def test_gzip_mede_tamanho():
    jsonl = montar_jsonl([
        {"event_id": "a", "tipo": "checkin"},
        {"event_id": "b", "tipo": "checkin"},
    ])
    gz = comprimir(jsonl)
    assert len(jsonl) > len(gz)
    assert gz[:2] == b"\x1f\x8b"
