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


def validar_consulta(sql: str) -> str:
    consulta = sql.strip()
    if consulta.endswith(";"):
        consulta = consulta[:-1].rstrip()
    if not consulta:
        sys.exit("Consulta vazia.")
    prefixo = consulta.upper()
    permitido = (
        prefixo.startswith("SELECT")
        or prefixo.startswith("WITH")
        or prefixo.startswith("CREATE TABLE")
        or prefixo.startswith("CREATE MATERIALIZED VIEW")
        or prefixo.startswith("CREATE VIEW")
        or prefixo.startswith("INSERT")
        or prefixo.startswith("TRUNCATE TABLE")
    )
    if not permitido:
        sys.exit("Comando não permitido.")
    if prefixo.startswith("TRUNCATE TABLE"):
        if "mackenzie.g00_dim_data" not in consulta.lower():
            sys.exit("TRUNCATE permitido somente em mackenzie.g00_dim_data.")
    if "mackenzie.db_ingestion" in consulta.lower():
        mv_seletiva = (
            prefixo.startswith("CREATE MATERIALIZED VIEW")
            and re.search(r"(?is)\bAS\s+(SELECT|WITH)\b", consulta) is not None
        )
        carga_seletiva = (
            prefixo.startswith("INSERT")
            and re.search(r"(?is)\bSELECT\b", consulta) is not None
            and re.search(r"(?is)\bFROM\s+mackenzie\.db_ingestion\b", consulta) is not None
        )
        direta = prefixo.startswith("SELECT") or prefixo.startswith("WITH")
        if not (direta or mv_seletiva or carga_seletiva):
            sys.exit("db_ingestion aceita somente SELECT ou cargas INSERT ... SELECT.")
    return consulta


def dividir_comandos(sql: str) -> list[str]:
    comandos = []
    atual = []
    aspas = None
    i = 0
    while i < len(sql):
        char = sql[i]
        if char in ("'", '"', "`"):
            if aspas is None:
                aspas = char
            elif aspas == char and (i == 0 or sql[i - 1] != "\\"):
                aspas = None
        if char == ";" and aspas is None:
            comando = "".join(atual).strip()
            if comando:
                comandos.append(comando)
            atual = []
        else:
            atual.append(char)
        i += 1
    final = "".join(atual).strip()
    if final:
        comandos.append(final)
    return [limpar_comentarios(comando) for comando in comandos if limpar_comentarios(comando)]


def limpar_comentarios(sql: str) -> str:
    linhas = []
    for linha in sql.splitlines():
        sem_linha = re.sub(r"--.*$", "", linha).strip()
        if sem_linha:
            linhas.append(sem_linha)
    texto = "\n".join(linhas)
    while texto.startswith("/*"):
        fim = texto.find("*/")
        if fim < 0:
            break
        texto = texto[fim + 2:].strip()
    return texto


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", help="consulta SQL")
    parser.add_argument("-f", "--file", help="arquivo SQL local")
    args = parser.parse_args()

    if (args.query is None) == (args.file is None):
        parser.error("use -q/--query ou -f/--file")

    carregar_env(pathlib.Path(".env"))
    url = exigir("CLICKHOUSE_URL").rstrip("/")
    user = exigir("CLICKHOUSE_USER")
    password = exigir("CLICKHOUSE_PASSWORD")
    if args.file:
        caminho = pathlib.Path(args.file)
        if not caminho.is_file():
            sys.exit(f"Arquivo SQL não encontrado: {caminho}")
        comandos = dividir_comandos(caminho.read_text(encoding="utf-8"))
    else:
        comandos = [args.query]

    for sql in comandos:
        consulta = validar_consulta(sql)
        request = urllib.request.Request(
            url + "/?" + urllib.parse.urlencode({"default_format": "TabSeparatedWithNamesAndTypes"}),
            data=consulta.encode("utf-8"),
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
