from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .regras import evento_complexo, parse_utc


def avaliar(
    estado_da_chave: dict[str, Any] | None,
    evento: dict[str, Any],
    agora: datetime,
    quantidade: int = 2,
    janela: timedelta = timedelta(days=7),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    estado = estado_da_chave or {"ids": [], "datas": {}}
    ids = estado["ids"]
    datas = estado["datas"]
    event_id = evento["event_id"]

    if event_id in ids:
        return estado, []

    instante = parse_utc(evento["ocorrido_em"])
    ids_validos = []
    datas_validas = {}
    for id_antigo in ids:
        antigo = parse_utc(datas[id_antigo])
        if instante - antigo <= janela:
            ids_validos.append(id_antigo)
            datas_validas[id_antigo] = datas[id_antigo]

    ids_validos.append(event_id)
    datas_validas[event_id] = evento["ocorrido_em"]
    novo = {"ids": ids_validos, "datas": datas_validas}

    if len(ids_validos) >= quantidade:
        complexo = evento_complexo(
            "cobranca_reincidente",
            evento["aluno"],
            evento,
            agora,
            janela,
            ids_validos[-quantidade:],
            atrasado=False,
        )
        novo["ids"] = []
        novo["datas"] = {}
        return novo, [complexo]
    return novo, []
