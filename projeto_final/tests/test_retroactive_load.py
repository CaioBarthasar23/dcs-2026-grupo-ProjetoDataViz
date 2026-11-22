import json
from datetime import date
from pathlib import Path

import py7zr
import pytest

from src import carga_retroativa as r
from src.collector import LocalStorage


def make_archive(tmp_path: Path, files: dict[str, bytes]) -> bytes:
    source = tmp_path / "source"
    source.mkdir()
    for name, content in files.items():
        path = source / name.replace("/", "_")
        path.write_bytes(content)
    archive = tmp_path / "prices.7z"
    with py7zr.SevenZipFile(archive, "w") as seven:
        for name in files:
            seven.write(source / name.replace("/", "_"), arcname=name)
    return archive.read_bytes()


def prices_body(*rows: dict) -> bytes:
    return json.dumps({"success": True, "results": list(rows)}).encode()


def test_extracts_only_target_group_and_preserves_bytes(tmp_path, monkeypatch):
    day = date(2026, 11, 11)
    expected = prices_body({"productId": 1, "marketPrice": 2.5})
    archive = make_archive(
        tmp_path,
        {
            "2026-11-11/3/23651/prices": expected,
            "2026-11-11/3/23651/products": b"products",
            "2026-11-11/3/99999/prices": b"other-group",
            "2026-11-11/1/23651/prices": b"other-category",
        },
    )
    calls = []
    monkeypatch.setattr(r, "baixar_arquivo", lambda d: calls.append(d) or archive)

    result = r.carregar_dia(LocalStorage(tmp_path / "data"), day)

    key = "raw/tcgplayer/group_id=23651/data=2026-11-11/prices.json"
    assert result == "gravado"
    assert calls == [day]
    assert (tmp_path / "data" / key).read_bytes() == expected
    assert not (tmp_path / "data" / key.replace("prices.json", "products.json")).exists()


def test_existing_key_does_not_download_or_overwrite(tmp_path, monkeypatch):
    day = date(2026, 11, 11)
    storage = LocalStorage(tmp_path)
    key = "raw/tcgplayer/group_id=23651/data=2026-11-11/prices.json"
    storage.put(key, b"original")
    monkeypatch.setattr(r, "baixar_arquivo", lambda d: pytest.fail("download inesperado"))

    assert r.carregar_dia(storage, day) == "ja existia"
    assert (tmp_path / key).read_bytes() == b"original"


def test_rejects_key_outside_own_prefix(tmp_path, monkeypatch):
    day = date(2026, 11, 11)
    monkeypatch.setattr(r, "key_precos", lambda d: "raw/tcgplayer/group_id=99999/data=2026-11-11/prices.json")
    monkeypatch.setattr(r, "baixar_arquivo", lambda d: b"unused")

    with pytest.raises(ValueError, match="fora do prefixo"):
        r.carregar_dia(LocalStorage(tmp_path), day)


def test_empty_results_are_ignored(tmp_path, monkeypatch):
    day = date(2026, 11, 11)
    archive = make_archive(
        tmp_path,
        {"2026-11-11/3/23651/prices": b'{"success": true, "results": []}'},
    )
    monkeypatch.setattr(r, "baixar_arquivo", lambda d: archive)

    assert r.carregar_dia(LocalStorage(tmp_path / "data"), day) == "ignorado: resposta sem resultados"
    assert not list((tmp_path / "data").rglob("*"))


def test_missing_day_does_not_stop_interval(tmp_path, monkeypatch):
    archive = make_archive(
        tmp_path,
        {"2026-11-11/3/23651/prices": prices_body({"productId": 1})},
    )

    def download(day):
        if day == date(2026, 11, 10):
            raise r.ArquivoAusente("404")
        return archive

    monkeypatch.setattr(r, "baixar_arquivo", download)
    result = r.carregar_intervalo(
        LocalStorage(tmp_path / "data"), date(2026, 11, 10), date(2026, 11, 11)
    )

    assert result["2026-11-10"].startswith("ERRO")
    assert result["2026-11-11"] == "gravado"


def test_invalid_interval_raises():
    with pytest.raises(ValueError):
        r.validar_intervalo(date(2026, 11, 11), date(2026, 11, 10))


def test_today_or_future_end_date_is_rejected(monkeypatch):
    monkeypatch.setattr(r, "hoje", lambda: date(2026, 11, 19))

    with pytest.raises(ValueError):
        r.validar_intervalo(date(2026, 11, 18), date(2026, 11, 19))
    with pytest.raises(ValueError):
        r.validar_intervalo(date(2026, 11, 18), date(2026, 11, 20))
