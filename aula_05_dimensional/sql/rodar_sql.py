"""Executa uma consulta no ClickHouse da turma pela interface HTTPS."""

import argparse
import base64
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def carregar_env(caminho: pathlib.Path) -> None:
    """Carrega KEY=VALUE sem sobrescrever variáveis já definidas no ambiente."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def exigir(nome: str) -> str:
    valor = os.environ.get(nome, "")
    if not valor:
        sys.exit(f"Variável {nome} ausente. Copie .env.example para .env e preencha.")
    return valor


def validar_select(sql: str) -> str:
    consulta = sql.strip()
    if consulta.endswith(";"):
        consulta = consulta[:-1].rstrip()
    if not consulta or not re.match(r"(?is)^SELECT\b", consulta):
        sys.exit("Somente uma consulta SELECT é permitida.")
    if ";" in consulta:
        sys.exit("Informe somente uma consulta SELECT por execução.")
    return consulta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", required=True, help="consulta SELECT")
    args = parser.parse_args()

    carregar_env(pathlib.Path(".env"))
    url = exigir("CLICKHOUSE_URL").rstrip("/")
    user = exigir("CLICKHOUSE_USER")
    password = exigir("CLICKHOUSE_PASSWORD")
    sql = validar_select(args.query)

    request = urllib.request.Request(
        url + "/?" + urllib.parse.urlencode({"default_format": "TabSeparatedWithNamesAndTypes"}),
        data=sql.encode("utf-8"),
        headers={
            "Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode(),
            "Content-Type": "text/plain; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(response.read().decode("utf-8"), end="")
    except urllib.error.HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="replace").strip()
        print(f"ClickHouse HTTP {exc.code}: {detalhe}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Falha na conexão HTTPS: {exc.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
