"""Coletor diario da colecao SSP (SV08: Surging Sparks, groupId 23651).

Comandos:
    python -m src.collector collect   # coleta o dia e grava o bruto (idempotente)
    python -m src.collector upload    # sobe o bruto local para o MinIO, sem sobrescrever
    python -m src.collector check     # lista as colecoes ja ocupadas no MinIO

Regras do bruto: nenhum objeto em raw/ e sobrescrito ou apagado; antes de
gravar, o coletor confere se a chave ja existe.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

import requests
from src.prefixo import PREFIXO_PROPRIO, validar_chave

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv e opcional
    pass

GROUP_ID = int(os.getenv("GROUP_ID", "23651"))
CATEGORY_ID = 3  # Pokemon
TZ = ZoneInfo("America/Sao_Paulo")
USER_AGENT = os.getenv("USER_AGENT", "colecao-ssp/1.0")
PAUSE_SECONDS = 0.15  # o TCGCSV pede no minimo 100 ms entre chamadas
BUCKET = os.getenv("S3_BUCKET", "tcg")
LOCAL_ROOT = Path(os.getenv("LOCAL_ROOT", "data_local"))
# Apos esta hora (Brasilia) uma resposta vazia da PTAX significa "sem boletim"
# (fim de semana ou feriado) e nao "boletim ainda nao publicado".
PTAX_HORA_CORTE = 15
# O TCGCSV atualiza por volta de 20h UTC (17h de Brasilia). Antes disso o
# arquivo ainda tem os precos do dia anterior, e grava-los com a data de hoje
# poluiria a serie (e a coleta correta cairia em "ja existia").
TCGCSV_HORA_MIN_BRT = 18

TCGCSV_BASE = f"https://tcgcsv.com/tcgplayer/{CATEGORY_ID}"
PTAX_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)"
    "?@moeda='USD'&@dataCotacao='{mdY}'&$format=json"
)
CDI_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
    "?formato=json&dataInicial={ini}&dataFinal={fim}"
)
CDI_JANELA_DIAS = 10

log = logging.getLogger("coletor")


# --------------------------------------------------------------------------
# Armazenamento
# --------------------------------------------------------------------------
class Storage(Protocol):
    def exists(self, key: str) -> bool: ...
    def put(self, key: str, data: bytes) -> None: ...


class LocalStorage:
    def __init__(self, root: Path):
        self.root = Path(root)

    def exists(self, key: str) -> bool:
        validar_chave(key)
        return (self.root / key).exists()

    def put(self, key: str, data: bytes) -> None:
        validar_chave(key)
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as f:  # "x": falha se o arquivo ja existir
            f.write(data)


class S3Storage:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=os.getenv("S3_REGION", "us-east-1"),
            # RustFS/MinIO: endereco em estilo path (https://host/bucket/chave)
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def exists(self, key: str) -> bool:
        validar_chave(key)
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def put(self, key: str, data: bytes) -> None:
        validar_chave(key)
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data, ContentType="application/json"
        )

    def prefixes(self, prefix: str) -> list[str]:
        out, token = [], None
        while True:
            kw = dict(Bucket=self.bucket, Prefix=prefix, Delimiter="/")
            if token:
                kw["ContinuationToken"] = token
            resp = self.client.list_objects_v2(**kw)
            out += [p["Prefix"] for p in resp.get("CommonPrefixes", [])]
            if not resp.get("IsTruncated"):
                return out
            token = resp["NextContinuationToken"]


def get_s3() -> S3Storage:
    endpoint = os.getenv("S3_ENDPOINT")
    if not endpoint:
        raise SystemExit("Defina S3_ENDPOINT, S3_ACCESS_KEY e S3_SECRET_KEY no .env")
    return S3Storage(
        endpoint,
        os.environ["S3_ACCESS_KEY"],
        os.environ["S3_SECRET_KEY"],
        BUCKET,
    )


def get_storage() -> Storage:
    mode = os.getenv("STORAGE", "local").lower()
    if mode == "s3":
        return get_s3()
    return LocalStorage(LOCAL_ROOT)


# --------------------------------------------------------------------------
# Chaves do bruto
# --------------------------------------------------------------------------
def key_tcg(d: date, nome: str) -> str:
    return f"raw/tcgplayer/group_id={GROUP_ID}/data={d.isoformat()}/{nome}.json"


def key_ptax(d: date) -> str:
    return f"raw/bcb_ptax/group_id={GROUP_ID}/data={d.isoformat()}/cotacao.json"


def key_cdi(d: date) -> str:
    return f"raw/bcb_cdi/group_id={GROUP_ID}/data={d.isoformat()}/cdi.json"


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT
_last_call = 0.0


def http_get(url: str, tentativas: int = 3) -> requests.Response:
    """GET com pausa minima entre chamadas e novas tentativas."""
    global _last_call
    ultimo_erro: Exception | None = None
    for i in range(tentativas):
        espera = PAUSE_SECONDS - (time.monotonic() - _last_call)
        if espera > 0:
            time.sleep(espera)
        try:
            resp = _session.get(url, timeout=30)
            _last_call = time.monotonic()
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            _last_call = time.monotonic()
            ultimo_erro = e
            log.warning("falha em %s (tentativa %d/%d): %s", url, i + 1, tentativas, e)
            time.sleep(2**i)
    raise RuntimeError(f"nao foi possivel obter {url}: {ultimo_erro}")


# --------------------------------------------------------------------------
# Validacoes leves (o bruto e gravado como veio; aqui so evitamos gravar lixo)
# --------------------------------------------------------------------------
def tcg_ok(resp: requests.Response) -> bool:
    body = resp.json()
    return bool(body.get("success")) and len(body.get("results") or []) > 0


def ptax_tipos(resp: requests.Response) -> list[str]:
    valores = resp.json().get("value") or []
    return [str(v.get("tipoBoletim")) for v in valores]


def ptax_tem_fechamento(resp: requests.Response) -> bool:
    # tolerante ao texto exato ("Fechamento", "Fechamento PTAX", ...)
    return any("fechamento" in t.lower() for t in ptax_tipos(resp))


def ptax_vazia(resp: requests.Response) -> bool:
    return not (resp.json().get("value") or [])


def cdi_ok(resp: requests.Response) -> bool:
    dados = resp.json()
    return isinstance(dados, list) and len(dados) > 0


# --------------------------------------------------------------------------
# Coleta
# --------------------------------------------------------------------------
def gravar(storage: Storage, key: str, resp: requests.Response) -> str:
    """Grava o corpo original da resposta, sem alteracao, se a chave nao existir."""
    validar_chave(key)
    if storage.exists(key):
        return "ja existia"
    storage.put(key, resp.content)
    return "gravado"


def coletar_ptax(storage: Storage, dia: date, apos_corte: bool) -> str:
    """Grava a PTAX de `dia` (todos os boletins), sem sobrescrever.

    apos_corte: True quando ja passou da hora em que o fechamento deveria existir
    (ou quando `dia` ja passou). Nesse caso uma resposta vazia significa "sem
    boletim" (fim de semana ou feriado) e e gravada como tal.
    """
    key = key_ptax(dia)
    try:
        validar_chave(key)
        if storage.exists(key):
            return "ja existia"
        resp = http_get(PTAX_URL.format(mdY=dia.strftime("%m-%d-%Y")))
        if ptax_tem_fechamento(resp):
            return gravar(storage, key, resp)
        if ptax_vazia(resp) and apos_corte:
            return gravar(storage, key, resp) + " (sem boletim no dia)"
        if ptax_vazia(resp):
            return "ignorado: fechamento ainda nao publicado, rode de novo"
        return f"ignorado: resposta sem boletim de fechamento (tipos: {ptax_tipos(resp)})"
    except Exception as e:  # noqa: BLE001
        return f"ERRO: {e}"


def backfill_ptax(storage: Storage, de: date, ate: date) -> dict[str, str]:
    """Coleta retroativa da PTAX de dias passados (a PTAX e um registro publico por data)."""
    out: dict[str, str] = {}
    d = de
    while d <= ate:
        out[key_ptax(d)] = coletar_ptax(storage, d, True)
        d += timedelta(days=1)
    return out


def coletar(
    storage: Storage, agora: datetime | None = None, forcar: bool = False
) -> dict[str, str]:
    """Coleta o dia. Cada fonte e independente: falha em uma nao impede as outras."""
    agora = agora or datetime.now(TZ)
    hoje = agora.date()
    resultado: dict[str, str] = {}

    # 1) TCGCSV: produtos e precos (a data do preco e a da coleta, entao so hoje)
    for nome in ("products", "prices"):
        key = key_tcg(hoje, nome)
        try:
            validar_chave(key)
            if storage.exists(key):
                resultado[key] = "ja existia"
                continue
            if agora.hour < TCGCSV_HORA_MIN_BRT and not forcar:
                resultado[key] = (
                    f"ignorado: TCGCSV atualiza ~17h BRT, rode depois das {TCGCSV_HORA_MIN_BRT}h"
                )
                continue
            resp = http_get(f"{TCGCSV_BASE}/{GROUP_ID}/{nome}")
            if not tcg_ok(resp):
                resultado[key] = "ignorado: resposta sem resultados"
                continue
            resultado[key] = gravar(storage, key, resp)
        except Exception as e:  # noqa: BLE001
            resultado[key] = f"ERRO: {e}"

    # 2) PTAX do dia (todos os boletins)
    resultado[key_ptax(hoje)] = coletar_ptax(storage, hoje, agora.hour >= PTAX_HORA_CORTE)

    # 3) CDI: janela dos ultimos dias (a taxa de um dia util sai na manha seguinte)
    key = key_cdi(hoje)
    try:
        validar_chave(key)
        if storage.exists(key):
            resultado[key] = "ja existia"
        else:
            ini = (hoje - timedelta(days=CDI_JANELA_DIAS)).strftime("%d/%m/%Y")
            fim = hoje.strftime("%d/%m/%Y")
            resp = http_get(CDI_URL.format(ini=ini, fim=fim))
            if cdi_ok(resp):
                resultado[key] = gravar(storage, key, resp)
            else:
                resultado[key] = "ignorado: janela sem taxas"
    except Exception as e:  # noqa: BLE001
        resultado[key] = f"ERRO: {e}"

    return resultado


# --------------------------------------------------------------------------
# Upload do bruto local para o MinIO (sem sobrescrever)
# --------------------------------------------------------------------------
def subir_local(local: LocalStorage, s3: Storage) -> dict[str, int]:
    contagem = {"enviados": 0, "ja_existiam": 0}
    raiz = local.root / "raw"
    if not raiz.exists():
        log.warning("nada para subir em %s", raiz)
        return contagem
    for arq in sorted(p for p in raiz.rglob("*") if p.is_file()):
        key = arq.relative_to(local.root).as_posix()
        validar_chave(key)
        if s3.exists(key):
            contagem["ja_existiam"] += 1
            continue
        s3.put(key, arq.read_bytes())
        contagem["enviados"] += 1
        log.info("enviado %s", key)
    return contagem


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout
    )
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("comando", choices=["collect", "upload", "check", "backfill-ptax"])
    ap.add_argument("--de", default=None, help="backfill-ptax: primeira data (AAAA-MM-DD)")
    ap.add_argument("--ate", default=None, help="backfill-ptax: ultima data (AAAA-MM-DD)")
    ap.add_argument(
        "--forcar",
        action="store_true",
        help="ignora a trava de horario do TCGCSV (so para testar; NAO use na serie real)",
    )
    ap.add_argument(
        "--origem",
        default=None,
        help="upload: pasta que contem 'raw/' (padrao: LOCAL_ROOT). Ex.: um artifact extraido",
    )
    args = ap.parse_args(argv)

    group_id_configurado = os.getenv("GROUP_ID", "23651")
    try:
        group_id_numerico = int(group_id_configurado)
    except ValueError:
        log.error(
            "ERRO escrita recusada: GROUP_ID=%s inválido; prefixo permitido %s",
            group_id_configurado,
            PREFIXO_PROPRIO,
        )
        return 1
    if group_id_numerico != 23651 or GROUP_ID != 23651:
        log.error(
            "ERRO escrita recusada: GROUP_ID=%s fora do prefixo %s",
            group_id_configurado,
            PREFIXO_PROPRIO,
        )
        return 1

    if args.comando == "collect":
        res = coletar(get_storage(), forcar=args.forcar)
        for k, v in res.items():
            log.info("%-70s %s", k, v)
        erros = [k for k, v in res.items() if v.startswith("ERRO")]
        return 1 if erros else 0

    if args.comando == "backfill-ptax":
        if not (args.de and args.ate):
            raise SystemExit("use --de AAAA-MM-DD --ate AAAA-MM-DD")
        de, ate = date.fromisoformat(args.de), date.fromisoformat(args.ate)
        if ate >= datetime.now(TZ).date():
            raise SystemExit("--ate precisa ser anterior a hoje (o dia de hoje e coletado pelo 'collect')")
        res = backfill_ptax(get_storage(), de, ate)
        for k, v in res.items():
            log.info("%-70s %s", k, v)
        return 1 if any(v.startswith("ERRO") for v in res.values()) else 0

    if args.comando == "upload":
        origem = Path(args.origem) if args.origem else LOCAL_ROOT
        if not (origem / "raw").exists():
            raise SystemExit(f"nao existe a pasta 'raw' em {origem}")
        log.info("subindo de %s", origem)
        try:
            c = subir_local(LocalStorage(origem), get_s3())
        except ValueError as e:
            log.error("%s", e)
            return 1
        log.info("enviados=%d ja_existiam=%d", c["enviados"], c["ja_existiam"])
        return 0

    if args.comando == "check":
        pref = get_s3().prefixes("raw/tcgplayer/")
        for p in pref:
            log.info("ocupada: %s", p)
        mine = f"raw/tcgplayer/group_id={GROUP_ID}/"
        if mine in pref:
            log.info("group_id=%d ja tem dados (confira se foram seus)", GROUP_ID)
        else:
            log.info("group_id=%d esta livre", GROUP_ID)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
