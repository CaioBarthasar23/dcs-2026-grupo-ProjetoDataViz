import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.storage import GravadorS3


ITEM_STATES = {
    "pendente",
    "baixando",
    "aguardando",
    "baixado",
    "gravado",
    "falhou",
}
ITEM_TRANSITIONS = {
    "pendente": {"baixando", "falhou"},
    "baixando": {"aguardando", "baixado", "falhou"},
    "aguardando": {"baixando", "falhou"},
    "baixado": {"gravado", "falhou"},
    "gravado": set(),
    "falhou": set(),
}
MANIFEST_STATES = {"sucesso", "incompleta", "falha", "completa"}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
BEARER_TOKEN = re.compile(r"(?i)\bBearer\s+\S+")
URL_CREDENTIALS = re.compile(r"://[^/@\s]+:[^/@\s]+@")


def _isoformat(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, (date, datetime)) else value


@dataclass
class ItemManifesto:
    url: str
    status_http: int | None
    tentativas: int
    bytes: int
    estado: str
    chave: str | None = None
    sha256: str | None = None
    erro: str | None = None

    def __post_init__(self) -> None:
        if self.estado not in ITEM_STATES:
            raise ValueError("estado de item inválido")
        if not isinstance(self.tentativas, int) or self.tentativas < 0:
            raise ValueError("tentativas deve ser um inteiro não negativo")
        if not isinstance(self.bytes, int) or self.bytes < 0:
            raise ValueError("bytes deve ser um inteiro não negativo")
        if self.status_http is not None and not 100 <= self.status_http <= 599:
            raise ValueError("status_http inválido")
        if self.estado == "falhou":
            if self.chave is not None or self.sha256 is not None:
                raise ValueError("item falho não pode referenciar objeto não confirmado")
            if not self.erro:
                raise ValueError("item falho precisa registrar a causa")
        self.erro = sanitizar_erro(self.erro)

    @property
    def attempts(self) -> int:
        return self.tentativas

    @property
    def state(self) -> str:
        return self.estado

    @property
    def key(self) -> str | None:
        return self.chave

    @property
    def error(self) -> str | None:
        return self.erro

    def transicionar(
        self,
        estado: str,
        *,
        status_http: int | None = None,
        tentativas: int | None = None,
        bytes_recebidos: int | None = None,
        chave: str | None = None,
        sha256: str | None = None,
        erro: str | None = None,
    ) -> None:
        if estado not in ITEM_TRANSITIONS.get(self.estado, set()):
            raise ValueError(f"transição de item inválida: {self.estado} -> {estado}")
        if estado == "falhou" and (chave is not None or sha256 is not None):
            raise ValueError("item falho não pode referenciar objeto não confirmado")
        if status_http is not None and not 100 <= status_http <= 599:
            raise ValueError("status_http inválido")
        if tentativas is not None and (not isinstance(tentativas, int) or tentativas < 0):
            raise ValueError("tentativas deve ser um inteiro não negativo")
        if bytes_recebidos is not None and (
            not isinstance(bytes_recebidos, int) or bytes_recebidos < 0
        ):
            raise ValueError("bytes deve ser um inteiro não negativo")
        if estado == "falhou" and not erro:
            raise ValueError("item falho precisa registrar a causa")
        self.estado = estado
        if status_http is not None:
            self.status_http = status_http
        if tentativas is not None:
            self.tentativas = tentativas
        if bytes_recebidos is not None:
            self.bytes = bytes_recebidos
        self.chave = None if estado == "falhou" else chave or self.chave
        self.sha256 = None if estado == "falhou" else sha256 or self.sha256
        if erro is not None:
            self.erro = sanitizar_erro(erro)


def sanitizar_erro(erro: str | None) -> str | None:
    if erro is None:
        return None
    sanitized = SECRET_ASSIGNMENT.sub(r"\1\2[REDACTED]", str(erro))
    sanitized = BEARER_TOKEN.sub("Bearer [REDACTED]", sanitized)
    return URL_CREDENTIALS.sub("://[REDACTED]@", sanitized)


@dataclass
class Manifesto:
    id: str
    data_ref: date | str
    inicio: datetime
    fim: datetime | str | None = None
    estado: str = "em_andamento"
    total_declarado: int | None = None
    total_extraido: int | None = None
    sources: list[str] = field(default_factory=list)
    escopo: dict[str, object] = field(default_factory=dict)
    robots: dict | None = None
    itens: list[ItemManifesto] = field(default_factory=list)

    @classmethod
    def iniciar(cls, data_ref: date | str) -> "Manifesto":
        return create_manifest(data_ref=data_ref)

    @property
    def started_at(self) -> str:
        return _isoformat(self.inicio) or ""

    @property
    def finished_at(self) -> str | None:
        return _isoformat(self.fim)

    @property
    def state(self) -> str:
        return self.estado

    @property
    def declared_total(self) -> int | None:
        return self.total_declarado

    @property
    def extracted_total(self) -> int | None:
        return self.total_extraido

    @property
    def items(self) -> list[ItemManifesto]:
        return self.itens

    def registrar_robots(self, item: ItemManifesto | dict) -> None:
        self.robots = asdict(item) if isinstance(item, ItemManifesto) else dict(item)

    def registrar_source(self, source: str) -> None:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source deve ser uma string não vazia")
        if source not in self.sources:
            self.sources.append(source)

    def registrar_item(self, item: ItemManifesto) -> None:
        if not isinstance(item, ItemManifesto):
            raise TypeError("item deve ser ItemManifesto")
        self.itens.append(item)

    def finalizar(self, estado: str) -> None:
        if estado not in MANIFEST_STATES:
            raise ValueError("estado final do manifesto inválido")
        self.estado = estado
        self.fim = datetime.now(timezone.utc)

    def chaves_raw(self) -> list[str]:
        return [
            item.chave
            for item in self.itens
            if item.chave is not None and item.estado == "gravado"
        ]

    def para_dict(self) -> dict:
        return {
            "id": self.id,
            "inicio": self.started_at,
            "fim": self.finished_at,
            "data_ref": _isoformat(self.data_ref),
            "robots_txt": self.robots,
            "total_declarado": self.total_declarado,
            "total_extraido": self.total_extraido,
            "estado": self.estado,
            "sources": list(self.sources),
            "escopo": dict(self.escopo),
            "itens": [
                {
                    "url": item.url,
                    "estado": item.estado,
                    "chave": item.chave,
                    "status_http": item.status_http,
                    "tentativas": item.tentativas,
                    "bytes": item.bytes,
                    "sha256": item.sha256,
                    "erro": item.erro,
                }
                for item in self.itens
            ],
        }

    def para_json(self) -> str:
        return json.dumps(self.para_dict(), ensure_ascii=False, separators=(",", ":"))

    def chave_manifesto(self) -> str:
        return (
            f"raw/manifestos/data={_isoformat(self.data_ref)}"
            f"/execucao={self.id}.json"
        )

    def persistir(self, gravador: "GravadorS3") -> str:
        key = self.chave_manifesto()
        body = self.para_json().encode("utf-8")
        gravador.gravar_raw(
            key,
            body,
            {
                "data-ref": str(_isoformat(self.data_ref)),
                "content-type": "application/json",
            },
        )
        return key


Item = ItemManifesto
Manifest = Manifesto


def create_manifest(*, data_ref):
    return Manifesto(
        id=str(uuid.uuid4()),
        data_ref=data_ref,
        inicio=datetime.now(timezone.utc),
    )


def record_item(
    manifest,
    *,
    url,
    status_http,
    attempts,
    bytes_received,
    state,
    key=None,
    sha256=None,
    error=None,
):
    if state not in ITEM_STATES:
        raise ValueError("estado de item inválido")
    if state == "falhou" and (key is not None or sha256 is not None):
        raise ValueError("item falho não pode referenciar objeto não confirmado")
    if state == "falhou" and not error:
        raise ValueError("item falho precisa registrar a causa")
    item = ItemManifesto(
        url=url,
        status_http=status_http,
        tentativas=attempts,
        bytes=bytes_received,
        estado=state,
        chave=key,
        sha256=sha256,
        erro=error,
    )
    manifest.registrar_item(item)
    return item


def finalize_manifest(
    manifest,
    *,
    finished_at,
    state,
    declared_total,
    extracted_total,
    sources,
    robots,
):
    if state not in MANIFEST_STATES:
        raise ValueError("estado final do manifesto inválido")
    manifest.fim = finished_at
    manifest.estado = state
    manifest.total_declarado = declared_total
    manifest.total_extraido = extracted_total
    manifest.sources = list(sources)
    manifest.robots = robots
    return manifest
