from __future__ import annotations

import json
from datetime import datetime

import requests

from src import collector as c


class FakeResponse:
    def __init__(self, body):
        self.content = json.dumps(body).encode()
        self._body = body

    def json(self):
        return self._body

    def raise_for_status(self):
        return None


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeSession:
    def __init__(self, clock):
        self.headers = {"User-Agent": c.USER_AGENT}
        self.clock = clock
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, dict(self.headers), self.clock.monotonic()))
        if "/products" in url or "/prices" in url:
            return FakeResponse({"success": True, "results": [{"id": 1}]})
        if "olinda" in url:
            return FakeResponse({"value": [{"tipoBoletim": "Fechamento"}]})
        if "bcdata" in url:
            return FakeResponse([{"data": "11/11/2026", "valor": "0.05"}])
        raise AssertionError("URL fora das fontes esperadas")


def test_coleta_respeita_limites_de_uso_do_tcgcsv(tmp_path, monkeypatch):
    clock = FakeClock()
    session = FakeSession(clock)
    monkeypatch.setattr(c, "_session", session)
    monkeypatch.setattr(c, "time", clock)
    monkeypatch.setattr(c, "_last_call", clock.monotonic())

    result = c.coletar(
        c.LocalStorage(tmp_path),
        datetime(2026, 11, 12, 19, 0, tzinfo=c.TZ),
    )

    tcg_calls = [call for call in session.calls if "tcgcsv.com" in call[0]]
    assert len(tcg_calls) == 2, f"contagem observada de chamadas TCGCSV: {len(tcg_calls)}"
    assert len(tcg_calls) <= 3
    worst_case_daily_calls = 3 * 3  # três chamadas por execução, três tentativas do workflow
    assert worst_case_daily_calls < 10_000
    assert "products" in tcg_calls[0][0] and "prices" in tcg_calls[1][0]

    assert session.calls
    assert c.USER_AGENT != requests.utils.default_user_agent()
    assert all(call[1].get("User-Agent") == c.USER_AGENT for call in session.calls)
    intervals = [b[2] - a[2] for a, b in zip(session.calls, session.calls[1:])]
    assert all(interval >= 0.1 for interval in intervals), intervals
    assert all(value == "gravado" for value in result.values())
