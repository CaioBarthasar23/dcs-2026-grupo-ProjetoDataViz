from datetime import date
from urllib.parse import parse_qs, urlsplit

import src.collectors.ptax as ptax_module

from src.collectors.ptax import ColetorPtax, collect_ptax
from src.http import ClienteHttp
from src.manifest import create_manifest


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.events = []

    def gravar_raw(self, chave, corpo, metadados):
        assert isinstance(corpo, bytes)
        self.objects[chave] = (corpo, metadados)
        self.events.append(("raw", chave))


def test_seleciona_fechamento_mais_recente_e_formata_janela(
    ptax_fechamento, fake_get
):
    fake_get.queue_response(200, ptax_fechamento)

    quote = collect_ptax(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 10, 29),
        response_body=None,
        get=fake_get,
    )

    query = parse_qs(urlsplit(fake_get.calls[0][0]).query)
    assert query["@moeda"] == ["'GBP'"]
    assert query["@dataInicial"] == ["'10-29-2026'"]
    assert query["@dataFinalCotacao"] == ["'11-02-2026'"]
    assert query["$format"] == ["json"]
    assert quote.tipoBoletim == "Fechamento"
    assert quote.dataHoraCotacao.startswith("2026-10-30")
    assert quote.cotacaoCompra == 7.2609
    assert fake_get.calls[0][1]["timeout"] == (5.0, 10.0)


def test_janela_vazia_preserva_json_e_marca_incompleta(
    ptax_vazia, fake_get, monkeypatch
):
    fake_get.queue_response(200, ptax_vazia)
    storage = MemoryStorage()
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorPtax(
        get=fake_get,
        gravador=storage,
        manifesto=manifest,
    )
    parse_ptax = ptax_module.collect_ptax

    def tracked_parse(**kwargs):
        storage.events.append(("parse", None))
        return parse_ptax(**kwargs)

    monkeypatch.setattr(ptax_module, "collect_ptax", tracked_parse)

    result = collector.coletar(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 11, 2),
    )

    assert result.quote is None
    assert result.response_body == ptax_vazia
    assert result.execution_state == "incompleta"
    assert manifest.estado == "incompleta"
    assert manifest.sources == ["PTAX"]
    assert manifest.itens[0].erro
    assert "fechamento" in manifest.itens[0].erro.lower()
    assert len(storage.objects) == 1
    assert next(iter(storage.objects.values()))[0] == ptax_vazia
    assert storage.events == [("raw", next(iter(storage.objects))), ("parse", None)]


def test_ptax_tem_quatro_tentativas_totais_com_cliente_http(
    ptax_fechamento, fake_get
):
    for _ in range(3):
        fake_get.queue_response(503, b"temporarily unavailable")
    fake_get.queue_response(200, ptax_fechamento)
    http = ClienteHttp(
        get=fake_get,
        max_tentativas=4,
        intervalo_minimo=0,
        sleep=lambda _: None,
        random_uniform=lambda low, high: low,
    )
    storage = MemoryStorage()
    manifest = create_manifest(data_ref="2026-11-02")
    collector = ColetorPtax(
        get=http.get_once,
        gravador=storage,
        manifesto=manifest,
        max_attempts=4,
        sleep=lambda _: None,
        random_uniform=lambda low, high: low,
    )

    result = collector.coletar(
        data_ref=date(2026, 11, 2),
        window_start=date(2026, 10, 30),
    )

    assert result.execution_state == "sucesso"
    assert len(fake_get.calls) == 4
    assert manifest.itens[0].tentativas == 4
