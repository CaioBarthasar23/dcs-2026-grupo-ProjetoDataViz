import hashlib
from uuid import uuid4

import pytest

from src.storage import save_raw


@pytest.mark.minio
def test_minio_real_le_e_grava_no_bucket_teste(minio_client, detalhe_html):
    # RF-09, RNF-04, RNF-10
    resource = f"integration-test={uuid4().hex}/raw"
    first = save_raw(
        source_url="https://books.toscrape.com/",
        data_ref="2026-11-02",
        resource=resource,
        body=detalhe_html,
        bucket="teste",
    )
    keys = [first.key]
    try:
        before = minio_client.get_object(Bucket="teste", Key=first.key)
        before_body = before["Body"].read()
        before_metadata = before["Metadata"]
        second = save_raw(
            source_url="https://books.toscrape.com/",
            data_ref="2026-11-02",
            resource=resource,
            body=detalhe_html,
            bucket="teste",
        )
        keys.append(second.key)
        after = minio_client.get_object(Bucket="teste", Key=second.key)
        after_body = after["Body"].read()
        after_metadata = after["Metadata"]
        assert second.key == first.key
        assert first.sha256 == second.sha256
        assert first.sha256 == hashlib.sha256(detalhe_html).hexdigest()
        assert before_body == after_body == detalhe_html
        assert before_metadata == after_metadata
        assert after_metadata["sha256"] == second.sha256
        assert after_metadata["source-url"] == "https://books.toscrape.com/"
        assert after_metadata["collected-at"]
        assert all(
            value.encode("ascii").decode("ascii") == value
            for value in (*after_metadata.keys(), *after_metadata.values())
        )
    finally:
        for key in set(keys):
            minio_client.delete_object(Bucket="teste", Key=key)


@pytest.mark.minio
def test_proxy_502_repete_put_mesma_chave(minio_client, detalhe_html):
    # RF-09, RNF-06, RNF-07
    result = save_raw(
        source_url="https://books.toscrape.com/",
        data_ref="2026-11-02",
        resource=f"integration-test={uuid4().hex}/proxy-retry",
        body=detalhe_html,
        bucket="teste",
        proxy_first_status=502,
        retry=True,
    )
    try:
        stored = minio_client.get_object(Bucket="teste", Key=result.key)
        assert stored["Body"].read() == detalhe_html
        assert result.attempts == 2
        assert result.attempt_keys == [result.key, result.key]
        assert result.attempt_bodies == [detalhe_html, detalhe_html]
    finally:
        minio_client.delete_object(Bucket="teste", Key=result.key)
