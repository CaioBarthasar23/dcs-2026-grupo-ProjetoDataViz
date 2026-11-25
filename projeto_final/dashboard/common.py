"""Leitura somente de silver local e utilitários comuns às telas."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

# Mantém a grafia usada na classificação e nas exclusões existentes:
# src/silver.py:125, src/concentracao_valor.py:104 e src/decomposicao.py:52.
RARIDADE_CODE_CARD = "Code Card"
GROUP_ID = 23651


def _ler_parquet(con: duckdb.DuckDBPyConnection, path: Path) -> list[dict[str, Any]]:
    return con.execute("SELECT * FROM read_parquet(?)", [str(path)]).to_arrow_table().to_pylist()


def carregar_silver(raiz: str | Path = Path("data_local/silver")) -> dict[str, list[dict[str, Any]]]:
    """Lê produto, preços e câmbio de uma raiz silver local; nunca grava nela."""
    raiz = Path(raiz)
    produtos_path = raiz / "produto" / f"group_id={GROUP_ID}" / "produto.parquet"
    cambios_path = raiz / "cambio_diario" / f"group_id={GROUP_ID}" / "cambio.parquet"
    precos_dir = raiz / "preco_diario" / f"group_id={GROUP_ID}"
    precos_paths = sorted(precos_dir.glob("data=*/preco.parquet"))
    if not produtos_path.is_file():
        raise FileNotFoundError(f"silver de produto ausente: {produtos_path}")
    if not cambios_path.is_file():
        raise FileNotFoundError(f"silver de câmbio ausente: {cambios_path}")
    if not precos_paths:
        raise FileNotFoundError(f"silver de preços ausente: {precos_dir}/data=*/preco.parquet")

    with duckdb.connect(database=":memory:") as con:
        produtos = _ler_parquet(con, produtos_path)
        cambios = _ler_parquet(con, cambios_path)
        precos = [row for path in precos_paths for row in _ler_parquet(con, path)]
    return {
        "produtos": produtos,
        "precos": sorted(precos, key=lambda row: (row["data"], row["product_id"], row["acabamento"])),
        "cambios": sorted(cambios, key=lambda row: row["data"]),
        "caminhos": [str(produtos_path), *(str(path) for path in precos_paths), str(cambios_path)],
    }
