from hashlib import sha256
from io import BytesIO
import json

from pyarrow import parquet

from src.lake import Lake, MensagemRecebida


class S3Falso:
    def __init__(self):
        self.puts = []

    def put_object(self, **kwargs):
        self.puts.append(kwargs)


def test_raw_jsonl_preserva_corpo_e_metadados_sha256_lote() -> None:
    s3 = S3Falso()
    lake = Lake(cliente_s3=s3)
    corpo = b'{"data_tag":"livros",\n"data":{"upc":"x"}}'

    arquivo = lake.gravar_raw(
        "lote_120000_uuid",
        "livros",
        "2026-11-11",
        [MensagemRecebida(corpo=corpo, recebido_em_ms=1_794_000_000_123)],
    )

    put = s3.puts[0]
    linhas = put["Body"].decode("utf-8").splitlines()
    registro = json.loads(linhas[0])
    assert len(linhas) == 1
    assert registro["recebido_em_ms"] == 1_794_000_000_123
    assert registro["envelope"] == '{"data_tag":"livros", "data":{"upc":"x"}}'
    assert put["Metadata"] == {
        "sha256": sha256(put["Body"]).hexdigest(),
        "lote": "lote_120000_uuid",
    }
    assert arquivo["sha256"] == put["Metadata"]["sha256"]


def test_bronze_e_parquet_zstd_escrito_do_arrow_com_metadados() -> None:
    s3 = S3Falso()
    lake = Lake(cliente_s3=s3)

    arquivo = lake.gravar_bronze(
        "lote_120000_uuid",
        "livros",
        "2026-11-11",
        [{"timestamp": 1_794_000_000_123, "data_json": {"upc": "x"}}],
    )

    put = s3.puts[0]
    tabela = parquet.read_table(BytesIO(put["Body"]))
    coluna = tabela.column("data_json").to_pylist()
    assert tabela.column_names == ["timestamp", "data_json"]
    assert tabela.column("timestamp").to_pylist() == [1_794_000_000_123]
    assert json.loads(coluna[0]) == {"upc": "x"}
    assert parquet.ParquetFile(BytesIO(put["Body"])).metadata.row_group(0).column(
        0
    ).compression == "ZSTD"
    assert put["Metadata"]["sha256"] == sha256(put["Body"]).hexdigest()
    assert put["Metadata"]["lote"] == "lote_120000_uuid"
    assert arquivo["linhas"] == 1


def test_manifesto_e_rejeicao_tambem_carregam_sha256_e_lote() -> None:
    s3 = S3Falso()
    lake = Lake(cliente_s3=s3)

    manifesto = lake.gravar_manifesto(
        "lote_120000_uuid", "2026-11-11", {"lote": "lote_120000_uuid"}
    )
    rejeitado = lake.rejeitar(1_794_000_000_123, "data ausente", b"corpo ruim")

    assert len(s3.puts) == 2
    for put, registro in zip(s3.puts, (manifesto, rejeitado), strict=True):
        assert put["Metadata"]["sha256"] == sha256(put["Body"]).hexdigest()
        assert put["Metadata"]["lote"]
        assert registro["sha256"] == put["Metadata"]["sha256"]
    corpo_rejeitado = json.loads(s3.puts[1]["Body"])
    assert corpo_rejeitado["motivo"] == "data ausente"
    assert corpo_rejeitado["corpo"] == "corpo ruim"
