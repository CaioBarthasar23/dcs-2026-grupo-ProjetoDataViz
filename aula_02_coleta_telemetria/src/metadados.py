from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.leitura import nome_valido


_FUSO_ORIGEM = ZoneInfo("America/Sao_Paulo")


def _iso_utc(instante: datetime) -> str:
    return instante.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def montar_metadados(
    nome_arquivo: str,
    *,
    sha256: str,
    versao_coletor: str,
    recebido_em: datetime,
) -> dict[str, str]:
    if not nome_valido(nome_arquivo):
        raise ValueError(f"Nome de lote inválido: {nome_arquivo}")
    if recebido_em.tzinfo is None or recebido_em.utcoffset() is None:
        raise ValueError("recebido_em deve incluir fuso horário")

    caminhao, janela_nome = nome_arquivo.split("_", maxsplit=1)
    janela_local = datetime.strptime(
        janela_nome.removesuffix(".txt"), "%Y%m%dT%H%M"
    ).replace(tzinfo=_FUSO_ORIGEM)
    metadados = {
        "fonte": "provedor-satelite",
        "recebido-em": _iso_utc(recebido_em),
        "versao-coletor": versao_coletor,
        "sha256": sha256,
        "caminhao": caminhao,
        "janela-inicio": _iso_utc(janela_local),
        "arquivo-origem": nome_arquivo,
    }

    for valor in metadados.values():
        valor.encode("ascii")
    return metadados
