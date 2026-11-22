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

## Etapa 00 — preparação adicional

- Data: 2026-11-22
- Prompt recebido:

  > [C] Personagem
  > Você é engenheiro de dados que prepara a pasta de trabalho do grupo
  > para usar o ClickHouse da turma. Não lê nem imprime o .env.
  >
  > [R] Pedido
  > Na pasta aula_05_dimensional/:
  > 1. Confira que rodar_sql.py, AGENTS.md e .env.example estão na pasta
  >    e que o .env está ignorado pelo Git (git check-ignore .env).
  > 2. Crie as pastas specs/, sql/ e docs/adr/, se não existirem.
  > 3. Crie docs/prompts.md com o título "Registro de prompts".
  > 4. Rode e mostre a saída de três consultas com python rodar_sql.py -q:
  >    a) o usuário e a versão do servidor;
  >    b) as linhas por data_tag em mackenzie.db_ingestion;
  >    c) um exemplo de data_json por data_tag (toJSONString, LIMIT 1 BY).
  >
  > [E] Exemplos
  > python rodar_sql.py -q "SELECT currentUser(), version()"
  >   -> turma | 25.8.33.6
  > Contagem esperada: livros 1000, ptax 40, telemetria 31265.
  >
  > [A] Ajustes
  > - Só SELECT. Nenhum objeto é criado no banco nesta etapa.
  > - Use os nomes das variáveis do .env, nunca os valores.
  > - Se GRUPO ainda estiver como g00, pare e peça o número do grupo:
  >   g00 é o prefixo do professor.
  >
  > [T] Tipo de saída
  > docs/prompts.md criado e as três saídas copiadas na resposta.
  >
  > [E] Extras
  > Leia AGENTS.md. Mostre o plano, espere meu ok, execute, registre este
  > prompt em docs/prompts.md e pare.

- Confirmação: execução autorizada pelo usuário.

## Etapa 03 — documentação de views

- Data: 2026-11-22
- Prompt recebido:

  > [C] Personagem
  > Você é engenheiro de dados que documenta para o time como cada objeto
  > do grupo no banco mackenzie funciona. Explica mecanismo e consequência.
  >
  > [R] Pedido
  > Criar docs/views.md com comparação de VIEW, MATERIALIZED VIEW ... TO
  > incremental e MATERIALIZED VIEW ... REFRESH refreshable, consequências
  > da incremental e objetos g00 confirmados por system.tables.
  >
  > [A] Ajustes
  > - Nenhum DDL nesta etapa.
  > - WINDOW VIEW fora de escopo; LIVE VIEW obsoleta.
  > - EXPLAIN de view comum marcado como pendente para a Etapa 05.

- Comando registrado:

  ```bash
  python sql/rodar_sql.py -q "SELECT name, engine, engine_full, total_rows FROM system.tables WHERE database='mackenzie' AND startsWith(name,'g00_') ORDER BY name"
  ```

  ```sql
  SELECT name, engine, engine_full, total_rows
  FROM system.tables
  WHERE database='mackenzie' AND startsWith(name,'g00_')
  ORDER BY name;
  ```

- Confirmação: execução autorizada pelo usuário.

## Saída da Etapa 02

Comandos executados:

```bash
python sql/rodar_sql.py -f sql/001_dimensoes_e_fatos.sql
python sql/rodar_sql.py -q "SELECT count() AS linhas FROM mackenzie.g00_fato_preco_livro FINAL"
python sql/rodar_sql.py -f sql/002_carga_historico.sql
python sql/rodar_sql.py -f sql/002_carga_historico.sql
python sql/rodar_sql.py -f sql/005_consultas.sql
```

Contagem antes da carga:

```text
linhas
UInt64
0
```

Dimensão de data após recarga:

```text
linhas  731
chaves  731
```

Fato de livros após carga:

```text
linhas
UInt64
1000
```

Teste do grão:

```text
fato                         modo       linhas  chaves
g00_fato_preco_livro         sem FINAL  2000    1000
g00_fato_cotacao_ptax        sem FINAL  80      40
g00_fato_leitura_telemetria  sem FINAL  57600   28800
g00_fato_alerta_direcao      sem FINAL  138     69
g00_fato_alerta_direcao      com FINAL  69      69
g00_fato_preco_livro         com FINAL  1000    1000
g00_fato_cotacao_ptax        com FINAL  40      40
g00_fato_leitura_telemetria  com FINAL  28800   28800
```

Roteamento de telemetria:

```text
destino             linhas
alerta              69
descarte ERR SAT    932
descarte RADIO      1464
leitura barra       22432
leitura espaço      6368
```

Os arquivos `001`, `002` e `005` foram criados em `sql/`.
`rodar_sql.py` passou a aceitar SELECT, WITH, CREATE TABLE,
CREATE MATERIALIZED VIEW, CREATE VIEW, INSERT e TRUNCATE restrito a
`mackenzie.g00_dim_data`.

## Etapa 02 — DDL dimensional no ClickHouse

- Data: 2026-11-22
- Prompt recebido:

  > [C] Personagem
  > Você é engenheiro de dados que escreve DDL para ClickHouse 25.8.
  >
  > [R] Pedido
  > Criar 001_dimensoes_e_fatos.sql, 002_carga_historico.sql e
  > 005_consultas.sql para dimensões, fatos, views incrementais,
  > carga histórica e testes de grão e classificação de telemetria.
  >
  > [A] Ajustes
  > - ReplacingMergeTree com versao_ms; AggregatingMergeTree para caminhão.
  > - datas em America/Sao_Paulo.
  > - ERR SAT e #RADIO ficam fora dos fatos.
  > - adaptar rodar_sql.py para DDL/INSERT e arquivos SQL.
  >
  > [T] Tipo de saída
  > três arquivos SQL comentados e saídas da contagem antes da carga
  > e das consultas 1 e 2.

- Confirmação: execução autorizada pelo usuário.

## Etapa 01 — modelo dimensional

- Data: 2026-11-22
- Prompt recebido:

  > [C] Personagem
  > Você é engenheiro de dados que modela no estilo de Kimball. Declara o
  > grão antes de qualquer coluna e não escreve DDL nesta etapa.
  >
  > [R] Pedido
  > Crie specs/04_modelo_dimensional.md a partir de mackenzie.db_ingestion
  > (livros, ptax e telemetria), com quatro fatos, dimensões g00, testes
  > do grão com FINAL, diagrama Mermaid e matriz de barramento.
  >
  > [A] Ajustes
  > - tipo_boletim da PTAX é dimensão degenerada.
  > - posição e alerta são fatos separados.
  > - ERR SAT e #RADIO são descarte.
  > - nenhuma coluna é número sem consulta que o gere.

- Confirmação: execução autorizada pelo usuário.
