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
