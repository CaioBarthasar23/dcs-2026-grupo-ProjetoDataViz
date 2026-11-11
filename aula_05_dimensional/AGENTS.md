# AGENTS.md · aula_05_dimensional

Leia este arquivo antes de trabalhar nesta pasta.

## Escopo e restrições

- Todo SQL desta aula é executado no ClickHouse da turma pela interface HTTPS, usando `sql/rodar_sql.py`.
- Não usar Docker, cliente local, nem instalar pacotes. O utilitário usa somente a biblioteca padrão do Python.
- Credenciais ficam somente em `.env`, que não é versionado. Nunca imprima ou registre o conteúdo do `.env` ou a senha.
- `GRUPO` tem o formato `g` seguido de dois dígitos.
- Na tabela `mackenzie.db_ingestion`, execute somente consultas `SELECT`.
- Trabalhe somente dentro de `aula_05_dimensional/`.
- Se houver outro arquivo de instruções, como `CLAUDE.md` ou `GEMINI.md`, ele deve apontar para este `AGENTS.md`.

## Etapa 00

Preparação do ambiente e registro do prompt em `docs/prompts.md`. Pare ao concluir esta etapa.
