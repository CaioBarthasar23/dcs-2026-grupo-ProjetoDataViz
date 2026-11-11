import argparse
import json
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.config import Config, load_config
from src.manifest import ItemManifesto, Manifesto
from src.storage import GravadorS3

PTAX_LOOKBACK_DAYS = 30


class _PipelineStorage:
    def __init__(self, raw, bronze):
        self.raw = raw
        self.bronze = bronze

    def gravar_raw(self, chave, corpo, metadados):
        return self.raw.gravar_raw(chave, corpo, metadados)

    def ler_raw(self, chave):
        return self.raw.ler_raw(chave)

    def gravar_bronze(self, chave, linhas):
        return self.bronze.gravar_bronze(chave, linhas)


def _parser():
    parser = argparse.ArgumentParser(prog="aula-03")
    commands = parser.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("executar")
    execute.add_argument("--data", "--data-ref", dest="data_ref")
    collect = commands.add_parser("coletar")
    collect.add_argument("--data", "--data-ref", dest="data_ref")
    extract = commands.add_parser("extrair")
    extract.add_argument("--data", "--data-ref", dest="data_ref", required=True)
    return parser


def _parse_data_ref(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("data-ref deve usar o formato AAAA-MM-DD") from None


def _ptax_window_start(data_ref):
    return data_ref - timedelta(days=PTAX_LOOKBACK_DAYS)


def _new_storage(config: Config):
    return (
        GravadorS3(config, bucket=config.bucket_raw),
        GravadorS3(config, bucket=config.bucket_bronze),
    )


def _load_manifest(raw, reference):
    prefix = f"raw/manifestos/data={reference}/"
    response = raw.client.list_objects_v2(Bucket=raw.bucket, Prefix=prefix)
    objects = response.get("Contents", [])
    if not objects:
        raise FileNotFoundError("Nenhum manifesto encontrado para a data solicitada")
    latest = max(objects, key=lambda item: item["LastModified"])
    stored = raw.client.get_object(Bucket=raw.bucket, Key=latest["Key"])
    body = stored["Body"]
    try:
        content = body.read()
    finally:
        body.close()
    payload = json.loads(content)
    items = [
        ItemManifesto(
            url=item["url"],
            status_http=item["status_http"],
            tentativas=item["tentativas"],
            bytes=item["bytes"],
            estado=item["estado"],
            chave=item["chave"],
            sha256=item["sha256"],
            erro=item["erro"],
        )
        for item in payload.get("itens", [])
    ]
    return Manifesto(
        id=payload["id"],
        data_ref=payload["data_ref"],
        inicio=datetime.fromisoformat(payload["inicio"]),
        fim=payload.get("fim"),
        estado=payload["estado"],
        total_declarado=payload.get("total_declarado"),
        total_extraido=payload.get("total_extraido"),
        sources=payload.get("sources", []),
        escopo=payload.get("escopo", {}),
        robots=payload.get("robots_txt"),
        itens=items,
    )


def run_command(command, data_ref=None):
    from src.collectors.books import ColetorBooks
    from src.collectors.ptax import ColetorPtax
    from src.extractor import Extrator
    from src.http import ClienteHttp
    from src.manifest import create_manifest

    config = load_config()
    raw, bronze = _new_storage(config)
    storage = _PipelineStorage(raw, bronze)
    reference = _parse_data_ref(data_ref) if data_ref is not None else None
    if command == "extrair":
        manifest = _load_manifest(raw, reference.isoformat())
        extractor = Extrator(gravador=storage, manifesto=manifest)
        result = extractor.extrair()
        extractor.publicar(
            result,
            livros_declarados=len(result.livros),
            cotacoes_declaradas=len(result.cotacoes),
        )
        manifest.persistir(raw)
        return manifest.estado

    reference = reference or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    manifest = create_manifest(data_ref=reference)
    manifest.escopo = {
        "tipo": "filtrado" if config.categorias else "completo",
        "categorias": list(config.categorias),
    }
    http = ClienteHttp(
        timeout=config.timeout,
        max_tentativas=config.max_tentativas,
        intervalo_minimo=config.intervalo_minimo,
        user_agent=config.user_agent,
    )
    books = ColetorBooks(
        get=http.get,
        gravador=storage,
        manifesto=manifest,
        categorias=",".join(config.categorias),
        timeout=config.timeout,
        user_agent=config.user_agent,
    )
    books.coletar(reference)
    ptax = ColetorPtax(
        get=http.get_once,
        gravador=storage,
        manifesto=manifest,
        timeout=config.timeout,
        max_attempts=config.max_tentativas,
        user_agent=config.user_agent,
    )
    ptax_result = ptax.coletar(
        data_ref=reference,
        window_start=_ptax_window_start(reference),
    )
    declared_books = sum(len(page.books) for page in books.paginas_coletadas)
    manifest.total_declarado = declared_books + 1
    manifest.total_extraido = len(books.livros_coletados) + (
        1 if ptax_result.quote else 0
    )
    if ptax_result.execution_state == "incompleta":
        manifest.finalizar("incompleta")
    elif manifest.estado not in {"falha", "incompleta"}:
        manifest.finalizar("completa")

    if command == "executar" and manifest.estado != "incompleta":
        extractor = Extrator(gravador=storage, manifesto=manifest)
        result = extractor.extrair()
        extractor.publicar(
            result,
            livros_declarados=declared_books,
            cotacoes_declaradas=1 if ptax_result.quote else 0,
        )
    manifest.persistir(raw)
    return manifest.estado


def main(argv=None, *, command_runner=None, stderr=None):
    output = stderr or sys.stderr
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        data_ref = (
            _parse_data_ref(args.data_ref).isoformat()
            if args.data_ref
            else None
        )
        runner = command_runner or run_command
        state = runner(args.command, data_ref)
    except Exception as error:
        print(f"Falha no comando: {type(error).__name__}", file=output)
        return 1
    if state in {"falha", "incompleta"}:
        print(f"Execução finalizada com estado {state}.", file=output)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
