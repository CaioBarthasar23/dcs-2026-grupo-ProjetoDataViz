# Registro de prompts

## Etapa 01 · Personas e objetivos

- **Data:** 2026-11-02.
- **Quem enviou: CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/00_persona.md`, `docs/01_objetivos.md`, `docs/prompts.md`.
- **Confirmação do plano:**

```text
Ok, pode executar, com estas restrições. (1) Altere somente docs/00_persona.md, docs/01_objetivos.md e docs/prompts.md; não leia o .env, não acesse o Railway. (2) Personas: P1 time dono de fonte, P2 analista no ClickHouse, P3 engenheiro que opera a ingestão e é acionado quando a/exitlgo para; cada uma com a decisão que toma. (3) Objetivos OBJ-01... com persona, métrica, como medir (comando ou consulta) e meta; cubra P1 (fonte nova sem mudar o banco), P2 (dado consultável logo após o 202 do POST) e P3 (saber o que parou e recuperar sem perder dado). (4) Meta sem origem fica “hipótese, validação pendente”; “poucos segundos” não é meta, não invente números. (5) Domínios: telemetria, livros e ptax. Fora de escopo: schema por domínio, DLX, prefetch, ReplacingMergeTree, modelo dimensional e painel. (6) No prompts.md, registre data, quem enviou, agente e modelo, arquivos alterados e o prompt literal. Nada de código.
```

- **Prompt literal recebido:**

```text
[C] Personagem
Você é gerente de produto de dados. Descreve quem empurra dado para a
plataforma, quem consome e que decisão cada um toma. Não escreve código.

[R] Pedido
Crie dois arquivos:
1. docs/00_persona.md com três personas: P1 time dono de uma fonte que
   precisa entregar dado novo sem pedir tabela nova; P2 analista que
   consulta o dado no ClickHouse; P3 engenheiro de dados que opera o
   servidor de ingestão e é acionado quando algo para.
2. docs/01_objetivos.md com objetivos OBJ-01... ligados às personas,
   cada um com métrica, como medir (comando ou consulta) e meta.

[E] Exemplos
## OBJ-01 · Fonte nova sem mudar o banco
- Persona: P1.
- Métrica: passos para uma fonte nova começar a gravar.
- Como medir: incluir a tag em DOMINIOS no .env e reiniciar o servidor;
  nenhum CREATE TABLE.
- Meta: hipótese, validação pendente.
## OBJ-02 · Dado consultável em poucos segundos
- Persona: P2.
- Métrica: tempo entre o 202 do POST e a linha no ClickHouse.
- Como medir: script de medição da Etapa 09.

[A] Ajustes
- Domínios desta aula: telemetria (Aula 02), livros e ptax (Aula 03).
- Fora de escopo: schema de cada domínio (Aula 07), DLX, prefetch e
  ReplacingMergeTree (Aula 06), modelo dimensional (Aula 05), painel.
- Valor sem origem: "hipótese, validação pendente".
- Nada de código.

[T] Tipo de saída
Markdown. 00_persona.md com até 60 linhas; 01_objetivos.md com até 70
linhas e as seções Objetivos, Restrições, Fora de escopo e Hipóteses.

[E] Extras
Leia AGENTS.md. Mostre o plano, espere meu ok, escreva, registre o
prompt em docs/prompts.md e pare.
```

## Etapa 02 · Contrato do envelope e exemplos

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `docs/prompts.md`, `specs/01_contrato_envelope.md`, `specs/exemplos/valido_telemetria_linha.json`, `specs/exemplos/valido_livros_objeto.json`, `specs/exemplos/valido_ptax_lista.json`, `specs/exemplos/invalido_422_sem_data_tag.json`, `specs/exemplos/invalido_422_data_tag_desconhecida.json`, `specs/exemplos/invalido_422_data_texto.json`, `specs/exemplos/invalido_422_data_lista_vazia.json`, `specs/exemplos/invalido_422_lista_com_texto.json`, `specs/exemplos/invalido_422_campo_extra_timestamp.json`, `specs/exemplos/invalido_400_nao_json.txt`, `specs/exemplos/invalido_422_sem_data.json`, `specs/exemplos/invalido_413_corpo_grande_demais.json`.
- **Confirmação do plano:** confirmado pelo aluno.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é engenheiro de dados responsável pelo contrato entre quem produz e
quem consome. Escreve regras verificáveis, sem código.

[R] Pedido
Crie specs/01_contrato_envelope.md e copie fixtures/exemplos/ para
specs/exemplos/:
1. O envelope: campos data_tag e data, tipos, obrigatoriedade.
2. Regras CT-01...: data_tag está em DOMINIOS; data é objeto ou lista
   não vazia de objetos; envelope fechado (campo extra é recusado);
   corpo HTTP até HTTP_MAX_BYTES (1 MiB); o produtor não manda
   timestamp de ingestão.
3. O que o servidor acrescenta: timestamp unix em milissegundos.
4. Respostas: 202 aceito, 422 envelope inválido (com o motivo), 413
   corpo grande demais, 400 corpo que não é JSON.
5. O que o contrato não cobre: os campos dentro de data.
6. Exemplos: os 10 arquivos de specs/exemplos/ (3 válidos, 6 com 422,
   1 com 400; o código esperado está no nome), citados nas regras.

[E] Exemplos
specs/exemplos/valido_livros_objeto.json
{"data_tag": "livros", "data": {"upc": "a897fe39b1053632",
 "titulo": "A Light in the Attic", "preco_gbp": 51.77, ...}}
specs/exemplos/invalido_422_data_tag_desconhecida.json
{"data_tag": "vendas", "data": {"id": 1}}
-> 422, motivo: data_tag 'vendas' fora de DOMINIOS

[A] Ajustes
- Toda regra CT tem pelo menos um exemplo inválido; se faltar, crie
  outro arquivo no mesmo padrão de nome (invalido_<código>_<caso>).
- Os campos dentro de data são os do bronze da Aula 03 e da linha de
  telemetria da Aula 02; não renomeie nem traduza.
- Nada de código. Nada de schema por domínio (Aula 07).

[T] Tipo de saída
Markdown com até 90 linhas, tabela "regra | exemplo que viola |
resposta".

[E] Extras
Leia AGENTS.md, docs/00_persona.md e fixtures/. Mostre o plano, espere
meu ok, escreva, registre o prompt e pare.
```

### Complemento à Etapa 02 · Tipo de `data_tag`

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `docs/prompts.md`, `specs/01_contrato_envelope.md`, `specs/exemplos/invalido_422_data_tag_tipo.json`.
- **Prompt literal recebido:** `pode acrescentar`

## Etapa 03 · Requisitos funcionais e não funcionais

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `specs/02_requisitos.md`, `docs/prompts.md`.
- **Confirmação do plano:** ok do aluno.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é analista de requisitos. Escreve requisitos que um teste
consegue verificar.

[R] Pedido
Crie specs/02_requisitos.md com:
1. Requisitos funcionais RF-01... no formato Dado, Quando, Então:
   receber por HTTP e publicar na fila; receber pela fila; recusar
   envelope inválido (HTTP 422; fila: raw/ingestao_rejeitados com o
   motivo); gravar cada lote no lake (raw em JSON Lines e bronze em
   Parquet); inserir no ClickHouse; gravar o manifesto do lote;
   confirmar (ack) a mensagem só depois de tudo gravado.
2. Requisitos não funcionais RNF-01... com número e forma de medir:
   tempo até consultável, perda zero com o processo derrubado, fonte
   nova sem DDL, reprocesso do ClickHouse a partir do lake.
3. Matriz RF/RNF x OBJ.

[E] Exemplos
## RF-03 · Envelope inválido pela fila
Dado uma mensagem na fila ingestao com data_tag ausente
Quando o consumidor a lê
Então existe um objeto em raw/ingestao_rejeitados/data=D/ com a
mensagem e o motivo
E a mensagem recebe ack
E nenhuma linha nova aparece em ingestao.db_ingestion
## RNF-02 · Nada se perde se o processo cair
Medida: publicar 10.000 envelopes, matar o processo com kill -9 no
meio, reiniciar; linhas distintas no ClickHouse = 10.000.
Duplicatas são aceitas nesta aula e contadas.

[A] Ajustes
- Entrega pelo menos uma vez: duplicata é possível e declarada.
- Metas sem origem: "hipótese, validação pendente".
- Preserve P, OBJ e CT.

[T] Tipo de saída
Markdown com até 120 linhas.

[E] Extras
Leia AGENTS.md, docs/ e specs/01_contrato_envelope.md. Mostre o plano,
espere meu ok, escreva, registre o prompt e pare.
```

## Etapa 04 · Modelo de dados

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `specs/03_modelo_de_dados.md`, `docs/prompts.md`.
- **Arquivos conferidos sem alteração:** `sql/001_db_ingestion.sql`.
- **Confirmação do plano:** confirmado pelo aluno.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é engenheiro de dados. Desenha onde e como o dado fica guardado,
com DDL e layout de chaves, sem código Python.

[R] Pedido
Crie specs/03_modelo_de_dados.md e confira sql/001_db_ingestion.sql:
1. Tabela ingestao.db_ingestion: timestamp UInt64 (unix ms da
   ingestão), data_json JSON (o dado recebido, no tipo JSON do
   ClickHouse, com datas e horas inferidas como texto), data_tag
   LowCardinality(String). Motor, ORDER BY e PARTITION BY, com o
   porquê de cada escolha.
2. Lake, na organização da Aula 03, com D = data do recebimento em
   America/Sao_Paulo e o mesmo nome de lote nas três chaves:
   - raw/ingestao/data_tag=X/data=D/lote_<HHMMSS>_<id>.jsonl: um
     envelope por linha, como chegou, com recebido_em_ms;
   - bronze/ingestao/data_tag=X/data=D/lote_<HHMMSS>_<id>.parquet:
     uma linha por objeto de data, colunas timestamp (UBIGINT) e
     data_json (VARCHAR), ZSTD; data_tag e data ficam no caminho;
   - raw/_manifestos/ingestao/data=D/lote_<HHMMSS>_<id>.json: id do
     lote, mensagens e linhas por data_tag, chaves gravadas, bytes e
     SHA-256 de cada arquivo, tempos de cada passo e status;
   - raw/ingestao_rejeitados/data=D/rejeitado_<HHMMSS>_<id>.json, com
     recebido_em_ms, motivo e corpo.
3. Uma linha por objeto de data (lista vira várias linhas, todas com o
mesmo timestamp do envelope).
4. Como recriar o bronze a partir do raw e a tabela do ClickHouse a
partir do bronze, em comandos.

[E] Exemplos
| timestamp     | data_tag | data_json                                   |
|---------------|----------|---------------------------------------------|
| 1793452800123 | livros   | {"upc":"a897fe39b1053632","preco_gbp":51.77} |

[A] Ajustes
- Não troque nomes nem tipos das três colunas.
- Explique por que unix em milissegundos e não segundos nem DateTime.
- Diga o que se ganha guardando data_json no tipo JSON e o que se perde
  em relação ao texto que chegou, e onde esse texto continua guardado.
- Explique por que o INSERT desliga a inferência de datas
  (input_format_try_infer_dates e input_format_try_infer_datetimes).
- Diga por que a chave do lote não é determinística, ao contrário das
  chaves da Aula 03.
- Nada de colunas por domínio (é a discussão do TBL da Aula 05).

[T] Tipo de saída
Markdown com até 100 linhas, com o DDL em bloco sql.

[E] Extras
Leia AGENTS.md, specs/ e sql/001_db_ingestion.sql. Mostre o plano,
espere meu ok, escreva, registre o prompt e pare.
```

## Etapa 05 · Arquitetura e ADRs

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `docs/arquitetura.md`, `docs/adr/ADR-001.md`, `docs/adr/ADR-002.md`, `docs/adr/ADR-003.md`, `docs/adr/ADR-004.md`, `docs/adr/ADR-005.md`, `docs/prompts.md`.
- **Confirmação do plano:** ok pelo aluno.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é arquiteto de software de dados. Desenha componentes e sequência
e registra cada decisão com alternativas.

[R] Pedido
1. docs/arquitetura.md com:
   - diagrama de componentes em Mermaid: produtor HTTP, produtor AMQP,
     API, fila ingestao, consumidor, buffer de micro-lote, gravador do
     raw, gravador do bronze (DuckDB), gravador do manifesto, gravador
     do ClickHouse, RustFS, ClickHouse;
   - diagrama de sequência do caminho feliz e de uma falha do
     ClickHouse no meio do lote.
2. ADRs em docs/adr/ (Contexto, Decisão, Alternativas, Consequências,
   Custos, Previsão de esforço em HH, Status: Proposta):
   ADR-001 HTTP publica na fila em vez de gravar direto
   ADR-002 raw e bronze antes do ClickHouse
   ADR-003 manifesto do lote depois do ClickHouse e ack só depois de
           tudo gravado
   ADR-004 micro-lote por tamanho ou tempo (N e T no .env)
   ADR-005 tabela de três colunas com data_json no tipo JSON

[E] Exemplos
sequenceDiagram
  participant P as Produtor
  participant A as API
  participant Q as Fila ingestao
  participant C as Consumidor
  P->>A: POST /ingest
  A->>Q: publish (persistente)
  A-->>P: 202
  Q->>C: entrega
  C->>C: acumula até N ou T
  C->>RustFS: raw, envelopes do lote em JSON Lines
  C->>RustFS: bronze, Parquet do lote
  C->>ClickHouse: INSERT do lote
  C->>RustFS: manifesto do lote com status ok
  C->>Q: ack multiple

[A] Ajustes
- Cada ADR liga a um RF ou RNF.
- Sem ponto e vírgula dentro de rótulo Mermaid.
- Prefetch, DLX e deduplicação ficam como "Aula 06" nas consequências.
- Custos de cada ADR, da decisão e de cada alternativa descartada:
  infraestrutura (serviços no Railway: crédito de teste de US$ 5 por
  até 30 dias, depois plano Free de US$ 1/mês; no ambiente local, zero)
  e mão de obra (quem do grupo faz cada atividade).
- Previsão de esforço em HH (homem-hora = pessoas x horas) numa tabela
  atividade | HH da decisão | HH da alternativa | base da estimativa,
  com as linhas implementar, testar, documentar e operar por mês.
  Feche com o total em HH e o custo = HH x valor-hora, com o
  valor-hora como parâmetro que o grupo declara.
- Estimativa sem base (medição, código existente ou tarefa parecida já
  feita) vira pergunta para o grupo, não número.

[T] Tipo de saída
Markdown; arquitetura.md com até 120 linhas; cada ADR com até 60.

[E] Extras
Leia AGENTS.md, docs/ e specs/. Mostre o plano, espere meu ok, escreva,
registre o prompt e pare.
```

## Etapa 06 · Plano, tarefas e testes vermelhos

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `specs/plan.md`, `specs/tasks.md`, `tests/test_contrato.py`, `tests/test_api.py`, `tests/test_integracao.py`, `pytest.ini`, `docs/prompts.md`.
- **Confirmação do plano:** ok pelo aluno.

- **Prompt literal recebido:**

```text
[C] Personagem
Você é engenheiro de software. Quebra a construção em tarefas de até
30 minutos e escreve os testes antes do código.

[R] Pedido
1. specs/plan.md e specs/tasks.md (T-01...), cada tarefa com RF/RNF,
   arquivo e teste que a fecha.
2. tests/test_contrato.py: um teste por arquivo de specs/exemplos/
   (válido aceita, inválido recusa com o motivo; o código esperado
   está no nome do arquivo).
3. tests/test_api.py: POST válido devolve 202, inválido 422, corpo que
   não é JSON 400, corpo grande 413 (com a publicação na fila
   substituída por um dublê).
4. tests/test_integracao.py: com os três serviços do compose, publica
   20 envelopes e confere 20 linhas no ClickHouse e no lake (marcado
   com pytest.mark.integracao).
Rode pytest -q e mostre que os testes falham pelo motivo certo.

[E] Exemplos
@pytest.mark.parametrize("arquivo", sorted(EXEMPLOS.glob("invalido_422_*.json")))
def test_envelope_invalido_e_recusado(arquivo):
    with pytest.raises(EnvelopeInvalido):
        validar(arquivo.read_bytes(), DOMINIOS)

[A] Ajustes
- Ainda não escreva src/. Os testes importam de src.contrato, src.api,
  src.consumidor.
- Testes de integração usam o bucket teste e uma fila de teste.

[T] Tipo de saída
Markdown para plan e tasks; Python para tests/.

[E] Extras
Leia AGENTS.md, specs/ e docs/arquitetura.md. Mostre o plano, espere
meu ok, escreva, rode, registre o prompt e pare.
```

## Etapa 07 · Configuração, contrato e API

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `src/config.py`, `src/contrato.py`, `src/api.py`, `tests/test_contrato.py`, `tests/test_api.py`, `pytest.ini`, `specs/tasks.md`, `docs/prompts.md`.
- **Confirmação:** o aluno autorizou atualizar `tests/test_contrato.py` para a assinatura nova.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é engenheiro de software Python. Implementa só o que as tarefas
pedem, uma por vez, até os testes ficarem verdes.

[R] Pedido
Implemente as tarefas do contrato e da API:
1. src/config.py: lê o .env (DOMINIOS, RabbitMQ, ClickHouse, RustFS
   pelas variáveis S3_*, FLUSH_N, FLUSH_SEGUNDOS, HTTP_MAX_BYTES).
2. src/contrato.py: validar(corpo, dominios) devolve (data_tag, lista
   de objetos), ou levanta CorpoNaoJson ou EnvelopeInvalido com o
   motivo.
3. src/api.py: FastAPI com POST /ingest (202/400/413/422) que publica
   o corpo na fila ingestao (durável, mensagem persistente, com
   confirmação do broker e o cabeçalho recebido_em_ms) e GET /health.
Rode pytest -q tests/test_contrato.py tests/test_api.py.

[E] Exemplos
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/ingest \
  -H 'content-type: application/json' \
  --data-binary @specs/exemplos/valido_livros_objeto.json
202

[A] Ajustes
- Uma tarefa por vez; mostre o diff de cada uma.
- Não grave no lake nem no ClickHouse pela API.
- Sem segredo no código.

[T] Tipo de saída
Python em src/; testes verdes.

[E] Extras
Leia AGENTS.md, specs/tasks.md e tests/. Registre o prompt, marque as
tarefas feitas em tasks.md e pare.
```

## Etapa 08 · Lake, ClickHouse, consumidor e servidor

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `src/lake.py`, `src/clickhouse.py`, `src/consumidor.py`, `src/servidor.py`, `tests/test_integracao.py`, `tests/test_lake.py`, `tests/test_clickhouse.py`, `tests/test_consumidor.py`, `specs/tasks.md`, `docs/prompts.md`.
- **Confirmação:** o aluno autorizou ajustar `tests/test_integracao.py` para iniciar o servidor.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é engenheiro de software Python. Implementa o consumidor e os
gravadores, uma tarefa por vez.

[R] Pedido
1. src/lake.py, no layout de specs/03_modelo_de_dados.md:
   - gravar_raw: um JSON Lines por lote e data_tag, uma linha
     {"recebido_em_ms", "envelope"} por mensagem, com o corpo como
     chegou (quebras de linha trocadas por espaço);
   - gravar_bronze: Parquet ZSTD com timestamp e data_json escrito
     pelo DuckDB a partir de uma tabela Arrow (pyarrow, con.register,
     COPY para arquivo temporário) e enviado com boto3;
   - gravar_manifesto: o JSON do lote;
   - rejeitar: raw/ingestao_rejeitados/ com recebido_em_ms, motivo e
     corpo.
   Cada PUT leva os metadados sha256 e lote; o SHA-256 vai também
   para o manifesto.
2. src/clickhouse.py: insere o lote em ingestao.db_ingestion com
   clickhouse-connect, num INSERT só.
3. src/consumidor.py: lê a fila ingestao, valida de novo, rejeitado vai
   para raw/ingestao_rejeitados com o motivo e recebe ack; válido entra
   no buffer; flush a cada FLUSH_N envelopes ou FLUSH_SEGUNDOS; no
   flush, raw, depois bronze, depois ClickHouse, depois manifesto com
   status ok, depois ack multiple da última mensagem do lote. Se o
   ClickHouse falhar, grave o manifesto com status erro_clickhouse e
   não dê ack.
4. src/servidor.py: sobe a API e o consumidor (thread) no mesmo
   processo.

[E] Exemplos
def flush(self, canal):
    lote = novo_lote(primeiro_timestamp)      # lote_<HHMMSS>_<id>
    self.lake.gravar_raw(...)                 # 1. raw, por data_tag
    self.lake.gravar_bronze(...)              # 2. bronze, por data_tag
    self.ch.inserir(linhas)                   # 3. ClickHouse, um INSERT
    self.lake.gravar_manifesto(...)           # 4. manifesto, status ok
    canal.basic_ack(self.ultima_tag_entrega, multiple=True)  # 5. ack

[A] Ajustes
- Se o lake ou o ClickHouse falhar, não dê ack: a fila reentrega.
- timestamp em unix ms: o cabeçalho recebido_em_ms da mensagem; sem
  ele, a hora do consumo.
- prefetch_count do consumidor pelo menos igual a FLUSH_N.
- Cliente do ClickHouse com async_insert de CLICKHOUSE_ASYNC_INSERT.
- Logs com o nome do lote, data_tag, tamanho e tempo de cada passo.

[T] Tipo de saída
Python em src/; pytest -q inteiro verde.

[E] Extras
Leia AGENTS.md, specs/, docs/adr/ e tests/. Registre o prompt, marque as
tarefas e pare.
```

## Etapa 09 · Produtores das fontes e conferência

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos criados ou alterados:** `src/config.py`, `src/produtores/__init__.py`, `src/produtores/_amqp.py`, `src/produtores/livros_http.py`, `src/produtores/ptax_fila.py`, `src/produtores/telemetria_fila.py`, `src/conferir.py`, `docs/prompts.md`.
- **Prompt literal recebido:**

```text
[C] Personagem
Você é engenheiro de dados. Liga as fontes das aulas anteriores ao
servidor e mede o que entra e o que sai.

[R] Pedido
1. src/produtores/livros_http.py: lê entrada/livros/*.jsonl (os testes
   usam fixtures/livros.jsonl) e manda um POST /ingest por livro.
2. src/produtores/ptax_fila.py: lê entrada/ptax/*.jsonl (testes:
   fixtures/ptax_cotacoes.jsonl) e publica na fila um envelope por
   arquivo, com a lista de cotações.
3. src/produtores/telemetria_fila.py: lê entrada/telemetria/*.txt
   (testes: fixtures/telemetria) e publica uma mensagem por linha,
   data = {arquivo, numero_linha, linha}, com arquivo =
   "entrada/telemetria/<nome>.txt".
4. src/conferir.py: por data_tag, linhas esperadas x linhas no
   ClickHouse x linhas no bronze x envelopes no raw x distintas por
   (timestamp, data_json); manifestos por status com a soma de
   linhas; a fila com mensagens e sem ack.

[E] Exemplos
data_tag    esperadas  clickhouse  bronze  raw_envelopes  distintas
livros           1000        1000    1000           1000       1000
ptax               40          40      40              1         40
telemetria      31265       31265   31265          31265      31265
manifestos ok: 65, linhas 32305

[A] Ajustes
- Produtor não conhece ClickHouse nem RustFS de destino; só a API ou
  a fila.
- Sem paralelismo nos produtores.

[T] Tipo de saída
Python; tabela da conferência no terminal.

[E] Extras
Leia AGENTS.md e specs/. Registre o prompt e pare.
```

## Etapa 10 · Casts DuckDB/ClickHouse e silver livros/PTAX

- **Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `sql/duckdb_cast.sql`, `sql/silver_livros_ptax.sql`, `docs/prompts.md`.
- **Confirmação:** o aluno aprovou a correção dos prefixos de leitura do RustFS antes da edição. `sql/clickhouse_cast.sql` permaneceu sem alteração.
- **Contrato consultado:** não existe `aula_03_api_scraping/README.md` neste workspace. Foram usados os tipos informados no prompt e o modelo em `aula_03_api_scraping/specs/03_modelo_de_dados.md`.

### Resultado da comparação

Tempos observados por instrução, com `python sql/rodar_sql.py` no DuckDB e `clickhouse-client --time --multiquery` no ClickHouse. Consultas equivalentes com ordenação de empate não garantida são comparadas pelos valores, não pela ordem.

| consulta | DuckDB | ClickHouse | tempo | igual? |
|---|---|---|---|---|
| 1 · contagem por domínio | livros 1.000; PTAX 40; telemetria 31.265 | livros 1.000; PTAX 40; telemetria 31.385 | 0,584 s / 0,025 s | parcial: ClickHouse tem 120 linhas extras de telemetria |
| 1a · raw contra contagem do ClickHouse | raw: livros 1.000 envelopes/1.000 linhas; PTAX 1/1 pela expressão SQL; telemetria 31.265/31.265. Leitura direta do raw confirma PTAX 1 envelope/40 linhas | livros 1.000; PTAX 40; telemetria 31.385 | 0,608 s / 0,025 s | parcial: expressão do SQL conta envelope PTAX como 1 linha; ClickHouse ainda tem 120 linhas de telemetria extras |
| 1b · manifestos | a consulta SQL falha: coluna `linhas` não existe; contagem direta dos objetos: 85 `ok`, 32.305 linhas | — | falha / — | não comparável |
| 2 · preço médio por categoria, top 10 | Default 152/34,39; Nonfiction 110/34,26; Sequential Art 75/34,57; Add a comment 67/35,80; Fiction 65/36,07; Young Adult 54/35,45; Fantasy 48/39,59; Romance 35/33,93; Mystery 32/31,72; Food and Drink 30/31,41 | mesmas dez categorias e valores | 0,078 s / 0,007 s | sim |
| 3 · preço médio por categoria, top 5 | Academic 13,12; Add a comment 35,80; Adult Fiction 15,36; Art 38,52; Autobiography 37,05 | mesmos cinco valores | 0,027 s / 0,006 s | sim |
| 4 · `from_json`, média e estoque por categoria | top 5: Default 34,39/1.345; Nonfiction 34,26/975; Sequential Art 34,57/686; Fiction 36,07/588; Add a comment 35,80/516 | sem consulta equivalente | 0,055 s / — | não comparável |
| 5 · PTAX, venda média por boletim | Abertura 6,96616; Fechamento 6,95758; Intermediário 6,95235 | Abertura 6,96616; Fechamento 6,95757; Intermediário 6,95235 | 0,030 s / 0,005 s | diferença de 0,00001 em Fechamento, compatível com arredondamento binário das médias |
| 6 · telemetria por caminhão | nulo 2.396; CAM-5707 1.452; CAM-1060 1.450; CAM-3300 1.450; CAM-3126 1.449 | nulo 2.516; CAM-5707 1.452; CAM-3300 1.450; CAM-1060 1.450; CAM-3126 1.449 | 0,422 s / 0,019 s | parcial: +120 linhas extras sem caminhão no ClickHouse; CAM-1060/CAM-3300 empatam |
| 7 · distintas por `(timestamp, data_json)` | livros 1.000/1.000; PTAX 40/40; telemetria 31.265/31.265 | livros 1.000/1.000; PTAX 40/40; telemetria 31.385/31.385 | 0,285 s / 0,178 s | parcial: 120 registros adicionais no ClickHouse também são distintos |
| 8 · partes e compressão | sem consulta equivalente | 1 parte ativa; 32.425 linhas; 938,64 KiB comprimidos; 4,84 MiB descomprimidos | — / 0,010 s | não comparável |

Raw medido diretamente: 32.266 envelopes carregam 32.305 objetos de dados. Os manifestos somam 32.305 linhas. A fila estava vazia, sem mensagens não confirmadas, após a execução dos produtores. As 120 linhas extras do ClickHouse contêm `indice` e `integracao_id`, distintos dos 31.265 registros de telemetria da bronze; são compatíveis com dados dos testes de integração anteriores (inferência a partir dos campos `indice` e `integracao_id`).

### Leitura dos campos e decisão de tipo

| consulta | leitura no DuckDB | leitura no ClickHouse | momento em que o tipo é decidido |
|---|---|---|---|
| 1 | partições e `count(*)`; não faz cast de campos de `data_json` | `count()` e conversão de timestamp para hora | não há tipo de domínio nesta consulta |
| 1a | envelope raw é texto JSON; `data` precisa ser reinterpretado antes de contar os elementos da lista | sem leitura equivalente do raw | query; o SQL atual não reinterpreta o JSON interno e subconta listas |
| 1b | lê campos do manifesto; o SQL pede `linhas`, ausente no contrato do manifesto (`linhas_por_data_tag`) | — | query; a instrução atual falha no binding |
| 2 | `data_json ->>` devolve VARCHAR; `CAST(... AS DECIMAL(10,2))` tipa preço e média | `data_json.categoria::String`, `data_json.preco_gbp::Float64` | DuckDB: consulta. ClickHouse: forma JSON do valor é conhecida no INSERT; casts para String/Float64 ocorrem na consulta |
| 3 | `json_extract_string` devolve VARCHAR; `json_extract(...)::DOUBLE` tipa preço | `data_json.categoria::String`, `data_json.preco_gbp::Decimal(10,2)` | casts na consulta; o JSON original do ClickHouse foi armazenado no INSERT |
| 4 | `from_json` aplica o STRUCT declarado, incluindo DECIMAL e INTEGER | — | consulta |
| 5 | `->>` devolve VARCHAR; CAST para DECIMAL(12,5) | `data_json.tipoBoletim::String`, `data_json.cotacaoVenda::Float64` | DuckDB: consulta. ClickHouse: tipo do valor JSON no INSERT e cast na consulta |
| 6 | `->>` lê linha como VARCHAR; expressão regular extrai CAM | `data_json.linha::String`; `extract` extrai CAM | consulta; a linha permanece texto no INSERT |
| 7 | compara JSON lido do VARCHAR e timestamp sem cast de domínio | JSON armazenado no INSERT e serializado por `toJSONString` na consulta | DuckDB interpreta o JSON na consulta; ClickHouse conserva a estrutura/tipos JSON do INSERT |
| 8 | — | lê contagens e bytes de partes de `system.parts` | metadados mantidos pelo ClickHouse; sem cast de domínio |

### Silver executada

Comando: `python sql/rodar_sql.py sql/silver_livros_ptax.sql --var DATA=2026-10-30`. Resultado: 1.000 livros e 1.000 UPCs, preço GBP entre 10,00 e 59,99, zero linhas sem `arquivo_origem`. O Parquet físico de livros contém as 11 colunas do contrato: `upc VARCHAR`, `url VARCHAR`, `titulo VARCHAR`, `categoria VARCHAR`, `avaliacao TINYINT`, `preco_gbp DECIMAL(10,2)`, `em_estoque BOOLEAN`, `qtd_estoque INTEGER`, `coletado_em TIMESTAMP WITH TIME ZONE`, `arquivo_origem VARCHAR`, `processado_em TIMESTAMP WITH TIME ZONE`. O `DESCRIBE` da consulta com Hive também mostra `data_coleta DATE`, coluna virtual do diretório, não gravada no Parquet.

O Parquet PTAX físico tem as sete colunas do contrato: `moeda VARCHAR`, `data_hora_cotacao TIMESTAMP`, `tipo_boletim VARCHAR`, `cotacao_compra DECIMAL(12,5)`, `cotacao_venda DECIMAL(12,5)`, `arquivo_origem VARCHAR`, `processado_em TIMESTAMP WITH TIME ZONE`. A execução leu 40 boletins, com deduplicação pela chave indicada no SQL.

- **Prompt literal recebido:**

```text
[C] Personagem
Você é analista de dados. Lê o JSON do bronze (texto, no DuckDB) e o
da tabela de pouso (tipo JSON, no ClickHouse) e devolve colunas
tipadas.

[R] Pedido
Os arquivos sql/duckdb_cast.sql, sql/clickhouse_cast.sql e
sql/silver_livros_ptax.sql vieram do laboratório.
1. Rode duckdb_cast.sql (python sql/rodar_sql.py) e clickhouse_cast.sql
   (clickhouse-client --time --multiquery) e compare, consulta a
   consulta, o resultado e o tempo, e as contagens do raw (envelopes
   e linhas que eles carregam) e dos manifestos por status.
2. Para cada consulta, diga como o campo é lido (->>,
   json_extract_string, from_json no DuckDB; data_json.caminho::Tipo
   no ClickHouse) e em que momento o tipo é decidido: no INSERT, na
   consulta ou nos dois.
3. sql/silver_livros_ptax.sql: DuckDB lendo o bronze e gravando
   s3://silver/... no contrato da silver. Rode com
   --var DATA=2026-10-30 (dia da coleta dos livros do zip) e confira
   as colunas e os tipos com DESCRIBE.

[E] Exemplos
SELECT data_json ->> 'categoria' AS categoria,
       avg(CAST(data_json ->> 'preco_gbp' AS DECIMAL(10,2)))
FROM read_parquet('s3://bronze/ingestao/data_tag=livros/*/*.parquet',
                  hive_partitioning = true)
GROUP BY ALL;

[A] Ajustes
- Colunas e tipos da silver exatamente como no contrato da silver:
  livros (upc, url, titulo, categoria, avaliacao TINYINT, preco_gbp
  DECIMAL(10,2), em_estoque BOOLEAN, qtd_estoque INTEGER, coletado_em
  TIMESTAMPTZ, arquivo_origem, processado_em); ptax (moeda,
  data_hora_cotacao TIMESTAMP, tipo_boletim, cotacao_compra e
  cotacao_venda DECIMAL(12,5), arquivo_origem, processado_em).
- Deduplicar: livros por upc (coleta mais recente), ptax por moeda,
  data_hora_cotacao e tipo_boletim.
- Não altere os arquivos SQL sem mostrar o diff e esperar meu ok.
- Diferença de arredondamento entre as engines é explicada, não
  escondida.

[T] Tipo de saída
Tabela "consulta | DuckDB | ClickHouse | tempo | igual?" no terminal
e em docs/prompts.md, junto do prompt.

[E] Extras
Leia AGENTS.md, specs/03_modelo_de_dados.md e o contrato silver no
README do laboratório. Registre o prompt e pare.
```
