"""Publica uma mensagem de telemetria por linha, em série."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.produtores._amqp import Publicador


def publicar_telemetria(arquivos: list[Path] | None = None) -> int:
    fontes = (
        arquivos
        if arquivos is not None
        else sorted(Path("entrada/telemetria").glob("*.txt"))
    )
    quantidade = 0
    with Publicador() as publicador:
        for arquivo in fontes:
            with arquivo.open(encoding="utf-8") as entrada:
                for numero, linha in enumerate(entrada, start=1):
                    valor = linha.rstrip("\r\n")
                    if not valor:
                        continue
                    nome = arquivo.name
                    publicador.publicar(
                        {
                            "data_tag": "telemetria",
                            "data": {
                                "arquivo": f"entrada/telemetria/{nome}",
                                "numero_linha": numero,
                                "linha": valor,
                            },
                        }
                    )
                    quantidade += 1
    return quantidade


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path, action="append")
    args = parser.parse_args()
    print(f"linhas de telemetria publicadas: {publicar_telemetria(args.arquivo)}")


if __name__ == "__main__":
    main()
