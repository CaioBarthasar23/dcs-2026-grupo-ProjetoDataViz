"""Carga local do arquivo diário de preços do TCGCSV."""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

import py7zr

from src import collector
from src.prefixo import validar_chave

GROUP_ID = 23651
CATEGORY_ID = 3
ARCHIVE_URL = "https://tcgcsv.com/archive/tcgplayer/prices-{day}.ppmd.7z"


class ArquivoAusente(RuntimeError):
    """O arquivo diário não foi publicado pela fonte."""


def hoje() -> date:
    return datetime.now(collector.TZ).date()


def validar_intervalo(de: date, ate: date) -> None:
    if de > ate:
        raise ValueError("--de não pode ser posterior a --ate")
    if ate >= hoje():
        raise ValueError("--ate precisa ser anterior a hoje")


def key_precos(dia: date) -> str:
    key = f"raw/tcgplayer/group_id={GROUP_ID}/data={dia.isoformat()}/prices.json"
    return validar_chave(key)


def baixar_arquivo(dia: date) -> bytes:
    try:
        return collector.http_get(ARCHIVE_URL.format(day=dia.isoformat())).content
    except RuntimeError as exc:
        if "404" in str(exc):
            raise ArquivoAusente(str(exc)) from exc
        raise


def _extrair_precos(arquivo: bytes, dia: date) -> bytes:
    interno = f"{dia.isoformat()}/{CATEGORY_ID}/{GROUP_ID}/prices"
    with tempfile.TemporaryDirectory() as td:
        archive_path = Path(td) / "prices.7z"
        archive_path.write_bytes(arquivo)
        with py7zr.SevenZipFile(archive_path, mode="r") as seven:
            if interno not in seven.getnames():
                raise ValueError(f"arquivo sem o caminho interno esperado: {interno}")
            seven.extract(path=td, targets=[interno])
        return (Path(td) / interno).read_bytes()


def _tem_resultados(conteudo: bytes) -> bool:
    body = json.loads(conteudo)
    return isinstance(body, dict) and bool(body.get("results"))


def carregar_dia(storage: collector.Storage, dia: date) -> str:
    key = key_precos(dia)
    if storage.exists(key):
        return "ja existia"

    conteudo = _extrair_precos(baixar_arquivo(dia), dia)
    if not _tem_resultados(conteudo):
        return "ignorado: resposta sem resultados"

    try:
        storage.put(key, conteudo)
    except FileExistsError:
        return "ja existia"
    return "gravado"


def carregar_intervalo(
    storage: collector.Storage, de: date, ate: date
) -> dict[str, str]:
    validar_intervalo(de, ate)
    resultado: dict[str, str] = {}
    dia = de
    while dia <= ate:
        try:
            resultado[dia.isoformat()] = carregar_dia(storage, dia)
        except Exception as exc:  # noqa: BLE001
            resultado[dia.isoformat()] = f"ERRO: {exc}"
        dia += timedelta(days=1)
    return resultado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--de", required=True, help="primeira data (AAAA-MM-DD)")
    parser.add_argument("--ate", required=True, help="última data (AAAA-MM-DD)")
    parser.add_argument("--destino", choices=("local", "s3"), default="local")
    args = parser.parse_args(argv)

    try:
        de = date.fromisoformat(args.de)
        ate = date.fromisoformat(args.ate)
        validar_intervalo(de, ate)
        storage = (
            collector.LocalStorage(collector.LOCAL_ROOT)
            if args.destino == "local"
            else collector.get_s3()
        )
        resultado = carregar_intervalo(storage, de, ate)
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))

    for dia, status in resultado.items():
        print(f"{dia} {status}")
    return 1 if any(status.startswith("ERRO:") for status in resultado.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
