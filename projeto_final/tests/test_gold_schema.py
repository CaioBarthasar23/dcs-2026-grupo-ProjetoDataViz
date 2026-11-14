import io
from datetime import date, datetime

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.silver import LocalLake


GROUP = 23651
GOLD_TABLES = {
    "fato_preco_diario",
    "dim_produto",
    "dim_colecao",
    "dim_data",
    "dim_acabamento",
    "fato_cambio_diario",
}


def parquet_bytes(rows):
    buf = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows), buf, compression="snappy")
    return buf.getvalue()


def silver_fixture(root):
    lake = LocalLake(root)
    lake.put(
        f"silver/colecao/group_id={GROUP}/colecao.parquet",
        parquet_bytes(
            [
                {
                    "group_id": GROUP,
                    "nome": "SV08: Surging Sparks",
                    "sigla": "SSP",
                    "data_lancamento": date(2024, 11, 8),
                    "responsavel": "colecionador",
                }
            ]
        ),
    )
    lake.put(
        f"silver/produto/group_id={GROUP}/produto.parquet",
        parquet_bytes(
            [
                {
                    "product_id": 1001,
                    "group_id": GROUP,
                    "nome": "Carta de teste",
                    "tipo_produto": "carta",
                    "raridade": "Rare",
                    "numero": "1/10",
                    "image_url": "https://example.test/card.jpg",
                    "url": "https://example.test/product/1001",
                    "categoria_selado": None,
                },
                {
                    "product_id": 1002,
                    "group_id": GROUP,
                    "nome": "Code Card",
                    "tipo_produto": "carta",
                    "raridade": "Code Card",
                    "numero": None,
                    "image_url": "https://example.test/code.jpg",
                    "url": "https://example.test/product/1002",
                    "categoria_selado": None,
                },
            ]
        ),
    )
    prices = [
        {
            "data": date(2026, 10, 8),
            "product_id": 1001,
            "group_id": GROUP,
            "acabamento": "Normal",
            "market_price": 2.0,
            "low_price": None,
            "mid_price": None,
            "high_price": None,
            "moeda": "USD",
            "fonte": "tcgplayer",
            "chave_raw": "raw/tcgplayer/group_id=23651/data=2026-10-08/prices.json",
        },
        {
            "data": date(2026, 10, 9),
            "product_id": 1001,
            "group_id": GROUP,
            "acabamento": "Normal",
            "market_price": 2.0,
            "low_price": 1.5,
            "mid_price": None,
            "high_price": 3.0,
            "moeda": "USD",
            "fonte": "tcgplayer",
            "chave_raw": "raw/tcgplayer/group_id=23651/data=2026-10-09/prices.json",
        },
        {
            "data": date(2026, 10, 12),
            "product_id": 1001,
            "group_id": GROUP,
            "acabamento": "Normal",
            "market_price": 3.0,
            "low_price": None,
            "mid_price": None,
            "high_price": None,
            "moeda": "USD",
            "fonte": "tcgplayer",
            "chave_raw": "raw/tcgplayer/group_id=23651/data=2026-10-12/prices.json",
        },
        {
            "data": date(2026, 10, 13),
            "product_id": 1002,
            "group_id": GROUP,
            "acabamento": "Reverse Holofoil",
            "market_price": None,
            "low_price": None,
            "mid_price": None,
            "high_price": None,
            "moeda": "USD",
            "fonte": "tcgplayer",
            "chave_raw": "raw/tcgplayer/group_id=23651/data=2026-10-13/prices.json",
        },
    ]
    for dia in sorted({row["data"] for row in prices}):
        lake.put(
            f"silver/preco_diario/group_id={GROUP}/data={dia.isoformat()}/preco.parquet",
            parquet_bytes([row for row in prices if row["data"] == dia]),
        )
    lake.put(
        f"silver/cambio_diario/group_id={GROUP}/cambio.parquet",
        parquet_bytes(
            [
                {
                    "data": date(2026, 10, 9),
                    "cotacao_compra": 5.0,
                    "cotacao_venda": 7.0,
                    "data_hora_cotacao": datetime(2026, 10, 9, 18, 0),
                    "boletim": "Fechamento",
                    "chave_raw": "raw/bcb_ptax/group_id=23651/data=2026-10-09/cotacao.json",
                },
                {
                    "data": date(2026, 10, 13),
                    "cotacao_compra": 6.0,
                    "cotacao_venda": 8.0,
                    "data_hora_cotacao": datetime(2026, 10, 13, 18, 0),
                    "boletim": "Fechamento",
                    "chave_raw": "raw/bcb_ptax/group_id=23651/data=2026-10-13/cotacao.json",
                },
                {
                    "data": date(2026, 10, 14),
                    "cotacao_compra": 99.0,
                    "cotacao_venda": 101.0,
                    "data_hora_cotacao": datetime(2026, 10, 14, 18, 0),
                    "boletim": "Fechamento",
                    "chave_raw": "raw/bcb_ptax/group_id=23651/data=2026-10-14/cotacao.json",
                },
            ]
        ),
    )
    return lake


def gold_module():
    from src import gold

    return gold


def build_fixture(tmp_path):
    source = silver_fixture(tmp_path / "silver")
    destination = LocalLake(tmp_path / "gold")
    gold = gold_module()
    gold.build(source, destination)
    return gold, source, destination


def read_gold(destination, table):
    key = f"gold/group_id={GROUP}/{table}.parquet"
    payload = destination.get(key)
    assert payload is not None, f"faltou {key}"
    return pq.read_table(io.BytesIO(payload))


def test_gold_tem_tabelas_colunas_e_preserva_code_card(tmp_path):
    _, _, destination = build_fixture(tmp_path)

    paths = list(destination.root.glob("gold/group_id=23651/*.parquet"))
    relative_keys = {path.relative_to(destination.root).as_posix() for path in paths}
    assert relative_keys == {
        f"gold/group_id={GROUP}/{table}.parquet" for table in GOLD_TABLES
    }
    assert {path.stem for path in paths} == GOLD_TABLES

    fato_preco = read_gold(destination, "fato_preco_diario")
    assert set(
        ["group_id", "product_id", "data", "acabamento", "market_price", "market_price_brl", "data_ptax_usada"]
    ).issubset(fato_preco.column_names)
    assert set(
        ["low_price", "mid_price", "high_price", "moeda", "fonte", "chave_raw"]
    ).issubset(fato_preco.column_names)
    assert {"group_id", "product_id", "nome", "tipo_produto", "raridade"}.issubset(
        read_gold(destination, "dim_produto").column_names
    )
    assert {"group_id", "nome", "sigla", "data_lancamento", "responsavel"}.issubset(
        read_gold(destination, "dim_colecao").column_names
    )
    assert read_gold(destination, "dim_data").column_names == ["data"]
    assert read_gold(destination, "dim_acabamento").column_names == ["acabamento"]
    assert {"data", "cotacao_compra", "cotacao_venda"}.issubset(
        read_gold(destination, "fato_cambio_diario").column_names
    )
    raridades = read_gold(destination, "dim_produto").column("raridade").to_pylist()
    assert "Code Card" in raridades


def test_fatos_tem_relacoes_sem_chaves_orfas(tmp_path):
    _, _, destination = build_fixture(tmp_path)
    tables = {
        table: pq.read_table(
            io.BytesIO(destination.get(f"gold/group_id={GROUP}/{table}.parquet"))
        )
        for table in GOLD_TABLES
    }
    con = duckdb.connect()
    for table, arrow_table in tables.items():
        con.register(table, arrow_table)

    assert con.execute(
        """SELECT count(*) FROM fato_preco_diario f
           LEFT JOIN dim_produto p USING (group_id, product_id)
           WHERE p.product_id IS NULL"""
    ).fetchone()[0] == 0
    assert con.execute(
        """SELECT count(*) FROM fato_preco_diario f
           LEFT JOIN dim_colecao c USING (group_id)
           WHERE c.group_id IS NULL"""
    ).fetchone()[0] == 0
    assert con.execute(
        """SELECT count(*) FROM fato_preco_diario f
           LEFT JOIN dim_data d USING (data)
           WHERE d.data IS NULL"""
    ).fetchone()[0] == 0
    assert con.execute(
        """SELECT count(*) FROM fato_preco_diario f
           LEFT JOIN dim_acabamento a USING (acabamento)
           WHERE a.acabamento IS NULL"""
    ).fetchone()[0] == 0
    assert con.execute(
        """SELECT count(*) FROM fato_cambio_diario f
           LEFT JOIN dim_data d USING (data)
           WHERE d.data IS NULL"""
    ).fetchone()[0] == 0
    con.close()


def test_reconstruir_duas_vezes_produz_parquets_identicos(tmp_path):
    gold, source, destination = build_fixture(tmp_path)
    antes = {
        str(path.relative_to(destination.root)): path.read_bytes()
        for path in destination.root.glob("gold/group_id=23651/*.parquet")
    }

    gold.build(source, destination)

    depois = {
        str(path.relative_to(destination.root)): path.read_bytes()
        for path in destination.root.glob("gold/group_id=23651/*.parquet")
    }
    assert depois == antes


def test_todas_as_chaves_gravadas_usam_group_id_proprio(tmp_path):
    gold = gold_module()
    source = silver_fixture(tmp_path / "silver")
    base = LocalLake(tmp_path / "gold")

    class RecordingLake:
        def __init__(self, lake):
            self.lake = lake
            self.keys = []
            self.root = lake.root

        def put(self, key, data):
            self.keys.append(key)
            self.lake.put(key, data)

        def get(self, key):
            return self.lake.get(key)

    destination = RecordingLake(base)
    gold.build(source, destination)

    assert set(destination.keys) == {
        f"gold/group_id={GROUP}/{table}.parquet" for table in GOLD_TABLES
    }
    assert all(key.startswith(f"gold/group_id={GROUP}/") for key in destination.keys)


def test_group_id_alheio_e_recusado_antes_de_qualquer_escrita(tmp_path):
    gold = gold_module()
    source = silver_fixture(tmp_path / "silver")
    destination = LocalLake(tmp_path / "gold")

    with pytest.raises(ValueError, match="ERRO escrita recusada"):
        gold.build(source, destination, group_id=24269)

    assert not destination.root.exists() or not list(destination.root.rglob("*.parquet"))


def test_main_recusa_group_id_alheio_antes_de_criar_lakes(monkeypatch, caplog):
    gold = gold_module()
    monkeypatch.setenv("GROUP_ID", "24269")
    monkeypatch.setattr(
        gold,
        "make_lake",
        lambda tipo: pytest.fail(f"main criou lake {tipo!r} antes de recusar GROUP_ID"),
    )

    with caplog.at_level("ERROR", logger="gold"):
        status = gold.main(["build", "--fonte", "local", "--destino", "local"])

    assert status != 0
    assert "GROUP_ID=24269" in caplog.text
    assert "group_id=23651" in caplog.text


def test_preco_brl_usa_ultima_ptax_ate_data_sem_usar_cotacao_futura(tmp_path):
    _, _, destination = build_fixture(tmp_path)
    rows = read_gold(destination, "fato_preco_diario").to_pylist()
    by_date = {row["data"]: row for row in rows if row["product_id"] == 1001}

    assert by_date[date(2026, 10, 8)]["market_price_brl"] is None
    assert by_date[date(2026, 10, 8)]["data_ptax_usada"] is None
    assert by_date[date(2026, 10, 9)]["data_ptax_usada"] == date(2026, 10, 9)
    assert by_date[date(2026, 10, 9)]["market_price_brl"] == 10.0
    assert by_date[date(2026, 10, 12)]["data_ptax_usada"] == date(2026, 10, 9)
    assert by_date[date(2026, 10, 12)]["market_price_brl"] == 15.0


def test_market_price_nulo_permanece_nulo(tmp_path):
    _, _, destination = build_fixture(tmp_path)
    rows = read_gold(destination, "fato_preco_diario").to_pylist()
    row = next(row for row in rows if row["product_id"] == 1002)

    assert row["market_price"] is None
    assert row["market_price_brl"] is None
