import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal, Sequence


StatusManifesto = Literal["gravado", "ja_existia", "erro", "conflito_hash"]


@dataclass(frozen=True)
class ResultadoManifesto:
    arquivo: str
    chave: str | None
    status: StatusManifesto
    bytes: int | None
    sha256: str | None
    linhas: int | None
    alertas: int | None
    motivo: str | None = None


def caminho_manifesto(inicio: datetime) -> str:
    if inicio.utcoffset() is None:
        raise ValueError("inicio deve conter fuso horário")
    inicio_utc = inicio.astimezone(timezone.utc)
    return (
        f"_manifestos/telemetria/data={inicio_utc:%Y-%m-%d}/"
        f"hora={inicio_utc:%H}/"
        f"execucao_{inicio_utc:%Y%m%dT%H%M%SZ}.jsonl"
    )


def serializar_manifesto(resultados: Sequence[ResultadoManifesto]) -> bytes:
    linhas: list[str] = []
    for resultado in resultados:
        registro = asdict(resultado)
        if resultado.motivo is None:
            del registro["motivo"]
        linhas.append(json.dumps(registro, ensure_ascii=True, separators=(",", ":")))
    return ("\n".join(linhas) + ("\n" if linhas else "")).encode("utf-8")
