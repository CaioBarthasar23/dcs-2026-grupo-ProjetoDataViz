import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import isfinite

import requests

from src.config import DEFAULT_HTTP_TIMEOUT
from src.models import Resposta


TRANSIENT_STATUSES = {408, 429}


def _validate_timeout(timeout):
    if (
        not isinstance(timeout, tuple)
        or len(timeout) != 2
        or any(
            not isinstance(part, (int, float))
            or not isfinite(part)
            or part <= 0
            for part in timeout
        )
    ):
        raise ValueError("timeout deve conter limites positivos e finitos")
    return timeout


def get_with_timeout(url, *, get, timeout, headers=None):
    _validate_timeout(timeout)
    kwargs = {"timeout": timeout}
    if headers is not None:
        kwargs["headers"] = headers
    return get(url, **kwargs)


def _retry_after(headers, now=None):
    value = next(
        (value for key, value in headers.items() if key.lower() == "retry-after"),
        None,
    )
    if value is None:
        return None
    try:
        delay = float(value)
        return delay if isfinite(delay) and delay >= 0 else None
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(value)
            current = now or datetime.now(timezone.utc)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - current).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def _status(response):
    return getattr(response, "status_code", getattr(response, "status_http", 0))


def _headers(response):
    return getattr(response, "headers", {}) or {}


def _is_transient_status(status):
    return status in TRANSIENT_STATUSES or 500 <= status <= 599


def _as_response(response, url, attempts):
    return Resposta(
        url=getattr(response, "url", url),
        status_http=_status(response),
        headers=dict(_headers(response)),
        corpo=bytes(getattr(response, "content", getattr(response, "corpo", b""))),
        tentativas=attempts,
        recebido_em=datetime.now(timezone.utc),
    )


def get_with_retry(
    url,
    *,
    get,
    max_attempts=4,
    timeout=DEFAULT_HTTP_TIMEOUT,
    sleep=time.sleep,
    random_uniform=random.uniform,
    base_delay=0.5,
    max_delay=8.0,
    headers=None,
):
    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts deve ser um inteiro positivo")
    if not isfinite(base_delay) or base_delay < 0:
        raise ValueError("base_delay deve ser finito e não negativo")
    if not isfinite(max_delay) or max_delay < 0:
        raise ValueError("max_delay deve ser finito e não negativo")

    for attempt in range(max_attempts):
        try:
            response = get_with_timeout(
                url,
                get=lambda request_url, timeout: get_with_timeout(
                    request_url, get=get, timeout=timeout, headers=headers
                ),
                timeout=timeout,
            )
        except (requests.Timeout, requests.ConnectionError, TimeoutError, ConnectionError):
            if attempt + 1 == max_attempts:
                raise
            delay = random_uniform(0.0, min(max_delay, base_delay * 2**attempt))
            sleep(delay)
            continue

        status = _status(response)
        if not _is_transient_status(status) or attempt + 1 == max_attempts:
            return _as_response(response, url, attempt + 1)
        delay = _retry_after(_headers(response))
        if delay is None:
            delay = random_uniform(0.0, min(max_delay, base_delay * 2**attempt))
        sleep(delay)
    raise AssertionError("unreachable")


class ClienteHttp:
    def __init__(
        self,
        *,
        timeout=DEFAULT_HTTP_TIMEOUT,
        max_tentativas=4,
        intervalo_minimo=1.0,
        user_agent="aula_03_api_scraping",
        get=requests.get,
        sleep=time.sleep,
        monotonic=time.monotonic,
        random_uniform=random.uniform,
    ):
        _validate_timeout(timeout)
        if not isinstance(max_tentativas, int) or max_tentativas < 1:
            raise ValueError("max_tentativas deve ser positivo")
        if not isfinite(intervalo_minimo) or intervalo_minimo < 0:
            raise ValueError("intervalo_minimo deve ser finito e não negativo")
        if not user_agent.strip():
            raise ValueError("user_agent não pode ser vazio")
        self.timeout = timeout
        self.max_tentativas = max_tentativas
        self.intervalo_minimo = intervalo_minimo
        self.user_agent = user_agent
        self._get = get
        self._sleep = sleep
        self._monotonic = monotonic
        self._random_uniform = random_uniform
        self._last_started = None
        self._lock = threading.Lock()

    def _request(self, url, *, timeout, headers=None):
        if self._last_started is not None:
            elapsed = self._monotonic() - self._last_started
            remaining = self.intervalo_minimo - elapsed
            if remaining > 0:
                self._sleep(remaining)
        self._last_started = self._monotonic()
        return self._get(url, timeout=timeout, headers=headers)

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> Resposta:
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)
        request_timeout = self.timeout if timeout is None else timeout
        _validate_timeout(request_timeout)
        with self._lock:
            response = get_with_retry(
                url,
                get=self._request,
                max_attempts=self.max_tentativas,
                timeout=request_timeout,
                sleep=self._sleep,
                random_uniform=self._random_uniform,
                headers=request_headers,
            )
        return response

    def get_once(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> Resposta:
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)
        request_timeout = self.timeout if timeout is None else timeout
        _validate_timeout(request_timeout)
        with self._lock:
            response = self._request(
                url,
                timeout=request_timeout,
                headers=request_headers,
            )
        return _as_response(response, url, 1)


@dataclass(frozen=True)
class PolitenessResult:
    max_concurrent: int
    user_agent_identifiable: bool
    minimum_start_interval: float


def validate_politeness(*, urls, get, user_agent, min_interval):
    if min_interval < 0 or not isfinite(min_interval):
        raise ValueError("min_interval deve ser finito e não negativo")
    starts = []
    client = ClienteHttp(
        timeout=DEFAULT_HTTP_TIMEOUT,
        max_tentativas=1,
        intervalo_minimo=min_interval,
        user_agent=user_agent,
        get=get,
    )
    for url in urls:
        client.get(url)
        starts.append(client._last_started)
    intervals = [later - earlier for earlier, later in zip(starts, starts[1:])]
    return PolitenessResult(
        max_concurrent=1,
        user_agent_identifiable=bool(user_agent),
        minimum_start_interval=min(intervals) if intervals else 0.0,
    )
