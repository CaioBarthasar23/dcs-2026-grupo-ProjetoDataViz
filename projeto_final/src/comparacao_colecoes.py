"""Calcula o valor e o índice diário de coleções em uma janela comum.

As entradas são mapas ``group_id -> {"preco_diario": [...], "produto": [...]}``
no contrato silver. A escolha do exemplar é feita no primeiro dia comum e
mantida durante a janela. A conversão USD/BRL e a associação ASOF reutilizam
``src.fx_asof.converter_precos``.
"""
from __future__ import annotations

from datetime import date
from math import isfinite
from typing import Any, Mapping, Sequence

from src.fx_asof import converter_precos


def calcular_comparacao_colecoes(
    colecoes: Mapping[int, Mapping[str, Sequence[Mapping[str, Any]]]],
    cambios: Sequence[Mapping[str, Any]],
    *,
    moeda: str = "brl",
    preco_minimo_usd: float | None = None,
) -> dict[str, Any]:
    """Retorna período, disponibilidade, cobertura, valores e índices.

    ``colecoes`` contém para cada ``group_id`` as linhas de ``preco_diario`` e
    ``produto``. O período comum é a interseção das datas de preço das
    coleções com ambas as tabelas. Preço nulo não é preço e não substitui o
    último preço válido. O filtro USD é estrito e só é aplicado na seleção do
    exemplar do primeiro dia comum.
    """
    if moeda not in ("brl", "usd"):
        raise ValueError("moeda deve ser 'brl' ou 'usd'")
    if preco_minimo_usd is not None and not isfinite(preco_minimo_usd):
        raise ValueError("preco_minimo_usd deve ser finito")

    # Validar e normalizar entradas antes de calcular interseção ou seleção.
    normalized: dict[int, tuple[list[dict], dict[Any, Mapping[str, Any]], set[date]]] = {}
    excluidas: dict[int, dict[str, str]] = {}
    for gid in sorted(colecoes):
        pacote = colecoes[gid]
        precos = [dict(row) for row in pacote.get("preco_diario", ())]
        produtos_linhas = [dict(row) for row in pacote.get("produto", ())]
        if any(row.get("group_id") != gid for row in precos + produtos_linhas):
            raise ValueError(f"registro fora de group_id={gid}")
        vistos: set[tuple[Any, Any, date]] = set()
        for row in precos:
            chave = (row.get("product_id"), row.get("acabamento"), row["data"])
            if chave in vistos:
                raise ValueError(
                    "linha duplicada para (coleção, produto, acabamento, data): "
                    f"group_id={gid}, product_id={chave[0]}, acabamento={chave[1]!r}, data={chave[2]}"
                )
            vistos.add(chave)
        produtos: dict[Any, Mapping[str, Any]] = {}
        for produto in produtos_linhas:
            pid = produto["product_id"]
            if pid in produtos:
                raise ValueError(f"produto duplicado product_id={pid} em group_id={gid}")
            produtos[pid] = produto
        datas = {row["data"] for row in precos if row.get("market_price") is not None}
        if not datas:
            excluidas[gid] = {"motivo": "sem nenhuma data com preço não nulo"}
            continue
        if not produtos:
            excluidas[gid] = {"motivo": "sem produtos na silver"}
            continue
        normalized[gid] = (precos, produtos, datas)

    # Excluir coleções sem carta elegível e recalcular a interseção até
    # estabilizar: a coleção excluída não pode restringir as demais.
    while normalized:
        iterator = iter(normalized.values())
        periodo = set(next(iterator)[2])
        for _, _, datas in iterator:
            periodo.intersection_update(datas)
        periodo_comum = sorted(periodo)
        if not periodo_comum:
            for gid in normalized:
                excluidas[gid] = {"motivo": "período comum vazio"}
            normalized.clear()
            break

        inicio = periodo_comum[0]
        sem_elegivel = []
        for gid, (precos, produtos, _) in normalized.items():
            converted_inicio = converter_precos(
                [row for row in precos if row["data"] == inicio], cambios, cotacao="compra"
            )
            tem_elegivel = False
            for row in converted_inicio:
                produto = produtos.get(row["product_id"], {})
                usd = row.get("market_price")
                if (produto.get("tipo_produto") != "carta"
                        or produto.get("raridade") == "Code Card"
                        or row.get("market_price_brl") is None or usd is None):
                    continue
                if preco_minimo_usd is not None and usd <= preco_minimo_usd:
                    continue
                tem_elegivel = True
                break
            if not tem_elegivel:
                sem_elegivel.append(gid)
        if not sem_elegivel:
            break
        for gid in sem_elegivel:
            del normalized[gid]
            excluidas[gid] = {
                "motivo": "nenhuma carta elegível com preço em reais no primeiro dia comum"
            }
    else:
        periodo_comum = []

    # Uma linha sintética de preço igual a 1 permite expor a taxa ASOF exata
    # escolhida pelo conversor, sem replicar sua lógica de associação.
    ptax_linhas = converter_precos(
        [
            {
                "data": dia,
                "product_id": 1,
                "group_id": 0,
                "acabamento": "PTAX",
                "market_price": 1.0,
                "moeda": "USD",
            }
            for dia in periodo_comum
        ],
        cambios,
        cotacao="compra",
    )
    taxas_ptax = {row["data"]: row["market_price_brl"] for row in ptax_linhas}
    base_ptax = taxas_ptax.get(periodo_comum[0]) if periodo_comum else None
    indice_ptax = [
        {
            "data": dia,
            "valor_ptax": taxas_ptax.get(dia),
            "indice": (
                100 * taxas_ptax[dia] / base_ptax
                if taxas_ptax.get(dia) is not None and base_ptax not in (None, 0)
                else None
            ),
        }
        for dia in periodo_comum
    ]

    disponiveis: dict[int, dict[str, Any]] = {}
    cobertura: dict[int, dict[str, Any]] = {}
    series: dict[int, list[dict[str, Any]]] = {}
    for gid, (precos, produtos, datas) in normalized.items():
        cobertura[gid] = {
            "dias_com_preco": len(datas.intersection(periodo_comum)),
            "dias_periodo_comum": len(periodo_comum),
            "proporcao_dias": (
                len(datas.intersection(periodo_comum)) / len(periodo_comum)
                if periodo_comum
                else 0.0
            ),
            "linhas_preco_periodo": sum(
                row["data"] in periodo and row.get("market_price") is not None
                for row in precos
            ),
        }
        inicio = periodo_comum[0]
        converted = converter_precos(precos, cambios, cotacao="compra")
        # Conversão de cada linha por meio do conversor comum; nulos continuam nulos.
        converted_by_key = {
            (row["product_id"], row.get("acabamento"), row["data"]): row
            for row in converted
            if row["data"] in periodo_comum
        }
        by_product: dict[Any, list[dict[str, Any]]] = {}
        for row in converted:
            if row["data"] in periodo_comum:
                by_product.setdefault(row["product_id"], []).append(row)

        chosen: dict[Any, str] = {}
        start_prices: dict[Any, dict[str, float]] = {}
        for pid in sorted(produtos):
            produto = produtos[pid]
            if produto.get("tipo_produto") != "carta" or produto.get("raridade") == "Code Card":
                continue
            candidates = []
            for row in by_product.get(pid, ()):
                if row["data"] != inicio:
                    continue
                brl = row.get("market_price_brl")
                usd = row.get("market_price")
                # A elegibilidade exige preço em reais na data-base, também na
                # apresentação USD, conforme a regra de seleção recebida.
                if brl is None or usd is None:
                    continue
                if preco_minimo_usd is not None and usd <= preco_minimo_usd:
                    continue
                candidates.append((brl, str(row.get("acabamento", "")), row))
            if not candidates:
                continue
            _, acabamento, inicial = min(candidates, key=lambda item: (item[0], item[1]))
            chosen[pid] = acabamento
            start_prices[pid] = {
                "brl": inicial["market_price_brl"],
                "usd": inicial["market_price"],
            }

        if not chosen:
            excluidas[gid] = {"motivo": "nenhuma carta elegível com preço em reais no primeiro dia comum"}
            continue

        coluna = "brl" if moeda == "brl" else "usd"
        ultimo_brl = {pid: vals["brl"] for pid, vals in start_prices.items()}
        ultimo_usd = {pid: vals["usd"] for pid, vals in start_prices.items()}
        base = sum(vals[coluna] for vals in start_prices.values())
        if base == 0:
            excluidas[gid] = {"motivo": "valor inicial da coleção é zero"}
            continue

        linhas_serie = []
        for dia in periodo_comum:
            carregados = 0
            valor_brl = 0.0
            valor_usd = 0.0
            for pid, acabamento in chosen.items():
                row = converted_by_key.get((pid, acabamento, dia))
                current_brl = None if row is None else row.get("market_price_brl")
                current_usd = None if row is None else row.get("market_price")
                if current_brl is None:
                    current_brl = ultimo_brl[pid]
                    if coluna == "brl":
                        carregados += 1
                else:
                    ultimo_brl[pid] = current_brl
                if current_usd is None:
                    current_usd = ultimo_usd[pid]
                    if coluna == "usd":
                        carregados += 1
                else:
                    ultimo_usd[pid] = current_usd
                valor_brl += current_brl
                valor_usd += current_usd
            valor_total = valor_brl if coluna == "brl" else valor_usd
            linhas_serie.append(
                {
                    "data": dia,
                    "valor": valor_total,
                    "valor_brl": valor_brl,
                    "valor_usd": valor_usd,
                    "indice_colecao": 100 * valor_total / base,
                    "quantidade_cartas": len(chosen),
                    "quantidade_carregados": carregados,
                }
            )
        disponiveis[gid] = {
            "motivo": "possui cartas elegíveis com preço em reais no primeiro dia comum",
            "quantidade_cartas": len(chosen),
            "acabamentos_escolhidos": chosen,
        }
        series[gid] = linhas_serie

    return {
        "periodo_comum": periodo_comum,
        "disponiveis": dict(sorted(disponiveis.items())),
        "excluidas": dict(sorted(excluidas.items())),
        "cobertura": dict(sorted(cobertura.items())),
        "series": dict(sorted(series.items())),
        "indice_ptax": indice_ptax,
        "moeda": moeda,
    }
