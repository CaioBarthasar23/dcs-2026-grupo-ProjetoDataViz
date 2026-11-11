# Requisitos da ingestão

## Requisitos funcionais

Cada resultado **Então** descreve uma observação verificável por teste, chamada HTTP ou consulta. Os comandos concretos de execução serão definidos na Etapa 06.

### RF-01 · Receber por HTTP e publicar na fila
**Origem:** CT-01 a CT-06; OBJ-02; P1 e P2.
- **Dado** um envelope válido em `POST /ingest`, **Quando** o broker confirmar a publicação, **Então** a API publica mensagem persistente na fila durável `ingestao` e responde 202.

### RF-02 · Responder a corpo inválido ou acima do limite
**Origem:** CT-04 e CT-06; P1.
- **Dado** um corpo não JSON ou acima de `HTTP_MAX_BYTES`, **Quando** for enviado a `POST /ingest`, **Então** a API responde 400 ou 413, respectivamente, e não publica mensagem.

### RF-03 · Recusar envelope inválido por HTTP
**Origem:** CT-01 a CT-05; OBJ-01; P1.
- **Dado** um JSON que viole o contrato, **Quando** for enviado a `POST /ingest`, **Então** a API responde 422 com o motivo e não publica a mensagem.

### RF-04 · Receber e revalidar mensagens da fila
**Origem:** CT-01 a CT-05; OBJ-03; P3.
- **Dado** um envelope na fila durável `ingestao`, **Quando** o consumidor o recebe, **Então** valida novamente a estrutura antes de iniciar a gravação.

### RF-05 · Rejeitar envelope inválido recebido pela fila
**Origem:** CT-01 a CT-05; OBJ-03; P3.
- **Dado** mensagem inválida da fila, **Quando** o consumidor a valida, **Então** grava mensagem e motivo em `raw/ingestao_rejeitados/data=D/`, envia ack depois da gravação e não cria linha em `ingestao.db_ingestion`.

### RF-06 · Gravar raw do lote em JSON Lines
**Origem:** OBJ-03; P3; layout do lake em `AGENTS.md`.
- **Dado** um micro-lote válido, **Quando** começa o flush, **Então** grava em `raw/ingestao/data_tag=X/data=D/lote_<HHMMSS>_<id>.jsonl` um envelope por linha, como recebido, com `recebido_em_ms` do servidor.

### RF-07 · Gravar bronze do lote em Parquet
**Origem:** OBJ-03; P3; layout do lake em `AGENTS.md`.
- **Dado** um lote válido, **Quando** a bronze é gravada, **Então** cria `bronze/ingestao/data_tag=X/data=D/lote_<HHMMSS>_<id>.parquet`, uma linha por objeto de `data`, colunas `timestamp` e `data_json` e o mesmo nome de lote do raw.

### RF-08 · Inserir linhas no ClickHouse
**Origem:** OBJ-02 e OBJ-03; P2 e P3; contrato em `AGENTS.md`.
- **Dado** as linhas válidas de um lote, **Quando** são inseridas em `ingestao.db_ingestion`, **Então** `data_json` usa tipo JSON, `timestamp` vem do servidor e o INSERT usa `input_format_try_infer_dates = 0` e `input_format_try_infer_datetimes = 0`.

### RF-09 · Gravar manifesto do lote
**Origem:** OBJ-03; P3; layout do manifesto em `AGENTS.md`.
- **Dado** um lote processado, **Quando** raw, bronze e ClickHouse terminarem, **Então** grava `raw/_manifestos/ingestao/data=D/lote_<HHMMSS>_<id>.json` com o mesmo identificador, contagens por `data_tag`, chaves, bytes, SHA-256, tempos e status.

### RF-10 · Confirmar mensagem somente após as gravações
**Origem:** OBJ-03; P3; ordem de flush em `AGENTS.md`.
- **Dado** uma mensagem válida no lote, **Quando** raw, bronze, ClickHouse e manifesto forem gravados com sucesso, nessa ordem, **Então** o consumidor envia ack somente após gravar o manifesto.

### RF-11 · Registrar falha e manter mensagem sem ack
**Origem:** OBJ-03; P3; regra de falha do ClickHouse em `AGENTS.md`.
- **Dado** uma falha no INSERT do ClickHouse, **Quando** o consumidor a tratar, **Então** grava manifesto com status de erro, não envia ack e permite nova entrega pela fila.

## Requisitos não funcionais

### RNF-01 · Medir tempo até consultável
**Atributo/origem:** latência; OBJ-02; P2.
**Métrica:** duração entre HTTP 202 de `POST /ingest` e primeira consulta que encontra a linha no ClickHouse.
**Medição/meta:** script da Etapa 09 correlaciona envio e primeira consulta e registra cada duração. Meta: **hipótese, validação pendente**.

### RNF-02 · Não perder mensagens aceitas após interrupção
**Atributo/origem:** durabilidade, entrega pelo menos uma vez; OBJ-03; P3.
**Métrica:** linhas distintas no ClickHouse após reiniciar o consumidor; duplicatas permitidas e contadas.
**Medição/critério:** publicar 10.000 envelopes, obter o PID do consumidor, interrompê-lo no meio com `kill -9 <PID>` e reiniciar. Critério: 10.000 linhas distintas no ClickHouse; registrar também duplicatas. Duplicatas são uma consequência possível e aceita da entrega pelo menos uma vez; não há garantia de exatamente uma vez.

### RNF-03 · Incluir fonte nova sem DDL
**Atributo/origem:** extensibilidade operacional; OBJ-01; P1.
**Métrica:** passos para habilitar fonte sem tabela dedicada.
**Medição/meta:** registrar inclusão de tag em `DOMINIOS` no `.env` e reinício; verificar envio pelo fluxo comum sem `CREATE TABLE`. Meta: **hipótese, validação pendente**.

### RNF-04 · Reprocessar ClickHouse a partir do lake
**Atributo/origem:** recuperabilidade; OBJ-03; P3.
**Métrica:** linhas reprocessadas do lake que ficam consultáveis no ClickHouse.
**Medição/meta:** reprocessar lote de teste do lake e comparar linhas processadas por `data_tag` com bronze; contar duplicatas, sem exigir deduplicação. Meta quantitativa: **hipótese, validação pendente**.

## Matriz RF/RNF por objetivo

| Requisito | OBJ-01 | OBJ-02 | OBJ-03 |
|---|---:|---:|---:|
| RF-01 |  | X |  |
| RF-02 |  |  | X |
| RF-03 | X |  |  |
| RF-04 |  |  | X |
| RF-05 |  |  | X |
| RF-06 |  |  | X |
| RF-07 |  |  | X |
| RF-08 |  | X | X |
| RF-09 |  |  | X |
| RF-10 |  |  | X |
| RF-11 |  |  | X |
| RNF-01 |  | X |  |
| RNF-02 |  |  | X |
| RNF-03 | X |  |  |
| RNF-04 |  |  | X |
