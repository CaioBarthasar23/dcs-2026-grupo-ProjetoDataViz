from datetime import datetime, timedelta, timezone

import pytest

from src.cep.academia_silenciosa import avaliar as avaliar_silencio
from src.cep.academia_silenciosa import vencidos as vencer_silencio
from src.cep.cobranca_reincidente import avaliar as avaliar_cobranca
from src.cep.experimental_sem_matricula import avaliar as avaliar_experimental
from src.cep.experimental_sem_matricula import vencidos as vencer_experimental
from src.cep.pico_cancelamentos import avaliar as avaliar_cancelamento
from src.cep.config import ConfiguracaoCEP
from src.cep.estado import EstadoPersistente
from src.cep.motor import MotorCEP


AGORA = datetime(2026, 11, 14, 11, 5, tzinfo=timezone.utc)


def evento(tipo, event_id, ocorrido, **extra):
    base = {
        "event_id": event_id,
        "tipo": tipo,
        "ocorrido_em": ocorrido,
        "regiao": "eu-estocolmo",
        "academia": "SE-STO-014",
        "origem": "app",
    }
    base.update(extra)
    return base


def test_cobranca_dispara_na_segunda():
    um = evento("cobranca_falhou", "1", "2026-11-14T10:00:00.000Z", aluno="aluno1")
    estado, encontrados = avaliar_cobranca(None, um, AGORA)
    assert encontrados == []
    dois = evento("cobranca_falhou", "2", "2026-11-14T10:30:00.000Z", aluno="aluno1")
    _, encontrados = avaliar_cobranca(estado, dois, AGORA)
    assert len(encontrados) == 1
    assert encontrados[0]["eventos_origem"] == ["1", "2"]


def test_cobranca_borda_exata_dias():
    um = evento("cobranca_falhou", "1", "2026-11-07T11:05:00.000Z", aluno="aluno1")
    estado, _ = avaliar_cobranca(None, um, AGORA)
    dois = evento("cobranca_falhou", "2", "2026-11-14T11:05:00.000Z", aluno="aluno1")
    _, encontrados = avaliar_cobranca(estado, dois, AGORA)
    assert len(encontrados) == 1


def test_cobranca_duplicada_nao_conta():
    um = evento("cobranca_falhou", "1", "2026-11-14T10:00:00.000Z", aluno="aluno1")
    estado, _ = avaliar_cobranca(None, um, AGORA)
    estado, encontrados = avaliar_cobranca(estado, um, AGORA)
    assert encontrados == []
    assert estado["ids"] == ["1"]


def test_cobranca_expira_estado():
    um = evento("cobranca_falhou", "1", "2026-11-01T10:00:00.000Z", aluno="aluno1")
    estado, _ = avaliar_cobranca(None, um, AGORA)
    dois = evento("cobranca_falhou", "2", "2026-11-14T10:30:00.000Z", aluno="aluno1")
    novo, encontrados = avaliar_cobranca(estado, dois, AGORA)
    assert encontrados == []
    assert novo["ids"] == ["2"]


def test_academia_silenciosa_dispara_no_timer():
    heartbeat = evento("heartbeat", "h1", "2026-11-14T10:00:00.000Z")
    estado, _ = avaliar_silencio(None, heartbeat, AGORA)
    modelo = dict(estado)
    encontrados = vencer_silencio(
        modelo,
        "SE-STO-014",
        evento("heartbeat", "h1", "2026-11-14T10:00:00.000Z"),
        AGORA,
    )
    assert len(encontrados) == 1


def test_academia_silenciosa_nao_dispara_antes_do_prazo():
    heartbeat = evento("heartbeat", "h1", "2026-11-14T11:02:00.000Z")
    estado, _ = avaliar_silencio(None, heartbeat, AGORA)
    encontrados = vencer_silencio(
        estado,
        "SE-STO-014",
        heartbeat,
        AGORA,
    )
    assert encontrados == []


def test_cancelamentos_borda_e_nao_disparo():
    estado = None
    encontrados = []
    for i, hora in enumerate(("10:00", "11:00")):
        estado, novos = avaliar_cancelamento(
            estado,
            evento("cancelamento", str(i), f"2026-11-13T{hora}:00.000Z"),
            AGORA,
        )
        encontrados.extend(novos)
    assert encontrados == []


def test_cancelamentos_disparam_em_24_horas():
    estado = None
    encontrados = []
    for i, hora in enumerate(("11:05", "11:05", "11:05")):
        estado, novos = avaliar_cancelamento(
            estado,
            evento("cancelamento", str(i), f"2026-11-13T{hora}:00.000Z"),
            AGORA,
        )
        encontrados.extend(novos)
    assert len(encontrados) == 1


def test_experimental_dispara_sem_matricula():
    experimental = evento(
        "aula_experimental",
        "e1",
        "2026-11-07T11:00:00.000Z",
        aluno="aluno1",
    )
    estado, _ = avaliar_experimental(None, experimental, AGORA)
    encontrados = vencer_experimental(
        estado,
        "aluno1",
        experimental,
        AGORA,
    )
    assert len(encontrados) == 1


def test_experimental_com_matricula_nao_dispara():
    estado = None
    matricula = evento(
        "matricula",
        "m1",
        "2026-11-10T11:00:00.000Z",
        aluno="aluno1",
    )
    estado, _ = avaliar_experimental(estado, matricula, AGORA)
    experimental = evento(
        "aula_experimental",
        "e1",
        "2026-11-14T11:00:00.000Z",
        aluno="aluno1",
    )
    estado, _ = avaliar_experimental(estado, experimental, AGORA)
    encontrados = vencer_experimental(
        estado,
        "aluno1",
        experimental,
        AGORA,
    )
    assert encontrados == []


def test_evento_atrasado_marca_complexo(tmp_path):
    estado = EstadoPersistente(tmp_path / "cep.json")
    motor = MotorCEP(estado, ConfiguracaoCEP())
    novo = evento("cobranca_falhou", "1", "2026-11-14T12:00:00.000Z", aluno="aluno1")
    motor.processar(novo)
    atrasado = evento("cobranca_falhou", "2", "2026-11-14T11:57:00.000Z", aluno="aluno1")
    complexos = motor.processar(atrasado)
    assert complexos[0]["atrasado"] is True


def test_estado_expira_e_persistencia(tmp_path):
    estado = EstadoPersistente(tmp_path / "cep.json")
    estado.salvar_chave("teste", "a", {"ids": ["1"]})
    recarregado = EstadoPersistente(tmp_path / "cep.json")
    assert recarregado.obter("teste", "a")["ids"] == ["1"]


def test_contagem_chaves_de_um_dia(tmp_path):
    estado = EstadoPersistente(tmp_path / "cep.json")
    motor = MotorCEP(estado, ConfiguracaoCEP())
    for i in range(24):
        item = evento(
            "heartbeat",
            str(i),
            f"2026-11-14T{(i // 3):02d}:00:00.000Z",
        )
        item["academia"] = f"SE-STO-{i % 3:03d}"
        motor.processar(item)
    assert estado.contar_chaves() == 3
