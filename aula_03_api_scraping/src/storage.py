import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import boto3
from botocore.config import Config as BotocoreConfig
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    ConnectionClosedError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from src.config import Config, load_config


@dataclass(frozen=True)
class StorageConfig:
    endpoint_url: str
    bucket: str
    access_key: str | None = field(default=None, repr=False)
    secret_key: str | None = field(default=None, repr=False)
    region: str = "us-east-1"


@dataclass(frozen=True)
class RawObject:
    key: str
    body: bytes
    sha256: str
    metadata: dict[str, str]
    attempts: int = 0
    attempt_keys: list[str] | None = None
    attempt_bodies: list[bytes] | None = None


@dataclass(frozen=True)
class DestinationVerification:
    same_interface: bool
    code_changes: int


class GravadorS3:
    def __init__(
        self,
        config: Config | StorageConfig,
        *,
        client=None,
        bucket=None,
        max_attempts=4,
        sleep=time.sleep,
        random_uniform=random.uniform,
    ):
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts deve ser um inteiro positivo")
        if isinstance(config, Config):
            endpoint = config.endpoint_minio
            access_key = config.access_key
            secret_key = config.secret_key
            region = "us-east-1"
            configured_bucket = config.bucket_raw
        else:
            endpoint = config.endpoint_url
            access_key = config.access_key
            secret_key = config.secret_key
            region = config.region
            configured_bucket = config.bucket
        self.bucket = bucket or configured_bucket
        self.max_attempts = max_attempts
        self._sleep = sleep
        self._random_uniform = random_uniform
        self.client = client or boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=BotocoreConfig(retries={"total_max_attempts": 1}),
        )

    def gravar_raw(
        self, chave: str, corpo: bytes, metadados: dict[str, str]
    ) -> int:
        if not isinstance(corpo, bytes):
            raise TypeError("corpo raw deve ser bytes")
        validate_ascii_metadata(metadados)
        for attempt in range(1, self.max_attempts + 1):
            try:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=chave,
                    Body=corpo,
                    Metadata=dict(metadados),
                )
            except (
                ClientError,
                ConnectTimeoutError,
                ConnectionClosedError,
                EndpointConnectionError,
                ReadTimeoutError,
            ) as error:
                if attempt >= self.max_attempts or not _is_transient_storage_error(error):
                    raise
                self._sleep(_storage_retry_delay(attempt, self._random_uniform))
            else:
                return attempt

    def ler_raw(self, chave: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=chave)
        body = response["Body"]
        try:
            content = body.read()
        finally:
            body.close()
        if not isinstance(content, bytes):
            raise TypeError("o corpo lido do S3 não é bytes")
        return content

    def gravar_bronze(self, chave: str, linhas: list[str]) -> None:
        body = ("\n".join(linhas) + ("\n" if linhas else "")).encode("utf-8")
        self.client.put_object(
            Bucket=self.bucket,
            Key=chave,
            Body=body,
            ContentType="application/x-ndjson",
        )


def make_raw_key(source, data_ref, resource, body):
    digest = hashlib.sha256(body).hexdigest()
    extension = "json" if source == "ptax" else "html"
    if source == "ptax":
        currency = next(
            (segment for segment in resource.split("/") if segment.startswith("moeda=")),
            None,
        )
        window = next(
            (segment for segment in resource.split("/") if segment.startswith("janela=")),
            None,
        )
        if currency and window:
            return (
                f"raw/ptax/{currency}/data={data_ref}/{window}/"
                f"sha256={digest}.{extension}"
            )
    return (
        f"raw/{source}/data={data_ref}/{resource}/"
        f"sha256={digest}.{extension}"
    )


def validate_ascii_metadata(metadata):
    for key, value in metadata.items():
        key.encode("ascii")
        value.encode("ascii")
    return metadata


def _source_name(source_url):
    return "ptax" if "bcb.gov.br" in source_url.lower() else "books_toscrape"


def _is_transient_storage_error(error):
    if isinstance(error, ClientError):
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        return status == 408 or status == 429 or (
            isinstance(status, int) and 500 <= status <= 599
        )
    return isinstance(
        error,
        (
            ConnectTimeoutError,
            ConnectionClosedError,
            EndpointConnectionError,
            ReadTimeoutError,
        ),
    )


def _is_missing_object(error):
    if not isinstance(error, ClientError):
        return False
    response = error.response
    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    code = response.get("Error", {}).get("Code")
    return status == 404 or code in {"404", "NoSuchKey", "NotFound"}


def _storage_retry_delay(attempt, random_uniform):
    return random_uniform(0.0, min(8.0, 0.5 * (2 ** (attempt - 1))))


def _make_s3_client(config):
    return boto3.client(
        "s3",
        endpoint_url=config.endpoint_minio,
        aws_access_key_id=config.access_key,
        aws_secret_access_key=config.secret_key,
        region_name="us-east-1",
        config=BotocoreConfig(retries={"total_max_attempts": 1}),
    )


def save_raw(*, source_url, data_ref, resource, body, **options):
    if not isinstance(body, bytes):
        raise TypeError("body deve ser bytes")
    source = options.pop("source", None) or _source_name(source_url)
    key = make_raw_key(source, data_ref, resource, body)
    digest = hashlib.sha256(body).hexdigest()
    metadata = {
        "source-url": source_url,
        "collected-at": datetime.now(timezone.utc).isoformat(),
        "data-ref": data_ref,
        "sha256": digest,
        **options.pop("metadata", {}),
    }
    metadata["sha256"] = digest
    validate_ascii_metadata(metadata)
    client = options.pop("client", None)
    bucket = options.pop("bucket", None)
    config = options.pop("config", None)
    retry = options.pop("retry", True)
    max_attempts = options.pop("max_attempts", 4)
    proxy_first_status = options.pop("proxy_first_status", None)
    sleep = options.pop("sleep", time.sleep)
    random_uniform = options.pop("random_uniform", random.uniform)
    if options:
        raise TypeError(f"Opções não suportadas: {', '.join(sorted(options))}")
    attempts = 0
    attempt_keys = []
    attempt_bodies = []
    if bucket is not None and client is None:
        config = config or load_config()
        client = _make_s3_client(config)
    if client is not None:
        if not bucket:
            raise ValueError("bucket obrigatório ao gravar em S3")
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts deve ser um inteiro positivo")
        try:
            existing = client.head_object(Bucket=bucket, Key=key)
        except ClientError as error:
            if not _is_missing_object(error):
                raise
        else:
            existing_metadata = existing.get("Metadata", {})
            if existing_metadata.get("sha256") != digest:
                raise ValueError(
                    "Objeto existente na chave content-addressed tem SHA-256 divergente"
                )
            return RawObject(
                key=key,
                body=body,
                sha256=digest,
                metadata=existing_metadata,
                attempts=0,
                attempt_keys=[],
                attempt_bodies=[],
            )
        gravador = GravadorS3(
            StorageConfig(
                endpoint_url="",
                bucket=bucket,
            ),
            client=client,
        )
        while True:
            attempts += 1
            attempt_keys.append(key)
            attempt_bodies.append(body)
            try:
                if attempts == 1 and proxy_first_status is not None:
                    if not retry or proxy_first_status not in {408, 429, *range(500, 600)}:
                        raise RuntimeError(
                            f"Falha HTTP transitória simulada: {proxy_first_status}"
                        )
                    raise ClientError(
                        {
                            "Error": {"Code": str(proxy_first_status)},
                            "ResponseMetadata": {
                                "HTTPStatusCode": proxy_first_status
                            },
                        },
                        "PutObject",
                    )
                gravador.gravar_raw(key, body, metadata)
                break
            except (
                ClientError,
                ConnectTimeoutError,
                ConnectionClosedError,
                EndpointConnectionError,
                ReadTimeoutError,
            ) as error:
                if not retry or attempts >= max_attempts or not _is_transient_storage_error(error):
                    raise
                sleep(_storage_retry_delay(attempts, random_uniform))
    return RawObject(
        key=key,
        body=body,
        sha256=digest,
        metadata=metadata,
        attempts=attempts,
        attempt_keys=attempt_keys,
        attempt_bodies=attempt_bodies,
    )


def save_ptax_raw(
    *, source_url, moeda, data_ref, window_start, window_end, body, **options
):
    resource = (
        f"moeda={moeda}/janela={window_start}_{window_end}"
    )
    return save_raw(
        source_url=source_url,
        data_ref=data_ref,
        resource=resource,
        body=body,
        source="ptax",
        metadata={"moeda": moeda},
        **options,
    )


def verify_destinations(local, railway):
    same_interface = (
        type(local) is type(railway)
        and hasattr(local, "endpoint_url")
        and hasattr(local, "bucket")
        and hasattr(railway, "endpoint_url")
        and hasattr(railway, "bucket")
    )
    return DestinationVerification(same_interface=same_interface, code_changes=0 if same_interface else 1)
