import json
from uuid import uuid4

import pytest

from src.manifest import create_manifest, record_item
from src.storage import GravadorS3, StorageConfig, save_raw


@pytest.mark.minio
def test_reexecucao_reutiliza_raw_preserva_manifesto_e_substitui_bronze(
    minio_client,
):
    suffix = uuid4().hex
    data_ref = "2026-11-02"
    resource = f"integration-test={suffix}/book-detail"
    bronze_key = f"bronze/integration-test={suffix}/livros.jsonl"
    storage_config = StorageConfig(
        endpoint_url="http://localhost:9000",
        bucket="teste",
    )
    storage = GravadorS3(storage_config, client=minio_client)
    raw_keys = []
    manifest_keys = []
    created_bronze = False
    body = b"<html><body>stable raw payload</body></html>"
    book_line = json.dumps(
        {
            "upc": "upc-once",
            "url": "https://books.toscrape.com/book",
            "titulo": "Book",
            "categoria": "Mystery",
            "avaliacao": "Five",
            "preco_gbp": 12.5,
            "em_estoque": True,
            "qtd_estoque": 1,
            "coletado_em": "2026-11-02T00:00:00Z",
        },
        separators=(",", ":"),
    )

    try:
        first_raw = save_raw(
            source_url="https://books.toscrape.com/book",
            data_ref=data_ref,
            resource=resource,
            body=body,
            client=minio_client,
            bucket="teste",
        )
        raw_keys.append(first_raw.key)
        first = create_manifest(data_ref=data_ref)
        record_item(
            first,
            url="https://books.toscrape.com/book",
            status_http=200,
            attempts=1,
            bytes_received=len(body),
            state="gravado",
            key=first_raw.key,
            sha256=first_raw.sha256,
        )
        first_manifest_key = first.persistir(storage)
        manifest_keys.append(first_manifest_key)
        storage.gravar_bronze(bronze_key, [book_line, book_line])
        created_bronze = True

        second_raw = save_raw(
            source_url="https://books.toscrape.com/book",
            data_ref=data_ref,
            resource=resource,
            body=body,
            client=minio_client,
            bucket="teste",
        )
        second = create_manifest(data_ref=data_ref)
        record_item(
            second,
            url="https://books.toscrape.com/book",
            status_http=200,
            attempts=1,
            bytes_received=len(body),
            state="gravado",
            key=second_raw.key,
            sha256=second_raw.sha256,
        )
        second_manifest_key = second.persistir(storage)
        manifest_keys.append(second_manifest_key)
        storage.gravar_bronze(bronze_key, [book_line])

        assert second_raw.key == first_raw.key
        assert second.id != first.id
        assert second_manifest_key != first_manifest_key
        assert storage.ler_raw(first_raw.key) == body
        first_saved = minio_client.get_object(
            Bucket="teste",
            Key=first_manifest_key,
        )
        second_saved = minio_client.get_object(
            Bucket="teste",
            Key=second_manifest_key,
        )
        assert json.loads(first_saved["Body"].read())["id"] == first.id
        assert json.loads(second_saved["Body"].read())["id"] == second.id
        bronze = minio_client.get_object(Bucket="teste", Key=bronze_key)
        lines = bronze["Body"].read().decode("utf-8").splitlines()
        upcs = [json.loads(line)["upc"] for line in lines]
        assert upcs == ["upc-once"]
    finally:
        for key in set(raw_keys + manifest_keys):
            minio_client.delete_object(Bucket="teste", Key=key)
        if created_bronze:
            minio_client.delete_object(Bucket="teste", Key=bronze_key)
