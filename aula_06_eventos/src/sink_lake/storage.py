from __future__ import annotations

import os
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class S3Storage:
    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
    ) -> None:
        endpoint = endpoint or os.environ.get("S3_ENDPOINT")
        access_key = access_key or os.environ.get("S3_ACCESS_KEY")
        secret_key = secret_key or os.environ.get("S3_SECRET_KEY")
        bucket = bucket or os.environ.get("S3_BUCKET", "tatame-bruto")
        if not endpoint or not access_key or not secret_key:
            raise RuntimeError(
                "S3_ENDPOINT, S3_ACCESS_KEY e S3_SECRET_KEY sao obrigatorios"
            )
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=os.environ.get("S3_REGION", "us-east-1"),
            config=Config(
                connect_timeout=5,
                read_timeout=15,
                retries={"max_attempts": 2, "mode": "standard"},
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )

    def criar_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as erro:
            codigo = erro.response["Error"]["Code"]
            if codigo not in ("404", "NoSuchBucket", "NotFound"):
                raise
            self.client.create_bucket(Bucket=self.bucket)

    def existe(self, chave: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=chave)
            return True
        except ClientError as erro:
            if erro.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def conteudo(self, chave: str) -> bytes | None:
        try:
            return self.client.get_object(
                Bucket=self.bucket,
                Key=chave,
            )["Body"].read()
        except ClientError as erro:
            if erro.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return None
            raise

    def gravar(self, chave: str, dados: bytes) -> None:
        existente = self.conteudo(chave)
        if existente is not None:
            if existente != dados:
                raise RuntimeError(
                    f"objeto ja existe com conteudo diferente: {chave}"
                )
            return
        self.client.put_object(
            Bucket=self.bucket,
            Key=chave,
            Body=dados,
            ContentType="application/gzip",
        )
