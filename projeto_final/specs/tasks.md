# Tarefas de implementação

Todas as tarefas estão pendentes (`[ ]`). A ordem e as dependências devem ser respeitadas. Cada tarefa de implementação cabe em um prompt e deve alterar poucos arquivos. Tarefas com `[bucket compartilhado]` escrevem no RustFS da turma; só podem ser executadas com autorização expressa do aluno na mesma mensagem e devem escrever somente no prefixo `group_id=23651`. Nenhum teste ou comando foi executado nesta etapa de planejamento.

## Tarefas manuais do aluno

| ID | Tarefa | Requisitos | Dependências | Verificação executável | Evidência esperada | Status |
|---|---|---|---|---|---|---|
| T-01 | Criar `.env` local com `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` e `S3_BUCKET`; não versionar nem copiar valores para evidências. | RNF-04; RES-06 | Nenhuma | `python -m src.collector check` termina com código zero e reconhece a configuração sem imprimir valores secretos. | Saída do check sem valores secretos; nunca anexar o `.env`. | [ ] |
| T-02 | Cadastrar `S3_ENDPOINT`, `S3_ACCESS_KEY` e `S3_SECRET_KEY` em GitHub Secrets e configurar `S3_BUCKET` para o workflow sem expor credenciais. | RNF-04; RES-06 | T-01 | `gh secret list` mostra os nomes dos secrets e `gh variable list` mostra `S3_BUCKET`, sem revelar valores. | Saída dos comandos com nomes apenas; nenhuma credencial em log, captura ou arquivo. | [ ] |
| T-03 | Conferir, em modo somente leitura, as pastas e o prefixo próprio da coleção no bucket. | RNF-03; RES-02 | T-01 | `python -m src.collector check` termina com código zero e identifica o prefixo próprio `group_id=23651`; o comando não escreve no bucket. | Saída do check sem credenciais e sem conteúdo sensível. | [ ] |

## Tarefas de implementação

| ID | Tarefa | Requisitos | Dependências | Verificação executável | Evidência esperada | Status |
|---|---|---|---|---|---|---|
| T-04 | Proteger a escrita para aceitar somente o prefixo da coleção SSP. | RNF-03; RF-02 | Nenhuma | `python -m pytest tests/test_prefix_isolation.py` | Saída real do teste e caso que rejeita prefixo de outra coleção em `docs/evidencias/`. | [ ] |
| T-05 | Impedir que credenciais ou `.env` sejam versionados ou impressos em evidências e logs. | RNF-04; RES-06 | T-01 | `python -m pytest tests/test_secrets_not_versioned.py` | Saída real do teste que confirma `.env` ignorado e não versionado, sem exibir valores em `docs/evidencias/`. | [ ] |
| T-06 | Tornar o coletor diário idempotente, preservar o bruto e respeitar as regras de uso do TCGCSV. **Código existente; evidência pendente.** [bucket compartilhado] | RF-01, RF-02, RF-03; RNF-03 | T-01, T-03, T-04 | `python -m pytest tests/test_collector_idempotency.py tests/test_tcgcsv_limits.py`; depois, com autorização expressa, executar `python -m src.collector collect` duas vezes para a mesma data e conferir código zero, ausência de sobrescrita/duplicata e log `ja existia`. | Saída dos testes; logs das execuções sem segredos; confirmação de que objetos existentes não mudaram em `docs/evidencias/`. | [ ] |
| T-07 | Agendar a execução diária às 18h30 de Brasília no GitHub Actions e configurar tentativas de reserva. [bucket compartilhado na execução do workflow] | RF-01, RF-03 | T-02, T-06; definir quantidade, horários e condição das tentativas | `python -m pytest tests/test_workflow_schedule.py` | Saída real do teste que verifica agenda diária e tentativas configuradas, em `docs/evidencias/`. | [ ] |
| T-08 | Validar e reconstruir a silver no contrato comum, colocando inválidos em quarentena com motivo e contagem. **Código existente; evidência pendente.** [bucket compartilhado na publicação] | RF-05, RF-06; RNF-01, RNF-03, RNF-05 | T-03, T-04 | `python -m src.silver rebuild --fonte local --destino local` duas vezes e `python -m pytest tests/test_silver_contract.py tests/test_silver_quarantine.py`; para publicar, `python -m src.silver rebuild --destino s3` somente com autorização expressa. | Saídas das duas reconstruções; mesmos resultados derivados; campos nulos preservados; motivos e contagem da quarentena no log em `docs/evidencias/`. | [ ] |
| T-09 | Fazer backfill de PTAX histórica por data sem alterar objetos brutos existentes. [bucket compartilhado] | RF-01, RF-02, RF-08; RNF-03 | T-01, T-03, T-04, T-06 | `python -m pytest tests/test_ptax_backfill.py`; depois, com autorização expressa, executar `python -m src.collector backfill-ptax` e conferir as chaves antes/depois sem sobrescrever. | Saída do teste, log do backfill e confirmação de prefixo e imutabilidade em `docs/evidencias/`. | [ ] |
| T-10 | Converter preços para reais por ASOF JOIN e reconhecer variações no texto do fechamento PTAX; testar a semana de 09/10 a 13/10. | RF-08, RF-09; RNF-01, RNF-02 | T-09; confirmar o ano da semana antes de fixar os dados esperados | `python -m pytest tests/test_fx_asof.py tests/test_ptax_closing_label.py` | Saída real dos testes cobrindo ausência de cotação posterior, rótulo `Fechamento PTAX` e datas da semana após confirmação do ano em `docs/evidencias/`. | [ ] |
| T-11 | Construir a gold em esquema estrela com fato de preço, dimensões de produto, coleção, data e acabamento, e fato de câmbio diário. | RF-06, RF-07; RNF-01 | T-08, T-10; decidir destino e ciclo de persistência da gold | `python -m pytest tests/test_gold_schema.py` | Saída do teste e consulta que comprova fatos, dimensões e relações no resultado gold, em `docs/evidencias/`. | [ ] |
| T-12 | Calcular a decomposição da variação em efeito da carta, efeito do câmbio e efeito cruzado. | RF-10; RNF-01 | T-10, T-11; validar antes a fórmula e o tratamento de ausências do OBJ-01 | `python -m pytest tests/test_decomposition.py` | Saída do teste com componentes que somam a variação total dentro da precisão monetária definida, em `docs/evidencias/`. | [ ] |
| T-13 | Calcular a comparação de valorização entre selados e cartas avulsas. | RF-11; RNF-01 | T-11; validar antes o critério de agregação do OBJ-02 | `python -m pytest tests/test_sealed_vs_singles_metrics.py` | Saída do teste com intervalo, valores inicial/final, itens válidos e regra de agregação documentada em `docs/evidencias/`. | [ ] |
| T-14 | Calcular a comparação da coleção com as coleções da turma no intervalo comum. | RF-11; RNF-01 | T-11; validar agregação e cobertura desigual do OBJ-03 | `python -m pytest tests/test_collection_comparison.py` | Saída do teste com intervalo comum, coleções disponíveis e cobertura em `docs/evidencias/`. | [ ] |
| T-15 | Calcular a participação e concentração de valor por produto e coleção. | RF-11; RNF-01 | T-11 | `python -m pytest tests/test_value_concentration.py` | Saída do teste com data de referência, cobertura e participação ordenada por produto em `docs/evidencias/`. | [ ] |
| T-16 | Calcular retorno e medida de risco das cartas da turma para o mesmo período. | RF-11; RNF-01 | T-11; validar definições e regra de ordenação do OBJ-05 | `python -m pytest tests/test_return_risk_metrics.py` | Saída do teste com período, observações, retorno, risco e regra de ordenação definidos em `docs/evidencias/`. | [ ] |
| T-17 | Definir e selecionar as cinco carteiras usando somente dados do primeiro dia da janela. | RF-13, RF-14 | T-09, T-10, T-11; confirmar composição das carteiras; ADR-006 concluído antes do cálculo | `python -m pytest tests/test_portfolio_selection.py` | Saída do teste com cinco composições reproduzíveis a partir do primeiro dia, em `docs/evidencias/`. | [ ] |
| T-18 | Calcular resultados das carteiras: PTAX de venda na compra, PTAX de compra na venda, unidades inteiras, sobra rendendo CDI, taxa parametrizada e último preço marcado. | RF-13; RNF-01 | T-10, T-11, T-17; validar regra da taxa de venda | `python -m pytest tests/test_portfolio_returns.py` | Saída dos testes com carteira, dólar parado e CDI no mesmo período, sobra em caixa, último preço observado e contrato comum em `docs/evidencias/`. | [ ] |
| T-19 | Testar que dados posteriores não alteram a composição inicial da cesta de raras. | RF-14 | T-17 | `python -m pytest tests/test_rare_basket_stability.py` | Saída do teste comparando a composição com e sem dias posteriores na silver, em `docs/evidencias/`. | [ ] |
| T-20 | Montar o dashboard em reais da pergunta 1, incluindo rankings, decomposição e filtros de produto. | RF-11, RF-12 | T-12 | `python -m pytest tests/test_dashboard_q1.py` | Saída do teste e captura mostrando maiores valorizações/desvalorizações, decomposição, filtro mínimo em dólar, chave, imagem, link e exclusão de Code Card em `docs/evidencias/`. | [ ] |
| T-21 | Montar o dashboard em reais da pergunta 2, comparando selados e cartas avulsas. | RF-11, RF-12 | T-13 | `python -m pytest tests/test_dashboard_q2.py` | Saída do teste e captura mostrando comparação, período, cobertura, filtro mínimo em dólar e identificadores disponíveis em `docs/evidencias/`. | [ ] |
| T-22 | Montar o dashboard em reais da pergunta 4, mostrando concentração de valor por coleção. | RF-11, RF-12 | T-15 | `python -m pytest tests/test_dashboard_q4.py` | Saída do teste e captura mostrando participação ordenada, filtro mínimo em dólar, identificadores e Code Card fora da pergunta 4 em `docs/evidencias/`. | [ ] |
| T-23 | Montar o dashboard em reais da pergunta 3, comparando a coleção SSP com as coleções da turma. | RF-11, RF-12 | T-14 | `python -m pytest tests/test_dashboard_q3.py` | Saída do teste e captura mostrando intervalo comum, cobertura, filtro mínimo em dólar, identificadores e Code Card fora da pergunta 3 em `docs/evidencias/`. | [ ] |
| T-24 | Montar o dashboard em reais da pergunta 5, comparando retorno e risco das cartas da turma. | RF-11, RF-12 | T-16 | `python -m pytest tests/test_dashboard_q5.py` | Saída do teste e captura mostrando período, observações, retorno, risco e filtro mínimo em dólar em `docs/evidencias/`. | [ ] |
| T-25 | Montar o painel da carteira no contrato comum. | RF-13 | T-18, T-19 | `python -m pytest tests/test_portfolio_dashboard.py` | Saída do teste e captura mostrando cinco carteiras, dólar parado, CDI, último preço observado e resultados no contrato comum em `docs/evidencias/`. | [ ] |
| T-26 | Montar o placar da turma com resultados comparáveis no período e cobertura disponíveis. | RF-11 | T-14, T-16, T-23, T-24 | `python -m pytest tests/test_class_leaderboard.py` | Saída do teste e captura do placar com período, cobertura e indicadores comparáveis em `docs/evidencias/`. | [ ] |
| T-27 | Reconstruir silver e gold a partir do bruto por um único comando local: `python -m src.pipeline rebuild --fonte local --destino local`. | RF-06, RF-07; RNF-01, RNF-05 | T-08, T-11 a T-18 | `python -m pytest tests/test_pipeline_rebuild.py`; o teste invoca o comando indicado com as camadas derivadas ausentes. | Saída real do teste e da reconstrução local, confirmando silver e gold produzidas do bruto em `docs/evidencias/`. | [ ] |
| T-28 | Documentar no README o comando do pipeline, o comando dos testes, os dias sem coleta e seus motivos. | RF-04, RF-15 | T-06 a T-27 | `python -m pytest tests/test_readme_pipeline_commands.py`; depois executar `python -m src.pipeline rebuild --fonte local --destino local` e `python -m pytest`. | README atualizado; saída real dos testes e dos dois comandos; lacunas com data e motivo registradas em `docs/evidencias/`, sem valores de credenciais. | [ ] |

## Cobertura de requisitos

| Requisito | Tarefas |
|---|---|
| RF-01 | T-06, T-07, T-09 |
| RF-02 | T-04, T-06, T-09 |
| RF-03 | T-06, T-07 |
| RF-04 | T-28 |
| RF-05 | T-08 |
| RF-06 | T-08, T-11, T-27 |
| RF-07 | T-11, T-27 |
| RF-08 | T-09, T-10 |
| RF-09 | T-10 |
| RF-10 | T-12 |
| RF-11 | T-13 a T-16, T-20 a T-24, T-26 |
| RF-12 | T-20 a T-24 |
| RF-13 | T-17, T-18, T-25 |
| RF-14 | T-17, T-19 |
| RF-15 | T-28 |
| RNF-01 | T-08, T-10 a T-18, T-27 |
| RNF-02 | T-10 |
| RNF-03 | T-03, T-04, T-06, T-08, T-09 |
| RNF-04 | T-01, T-02, T-05 |
| RNF-05 | T-08, T-27 |
