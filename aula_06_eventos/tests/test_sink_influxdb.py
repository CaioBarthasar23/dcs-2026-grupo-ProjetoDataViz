from datetime import timedelta

import pytest

from src.sink_influxdb.agregacao import (
    AgregadorMinuto,
    inicio_minuto,
    tags_do_evento,
)


def evento(event_id="id-1", tipo="checkin", academia="SE-STO-014", regiao="eu-estocolmo"):
    return {
        "event_id": event_id,
        "tipo": tipo,
        "ocorrido_em": "2026-11-14T11:02:07.412Z",
        "regiao": regiao,
        "academia": academia,
    }


def test_conjunto_exacto_de_tags():
    tags = tags_do_evento(evento())
    assert set(tags) == {"regiao", "academia", "tipo"}
    assert "aluno" not in tags


def test_agrega_no_minuto_pelo_tempo_do_evento(tmp_path):
    agregador = AgregadorMinuto(tmp_path / "influx.json")
    agregador.adicionar(evento("id-1"))
    agregador.adicionar(evento("id-2"))
    linhas = agregador.pontos_line_protocol()
    assert len(linhas) == 1
    assert "contagem=2i" in linhas[0]
    assert " 1794654120000000000" in linhas[0]


def test_duplicata_nao_incrementa(tmp_path):
    agregador = AgregadorMinuto(tmp_path / "influx.json")
    primeiro = agregador.adicionar(evento("id-1"))
    segundo = agregador.adicionar(evento("id-1"))
    assert len(primeiro) == 1
    assert segundo == []
    assert "contagem=1i" in agregador.pontos_line_protocol()[0]


def test_reprocessar_pos_reinicio_nao_altera_total(tmp_path):
    caminho = tmp_path / "influx.json"
    primeiro = AgregadorMinuto(caminho)
    primeiro.adicionar(evento("id-1"))
    primeiro.persistir()

    reiniciado = AgregadorMinuto(caminho)
    reiniciado.adicionar(evento("id-1"))
    assert "contagem=1i" in reiniciado.pontos_line_protocol()[0]


def test_evento_atrasado_atualiza_mesmo_minuto(tmp_path):
    agregador = AgregadorMinuto(tmp_path / "influx.json")
    um = evento("id-1")
    dois = evento("id-2")
    dois["ocorrido_em"] = "2026-11-14T11:02:59.900Z"
    agregador.adicionar(um)
    agregador.adicionar(dois)
    linha = agregador.pontos_line_protocol()[0]
    assert "contagem=2i" in linha
    assert inicio_minuto(um["ocorrido_em"]).minute == 2
