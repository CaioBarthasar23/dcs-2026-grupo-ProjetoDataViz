import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal, Protocol, Sequence

from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    ReadTimeoutError,
)

from src.limpeza import remover_confirmado
from src.metadados import montar_metadados


StatusGravacao = Literal["gravado", "ja_existia", "conflito_hash", "erro"]
_ERROS_TIMEOUT = (ConnectTimeoutError, ReadTimeoutError, TimeoutError)
_CODIGOS_REPETIVEIS = {"502", "503", "504"}


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
    atrasos: Sequence[float] = (),
    dormir: Callable[[float], None] | None = None,
) -> ResultadoGravacao:
    if any(atraso < 0 for atraso in atrasos) or any(
        atual <= anterior for anterior, atual in zip(atrasos, atrasos[1:])
    ):
        raise ValueError("atrasos devem ser não negativos e crescentes")
    if atrasos and dormir is None:
        raise ValueError("dormir é obrigatório quando atrasos são configurados")

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
        if not _chave_ausente(erro):
            if _codigo_http(erro) not in _CODIGOS_REPETIVEIS:
                raise
            return _finalizar(caminho, "erro", chave, sha256, len(conteudo))
    except _ERROS_TIMEOUT:
        return _finalizar(caminho, "erro", chave, sha256, len(conteudo))
    else:
        return _finalizar(
            caminho,
            _status_existente(existente, sha256, chave),
            chave,
            sha256,
            len(conteudo),
        )

    for atraso in (*atrasos, None):
        try:
            cliente.put_object(
                Bucket=bucket,
                Key=chave,
                Body=conteudo,
                Metadata=metadados,
            )
        except ClientError as erro:
            codigo = _codigo_http(erro)
            if codigo == "403":
                return _finalizar(caminho, "erro", chave, sha256, len(conteudo))
            if codigo not in _CODIGOS_REPETIVEIS:
                raise
        except _ERROS_TIMEOUT:
            pass
        else:
            return _finalizar(
                caminho, "gravado", chave, sha256, len(conteudo)
            )

        try:
            existente = cliente.head_object(Bucket=bucket, Key=chave)
        except ClientError as erro:
            if _chave_ausente(erro):
                pass
            else:
                return _finalizar(
                    caminho, "erro", chave, sha256, len(conteudo)
                )
        except _ERROS_TIMEOUT:
            return _finalizar(caminho, "erro", chave, sha256, len(conteudo))
        else:
            status_existente = _status_existente(existente, sha256, chave)
            return _finalizar(
                caminho,
                status_existente,
                chave,
                sha256,
                len(conteudo),
            )

        if atraso is None:
            return _finalizar(caminho, "erro", chave, sha256, len(conteudo))
        if dormir is None:
            raise ValueError("dormir é obrigatório quando atrasos são configurados")
        dormir(atraso)

    raise AssertionError("loop de tentativas terminou sem resultado")


def _codigo_http(erro: ClientError) -> str:
    response_metadata = erro.response.get("ResponseMetadata", {})
    status = response_metadata.get("HTTPStatusCode")
    if status is not None:
        return str(status)
    codigo = erro.response.get("Error", {}).get("Code", "")
    return str(codigo)


def _chave_ausente(erro: ClientError) -> bool:
    return _codigo_http(erro) == "404"


def _status_existente(
    resposta: Mapping[str, object], sha256: str, chave: str
) -> StatusGravacao:
    metadata = resposta.get("Metadata")
    if not isinstance(metadata, Mapping) or not metadata.get("sha256"):
        raise ValueError(f"Objeto existente sem metadado sha256: {chave}")
    return "ja_existia" if metadata["sha256"] == sha256 else "conflito_hash"


def _finalizar(
    caminho: Path,
    status: StatusGravacao,
    chave: str,
    sha256: str,
    tamanho: int,
) -> ResultadoGravacao:
    resultado = ResultadoGravacao(
        status=status,
        chave=chave,
        sha256=sha256,
        bytes=tamanho,
    )
    remover_confirmado(caminho, resultado.status)
    return resultado
