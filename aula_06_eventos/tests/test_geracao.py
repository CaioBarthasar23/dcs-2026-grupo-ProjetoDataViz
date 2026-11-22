from src.gerador.geracao import (
    criar_academias,
    gerar_eventos,
)


def test_total_de_academias_e_distribuicao_por_regiao():
    academias = criar_academias()
    assert len(academias) == 240
    contagem = {}
    for item in academias:
        contagem[item["regiao"]] = contagem.get(item["regiao"], 0) + 1
    assert contagem == {
        "sa-saopaulo": 96,
        "us-virginia": 72,
        "eu-estocolmo": 48,
        "ap-sydney": 24,
    }


def test_duas_execucoes_repetem_tipos_e_academias():
    primeira = gerar_eventos(1000, 42, "chave-teste")
    segunda = gerar_eventos(1000, 42, "chave-teste")
    assert [evento["tipo"] for evento in primeira] == [
        evento["tipo"] for evento in segunda
    ]
    assert [evento["academia"] for evento in primeira] == [
        evento["academia"] for evento in segunda
    ]


def test_eventos_validos_sem_campos_cadastrais():
    eventos = gerar_eventos(1000, 42, "chave-teste")
    proibidos = {"nome", "documento", "email", "e-mail", "telefone"}
    assert all(not (proibidos & set(evento)) for evento in eventos)
