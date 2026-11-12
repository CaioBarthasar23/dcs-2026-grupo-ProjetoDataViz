from datetime import datetime

import pytest
from botocore.exceptions import ReadTimeoutError

from src import collector as c


def test_cliente_s3_define_timeouts_e_tentativas():
    storage = c.S3Storage(
        endpoint="https://s3.fake.invalid",
        access_key="FAKE_ACCESS_KEY_FOR_TESTS",
        secret_key="FAKE_SECRET_KEY_FOR_TESTS",
        bucket="fake-bucket",
    )

    config = storage.client.meta.config
    assert config.connect_timeout == 5
    assert config.read_timeout == 15
    assert config.retries["mode"] == "standard"
    max_retries = config.retries.get("max_attempts")
    if max_retries is None:
        max_retries = config.retries["total_max_attempts"] - 1
    assert max_retries == 2


def test_timeout_em_exists_e_registrado_pela_coleta_sem_gravar(monkeypatch):
    storage = c.S3Storage(
        endpoint="https://s3.fake.invalid",
        access_key="FAKE_ACCESS_KEY_FOR_TESTS",
        secret_key="FAKE_SECRET_KEY_FOR_TESTS",
        bucket="fake-bucket",
    )
    put_calls = []

    def timeout(**kwargs):
        raise ReadTimeoutError(endpoint_url="https://s3.fake.invalid/", error="timeout fake")

    monkeypatch.setattr(storage.client, "head_object", timeout)
    monkeypatch.setattr(storage.client, "put_object", lambda **kwargs: put_calls.append(kwargs))

    key = "raw/tcgplayer/group_id=23651/data=2026-11-12/products.json"
    with pytest.raises(ReadTimeoutError):
        storage.exists(key)

    result = c.coletar(
        storage,
        datetime(2026, 11, 12, 19, 0, tzinfo=c.TZ),
    )
    assert result
    assert all(status.startswith("ERRO:") for status in result.values()), result
    assert put_calls == []
