from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.leitura import nome_valido


_FUSO_ORIGEM = ZoneInfo("America/Sao_Paulo")


def montar_chave(nome_arquivo: str) -> str:
    if not nome_valido(nome_arquivo):
        raise ValueError(f"Nome de lote inválido: {nome_arquivo}")

    caminhao, janela_nome = nome_arquivo.split("_", maxsplit=1)
    janela = datetime.strptime(janela_nome.removesuffix(".txt"), "%Y%m%dT%H%M")
    janela_utc = janela.replace(tzinfo=_FUSO_ORIGEM).astimezone(timezone.utc)

    return (
        f"telemetria/data={janela_utc:%Y-%m-%d}/hora={janela_utc:%H}/"
        f"caminhao={caminhao}/lote_{janela_utc:%H%M}.txt"
    )
