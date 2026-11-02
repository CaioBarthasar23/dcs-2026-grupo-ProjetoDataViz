import hashlib
from collections.abc import Mapping
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from botocore.exceptions import ClientError

from src.limpeza import remover_confirmado
from src.metadados import montar_metadados


StatusGravacao = Literal["gravado", "ja_existia", "conflito_hash"]


@dataclass(frozen=True)
class ResultadoGravacao:
    status: StatusGravacao
    chave: str
    sha256: str
    bytes: int


class ClienteS3(Protocol):
    def head_object(self, *, Bucket: str, Key: str) -> Mapping[str, object]: ...

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        Metadata: dict[str, str],
    ) -> object: ...


def gravar_lote(
    cliente: ClienteS3,
    *,
    bucket: str,
    caminho: Path,
    chave: str,
    versao_coletor: str,
    recebido_em: datetime,
) -> ResultadoGravacao:
    conteudo = caminho.read_bytes()
    sha256 = hashlib.sha256(conteudo).hexdigest()
    metadados = montar_metadados(
        caminho.name,
        sha256=sha256,
        versao_coletor=versao_coletor,
        recebido_em=recebido_em,
    )
    try:
        existente = cliente.head_object(Bucket=bucket, Key=chave)
    except ClientError as erro:
        codigo = erro.response.get("Error", {}).get("Code")
        if codigo not in (404, "404"):
            raise
        cliente.put_object(
            Bucket=bucket,
            Key=chave,
            Body=conteudo,
            Metadata=metadados,
        )
        status: StatusGravacao = "gravado"
    else:
        metadata = existente.get("Metadata")
        if not isinstance(metadata, Mapping) or not metadata.get("sha256"):
            raise ValueError(f"Objeto existente sem metadado sha256: {chave}")
        status = (
            "ja_existia" if metadata["sha256"] == sha256 else "conflito_hash"
        )

    resultado = ResultadoGravacao(
        status=status,
        chave=chave,
        sha256=sha256,
        bytes=len(conteudo),
    )
    remover_confirmado(caminho, resultado.status)
    return resultado
