from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .regras import evento_complexo, parse_utc


def avaliar(
    estado_da_chave: dict[str, Any] | None,
    evento: dict[str, Any],
    agora: datetime,
    quantidade: int = 3,
    janela: timedelta = timedelta(hours=24),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    estado = estado_da_chave or {"ids": [], "datas": {}}
    instante = parse_utc(evento["ocorrido_em"])
    event_id = evento["event_id"]
    if event_id in estado["ids"]:
        return estado, []

    ids = []
    datas = {}
    for id_antigo in estado["ids"]:
        antigo = parse_utc(estado["datas"][id_antigo])
        if instante - antigo <= janela:
            ids.append(id_antigo)
            datas[id_antigo] = estado["datas"][id_antigo]
    ids.append(event_id)
    datas[event_id] = evento["ocorrido_em"]
    novo = {"ids": ids, "datas": datas}

    if len(ids) >= quantidade:
        complexo = evento_complexo(
            "pico_de_cancelamentos",
            evento["academia"],
            evento,
            agora,
            janela,
            ids[-quantidade:],
            atrasado=False,
        )
        novo["ids"] = []
        novo["datas"] = {}
        return novo, [complexo]
    return novo, []
