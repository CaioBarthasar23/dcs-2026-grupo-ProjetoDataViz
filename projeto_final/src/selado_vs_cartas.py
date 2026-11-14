"""Compara a valorização de uma cesta fixa de selados e cartas elegíveis."""
from __future__ import annotations

from datetime import date
from math import isfinite
from typing import Any, Mapping, Sequence


RARIDADES_CARTAS_PADRAO = (
    "Double Rare",
    "Illustration Rare",
    "Ultra Rare",
    "Special Illustration Rare",
    "Hyper Rare",
)


def calcular_comparacao(
    fato_preco_diario: Sequence[Mapping[str, Any]],
    dim_produto: Sequence[Mapping[str, Any]],
    *,
    moeda: str = "brl",
    data_inicio: date | None = None,
    data_fim: date | None = None,
    raridades_cartas: Sequence[str] = RARIDADES_CARTAS_PADRAO,
    preco_minimo_usd: float | None = None,
) -> list[dict[str, Any]]:
    """Retorna médias/somas diárias e índices base 100 das duas cestas.

    As cestas são determinadas apenas pelos itens com preço na moeda escolhida
    no primeiro dia. Um limite opcional em USD é aplicado estritamente às duas
    cestas nesse mesmo dia. Em datas presentes no fato, item sem preço válido
    carrega o último preço observado; datas inteiramente ausentes não são
    criadas. Os valores nulos nunca entram como zero.
    """
    if moeda not in ("brl", "usd"):
        raise ValueError("moeda deve ser 'brl' ou 'usd'")
    if preco_minimo_usd is not None and not isfinite(preco_minimo_usd):
        raise ValueError("preco_minimo_usd deve ser finito")
    if (data_inicio is None) != (data_fim is None):
        raise ValueError("data_inicio e data_fim devem ser fornecidas juntas")

    fatos = list(fato_preco_diario)
    if data_inicio is None:
        if not fatos:
            raise ValueError("fato_preco_diario vazio: não há período para calcular")
        data_inicio = min(row["data"] for row in fatos)
        data_fim = max(row["data"] for row in fatos)
    if data_inicio > data_fim:
        raise ValueError("data_inicio deve ser anterior ou igual a data_fim")

    fatos_periodo = [row for row in fatos if data_inicio <= row["data"] <= data_fim]
    datas = sorted({row["data"] for row in fatos_periodo})
    if not datas:
        raise ValueError("não há datas de fato no período informado")

    por_chave: dict[tuple[Any, Any, date], Mapping[str, Any]] = {}
    for row in fatos_periodo:
        chave = (row.get("product_id"), row.get("acabamento"), row["data"])
        if chave in por_chave:
            raise ValueError(
                "mais de uma linha para (product_id, acabamento, data): "
                f"{chave}"
            )
        por_chave[chave] = row

    produtos = {row["product_id"]: row for row in dim_produto}
    raridades = set(raridades_cartas)
    coluna_preco = "market_price_brl" if moeda == "brl" else "market_price"

    pares_observados = {
        (row["product_id"], row.get("acabamento"))
        for row in fatos_periodo
        if row.get("product_id") in produtos
    }
    selados = []
    cartas = []
    for product_id, acabamento in sorted(
        pares_observados, key=lambda pair: (pair[0], str(pair[1]))
    ):
        produto = produtos[product_id]
        if produto.get("tipo_produto") == "selado":
            cesta = selados
        elif (
            produto.get("tipo_produto") == "carta"
            and produto.get("raridade") in raridades
        ):
            cesta = cartas
        else:
            continue

        linha_inicio = por_chave.get((product_id, acabamento, data_inicio))
        if linha_inicio is None:
            continue
        preco_inicio = linha_inicio.get(coluna_preco)
        if preco_inicio is None:
            continue
        if preco_minimo_usd is not None:
            preco_usd_inicio = linha_inicio.get("market_price")
            if preco_usd_inicio is None or preco_usd_inicio <= preco_minimo_usd:
                continue
        cesta.append((product_id, acabamento))

    if not selados:
        raise ValueError("cesta de selados vazia no primeiro dia")
    if not cartas:
        raise ValueError("cesta de cartas vazia no primeiro dia")

    def preco_inicial(cesta: list[tuple[Any, Any]], nome: str) -> dict:
        valores = {
            par: por_chave[(par[0], par[1], data_inicio)][coluna_preco]
            for par in cesta
        }
        valor = (
            sum(valores.values()) / len(valores)
            if nome == "selados"
            else sum(valores.values())
        )
        if valor == 0:
            raise ValueError(f"valor inicial da cesta de {nome} é zero")
        return valores

    ultimos_selados = preco_inicial(selados, "selados")
    ultimos_cartas = preco_inicial(cartas, "cartas")
    media_selados_inicial = sum(ultimos_selados.values()) / len(selados)
    soma_cartas_inicial = sum(ultimos_cartas.values())

    serie = []
    for dia in datas:
        carregados_selados = 0
        carregadas_cartas = 0
        valores_selados = []
        valores_cartas = []

        for par in selados:
            linha = por_chave.get((par[0], par[1], dia))
            valor_atual = linha.get(coluna_preco) if linha is not None else None
            if valor_atual is None:
                carregados_selados += 1
                valor_atual = ultimos_selados[par]
            else:
                ultimos_selados[par] = valor_atual
            valores_selados.append(valor_atual)

        for par in cartas:
            linha = por_chave.get((par[0], par[1], dia))
            valor_atual = linha.get(coluna_preco) if linha is not None else None
            if valor_atual is None:
                carregadas_cartas += 1
                valor_atual = ultimos_cartas[par]
            else:
                ultimos_cartas[par] = valor_atual
            valores_cartas.append(valor_atual)

        media_selados = sum(valores_selados) / len(selados)
        soma_cartas = sum(valores_cartas)
        serie.append(
            {
                "data": dia,
                "media_selados": media_selados,
                "soma_cartas": soma_cartas,
                "indice_selados": 100 * media_selados / media_selados_inicial,
                "indice_cartas": 100 * soma_cartas / soma_cartas_inicial,
                "quantidade_selados": len(selados),
                "quantidade_cartas": len(cartas),
                "quantidade_selados_carregados": carregados_selados,
                "quantidade_cartas_carregadas": carregadas_cartas,
            }
        )
    return serie
