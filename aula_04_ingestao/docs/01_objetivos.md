# Objetivos

## Objetivos

### OBJ-01 · Fonte nova sem mudar o banco

- **Persona:** P1.
- **Métrica:** passos necessários para uma fonte nova começar a gravar.
- **Como medir:** registrar os passos de configuração e início do envio, incluindo a inclusão da tag em `DOMINIOS` no `.env` e a reinicialização do servidor; verificar que não foi necessário executar `CREATE TABLE` para a fonte.
- **Meta:** hipótese, validação pendente.

### OBJ-02 · Dado consultável após o 202

- **Persona:** P2.
- **Métrica:** tempo entre a resposta HTTP 202 do `POST /ingest` e a disponibilidade da linha correspondente no ClickHouse.
- **Como medir:** script de medição da Etapa 09, correlacionando o envio aceito com a primeira consulta que encontra a linha no ClickHouse.
- **Meta:** hipótese, validação pendente.

### OBJ-03 · Identificar a parada e recuperar a ingestão

- **Persona:** P3.
- **Métrica:** capacidade de identificar o ponto da falha e recuperar o processamento sem perda de mensagens aceitas.
- **Como medir:** acompanhar uma mensagem de teste desde o 202 até a confirmação do lote no ClickHouse e no manifesto; em uma interrupção controlada, consultar logs, fila e manifesto para localizar a parada e verificar que a mensagem é processada após a recuperação.
- **Meta:** hipótese, validação pendente.

## Restrições

- Domínios desta aula: `telemetria`, `livros` e `ptax`.
- A medição de OBJ-02 começa na resposta 202 da API e termina quando a linha pode ser consultada no ClickHouse.
- Não há metas numéricas com origem definida nesta etapa; valores serão hipótese, validação pendente.

## Fora de escopo

- Schema por domínio, aprofundado na Aula 07.
- DLX, prefetch e ReplacingMergeTree, aprofundados na Aula 06.
- Modelo dimensional da Aula 05 e painel.

## Hipóteses

- As metas de OBJ-01, OBJ-02 e OBJ-03 precisam ser validadas pelo grupo; não há base fornecida para quantificá-las.
- A medição de OBJ-03 pressupõe que seja possível acompanhar uma mensagem de teste nos pontos indicados; validar o procedimento na implementação.
