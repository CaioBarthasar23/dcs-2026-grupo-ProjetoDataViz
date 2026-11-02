import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import Configuracao
from src.coletor import executar
from src.manifesto import caminho_manifesto
from tests.fakes import ArmazenamentoFalso


_INICIO = datetime(2026, 10, 17, 12, 4, 5, tzinfo=timezone.utc)


def test_caminho_manifesto_converte_inicio_para_utc() -> None:
    inicio = datetime(
        2026,
        10,
        17,
        9,
        4,
        5,
        tzinfo=timezone(timedelta(hours=-3)),
    )

    assert caminho_manifesto(inicio) == (
        "_manifestos/telemetria/data=2026-10-17/hora=12/"
        "execucao_20261017T120405Z.jsonl"
    )


def _configuracao(pouso: Path) -> Configuracao:
    return Configuracao(
        s3_endpoint_url="http://teste",
        s3_access_key="teste",
        s3_secret_key="teste",
        bucket_raw="raw",
        s3_region="teste",
        coletor_versao="teste",
        pouso_dir=pouso,
    )


def _linhas_manifesto(cliente: ArmazenamentoFalso) -> tuple[str, list[dict]]:
    manifesto = next(
        objeto
        for objeto in cliente.puts
        if objeto.chave.startswith("_manifestos/")
    )
    return manifesto.chave, [
        json.loads(linha)
        for linha in manifesto.body.decode("utf-8").splitlines()
    ]


def test_manifesto_tem_uma_linha_por_arquivo(tmp_path: Path) -> None:
    (tmp_path / "CAM-0451_20261017T0900.txt").write_bytes(
        b"posicao\nTAC;CAM-0451;20261017T091500;ALERTA;ALERTA\n"
    )
    (tmp_path / "invalido.txt").write_bytes(b"conteudo\n")
    cliente = ArmazenamentoFalso()

    codigo = executar(_configuracao(tmp_path), cliente, _INICIO)

    chave, linhas = _linhas_manifesto(cliente)
    assert codigo == 1
    assert chave == (
        "_manifestos/telemetria/data=2026-10-17/hora=12/"
        "execucao_20261017T120405Z.jsonl"
    )
    assert [linha["arquivo"] for linha in linhas] == [
        "CAM-0451_20261017T0900.txt",
        "invalido.txt",
    ]
    assert [linha["status"] for linha in linhas] == ["gravado", "erro"]


def test_manifesto_invalido_e_ilegivel_tem_campos_corretos(
    tmp_path: Path, monkeypatch
) -> None:
    invalido = tmp_path / "invalido.txt"
    conteudo = b"posicao\nTAC;CAM-0451;20261017T091500;ALERTA\nTAC;X;SEM_ALERTA\n"
    invalido.write_bytes(conteudo)
    ilegivel = tmp_path / "CAM-0452_20261017T0900.txt"
    ilegivel.write_bytes(b"nao deve ser lido")
    read_bytes = Path.read_bytes

    def ler_com_erro(caminho: Path) -> bytes:
        if caminho == ilegivel:
            raise OSError("falha simulada")
        return read_bytes(caminho)

    monkeypatch.setattr(Path, "read_bytes", ler_com_erro)
    cliente = ArmazenamentoFalso()

    codigo = executar(_configuracao(tmp_path), cliente, _INICIO)

    _, linhas = _linhas_manifesto(cliente)
    por_arquivo = {linha["arquivo"]: linha for linha in linhas}
    linha_invalida = por_arquivo["invalido.txt"]
    assert codigo == 1
    assert linha_invalida == {
        "arquivo": "invalido.txt",
        "chave": None,
        "status": "erro",
        "bytes": len(conteudo),
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "linhas": 3,
        "alertas": 1,
        "motivo": "nome_invalido",
    }

    linha_ilegivel = por_arquivo["CAM-0452_20261017T0900.txt"]
    assert linha_ilegivel["chave"] == (
        "telemetria/data=2026-10-17/hora=12/"
        "caminhao=CAM-0452/lote_1200.txt"
    )
    assert linha_ilegivel["status"] == "erro"
    assert linha_ilegivel["bytes"] is None
    assert linha_ilegivel["sha256"] is None
    assert linha_ilegivel["linhas"] is None
    assert linha_ilegivel["alertas"] is None
    assert invalido.exists()
    assert ilegivel.exists()
    assert not any(
        objeto.chave == "telemetria/data=2026-10-17/hora=12/"
        "caminhao=CAM-0452/lote_1200.txt"
        for objeto in cliente.puts
    )
    assert [
        objeto.chave
        for objeto in cliente.puts
        if not objeto.chave.startswith("_manifestos/")
    ] == []
