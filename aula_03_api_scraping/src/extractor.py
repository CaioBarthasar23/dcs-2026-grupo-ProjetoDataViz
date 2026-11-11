import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from botocore.exceptions import BotoCoreError

from src.manifest import record_item
from src.models import Cotacao, Livro, serialize_book, serialize_quote


@dataclass(frozen=True)
class ExtractionResult:
    livros: list[Livro]
    cotacoes: list[Cotacao]


class ExtractionValidation:
    def __init__(self, *, state, difference):
        self.state = state
        self.difference = difference
        self.publishable = state == "sucesso"

    @property
    def execution_state(self):
        return self.state


def _book_listing(html, base_url=""):
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("table.table-striped tr th"):
        return []
    records = []
    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a[href]")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        if not link or not price or not rating:
            continue
        grade = next(
            (value for value in rating.get("class", []) if value != "star-rating"),
            "",
        )
        records.append(
            {
                "url": urljoin(base_url, link.get("href", "")),
                "titulo": link.get("title") or link.get_text(strip=True),
                "avaliacao": grade,
                "preco_gbp": float(
                    price.get_text(strip=True).replace("£", "").replace(",", "")
                ),
            }
        )
    return records


def _book_detail(html, url, listing=None):
    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("div.product_main") or soup
    title = product.select_one("h1")
    price = product.select_one("p.price_color")
    rating = product.select_one("p.star-rating")
    upc = ""
    for row in soup.select("table.table-striped tr"):
        heading, value = row.find("th"), row.find("td")
        if heading and value and heading.get_text(strip=True).lower() == "upc":
            upc = value.get_text(strip=True)
            break
    breadcrumb = soup.select("ul.breadcrumb li a")
    category = breadcrumb[2].get_text(strip=True) if len(breadcrumb) > 2 else ""
    availability = soup.select_one("div.product_main p.availability")
    availability_text = availability.get_text(" ", strip=True) if availability else ""
    quantity = re.search(r"\((\d+)\s+available\)", availability_text)
    record = {
        "upc": upc,
        "url": url,
        "titulo": title.get_text(strip=True) if title else "",
        "categoria": category,
        "avaliacao": (
            next(
                (value for value in rating.get("class", []) if value != "star-rating"),
                "",
            )
            if rating
            else ""
        ),
        "preco_gbp": (
            float(price.get_text(strip=True).replace("£", "").replace(",", ""))
            if price
            else 0.0
        ),
        "em_estoque": "in stock" in availability_text.lower(),
        "qtd_estoque": int(quantity.group(1)) if quantity else None,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
    }
    if listing:
        record.update(
            {
                "url": url or listing.get("url", ""),
                "titulo": listing.get("titulo") or record["titulo"],
                "avaliacao": listing.get("avaliacao") or record["avaliacao"],
                "preco_gbp": listing.get("preco_gbp") or record["preco_gbp"],
            }
        )
    return record


def _read_raw(storage, key):
    reader = getattr(storage, "read_raw", None) or getattr(storage, "ler_raw", None)
    if reader is None:
        raise TypeError("storage deve fornecer ler_raw(chave)")
    body = reader(key)
    if not isinstance(body, bytes):
        raise TypeError("objeto raw precisa ser bytes")
    return body


def extract_books(*, storage, keys, http_get=None, source_urls=None):
    if http_get is not None:
        # Kept only for compatibility; extraction must never invoke this callable.
        if not callable(http_get):
            raise TypeError("http_get deve ser chamável")
    listings = []
    details = []
    for key in keys:
        body = _read_raw(storage, key)
        source_url = (source_urls or {}).get(key, "")
        found = _book_listing(body, source_url)
        if found:
            listings.extend((key, item) for item in found)
            continue
        details.append((key, source_url, body))

    rows = []
    listings_by_url = {
        listing["url"]: listing for _, listing in listings if listing.get("url")
    }
    unused_listings = [listing for _, listing in listings]
    for _, source_url, body in details:
        listing = listings_by_url.get(source_url)
        if listing is None and unused_listings:
            listing = unused_listings.pop(0)
        fields = _book_detail(body, source_url or (listing or {}).get("url", ""), listing)
        rows.append(Livro(**fields))
    return rows


def extract_quotes(*, storage, keys, data_ref=None):
    rows = []
    latest_date = data_ref or date.today()
    for key in keys:
        body = _read_raw(storage, key)
        payload = json.loads(body)
        values = payload.get("value", [])
        currency_match = re.search(r"moeda=([A-Z]{3})", key)
        currency = currency_match.group(1) if currency_match else "GBP"
        eligible = []
        for value in values:
            if value.get("tipoBoletim") != "Fechamento":
                continue
            quote_date = datetime.fromisoformat(value["dataHoraCotacao"]).date()
            if quote_date <= latest_date:
                eligible.append((quote_date, value))
        if eligible:
            value = max(eligible, key=lambda pair: pair[0])[1]
            rows.append(
                Cotacao(
                    moeda=currency,
                    dataHoraCotacao=value["dataHoraCotacao"],
                    tipoBoletim=value["tipoBoletim"],
                    cotacaoCompra=float(value["cotacaoCompra"]),
                    cotacaoVenda=float(value["cotacaoVenda"]),
                )
            )
    return rows


def validate_extraction(*, extracted, declared):
    if extracted < 0 or declared < 0:
        raise ValueError("contagens não podem ser negativas")
    difference = extracted - declared
    return ExtractionValidation(
        state="sucesso" if difference == 0 else "falha",
        difference=difference,
    )


def _register_extraction_failure(manifest, error, result, declared_books, declared_quotes):
    manifest.total_declarado = (
        declared_books + declared_quotes
        if isinstance(declared_books, int) and isinstance(declared_quotes, int)
        else None
    )
    manifest.total_extraido = (
        len(result.livros) + len(result.cotacoes)
        if isinstance(result, ExtractionResult)
        else None
    )
    record_item(
        manifest,
        url="bronze://validacao",
        status_http=None,
        attempts=0,
        bytes_received=0,
        state="falhou",
        error=str(error),
    )
    manifest.finalizar("falha")


class Extrator:
    def __init__(self, *, gravador, manifesto):
        self.gravador = gravador
        self.manifesto = manifesto

    def extrair(self, manifesto=None):
        current_manifest = manifesto or self.manifesto
        items = [
            item
            for item in current_manifest.itens
            if item.estado == "gravado" and item.chave and "robots.txt" not in item.url
        ]
        book_items = [
            item for item in items if "bcb.gov.br" not in item.url.lower()
        ]
        quote_items = [
            item for item in items if "bcb.gov.br" in item.url.lower()
        ]
        books = extract_books(
            storage=self.gravador,
            keys=[item.chave for item in book_items],
            source_urls={item.chave: item.url for item in book_items},
        )
        reference = current_manifest.data_ref
        if isinstance(reference, str):
            reference = date.fromisoformat(reference)
        quotes = extract_quotes(
            storage=self.gravador,
            keys=[item.chave for item in quote_items],
            data_ref=reference,
        )
        return ExtractionResult(livros=books, cotacoes=quotes)

    def publicar(
        self,
        result: ExtractionResult,
        *,
        livros_declarados: int,
        cotacoes_declaradas: int,
    ) -> ExtractionValidation:
        try:
            if not isinstance(result, ExtractionResult):
                raise TypeError("resultado de extração inválido")
            for name, count in (
                ("livros_declarados", livros_declarados),
                ("cotacoes_declaradas", cotacoes_declaradas),
            ):
                if not isinstance(count, int) or count < 0:
                    raise ValueError(f"{name} deve ser inteiro não negativo")
            if len(result.livros) != livros_declarados:
                raise ValueError("divergência de contagem de livros")
            if len(result.cotacoes) != cotacoes_declaradas:
                raise ValueError("divergência de contagem de cotações")

            book_lines = []
            for book in result.livros:
                fields = serialize_book(book)
                if (
                    not fields["upc"]
                    or not fields["url"]
                    or not fields["titulo"]
                    or not isinstance(fields["preco_gbp"], (int, float))
                    or not isinstance(fields["em_estoque"], bool)
                    or (
                        fields["qtd_estoque"] is not None
                        and not isinstance(fields["qtd_estoque"], int)
                    )
                ):
                    raise ValueError("campos de livro inválidos")
                book_lines.append(book.para_json())

            quote_lines = []
            for quote in result.cotacoes:
                fields = serialize_quote(quote)
                if (
                    not fields["moeda"]
                    or not fields["dataHoraCotacao"]
                    or fields["tipoBoletim"] != "Fechamento"
                    or not isinstance(fields["cotacaoCompra"], (int, float))
                    or not isinstance(fields["cotacaoVenda"], (int, float))
                ):
                    raise ValueError("campos de cotação inválidos")
                quote_lines.append(quote.para_json())
        except (TypeError, ValueError, KeyError, AttributeError) as error:
            _register_extraction_failure(
                self.manifesto,
                error,
                result,
                livros_declarados,
                cotacoes_declaradas,
            )
            raise ValueError(f"Falha ao validar extração: {error}") from error

        reference = current_manifest_date(self.manifesto.data_ref)
        try:
            self.gravador.gravar_bronze(
                f"bronze/livros/data={reference}/livros.jsonl",
                book_lines,
            )
            self.gravador.gravar_bronze(
                f"bronze/cotacoes/data={reference}/cotacoes.jsonl",
                quote_lines,
            )
        except (BotoCoreError, OSError, RuntimeError, TypeError, ValueError) as error:
            _register_extraction_failure(
                self.manifesto,
                error,
                result,
                livros_declarados,
                cotacoes_declaradas,
            )
            raise
        self.manifesto.total_declarado = livros_declarados + cotacoes_declaradas
        self.manifesto.total_extraido = len(result.livros) + len(result.cotacoes)
        self.manifesto.finalizar("sucesso")
        return ExtractionValidation(state="sucesso", difference=0)


def current_manifest_date(value):
    return value.isoformat() if isinstance(value, date) else str(value)
