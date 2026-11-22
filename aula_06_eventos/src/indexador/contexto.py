from __future__ import annotations

from pathlib import Path


CONTRATO_CONTEXTO = {
    "event_id",
    "tipo",
    "ocorrido_em",
    "regiao",
    "academia",
    "aluno",
    "turma",
    "faixa",
    "origem",
    "motivo",
    "dispositivo_id",
}


def montar_contexto(
    pergunta: str,
    trechos: list[dict],
    numeros: dict,
    consultas: list[str],
    destino: str | Path,
) -> dict:
    for trecho in trechos:
        extras = set(trecho) - {"event_id", "_score", "academia", "motivo"}
        if extras:
            raise ValueError(
                "contexto contem campo fora do contrato: "
                + ", ".join(sorted(extras))
            )
    markdown = [
        "# Contexto da pergunta",
        "",
        f"Pergunta: {pergunta}",
        "",
        "## Trechos recuperados",
    ]
    for trecho in trechos:
        markdown.append(
            "- "
            f"event_id={trecho.get('event_id')}; "
            f"pontuacao={trecho.get('_score')}; "
            f"academia={trecho.get('academia')}; "
            f"motivo={trecho.get('motivo')}"
        )
    markdown += ["", "## Numeros agregados"]
    for nome, valor in numeros.items():
        if isinstance(valor, dict):
            tipo_numero = valor.get("tipo", "estimativa")
            periodo = valor.get("periodo", "periodo nao informado")
            markdown.append(f"- {nome}: {valor.get('valor')} ({tipo_numero}; {periodo})")
        else:
            markdown.append(f"- {nome}: {valor}")
    markdown += ["", "## Consultas"]
    for consulta in consultas:
        markdown.extend(["```", consulta, "```"])

    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(markdown), encoding="utf-8")
    return {"pergunta": pergunta, "trechos": trechos, "numeros": numeros}
