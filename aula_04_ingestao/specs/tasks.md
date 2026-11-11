# Tarefas de construção

Cada tarefa foi dividida para caber em até 30 minutos de trabalho focado. Os testes desta etapa são escritos antes do código; os testes ficam vermelhos até a implementação futura. Todas começam pendentes.

| ID | Tarefa (até 30 min) | RF/RNF | Arquivo(s) | Teste que fecha | Verificação | Evidência esperada | Status |
|---|---|---|---|---|---|---|---|
| T-01 | Criar casos parametrizados para os exemplos do contrato | RF-03, CT-01 a CT-06 | `tests/test_contrato.py` | `test_exemplo_corresponde_ao_codigo_e_motivo_do_nome` | `pytest -q tests/test_contrato.py` | 13 casos passam, cobrindo todos os exemplos; recusas trazem motivo. | [x] |
| T-02 | Criar casos HTTP com publicação substituída por dublê | RF-01, RF-02, RF-03 | `tests/test_api.py` | Testes HTTP, `/health` e publicação com canal falso | `pytest -q tests/test_api.py` | Respostas HTTP corretas; fila durável, mensagem persistente, confirmação do broker e cabeçalho `recebido_em_ms` verificados. | [x] |
| T-03 | Criar integração isolada em fila e bucket de teste | RF-01, RF-04, RF-06 a RF-08 | `tests/test_integracao.py`, `pytest.ini` | `test_vinte_envelopes_aparecem_no_clickhouse_e_no_lake` | `pytest -q -m integracao tests/test_integracao.py` | 20 envelopes consultáveis no ClickHouse e 20 linhas em raw/bronze no bucket `teste`. | [x] |
| T-04 | Implementar validação do envelope e dos exemplos | RF-03, CT-01 a CT-03 | `src/config.py`, `src/contrato.py` | `tests/test_contrato.py` | `pytest -q tests/test_contrato.py` | Domínios válidos aceitos; violações recusadas com status e motivo. | [x] |
| T-05 | Implementar validação do tamanho e do corpo HTTP | RF-02, CT-04, CT-06 | `src/contrato.py`, `src/api.py` | `tests/test_contrato.py`, `tests/test_api.py` | `pytest -q tests/test_contrato.py tests/test_api.py` | Não JSON recebe 400; corpo acima do limite recebe 413 sem publicar. | [x] |
| T-06 | Implementar POST `/ingest` e publicação confirmada | RF-01, RF-03 | `src/api.py` | `tests/test_api.py` | `pytest -q tests/test_api.py` | Válido recebe 202; inválido recebe 422 com motivo; dublê confirma publicação. | [x] |
| T-07 | Consumir mensagem válida e revalidar o envelope | RF-04, RF-05 | `src/consumidor.py` | `tests/test_consumidor.py` e integração T-03 | `pytest -q tests/test_consumidor.py` e `pytest -q -m integracao` | Mensagem válida chega ao lote; inválida é rejeitada e recebe ack só depois da gravação. | [x] |
| T-08 | Gravar envelopes do lote no raw JSON Lines | RF-06 | `src/lake.py` | `tests/test_lake.py`, integração T-03 | `pytest -q tests/test_lake.py` e `pytest -q -m integracao` | Corpo em uma linha JSONL por mensagem; PUT inclui SHA-256 e lote. | [x] |
| T-09 | Gravar objetos em bronze Parquet | RF-07 | `src/lake.py` | `tests/test_lake.py`, integração T-03 | `pytest -q tests/test_lake.py` e `pytest -q -m integracao` | Parquet ZSTD com timestamp/data_json; 20 linhas no fluxo integrado. | [x] |
| T-10 | Inserir as linhas no ClickHouse | RF-08 | `src/clickhouse.py` | `tests/test_clickhouse.py`, integração T-03 | `pytest -q tests/test_clickhouse.py` e `pytest -q -m integracao` | Uma chamada INSERT com as três colunas, async_insert e inferência desativada. | [x] |
| T-11 | Gravar manifesto e confirmar após persistência completa | RF-09, RF-10 | `src/consumidor.py`, `src/lake.py` | `test_flush_grava_raw_bronze_clickhouse_manifesto_e_ack_nessa_ordem` | `pytest -q tests/test_consumidor.py` | Manifesto status ok antecede ack multiple da última entrega do lote. | [x] |
| T-12 | Registrar falha do ClickHouse e deixar lote sem ack | RF-11 | `src/consumidor.py`, `src/lake.py` | `test_falha_clickhouse_grava_manifesto_erro_e_nao_da_ack`, `test_falha_clickhouse_fecha_conexao_para_reentrega` | `pytest -q tests/test_consumidor.py` | Manifesto status `erro_clickhouse`; nenhuma confirmação; conexão fechada para redelivery. | [x] |
| T-13 | Escrever teste de recuperação e reprocessamento antes da implementação | RNF-02, RNF-04 | `tests/test_integracao.py` | Testes de reinício e replay, a criar | Criar os testes e verificar que falham antes de implementar | Linhas distintas recuperadas e contagem de duplicatas registrada. | [ ] |
| T-14 | Carregar configurações locais e de serviço sem expor credenciais | RF-01, RF-02, RF-06 a RF-08 | `src/config.py` | Importação e leitura de `config` | `python -c "from src.config import config; assert config.dominios and config.http_max_bytes > 0"` | Configuração carregada; nenhum segredo impresso ou versionado. | [x] |

## Tarefas manuais

| ID | Ação do aluno | RF/RNF | Arquivo(s) | Verificação/evidência | Status |
|---|---|---|---|---|---|
| TM-01 | Iniciar os serviços locais do compose para executar a integração | RF-01, RF-04, RF-06 a RF-08 | `docker-compose.yml` | Serviços RustFS, RabbitMQ e ClickHouse saudáveis; integração usa somente fila `ingestao_teste` e bucket `teste`. | [ ] |
| TM-02 | Disponibilizar as variáveis de conexão no ambiente local sem versionar segredos | RF-01, RF-06 a RF-08 | `.env` local | Verificar nomes conforme `.env.example`; nunca adicionar `.env` ao Git. | [ ] |

## Cobertura ainda pendente

| Requisito | Situação nesta etapa |
|---|---|
| RF-09 e RF-10 | Cobertos por T-11: teste confirma manifesto após ClickHouse e ack multiple por último. |
| RF-11 | Coberto por T-12: falha gera manifesto `erro_clickhouse`, não confirma e fecha a conexão para redelivery. |
| RNF-02 e RNF-04 | T-13 permanece pendente: teste de interrupção no meio do lote e replay completo ainda não criado. |
| RNF-01 e RNF-03 | Fora do conjunto de testes desta etapa; definir medição e teste antes da implementação correspondente. |
