from __future__ import annotations

import argparse
from typing import Iterable

from .gzip_lote import comprimir, montar_jsonl


def principal() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tamanho-jsonl", type=int)
    parser.add_argument("--tamanho-gzip", type=int)
    parser.add_argument("--quantidade", type=int, default=100)
    args = parser.parse_args()

    if args.tamanho_jsonl is not None and args.tamanho_gzip is not None:
        jsonl = args.tamanho_jsonl
        gz = args.tamanho_gzip
        taxa = gz / jsonl if jsonl else 0
        print(f"antes={jsonl} gzip={gz} taxa_compressao={taxa:.6f}")
        return 0

    eventos = [
        {
            "event_id": f"medicao-{indice}",
            "tipo": "checkin",
            "ocorrido_em": "2026-11-14T11:02:07.412Z",
            "regiao": "eu-estocolmo",
            "academia": "SE-STO-014",
            "origem": "catraca",
        }
        for indice in range(args.quantidade)
    ]
    jsonl = montar_jsonl(eventos)
    gz = comprimir(jsonl)
    taxa = len(gz) / len(jsonl) if jsonl else 0
    print(
        f"antes={len(jsonl)} gzip={len(gz)} "
        f"taxa_compressao={taxa:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
