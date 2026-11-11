# Registro de prompts

## Etapa 00 — preparação

- Data: 2026-11-07
- Prompt recebido:

  > [C] Personagem
  > Você é engenheiro de dados e prepara a pasta de trabalho da Aula 05.
  > Todo SQL vai ao ClickHouse da turma pela interface HTTPS, com o
  > rodar_sql.py. Nesta aula não há Docker nem cliente local.
  >
  > [R] Pedido
  > 1. Crie aula_05_dimensional/ com as pastas sql/, specs/ e docs/.
  > 2. Copie para ela o rodar_sql.py, o AGENTS.md e o .env.example do
  >    laboratório da Aula 05.
  > 3. Crie o .env a partir do .env.example, com a senha que vou colar e
  >    GRUPO com o número do nosso grupo; ponha .env no .gitignore.
  > 4. Crie docs/prompts.md com o título "Registro de prompts".
  > 5. Teste a conexão com as três consultas dos exemplos e mostre a
  >    saída.
  >
  > [E] Exemplos
  > python rodar_sql.py -q "SELECT currentUser(), version()"
  > python rodar_sql.py -q "SELECT data_tag, count() AS linhas FROM mackenzie.db_ingestion GROUP BY data_tag ORDER BY data_tag"
  > python rodar_sql.py -q "SELECT data_tag, toJSONString(data_json) FROM mackenzie.db_ingestion LIMIT 1 BY data_tag"
  >
  > Esperado: turma e 25.8.33.6; livros 1.000, ptax 40,
  > telemetria 31.265.
  >
  > [A] Ajustes
  > - GRUPO é g seguido de dois dígitos (g01, g07).
  > - Não imprima o .env nem a senha; cite os nomes das variáveis.
  > - git check-ignore .env tem de imprimir .env.
  > - Em mackenzie.db_ingestion, só SELECT.
  > - Nenhum pip install: o rodar_sql.py usa só a biblioteca padrão.
  > - Se o agente lê outro arquivo de instruções (CLAUDE.md, GEMINI.md),
  >   faça esse arquivo apontar para o AGENTS.md.
  >
  > [T] Tipo de saída
  > A árvore da pasta, a saída das três consultas e a seção "Etapa 00"
  > em docs/prompts.md, sem a senha.
  >
  > [E] Extras
  > Leia AGENTS.md. Mostre o plano, espere meu ok, execute, registre o
  > prompt e pare.

  Confirmação: `ok, 06, https://clickhouse.afonsolelis.tech` (porta 443), usuário `turma`, senha `[OMITIDA]`. A senha não foi registrada.
- Arquivos criados ou alterados: `AGENTS.md`, `.env.example`, `.gitignore`, `sql/rodar_sql.py`, `docs/prompts.md`, `.env`.
