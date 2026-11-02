import hashlib
from datetime import datetime
from pathlib import Path
from typing import Protocol

from src.metadados import montar_metadados


class ClienteS3(Protocol):
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
) -> None:
    conteudo = caminho.read_bytes()
    sha256 = hashlib.sha256(conteudo).hexdigest()
    metadados = montar_metadados(
        caminho.name,
        sha256=sha256,
        versao_coletor=versao_coletor,
        recebido_em=recebido_em,
    )
    cliente.put_object(
        Bucket=bucket,
        Key=chave,
        Body=conteudo,
        Metadata=metadados,
    )
