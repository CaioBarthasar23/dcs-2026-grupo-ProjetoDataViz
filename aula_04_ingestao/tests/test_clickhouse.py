import json

from src.clickhouse import ClickHouse
from src.config import config


class ClienteClickHouseFalso:
    def __init__(self):
        self.inserts = []

    def insert(self, *args, **kwargs):
        self.inserts.append((args, kwargs))


def test_lote_inteiro_e_enviado_em_um_insert_com_settings_do_contrato() -> None:
    cliente = ClienteClickHouseFalso()
    clickhouse = ClickHouse(cliente=cliente)
    linhas = [
        {"timestamp": 1001, "data_json": {"v": 1}, "data_tag": "livros"},
        {"timestamp": 1002, "data_json": '{"v":2}', "data_tag": "ptax"},
    ]

    quantidade = clickhouse.inserir(linhas, lote="lote_teste")

    assert quantidade == 2
    assert len(cliente.inserts) == 1
    args, kwargs = cliente.inserts[0]
    assert args[0] == f"{config.clickhouse_database}.{config.clickhouse_tabela}"
    assert kwargs["column_names"] == ["timestamp", "data_json", "data_tag"]
    assert args[1][0] == [
        1001,
        json.dumps({"v": 1}, separators=(",", ":")),
        "livros",
    ]
    assert args[1][1] == [1002, '{"v":2}', "ptax"]
    assert kwargs["settings"]["async_insert"] == config.clickhouse_async_insert
    assert kwargs["settings"]["input_format_try_infer_dates"] == 0
    assert kwargs["settings"]["input_format_try_infer_datetimes"] == 0
