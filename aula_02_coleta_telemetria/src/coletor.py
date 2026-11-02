import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.chaves import montar_chave
from src.config import Configuracao, carregar_configuracao
from src.gravacao import gravar_lote
from src.leitura import listar_arquivos, nome_valido
from src.manifesto import (
    ResultadoManifesto,
    caminho_manifesto,
    serializar_manifesto,
)


class ClienteColeta(Protocol):
    def head_object(self, *, Bucket: str, Key: str) -> object: ...

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        Metadata: dict[str, str],
    ) -> object: ...


def executar(
    configuracao: Configuracao,
    cliente: ClienteColeta,
    inicio: datetime | None = None,
) -> int:
    inicio_execucao = inicio or datetime.now(timezone.utc)
    if inicio_execucao.utcoffset() is None:
        raise ValueError("inicio deve conter fuso horário")

    resultados = [
        _processar_arquivo(configuracao, cliente, caminho, inicio_execucao)
        for caminho in listar_arquivos(configuracao.pouso_dir)
    ]

    cliente.put_object(
        Bucket=configuracao.bucket_raw,
        Key=caminho_manifesto(inicio_execucao),
        Body=serializar_manifesto(resultados),
        Metadata={},
    )
    return int(
        any(
            resultado.status in {"erro", "conflito_hash"}
            for resultado in resultados
        )
    )


def _processar_arquivo(
    configuracao: Configuracao,
    cliente: ClienteColeta,
    caminho: Path,
    inicio: datetime,
) -> ResultadoManifesto:
    valido = nome_valido(caminho.name)
    chave = montar_chave(caminho.name) if valido else None
    try:
        conteudo = caminho.read_bytes()
    except OSError:
        return ResultadoManifesto(
            arquivo=caminho.name,
            chave=chave,
            status="erro",
            bytes=None,
            sha256=None,
            linhas=None,
            alertas=None,
            motivo="falha_leitura",
        )

    linhas = conteudo.splitlines()
    campos = {
        "bytes": len(conteudo),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "linhas": len(linhas),
        "alertas": sum(
            linha.startswith(b"TAC;") and linha.endswith(b";ALERTA")
            for linha in linhas
        ),
    }
    if not valido or chave is None:
        return ResultadoManifesto(
            arquivo=caminho.name,
            chave=None,
            status="erro",
            **campos,
            motivo="nome_invalido",
        )

    try:
        gravacao = gravar_lote(
            cliente,
            bucket=configuracao.bucket_raw,
            caminho=caminho,
            chave=chave,
            versao_coletor=configuracao.coletor_versao,
            recebido_em=inicio,
        )
    except (BotoCoreError, ClientError, OSError, TimeoutError, ValueError) as erro:
        return ResultadoManifesto(
            arquivo=caminho.name,
            chave=chave,
            status="erro",
            **campos,
            motivo=type(erro).__name__,
        )

    return ResultadoManifesto(
        arquivo=caminho.name,
        chave=chave,
        status=gravacao.status,
        **campos,
    )


def main() -> int:
    configuracao = carregar_configuracao()
    cliente = boto3.client(
        "s3",
        endpoint_url=configuracao.s3_endpoint_url,
        aws_access_key_id=configuracao.s3_access_key,
        aws_secret_access_key=configuracao.s3_secret_key,
        region_name=configuracao.s3_region,
        config=Config(
            s3={"addressing_style": "path"},
            retries={"max_attempts": 0},
        ),
    )
    return executar(configuracao, cliente)


if __name__ == "__main__":
    raise SystemExit(main())
