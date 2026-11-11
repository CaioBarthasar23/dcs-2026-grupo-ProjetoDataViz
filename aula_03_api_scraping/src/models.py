import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class Resposta:
    url: str
    status_http: int
    headers: dict[str, str]
    corpo: bytes
    tentativas: int
    recebido_em: datetime

    def sucesso(self) -> bool:
        return 200 <= self.status_http < 300

    @property
    def status_code(self) -> int:
        return self.status_http

    @property
    def content(self) -> bytes:
        return self.corpo


@dataclass(frozen=True)
class Livro:
    upc: str
    url: str
    titulo: str
    categoria: str
    avaliacao: str
    preco_gbp: float
    em_estoque: bool
    qtd_estoque: int | None
    coletado_em: str

    def para_json(self) -> str:
        return json.dumps(serialize_book(self), ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class Cotacao:
    moeda: str
    dataHoraCotacao: str
    tipoBoletim: str
    cotacaoCompra: float
    cotacaoVenda: float

    def para_json(self) -> str:
        return json.dumps(serialize_quote(self), ensure_ascii=False, separators=(",", ":"))


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {
        "upc": value.upc,
        "url": value.url,
        "titulo": value.titulo,
        "categoria": value.categoria,
        "avaliacao": value.avaliacao,
        "preco_gbp": value.preco_gbp,
        "em_estoque": value.em_estoque,
        "qtd_estoque": value.qtd_estoque,
        "coletado_em": value.coletado_em,
    }


def serialize_book(book: Any) -> dict[str, Any]:
    fields = (
        "upc",
        "url",
        "titulo",
        "categoria",
        "avaliacao",
        "preco_gbp",
        "em_estoque",
        "qtd_estoque",
        "coletado_em",
    )
    values = _as_mapping(book)
    return {name: values[name] for name in fields}


def serialize_quote(quote: Cotacao | Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "moeda",
        "dataHoraCotacao",
        "tipoBoletim",
        "cotacaoCompra",
        "cotacaoVenda",
    )
    values = quote if isinstance(quote, Mapping) else vars(quote)
    return {name: values[name] for name in fields}
