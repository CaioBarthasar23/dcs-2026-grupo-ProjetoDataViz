"""Silver: transforma o bruto em Parquet tipado, validado com Pydantic.

A silver e derivada: pode ser apagada e reconstruida a partir do bruto com um
unico comando (o bruto em raw/ nunca e alterado):

    python -m src.silver rebuild --fonte s3 --destino s3
    python -m src.silver rebuild --fonte local --destino local   # teste sem rede

Contrato comum da turma (nomes e tipos nao mudam; colunas extras sao permitidas):
    colecao       group_id INTEGER, nome, sigla, data_lancamento DATE, responsavel
    produto       product_id INTEGER, group_id INTEGER, nome, tipo_produto, raridade,
                  numero, image_url, url            (+ categoria_selado, extra)
    preco_diario  data DATE, product_id, group_id, acabamento, market_price DOUBLE,
                  low_price, mid_price, high_price, moeda, fonte, chave_raw
    cambio_diario data DATE, cotacao_compra, cotacao_venda, data_hora_cotacao TIMESTAMP,
                  boletim, chave_raw
    cdi_diario    data DATE, taxa_dia DOUBLE (% ao dia, como publicada), chave_raw

Regras: nulo nao e zero; registro invalido vai para quarentena/ com o motivo.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.collector import GROUP_ID, LOCAL_ROOT, get_s3

log = logging.getLogger("silver")

SIGLA = os.getenv("SIGLA", "SSP")
COLECAO_NOME = os.getenv("COLECAO_NOME", "SV08: Surging Sparks")
DATA_LANCAMENTO = date.fromisoformat(os.getenv("DATA_LANCAMENTO", "2024-11-08"))
RESPONSAVEL = os.getenv("RESPONSAVEL", "CaioBarthasar23")
MOEDA = "USD"
FONTE_PRECO = "tcgplayer"


# --------------------------------------------------------------------------
# Modelos Pydantic (modo estrito: preco como texto NAO e convertido, vai para quarentena)
# --------------------------------------------------------------------------
class _Base(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Colecao(_Base):
    group_id: int
    nome: str = Field(min_length=1)
    sigla: str = Field(min_length=1)
    data_lancamento: date
    responsavel: str = Field(min_length=1)


class Produto(_Base):
    product_id: int = Field(gt=0)
    group_id: int
    nome: str = Field(min_length=1)
    tipo_produto: Literal["carta", "selado"]
    raridade: Optional[str] = None
    numero: Optional[str] = None
    image_url: str = Field(min_length=1)
    url: str = Field(min_length=1)
    categoria_selado: Optional[str] = None


class PrecoDiario(_Base):
    data: date
    product_id: int = Field(gt=0)
    group_id: int
    acabamento: str = Field(min_length=1)
    market_price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    low_price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    mid_price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    high_price: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    moeda: Literal["USD"]
    fonte: str = Field(min_length=1)
    chave_raw: str = Field(min_length=1)


class CambioDiario(_Base):
    data: date
    cotacao_compra: float = Field(gt=0, allow_inf_nan=False)
    cotacao_venda: float = Field(gt=0, allow_inf_nan=False)
    data_hora_cotacao: datetime
    boletim: Literal["Fechamento"]
    chave_raw: str = Field(min_length=1)


class CdiDiario(_Base):
    data: date
    taxa_dia: float = Field(ge=0, allow_inf_nan=False)
    chave_raw: str = Field(min_length=1)


# --------------------------------------------------------------------------
# Transformacoes (bruto -> dicionarios para os modelos)
# --------------------------------------------------------------------------
def _ext(produto: dict, nome: str) -> Optional[str]:
    """Valor de extendedData[nome]; vazio vira None."""
    for e in produto.get("extendedData") or []:
        if e.get("name") == nome:
            v = e.get("value")
            if isinstance(v, str):
                v = v.strip()
            return v or None
    return None


def classificar(produto: dict) -> str:
    """'carta' se tem numero; Code Card tambem e carta (sem numero), excluida por raridade."""
    if _ext(produto, "Number"):
        return "carta"
    if _ext(produto, "Rarity") == "Code Card":
        return "carta"
    return "selado"


def categoria_selado(nome: str) -> str:
    n = nome.lower()
    caixa = bool(re.search(r"\bcase\b", n))
    if "half booster box" in n:
        return "half_booster_box"
    if "booster box" in n:
        return "booster_box_case" if caixa else "booster_box"
    if "elite trainer box" in n:
        return "elite_trainer_box_case" if caixa else "elite_trainer_box"
    if "booster bundle" in n:
        return "booster_bundle_case" if caixa else "booster_bundle"
    if "booster pack art bundle" in n or "booster pack bundle" in n:
        return "booster_pack_bundle"
    if "booster pack" in n:
        return "booster_pack_case" if caixa else "booster_pack"
    if "blister" in n:
        return "blister_case" if caixa else "blister"
    if "build & battle box display" in n or "build and battle box display" in n:
        return "build_and_battle_box_display"
    if "build & battle box" in n or "build and battle box" in n:
        return "build_and_battle_box"
    if "fun pack" in n:
        return "fun_pack"
    return "outro"


def montar_produto(p: dict) -> dict:
    tipo = classificar(p)
    nome = p.get("name")
    return dict(
        product_id=p.get("productId"),
        group_id=p.get("groupId"),
        nome=nome,
        tipo_produto=tipo,
        raridade=_ext(p, "Rarity"),
        numero=_ext(p, "Number"),
        image_url=p.get("imageUrl"),
        url=p.get("url"),
        categoria_selado=categoria_selado(nome) if tipo == "selado" and nome else None,
    )


def montar_preco(q: dict, dia: date, group_id: int, chave: str) -> dict:
    return dict(
        data=dia,
        product_id=q.get("productId"),
        group_id=group_id,
        acabamento=q.get("subTypeName"),
        market_price=q.get("marketPrice"),
        low_price=q.get("lowPrice"),
        mid_price=q.get("midPrice"),
        high_price=q.get("highPrice"),
        moeda=MOEDA,
        fonte=FONTE_PRECO,
        chave_raw=chave,
    )


def _parse_dt(s: Any) -> Optional[datetime]:
    if s is None:
        return None
    return datetime.fromisoformat(str(s).replace(" ", "T"))


def montar_cambio(dia: date, payload: dict, chave: str) -> tuple[Optional[dict], Optional[str]]:
    """(registro, motivo). Sem registro e sem motivo = sem boletim no dia (fim de semana, feriado)."""
    valores = payload.get("value") or []
    if not valores:
        return None, None
    fech = [v for v in valores if "fechamento" in str(v.get("tipoBoletim", "")).lower()]
    if not fech:
        tipos = [str(v.get("tipoBoletim")) for v in valores]
        return None, f"sem boletim de fechamento (tipos: {tipos})"
    v = max(fech, key=lambda x: str(x.get("dataHoraCotacao")))
    return (
        dict(
            data=dia,
            cotacao_compra=v.get("cotacaoCompra"),
            cotacao_venda=v.get("cotacaoVenda"),
            data_hora_cotacao=_parse_dt(v.get("dataHoraCotacao")),
            boletim="Fechamento",  # a API devolve "Fechamento PTAX"; o contrato pede "Fechamento"
            chave_raw=chave,
        ),
        None,
    )


def montar_cdi(r: dict, chave: str) -> dict:
    return dict(
        data=datetime.strptime(r["data"], "%d/%m/%Y").date(),
        taxa_dia=float(str(r["valor"]).replace(",", ".")),
        chave_raw=chave,
    )


# --------------------------------------------------------------------------
# Leitura/escrita: disco local ou S3
# --------------------------------------------------------------------------
class LocalLake:
    def __init__(self, root: Path):
        self.root = Path(root)

    def get(self, key: str) -> Optional[bytes]:
        p = self.root / key
        return p.read_bytes() if p.exists() else None

    def put(self, key: str, data: bytes) -> None:  # silver e derivada: pode sobrescrever
        p = self.root / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def datas(self, prefix: str) -> list[date]:
        d = self.root / prefix
        if not d.exists():
            return []
        return _parse_datas(x.name for x in d.iterdir() if x.is_dir())


class S3Lake:
    def __init__(self, s3):
        self.s3 = s3

    def get(self, key: str) -> Optional[bytes]:
        from botocore.exceptions import ClientError

        try:
            return self.s3.client.get_object(Bucket=self.s3.bucket, Key=key)["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404", "NotFound"):
                return None
            raise

    def put(self, key: str, data: bytes) -> None:
        self.s3.client.put_object(Bucket=self.s3.bucket, Key=key, Body=data)

    def datas(self, prefix: str) -> list[date]:
        return _parse_datas(p.rstrip("/").split("/")[-1] for p in self.s3.prefixes(prefix))


def _parse_datas(nomes) -> list[date]:
    out = []
    for n in nomes:
        if n.startswith("data="):
            try:
                out.append(date.fromisoformat(n[5:]))
            except ValueError:
                log.warning("pasta ignorada (data invalida): %s", n)
    return sorted(out)


def make_lake(tipo: str):
    return S3Lake(get_s3()) if tipo == "s3" else LocalLake(LOCAL_ROOT)


# --------------------------------------------------------------------------
# Escrita do Parquet (isolada: precisa de pyarrow)
# --------------------------------------------------------------------------
def _schemas(pa) -> dict:
    s, i32, f64, d32 = pa.string(), pa.int32(), pa.float64(), pa.date32()
    return {
        "colecao": pa.schema(
            [("group_id", i32), ("nome", s), ("sigla", s), ("data_lancamento", d32), ("responsavel", s)]
        ),
        "produto": pa.schema(
            [
                ("product_id", i32), ("group_id", i32), ("nome", s), ("tipo_produto", s),
                ("raridade", s), ("numero", s), ("image_url", s), ("url", s),
                ("categoria_selado", s),
            ]
        ),
        "preco_diario": pa.schema(
            [
                ("data", d32), ("product_id", i32), ("group_id", i32), ("acabamento", s),
                ("market_price", f64), ("low_price", f64), ("mid_price", f64),
                ("high_price", f64), ("moeda", s), ("fonte", s), ("chave_raw", s),
            ]
        ),
        "cambio_diario": pa.schema(
            [
                ("data", d32), ("cotacao_compra", f64), ("cotacao_venda", f64),
                ("data_hora_cotacao", pa.timestamp("us")), ("boletim", s), ("chave_raw", s),
            ]
        ),
        "cdi_diario": pa.schema([("data", d32), ("taxa_dia", f64), ("chave_raw", s)]),
    }


def escrever_parquet(lake, key: str, tabela: str, registros: list[dict]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = _schemas(pa)[tabela]
    tabela_pa = pa.Table.from_pylist(registros, schema=schema)
    buf = io.BytesIO()
    pq.write_table(tabela_pa, buf, compression="snappy")
    lake.put(key, buf.getvalue())


Writer = Callable[[Any, str, str, list], None]


# --------------------------------------------------------------------------
# Reconstrucao completa
# --------------------------------------------------------------------------
def _motivo(e: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())


class _Tab:
    """Contagem e quarentena de uma tabela."""

    def __init__(self, nome: str):
        self.nome = nome
        self.lidos = 0
        self.validos = 0
        self.quarentena: dict[date, list[dict]] = {}

    def rejeitar(self, dia: date, motivo: str, registro: Any) -> None:
        self.quarentena.setdefault(dia, []).append(
            {"tabela": self.nome, "motivo": motivo, "registro": registro}
        )

    @property
    def n_quarentena(self) -> int:
        return sum(len(v) for v in self.quarentena.values())


def _validar(modelo, dados: dict, tab: _Tab, dia: date, original: Any):
    tab.lidos += 1
    try:
        obj = modelo(**dados)
    except ValidationError as e:
        tab.rejeitar(dia, _motivo(e), original)
        return None
    tab.validos += 1
    return obj


def _json(lake, key: str, tab: _Tab, dia: date):
    raw = lake.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except ValueError as e:
        tab.rejeitar(dia, f"arquivo bruto nao e JSON valido: {e}", {"chave_raw": key})
        log.error("JSON invalido em %s", key)
        return None


def rebuild(
    fonte, destino, writer: Writer = escrever_parquet, group_id: int = GROUP_ID
) -> dict[str, dict[str, int]]:
    gid = group_id
    tabs = {n: _Tab(n) for n in ("colecao", "produto", "preco_diario", "cambio_diario", "cdi_diario")}

    def gravar(tabela: str, key: str, objs: list) -> None:
        writer(destino, key, tabela, [o.model_dump() for o in objs])

    # colecao
    t = tabs["colecao"]
    col = _validar(
        Colecao,
        dict(group_id=gid, nome=COLECAO_NOME, sigla=SIGLA,
             data_lancamento=DATA_LANCAMENTO, responsavel=RESPONSAVEL),
        t, date.today(), {"group_id": gid},
    )
    if col:
        gravar("colecao", f"silver/colecao/group_id={gid}/colecao.parquet", [col])

    # produtos e precos (dia a dia, em ordem; produto do dia mais recente prevalece)
    tp, tq = tabs["produto"], tabs["preco_diario"]
    produtos: dict[int, Produto] = {}
    for dia in fonte.datas(f"raw/tcgplayer/group_id={gid}/"):
        base = f"raw/tcgplayer/group_id={gid}/data={dia.isoformat()}"
        kp, kq = f"{base}/products.json", f"{base}/prices.json"

        dp = _json(fonte, kp, tp, dia)
        if dp is not None:
            if not dp.get("success") or not isinstance(dp.get("results"), list):
                tp.rejeitar(dia, "resposta do TCGCSV sem success/results", {"chave_raw": kp})
            else:
                for p in dp["results"]:
                    try:
                        dados = montar_produto(p)
                    except (AttributeError, TypeError) as e:
                        tp.lidos += 1
                        tp.rejeitar(dia, f"registro ilegivel: {e}", p)
                        continue
                    obj = _validar(Produto, dados, tp, dia, p)
                    if obj is None:
                        continue
                    if obj.group_id != gid:
                        tp.validos -= 1
                        tp.rejeitar(dia, f"groupId {obj.group_id} diferente de {gid}", p)
                        continue
                    produtos[obj.product_id] = obj

        dq = _json(fonte, kq, tq, dia)
        if dq is None:
            if fonte.get(kq) is None:
                log.warning("sem prices.json em %s: dia nao entra na silver", dia)
            continue
        if not dq.get("success") or not isinstance(dq.get("results"), list):
            tq.rejeitar(dia, "resposta do TCGCSV sem success/results", {"chave_raw": kq})
            continue
        validos: dict[tuple[int, str], PrecoDiario] = {}
        for q in dq["results"]:
            try:
                dados = montar_preco(q, dia, gid, kq)
            except (AttributeError, TypeError) as e:
                tq.lidos += 1
                tq.rejeitar(dia, f"registro ilegivel: {e}", q)
                continue
            obj = _validar(PrecoDiario, dados, tq, dia, q)
            if obj is None:
                continue
            if obj.product_id not in produtos:
                tq.validos -= 1
                tq.rejeitar(dia, "product_id sem produto correspondente", q)
                continue
            chave = (obj.product_id, obj.acabamento)
            if chave in validos:
                tq.validos -= 1
                tq.rejeitar(dia, "duplicado (product_id, acabamento) no mesmo dia", q)
                continue
            validos[chave] = obj
        if validos:
            ordenados = [validos[k] for k in sorted(validos)]
            gravar("preco_diario",
                   f"silver/preco_diario/group_id={gid}/data={dia.isoformat()}/preco.parquet",
                   ordenados)

    if produtos:
        gravar("produto", f"silver/produto/group_id={gid}/produto.parquet",
               [produtos[k] for k in sorted(produtos)])

    # cambio (PTAX)
    tc = tabs["cambio_diario"]
    cambios: list[CambioDiario] = []
    for dia in fonte.datas(f"raw/bcb_ptax/group_id={gid}/"):
        key = f"raw/bcb_ptax/group_id={gid}/data={dia.isoformat()}/cotacao.json"
        payload = _json(fonte, key, tc, dia)
        if payload is None:
            continue
        try:
            dados, motivo = montar_cambio(dia, payload, key)
        except (AttributeError, TypeError, ValueError) as e:
            tc.lidos += 1
            tc.rejeitar(dia, f"registro ilegivel: {e}", {"chave_raw": key})
            continue
        if motivo:
            tc.lidos += 1
            tc.rejeitar(dia, motivo, {"chave_raw": key})
            continue
        if dados is None:  # sem boletim no dia: nao ha linha, e isso e esperado
            continue
        obj = _validar(CambioDiario, dados, tc, dia, {"chave_raw": key})
        if obj:
            cambios.append(obj)
    if cambios:
        gravar("cambio_diario", f"silver/cambio_diario/group_id={gid}/cambio.parquet",
               sorted(cambios, key=lambda c: c.data))

    # cdi (janelas que se sobrepõem: vale a primeira vez que a data apareceu)
    td = tabs["cdi_diario"]
    cdi: dict[date, CdiDiario] = {}
    divergentes = 0
    for dia in fonte.datas(f"raw/bcb_cdi/group_id={gid}/"):
        key = f"raw/bcb_cdi/group_id={gid}/data={dia.isoformat()}/cdi.json"
        payload = _json(fonte, key, td, dia)
        if payload is None:
            continue
        if not isinstance(payload, list):
            td.rejeitar(dia, "resposta do SGS nao e uma lista", {"chave_raw": key})
            continue
        for r in payload:
            try:
                dados = montar_cdi(r, key)
            except (KeyError, TypeError, ValueError) as e:
                td.lidos += 1
                td.rejeitar(dia, f"registro ilegivel: {e}", r)
                continue
            obj = _validar(CdiDiario, dados, td, dia, r)
            if obj is None:
                continue
            antigo = cdi.get(obj.data)
            if antigo is None:
                cdi[obj.data] = obj
            elif antigo.taxa_dia != obj.taxa_dia:
                divergentes += 1
    if divergentes:
        log.warning("cdi: %d datas com valor diferente entre janelas (mantida a primeira)", divergentes)
    if cdi:
        gravar("cdi_diario", f"silver/cdi_diario/group_id={gid}/cdi.parquet",
               [cdi[k] for k in sorted(cdi)])

    # quarentena
    for tab in tabs.values():
        for dia, regs in sorted(tab.quarentena.items()):
            corpo = "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in regs) + "\n"
            destino.put(
                f"quarentena/{tab.nome}/group_id={gid}/data={dia.isoformat()}/registros.jsonl",
                corpo.encode("utf-8"),
            )

    resumo = {
        n: {"lidos": t.lidos, "validos": t.validos, "quarentena": t.n_quarentena}
        for n, t in tabs.items()
    }
    for n, r in resumo.items():
        log.info("%-14s lidos=%d validos=%d quarentena=%d", n, r["lidos"], r["validos"], r["quarentena"])
    return resumo


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout
    )
    padrao = os.getenv("STORAGE", "local").lower()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("comando", choices=["rebuild"])
    ap.add_argument("--fonte", choices=["local", "s3"], default=padrao, help="de onde ler o bruto")
    ap.add_argument("--destino", choices=["local", "s3"], default=padrao, help="onde gravar a silver")
    args = ap.parse_args(argv)
    log.info("rebuild: fonte=%s destino=%s group_id=%d", args.fonte, args.destino, GROUP_ID)
    rebuild(make_lake(args.fonte), make_lake(args.destino))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
