import hashlib
import json
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import urlencode

from src.config import DEFAULT_HTTP_TIMEOUT
from src.http import get_with_retry
from src.manifest import record_item
from src.models import Cotacao
from src.storage import make_raw_key


PTAX_ENDPOINT = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,"
    "dataFinalCotacao=@dataFinalCotacao)"
)


@dataclass(frozen=True)
class PTAXResult:
    quote: Cotacao | None
    response_body: bytes | None
    execution_state: str
    status_http: int | None = None
    error: str | None = None


def format_ptax_date(value):
    return value.strftime("%m-%d-%Y")


def build_ptax_url(*, window_start, window_end):
    query = urlencode(
        {
            "@moeda": "'GBP'",
            "@dataInicial": f"'{format_ptax_date(window_start)}'",
            "@dataFinalCotacao": f"'{format_ptax_date(window_end)}'",
            "$format": "json",
        }
    )
    return f"{PTAX_ENDPOINT}?{query}"


def _response_status(response):
    return getattr(response, "status_code", getattr(response, "status_http", 0))


def _response_content(response):
    return bytes(getattr(response, "content", getattr(response, "corpo", b"")))


def collect_ptax(
    *,
    data_ref,
    window_start,
    response_body,
    get,
    timeout=DEFAULT_HTTP_TIMEOUT,
    max_attempts=4,
    user_agent="aula_03_api_scraping",
    sleep=time.sleep,
    random_uniform=random.uniform,
):
    status = 200
    if response_body is None:
        url = build_ptax_url(window_start=window_start, window_end=data_ref)
        try:
            response = get_with_retry(
                url,
                get=get,
                timeout=timeout,
                max_attempts=max_attempts,
                headers={"User-Agent": user_agent},
                sleep=sleep,
                random_uniform=random_uniform,
            )
        except (TimeoutError, ConnectionError) as error:
            return PTAXResult(None, None, "falha", error=str(error))
        status = _response_status(response)
        response_body = _response_content(response)
        if not 200 <= status < 300:
            return PTAXResult(
                None,
                response_body,
                "falha",
                status_http=status,
                error=f"Falha HTTP {status} na consulta PTAX",
            )

    try:
        payload = json.loads(response_body)
        values = payload.get("value", [])
        if not isinstance(values, list):
            raise ValueError("campo value inválido")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, ValueError):
        return PTAXResult(
            None,
            response_body,
            "falha",
            status_http=status,
            error="Resposta PTAX inválida",
        )

    eligible = []
    for value in values:
        try:
            bulletin_date = datetime.fromisoformat(value["dataHoraCotacao"]).date()
            if value["tipoBoletim"] == "Fechamento" and bulletin_date <= data_ref:
                eligible.append((bulletin_date, value))
        except (KeyError, TypeError, ValueError):
            continue
    if not eligible:
        return PTAXResult(None, response_body, "incompleta", status_http=status)

    selected = max(eligible, key=lambda item: item[0])[1]
    return Cotacao(
        moeda="GBP",
        dataHoraCotacao=selected["dataHoraCotacao"],
        tipoBoletim=selected["tipoBoletim"],
        cotacaoCompra=float(selected["cotacaoCompra"]),
        cotacaoVenda=float(selected["cotacaoVenda"]),
    )


class ColetorPtax:
    def __init__(
        self,
        *,
        get,
        gravador,
        manifesto,
        timeout=DEFAULT_HTTP_TIMEOUT,
        max_attempts=4,
        user_agent="aula_03_api_scraping",
        sleep=time.sleep,
        random_uniform=random.uniform,
    ):
        self.get = get
        self.gravador = gravador
        self.manifesto = manifesto
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.user_agent = user_agent
        self.sleep = sleep
        self.random_uniform = random_uniform

    def coletar(self, *, data_ref: date, window_start: date) -> PTAXResult:
        self.manifesto.registrar_source("PTAX")
        url = build_ptax_url(window_start=window_start, window_end=data_ref)
        response = get_with_retry(
            url,
            get=self.get,
            timeout=self.timeout,
            max_attempts=self.max_attempts,
            headers={"User-Agent": self.user_agent},
            sleep=self.sleep,
            random_uniform=self.random_uniform,
        )
        status = _response_status(response)
        body = _response_content(response)
        reference = data_ref.isoformat()
        resource = (
            f"moeda=GBP/janela={window_start.isoformat()}_a_{reference}"
        )
        digest = hashlib.sha256(body).hexdigest()
        key = make_raw_key("ptax", reference, resource, body)
        storage_attempts = self.gravador.gravar_raw(
            key,
            body,
            {
                "source-url": url,
                "collected-at": datetime.now(timezone.utc).isoformat(),
                "sha256": digest,
                "currency": "GBP",
            },
        )
        if not 200 <= status < 300:
            result = PTAXResult(
                None,
                body,
                "falha",
                status,
                f"Falha HTTP {status} na consulta PTAX",
            )
        else:
            quote_result = collect_ptax(
                data_ref=data_ref,
                window_start=window_start,
                response_body=body,
                get=self.get,
                timeout=self.timeout,
                max_attempts=self.max_attempts,
                user_agent=self.user_agent,
            )
            result = (
                PTAXResult(quote_result, body, "sucesso", status)
                if isinstance(quote_result, Cotacao)
                else quote_result
            )
        error = result.error
        if result.execution_state == "incompleta" and error is None:
            error = "Nenhum Fechamento elegível na janela PTAX"
        record_item(
            self.manifesto,
            url=url,
            status_http=status,
            attempts=getattr(response, "tentativas", 1)
            + max(1, storage_attempts or 1)
            - 1,
            bytes_received=len(body),
            state="gravado",
            key=key,
            sha256=digest,
            error=error,
        )
        self.manifesto.finalizar(result.execution_state)
        return result
