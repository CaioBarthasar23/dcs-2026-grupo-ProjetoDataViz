from __future__ import annotations

import gzip
import json
from typing import Iterable


def montar_jsonl(eventos: Iterable[dict]) -> bytes:
    linhas = [
        json.dumps(evento, ensure_ascii=False, separators=(",", ":"))
        for evento in eventos
    ]
    if not linhas:
        return b""
    return ("\n".join(linhas) + "\n").encode("utf-8")


def comprimir(jsonl: bytes) -> bytes:
    return gzip.compress(jsonl, mtime=0)
