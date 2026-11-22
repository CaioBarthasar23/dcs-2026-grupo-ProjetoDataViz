import pytest

from src.gerador.validacao import validar_evento, exigir_evento_valido


def evento_valido():
    return {
        "event_id": "7f3b1c9e-52a4-4d0e-9c1b-6a2f8e4d7b10",
        "tipo": "checkin",
        "ocorrido_em": "2026-11-14T11:02:07.412Z",
        "regiao": "eu-estocolmo",
        "academia": "SE-STO-014",
        "aluno": "a8f3c1d9e2b47f60",
        "turma": "adulto-fundamentos",
        "faixa": "branca",
        "origem": "catraca",
    }


def test_evento_valido():
    assert validar_evento(evento_valido()) == []


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("nome", "Pessoa"),
        ("documento", "123"),
        ("email", "pessoa@example.com"),
        ("telefone", "123"),
    ],
)
def test_campos_proibidos_sao_rejeitados(campo, valor):
    evento = evento_valido()
    evento[campo] = valor
    with pytest.raises(ValueError, match="proibido"):
        exigir_evento_valido(evento)


def test_cancelamento_exige_motivo():
    evento = evento_valido()
    evento["tipo"] = "cancelamento"
    evento["motivo"] = None
    erros = validar_evento(evento)
    assert any("motivo" in erro for erro in erros)
