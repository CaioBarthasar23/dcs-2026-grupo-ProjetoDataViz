import os

import pytest

from src.gerador.anonimizacao import (
    anonimizar_aluno,
    obter_chave_anonimizacao,
)


def test_mesmo_aluno_mesmo_codigo():
    assert anonimizar_aluno("aluno-1", "chave-teste") == anonimizar_aluno(
        "aluno-1",
        "chave-teste",
    )


def test_alunos_diferentes_codigos_diferentes():
    assert anonimizar_aluno("aluno-1", "chave-teste") != anonimizar_aluno(
        "aluno-2",
        "chave-teste",
    )


def test_codigo_tem_16_hexadecimais():
    codigo = anonimizar_aluno("aluno-1", "chave-teste")
    assert len(codigo) == 16
    assert set(codigo) <= set("0123456789abcdef")


def test_chave_ausente_interrompe_com_erro_claro(monkeypatch):
    monkeypatch.delenv("ANON_CHAVE", raising=False)
    with pytest.raises(RuntimeError, match="ANON_CHAVE"):
        obter_chave_anonimizacao()
