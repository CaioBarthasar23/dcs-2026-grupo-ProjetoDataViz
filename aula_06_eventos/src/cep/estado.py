from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


class EstadoPersistente:
    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self.regras: Dict[str, Dict[str, Any]] = {}
        self._carregar()

    def _carregar(self) -> None:
        if not self.caminho.exists():
            return
        dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        self.regras = dados.get("regras", {})

    def obter(self, regra: str, chave: str) -> dict[str, Any] | None:
        return self.regras.setdefault(regra, {}).get(chave)

    def salvar_chave(self, regra: str, chave: str, estado: dict[str, Any]) -> None:
        self.regras.setdefault(regra, {})[chave] = estado
        self.persistir()

    def remover(self, regra: str, chave: str) -> None:
        self.regras.setdefault(regra, {}).pop(chave, None)
        self.persistir()

    def contar_chaves(self) -> int:
        return sum(len(chaves) for chaves in self.regras.values())

    def persistir(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps({"regras": self.regras}, ensure_ascii=False),
            encoding="utf-8",
        )
        temporario.replace(self.caminho)
