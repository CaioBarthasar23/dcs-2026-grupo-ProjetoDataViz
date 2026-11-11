import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from src.config import DEFAULT_HTTP_TIMEOUT
from src.http import get_with_timeout
from src.manifest import record_item
from src.models import Livro
from src.storage import make_raw_key


BOOKS_HOME = "https://books.toscrape.com/"


@dataclass(frozen=True)
class Category:
    name: str
    url: str


@dataclass(frozen=True)
class Page:
    url: str
    books: list[dict]
    next_url: str | None


class BookListing(dict):
    @property
    def url(self):
        return self["url"]


@dataclass(frozen=True)
class RobotsResult:
    url: str
    status_http: int
    body: bytes
    consultado_em: str
    allowed_paths: list[str] | None


def _response_body(response):
    return bytes(getattr(response, "content", getattr(response, "corpo", b"")))


def _status(response):
    return getattr(response, "status_code", getattr(response, "status_http", 0))


def _listing_books(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a[href]")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        if link is None or price is None or rating is None:
            continue
        rating_labels = [value for value in rating.get("class", []) if value != "star-rating"]
        books.append(
            BookListing({
                "url": urljoin(base_url, link["href"]),
                "titulo": link.get("title") or link.get_text(strip=True),
                "avaliacao": rating_labels[0] if rating_labels else "",
                "preco_gbp": float(
                    price.get_text(strip=True).replace("£", "").replace(",", "")
                ),
            })
        )
    return books


def _detail_fields(html, url=""):
    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("div.product_main")
    product = product or soup
    title = product.select_one("h1")
    price = product.select_one("p.price_color")
    rating = product.select_one("p.star-rating")
    upc = None
    for row in soup.select("table.table-striped tr"):
        heading = row.find("th")
        value = row.find("td")
        if heading and value and heading.get_text(strip=True).lower() == "upc":
            upc = value.get_text(strip=True)
            break
    availability = soup.select_one("div.product_main p.availability")
    availability_text = availability.get_text(" ", strip=True) if availability else ""
    quantity_match = re.search(r"\((\d+)\s+available\)", availability_text)
    breadcrumb = soup.select("ul.breadcrumb li a")
    category = breadcrumb[2].get_text(strip=True) if len(breadcrumb) > 2 else ""
    return {
        "upc": upc or "",
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
        "qtd_estoque": int(quantity_match.group(1)) if quantity_match else None,
        "coletado_em": datetime.now(timezone.utc).isoformat(),
    }


def discover_categories(html, *, get):
    soup = BeautifulSoup(html, "html.parser")
    categories = []
    for link in soup.select("div.side_categories a[href]"):
        name = link.get_text(strip=True)
        if name and name.lower() != "books":
            categories.append(
                Category(
                    name=name.lower(),
                    url=urljoin(BOOKS_HOME, link["href"]),
                )
            )
    return categories


def _parse_page(url, html):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("article.product_pod")
    books = _listing_books(html, url)
    has_unrecognized_content = bool(
        any(tag.name not in {"html", "body"} for tag in soup.find_all(True))
        or soup.get_text(strip=True)
    )
    if (
        (not product_cards and has_unrecognized_content)
        or len(books) != len(product_cards)
    ):
        raise ValueError("Estrutura HTML inesperada na página de categoria")
    next_link = soup.select_one("li.next a[href]")
    return Page(
        url=url,
        books=books,
        next_url=urljoin(url, next_link["href"]) if next_link else None,
    )


def collect_category(
    url,
    *,
    get,
    first_html=None,
    timeout=DEFAULT_HTTP_TIMEOUT,
    user_agent="aula_03_api_scraping",
):
    pages = []
    current_url = url
    body = first_html
    seen_urls = set()
    seen_books = set()
    while current_url and current_url not in seen_urls:
        seen_urls.add(current_url)
        if body is None:
            response = get_with_timeout(
                current_url,
                get=get,
                timeout=timeout,
                headers={"User-Agent": user_agent},
            )
            if not 200 <= _status(response) < 300:
                raise RuntimeError(f"Falha HTTP {_status(response)} ao consultar categoria")
            body = _response_body(response)
        page = _parse_page(current_url, body)
        unique_books = []
        for book in page.books:
            if book["url"] not in seen_books:
                seen_books.add(book["url"])
                unique_books.append(book)
        pages.append(Page(page.url, unique_books, page.next_url))
        current_url = page.next_url
        body = None
    return pages


def select_categories(categories, configured):
    normalized = [
        category
        if hasattr(category, "name")
        else Category(name=str(category), url="")
        for category in categories
    ]
    if not configured or not str(configured).strip():
        return normalized
    names = {
        name.strip().lower()
        for name in str(configured).split(",")
        if name.strip()
    }

    def category_slug(url):
        segments = urlsplit(url).path.rstrip("/").split("/")
        if len(segments) > 1 and segments[-1] == "index.html":
            return segments[-2]
        return segments[-1]

    return [
        category
        for category in normalized
        if category.name.lower() in names
        or (
            category.url
            and category_slug(category.url).lower() in names
        )
    ]


def extract_book(
    listing_html,
    *,
    detail_html,
    get,
    timeout=DEFAULT_HTTP_TIMEOUT,
    user_agent="aula_03_api_scraping",
):
    listing_url = BOOKS_HOME
    listing = _listing_books(listing_html, listing_url)
    if detail_html is None:
        if not listing:
            raise ValueError("A listagem não contém endereço de detalhe")
        response = get_with_timeout(
            listing[0]["url"],
            get=get,
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )
        if not 200 <= _status(response) < 300:
            raise RuntimeError(f"Falha HTTP {_status(response)} ao consultar detalhe")
        detail_html = _response_body(response)
    listing_book = listing[0] if listing else {}
    detail = _detail_fields(detail_html, listing_book.get("url", ""))
    for field in ("titulo", "avaliacao", "preco_gbp"):
        if listing_book.get(field):
            detail[field] = listing_book[field]
    return Livro(**detail)


def collect_robots(
    *,
    get,
    timeout=DEFAULT_HTTP_TIMEOUT,
    user_agent="aula_03_api_scraping",
):
    url = urljoin(BOOKS_HOME, "robots.txt")
    response = get_with_timeout(
        url,
        get=get,
        timeout=timeout,
        headers={"User-Agent": user_agent},
    )
    body = _response_body(response)
    return RobotsResult(
        url=url,
        status_http=_status(response),
        body=body,
        consultado_em=datetime.now(timezone.utc).isoformat(),
        allowed_paths=None,
    )


class ColetorBooks:
    def __init__(
        self,
        *,
        get,
        gravador,
        manifesto,
        categorias="",
        timeout=DEFAULT_HTTP_TIMEOUT,
        user_agent="aula_03_api_scraping",
    ):
        self.get = get
        self.gravador = gravador
        self.manifesto = manifesto
        self.categorias_configuradas = categorias
        self.timeout = timeout
        self.user_agent = user_agent
        self.categorias_descobertas = []
        self.paginas_coletadas = []
        self.livros_coletados = []

    def _gravar_resposta(
        self, *, url, data_ref, resource, status_http, attempts, body
    ):
        digest = hashlib.sha256(body).hexdigest()
        key = make_raw_key("books_toscrape", data_ref, resource, body)
        collected_at = datetime.now(timezone.utc).isoformat()
        storage_attempts = self.gravador.gravar_raw(
            key,
            body,
            {
                "source-url": url,
                "collected-at": collected_at,
                "sha256": digest,
            },
        )
        return record_item(
            self.manifesto,
            url=url,
            status_http=status_http,
            attempts=attempts + max(1, storage_attempts or 1) - 1,
            bytes_received=len(body),
            state="gravado",
            key=key,
            sha256=digest,
        )

    def coletar(self, data_ref: date | str):
        self.manifesto.registrar_source("books.toscrape.com")
        reference = data_ref.isoformat() if isinstance(data_ref, date) else str(data_ref)
        robots = collect_robots(
            get=self.get,
            timeout=self.timeout,
            user_agent=self.user_agent,
        )
        robots_item = self._gravar_resposta(
            url=robots.url,
            data_ref=reference,
            resource="robots.txt",
            status_http=robots.status_http,
            attempts=1,
            body=robots.body,
        )
        self.manifesto.registrar_robots(
            {
                "url": robots.url,
                "status_http": robots.status_http,
                "consultado_em": robots.consultado_em,
                "allowed_paths": robots.allowed_paths,
                "chave": robots_item.chave,
            }
        )

        response = get_with_timeout(
            BOOKS_HOME,
            get=self.get,
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
        )
        status = _status(response)
        body = _response_body(response)
        if not 200 <= status < 300:
            raise RuntimeError(f"Falha HTTP {status} ao consultar página inicial")
        self._gravar_resposta(
            url=BOOKS_HOME,
            data_ref=reference,
            resource="inicio.html",
            status_http=status,
            attempts=getattr(response, "tentativas", 1),
            body=body,
        )
        self.categorias_descobertas = discover_categories(body, get=self.get)
        selected_categories = select_categories(
            self.categorias_descobertas, self.categorias_configuradas
        )
        self.paginas_coletadas = []
        self.livros_coletados = []
        for category in selected_categories:
            category_slug = re.sub(
                r"[^a-z0-9_-]+", "-", category.name.lower()
            ).strip("-") or "categoria"
            current_url = category.url
            page_number = 1
            seen_pages = set()
            seen_books = set()
            while current_url and current_url not in seen_pages:
                seen_pages.add(current_url)
                response = get_with_timeout(
                    current_url,
                    get=self.get,
                    timeout=self.timeout,
                    headers={"User-Agent": self.user_agent},
                )
                status = _status(response)
                if not 200 <= status < 300:
                    error = f"Falha HTTP {status} ao consultar categoria"
                    record_item(
                        self.manifesto,
                        url=current_url,
                        status_http=status,
                        attempts=getattr(response, "tentativas", 1),
                        bytes_received=0,
                        state="falhou",
                        error=error,
                    )
                    raise RuntimeError(error)
                page_body = _response_body(response)
                self._gravar_resposta(
                    url=current_url,
                    data_ref=reference,
                    resource=f"categoria={category_slug}/pagina={page_number}",
                    status_http=status,
                    attempts=getattr(response, "tentativas", 1),
                    body=page_body,
                )
                page = _parse_page(current_url, page_body)
                unique_books = []
                for book in page.books:
                    if book["url"] not in seen_books:
                        seen_books.add(book["url"])
                        unique_books.append(book)
                self.paginas_coletadas.append(
                    Page(page.url, unique_books, page.next_url)
                )
                for book in unique_books:
                    detail_response = get_with_timeout(
                        book["url"],
                        get=self.get,
                        timeout=self.timeout,
                        headers={"User-Agent": self.user_agent},
                    )
                    detail_status = _status(detail_response)
                    if not 200 <= detail_status < 300:
                        error = f"Falha HTTP {detail_status} ao consultar detalhe"
                        record_item(
                            self.manifesto,
                            url=book["url"],
                            status_http=detail_status,
                            attempts=getattr(detail_response, "tentativas", 1),
                            bytes_received=0,
                            state="falhou",
                            error=error,
                        )
                        continue
                    detail_body = _response_body(detail_response)
                    self._gravar_resposta(
                        url=book["url"],
                        data_ref=reference,
                        resource=f"detalhe={book['url'].rstrip('/').rsplit('/', 1)[-1]}",
                        status_http=detail_status,
                        attempts=getattr(detail_response, "tentativas", 1),
                        body=detail_body,
                    )
                    detail = _detail_fields(detail_body, book["url"])
                    for field in ("titulo", "avaliacao", "preco_gbp"):
                        if book.get(field):
                            detail[field] = book[field]
                    self.livros_coletados.append(Livro(**detail))
                current_url = page.next_url
                page_number += 1
        return selected_categories
