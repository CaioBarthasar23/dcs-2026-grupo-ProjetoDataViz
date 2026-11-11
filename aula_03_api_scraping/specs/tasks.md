# Tarefas de implementação · Etapas 12 a 15

Estimativas por tarefa: até 30 minutos. Cada teste é sem rede externa, exceto os testes explicitamente identificados como integração MinIO local.

## Etapa 12 · Configuração e cliente HTTP

### T-01 · Validar configuração do ambiente (20 min) — concluída
- **Objetivo:** carregar `.env`, validar campos obrigatórios e defaults sem expor segredos.
- **Arquivos:** `src/config.py`, `requirements.txt`, `.env.example`; contrato equivalente em `tests/test_execucao.py`.
- **Requisitos:** RF-03, RF-06; RNF-02, RNF-03, RNF-08, RNF-10.
- **ADR:** nenhum específico.
- **Teste:** `test_configuracao_nao_expoe_segredos` verifica que a configuração não expõe credenciais em `repr`/`str` e que `.env` não é versionado. O arquivo `tests/test_config.py` descrito no plano não existe; os testes existentes não foram alterados.
- **Comando:** `python -m pytest tests/test_execucao.py::test_configuracao_nao_expoe_segredos -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** nenhuma.

### T-02 · Implementar GET com timeout e identificação (25 min) — concluída
- **Objetivo:** criar `Resposta` e cliente HTTP com timeout finito, User-Agent e retorno de bytes/status/cabeçalhos.
- **Arquivos:** `src/http.py`, `src/models.py`, `src/collectors/books.py`, `src/collectors/ptax.py`; contratos equivalentes em `tests/test_coleta.py`.
- **Requisitos:** RF-05, RF-06, RF-07, RF-16; RNF-02.
- **ADR:** ADR-004.
- **Teste:** `test_timeout_explicito_conexao_leitura`, `test_user_agent_intervalo_e_sequencial` e `test_respeita_retry_after_em_429` cobrem timeout, identificação e corpo em bytes. `tests/test_http.py` não existe; os testes existentes não foram alterados.
- **Comando:** `python -m pytest tests/test_coleta.py::test_timeout_explicito_conexao_leitura tests/test_coleta.py::test_user_agent_intervalo_e_sequencial tests/test_coleta.py::test_respeita_retry_after_em_429 -q` — 3 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** T-01.

### T-03 · Repetir falhas transitórias com Retry-After (25 min) — concluída
- **Objetivo:** implementar classificação transitória, limite de tentativas e full jitter com precedência do `Retry-After`.
- **Arquivos:** `src/http.py`, `src/collectors/ptax.py`; contratos equivalentes em `tests/test_coleta.py`.
- **Requisitos:** RF-05, RF-06, RF-07, RF-16; RNF-02, RNF-06.
- **ADR:** ADR-003.
- **Teste:** `test_respeita_retry_after_em_429` simula 429 com `Retry-After: 2` e depois 200; verifica espera 2 s e retorno dos bytes. `test_repete_read_timeout_e_5xx_ate_sucesso_ou_limite` verifica retry de timeout de leitura e 503, enquanto `test_nao_repete_outros_4xx` cobre erros permanentes.
- **Contrato presente:** o arquivo `tests/test_http.py` não existe; o teste existente usa o nome `test_repete_read_timeout_e_5xx_com_limite`. Os testes não foram alterados.
- **Comando:** `python -m pytest tests/test_coleta.py::test_respeita_retry_after_em_429 tests/test_coleta.py::test_repete_read_timeout_e_5xx_com_limite tests/test_coleta.py::test_nao_repete_outros_4xx -q` — 3 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** T-02.

### T-04 · Impor intervalo e ausência de paralelismo (20 min) — concluída
- **Objetivo:** centralizar no cliente HTTP o intervalo mínimo entre inícios de chamadas ao site e evitar chamadas simultâneas.
- **Arquivos:** `src/http.py`; contrato equivalente em `tests/test_coleta.py`.
- **Requisitos:** RF-06; RNF-03.
- **ADR:** ADR-004.
- **Teste:** `test_user_agent_intervalo_e_sequencial` verifica a identificação e o intervalo configurado sem chamadas paralelas. `tests/test_http.py` não existe; o teste existente não foi alterado.
- **Comando:** `python -m pytest tests/test_coleta.py::test_user_agent_intervalo_e_sequencial -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** T-02, T-03.

## Etapa 13 · Gravador e manifesto

### T-05 · Criar adaptador S3 com chave e metadados raw (25 min) — concluída
- **Objetivo:** gravar e ler bytes via boto3, calcular SHA-256, derivar chave determinística e validar metadados ASCII.
- **Arquivos:** `src/storage.py`; contrato equivalente em `tests/test_gravacao.py`.
- **Requisitos:** RF-09, RF-10; RNF-04, RNF-07, RNF-10.
- **ADR:** ADR-002, ADR-005.
- **Teste:** `test_chave_raw_depende_de_recurso_data_e_hash_sem_timestamp` verifica mesma chave para mesmo conteúdo/contexto, chave distinta para corpo diferente, ausência de timestamp/ID e metadados ASCII.
- **Contrato presente:** `tests/test_storage.py` não existe; o baseline anterior do contrato `tests/test_gravacao.py` falhou com `NotImplementedError` antes da implementação. Nenhum teste foi alterado.
- **Comando:** `python -m pytest tests/test_gravacao.py -q` — 4 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** T-01.

### T-06 · Integrar gravador com MinIO local (25 min) — concluída
- **Objetivo:** provar PUT/GET real no bucket `teste` e retry idempotente quando um proxy simulado retorna 502 antes de encaminhar o PUT.
- **Arquivos:** `src/storage.py`, `tests/integration/test_storage_minio.py`, `tests/conftest.py`.
- **Requisitos:** RF-09, RF-10; RNF-04, RNF-07, RNF-10.
- **ADR:** ADR-002, ADR-005.
- **Teste:** `test_minio_real_le_e_grava_no_bucket_teste` compara bytes, chave, hash e metadados após leitura real. `test_proxy_502_repete_put_mesma_chave` injeta uma resposta 502, verifica o segundo PUT com chave K e bytes idênticos, e confirma o objeto no MinIO.
- **Comando:** integração executada com variáveis carregadas de `.env` sem imprimir valores: `python -c '... pytest.main(["tests/integration/test_storage_minio.py", "-q"])'` — 2 passed. Suíte completa: `python -m pytest -q` — 33 passed, 2 skipped.
- **Correção identificada no teste real:** reexecução sobrescrevia metadado `collected-at`; o gravador agora consulta a chave existente e não altera objeto com SHA-256 correspondente.
- **Depende de:** T-05; MinIO local e bucket `teste` disponíveis.

### T-07 · Persistir manifesto e itens por execução (25 min) — concluída
- **Objetivo:** modelar cabeçalho/itens e serializar o manifesto em chave exclusiva da execução.
- **Arquivos:** `src/manifest.py`; contrato equivalente em `tests/test_execucao.py`.
- **Requisitos:** RF-13; RNF-05, RNF-07.
- **ADR:** ADR-006.
- **Teste:** `test_manifesto_persiste_cabecalho_itens_e_id_unico` verifica campos do contrato, vínculo às chaves raw e manifests distintos em execuções diferentes.
- **Contrato presente:** `tests/test_manifest.py` não existe; o baseline inicial do equivalente falhou com `NotImplementedError`. O modelo também oferece serialização JSON e chave `raw/manifestos/.../execucao=<id>.json`.
- **Comando:** `python -m pytest tests/test_execucao.py::test_manifesto_registra_execucao_e_itens -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** T-05.

### T-08 · Registrar transições e falhas dos itens (20 min) — concluída
- **Objetivo:** validar estados permitidos e persistir estado final `falhou` com causa, tentativas e status.
- **Arquivos:** `src/manifest.py`, `tests/test_manifest.py`.
- **Requisitos:** RF-08, RF-13; RNF-05, RNF-07.
- **ADR:** ADR-006.
- **Teste:** `test_item_falhou_permanece_no_manifesto_com_causa` verifica que falha de retry/gravação fica registrada sem referenciar objeto não confirmado.
- **Contrato presente:** `tests/test_manifest.py` não existe; o teste equivalente em `tests/test_execucao.py` passou no estado anterior, portanto não forneceu uma falha vermelha. Nenhum teste foi alterado.
- **Comando:** `python -m pytest tests/test_execucao.py::test_item_falhou_permanece_no_manifesto_com_causa -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 33 passed, 2 skipped.
- **Depende de:** T-07.

## Etapa 14 · Coletores

### T-09 · Descobrir Books, consultar robots e filtrar categorias (25 min) — concluída
- **Objetivo:** obter `robots.txt` e página inicial, registrar resposta, descobrir categorias e aplicar `SCRAPER_CATEGORIAS`.
- **Arquivos:** `src/collectors/books.py`, `tests/test_books.py`.
- **Requisitos:** RF-01, RF-03, RF-05, RF-06; RNF-03, RNF-05.
- **ADR:** ADR-004, ADR-006.
- **Teste:** `test_descobre_categorias_registra_robots_e_aplica_filtro` usa respostas/HTML inline; verifica 404 registrado sem inventar permissões, preservação dos bytes raw e filtro vazio selecionando todas.
- **Contrato adicionado:** `tests/test_books.py` não existia; o teste contratual novo falhou antes da implementação por ausência de `ColetorBooks`.
- **Comando:** `python -m pytest tests/test_books.py::test_descobre_categorias_registra_robots_e_aplica_filtro -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 34 passed, 2 skipped.
- **Depende de:** T-02, T-04, T-05, T-07.

### T-10 · Percorrer paginação de categoria (25 min) — concluída
- **Objetivo:** seguir o link `next` até seu término sem duplicar livros dentro da categoria.
- **Arquivos:** `src/collectors/books.py`, `tests/test_books.py`.
- **Requisitos:** RF-02, RF-06, RF-09; RNF-03, RNF-06.
- **ADR:** ADR-001, ADR-004, ADR-005.
- **Teste:** `test_percorre_next_ate_fim_sem_repetir_livro` usa duas páginas HTML inline e verifica sequência, chaves raw e ausência de requisição adicional após não haver `next`.
- **Contrato adicionado:** `tests/test_books.py` não existia; o teste contratual novo falhou antes da implementação porque a coleta não percorria categorias.
- **Comando:** `python -m pytest tests/test_books.py::test_percorre_next_ate_fim_sem_repetir_livro -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 35 passed, 2 skipped.
- **Depende de:** T-09.

### T-11 · Coletar detalhe e preservar HTML do livro (25 min) — concluída
- **Objetivo:** visitar detalhe para UPC, estoque e categoria, manter campos da listagem vinculados à observação e gravar raw antes da interpretação.
- **Arquivos:** `src/collectors/books.py`, `tests/test_books.py`.
- **Requisitos:** RF-04, RF-09; RNF-01, RNF-03, RNF-07.
- **ADR:** ADR-001, ADR-002, ADR-005.
- **Teste:** `test_detalhe_fornece_upc_estoque_categoria_e_raw_precede_parse` usa HTML inline e spies; verifica extração do detalhe e ordem da gravação.
- **Contrato adicionado:** `tests/test_books.py` não existia; o teste contratual novo falhou antes da implementação porque o coletor não produzia detalhes.
- **Comando:** `python -m pytest tests/test_books.py::test_detalhe_fornece_upc_estoque_categoria_e_raw_precede_parse -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 36 passed, 2 skipped.
- **Depende de:** T-10.

### T-12 · Montar janela PTAX e selecionar fechamento (25 min) — concluída
- **Objetivo:** montar URL GBP com datas `MM-DD-AAAA` e selecionar Fechamento elegível mais recente até D.
- **Arquivos:** `src/collectors/ptax.py`, `tests/test_ptax.py`.
- **Requisitos:** RF-07, RF-16; RNF-01, RNF-02, RNF-06.
- **ADR:** ADR-003, ADR-007.
- **Teste:** `test_seleciona_fechamento_mais_recente_e_formata_janela` verifica parâmetros e seleção, inclusive fechamento de dia anterior.
- **Contrato adicionado:** `tests/test_ptax.py` não existia; o contrato passou antes de qualquer alteração em `src/collectors/ptax.py`, que já atendia à tarefa.
- **Comando:** `python -m pytest tests/test_ptax.py::test_seleciona_fechamento_mais_recente_e_formata_janela -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 37 passed, 2 skipped.
- **Depende de:** T-02, T-03, T-05, T-07.

### T-13 · Preservar PTAX e registrar ausência de fechamento (20 min) — concluída
- **Objetivo:** gravar resposta JSON vazia/bruta e marcar execução incompleta sem fabricar cotação.
- **Arquivos:** `src/collectors/ptax.py`, `tests/test_ptax.py`.
- **Requisitos:** RF-08, RF-10, RF-13; RNF-05, RNF-07.
- **ADR:** ADR-005, ADR-006, ADR-007.
- **Teste:** `test_janela_vazia_preserva_json_e_marca_incompleta` verifica raw gravado antes do parser, ausência da cotação e causa/estado no manifesto.
- **Contrato adicionado:** `tests/test_ptax.py` não existia; o teste contratual novo falhou antes da implementação porque não havia coletor PTAX integrado ao armazenamento/manifesto.
- **Comando:** `python -m pytest tests/test_ptax.py::test_janela_vazia_preserva_json_e_marca_incompleta -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 38 passed, 2 skipped.
- **Depende de:** T-08, T-12.

### T-14 · Orquestrar coleta e validar contagem (25 min) — concluída
- **Objetivo:** coordenar coletores, consolidar totais declarados/extraídos e marcar divergência como falha.
- **Arquivos:** `src/pipeline.py`, `tests/test_execucao.py`.
- **Requisitos:** RF-13, RF-14; RNF-01, RNF-03, RNF-05.
- **ADR:** ADR-001, ADR-006.
- **Teste:** contratos de contagem e duração verificam os escopos completo/filtrado, totais no manifesto e falha acima de 30 minutos com relógio monotônico injetado.
- **Contrato adicionado:** testes de integração novos falharam antes da implementação porque `run_collection` não aceitava manifesto nem registrava os totais.
- **Comando:** `python -m pytest tests/test_execucao.py::test_pipeline_registra_totais_e_divergencia_no_manifesto tests/test_execucao.py::test_pipeline_registra_duracao_e_estado_no_manifesto -q` — 2 passed.
- **Verificação completa:** `python -m pytest -q` — 40 passed, 2 skipped.
- **Depende de:** T-11, T-13.

## Etapa 15 · Extrator e linha de comando

### T-15 · Definir modelos e serialização dos contratos (20 min) — concluída
- **Objetivo:** criar `Livro` e `Cotacao` com serialização JSON Lines contendo exatamente nove e cinco campos, respectivamente.
- **Arquivos:** `src/models.py`, `tests/test_models.py`.
- **Requisitos:** RF-11, RF-12; RNF-01.
- **ADR:** ADR-001, ADR-005.
- **Teste:** `test_livro_e_cotacao_serializam_campos_exatos` valida chaves, tipos e JSON válido por linha.
- **Contrato adicionado:** `tests/test_models.py` não existia; o teste falhou antes da implementação porque `Livro` não tinha `para_json()`.
- **Comando:** `python -m pytest tests/test_models.py -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 41 passed, 2 skipped.
- **Depende de:** T-11, T-12.

### T-16 · Extrair somente de brutos MinIO (25 min) — concluída
- **Objetivo:** ler objetos referenciados pelo manifesto, decodificar/parsing offline e produzir modelos sem dependência de rede.
- **Arquivos:** `src/extractor.py`, `tests/test_extractor.py`.
- **Requisitos:** RF-11, RF-12; RNF-01, RNF-09.
- **ADR:** ADR-001, ADR-005.
- **Teste:** `test_extrator_le_raw_sem_cliente_http_e_produz_registros` usa HTML/JSON inline, bloqueia chamadas HTTP e verifica registros extraídos.
- **Contrato adicionado:** `tests/test_extractor.py` não existia; teste falhou antes da implementação porque `Extrator` não existia.
- **Comando:** `python -m pytest tests/test_extractor.py::test_extrator_le_raw_sem_cliente_http_e_produz_registros -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 42 passed, 2 skipped.
- **Depende de:** T-08, T-15.

### T-17 · Validar e publicar bronze diário (25 min) — concluída
- **Objetivo:** validar campos e contagens, gravar `livros.jsonl`/`cotacoes.jsonl` e registrar resultado ou falha.
- **Arquivos:** `src/extractor.py`, `src/manifest.py`, `tests/test_extractor.py`.
- **Requisitos:** RF-11, RF-12, RF-13, RF-14; RNF-01, RNF-05, RNF-07, RNF-10.
- **ADR:** ADR-001, ADR-006.
- **Teste:** `test_publica_jsonl_apos_validacao_e_nao_publica_contagem_invalida` verifica publicação completa e erro rastreado sem dados parciais.
- **Contrato adicionado:** `tests/test_extractor.py` não existia; o teste falhou antes da implementação porque `Extrator.publicar` não existia.
- **Comando:** `python -m pytest tests/test_extractor.py::test_publica_jsonl_apos_validacao_e_nao_publica_contagem_invalida -q` — 1 passed.
- **Regressão adicional:** falha de PUT bronze agora também atualiza o manifesto para `falha`; `python -m pytest tests/test_extractor.py -q` — 3 passed.
- **Verificação completa final:** `python -m pytest -q` — 45 passed, 3 skipped.
- **Depende de:** T-14, T-16.

### T-18 · Expor comandos de execução e extração (25 min) — concluída
- **Objetivo:** implementar `executar`, `coletar` e `extrair --data-ref` com códigos de saída explícitos e sem imprimir segredos.
- **Arquivos:** `src/cli.py`, `tests/test_cli.py`.
- **Requisitos:** RF-03, RF-06, RF-07, RF-13, RF-16; RNF-02, RNF-08, RNF-10.
- **ADR:** ADR-001, ADR-006, ADR-007.
- **Teste:** `test_cli_extrair_data_ref_e_propaga_falha_sem_segredos` verifica argumentos, propagação de erro por código de saída e mensagens seguras.
- **Contrato adicionado:** `tests/test_cli.py` não existia; o teste falhou antes da implementação porque `src/cli.py` não existia.
- **Comando:** `python -m pytest tests/test_cli.py -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 44 passed, 2 skipped.
- **Depende de:** T-01, T-14, T-17.

### T-19 · Provar reexecução sem duplicar no MinIO local (30 min) — concluída
- **Objetivo:** executar duas vezes a mesma data no MinIO local e verificar raw/manifests históricos e bronze corrente.
- **Arquivos:** `tests/integration/test_pipeline.py`, `tests/conftest.py`.
- **Requisitos:** RF-09, RF-10, RF-13, RF-15; RNF-04, RNF-07, RNF-10.
- **ADR:** ADR-002, ADR-006.
- **Teste:** `test_reexecucao_reutiliza_raw_preserva_manifesto_e_substitui_bronze` verifica chave igual para bytes iguais, manifesto novo, nenhum UPC duplicado e preservação do raw anterior.
- **Contrato adicionado:** teste de integração confirmou os contratos antes de alteração da implementação de armazenamento; `tests/conftest.py` carrega `.env` local via `python-dotenv` sem imprimir credenciais.
- **Comando:** `TEST_MINIO=1 python -m pytest tests/integration/test_pipeline.py -q` — 1 passed.
- **Verificação completa:** `python -m pytest -q` — 44 passed, 3 skipped.
- **Depende de:** T-06, T-17, T-18.

### T-20 · Verificar configuração do MinIO no Railway (25 min) — concluída
- **Objetivo:** rodar os mesmos testes de armazenamento contra Railway com configuração de ambiente, sem alterar código ou expor credenciais.
- **Arquivos:** `tests/integration/test_storage_minio.py`, `tests/conftest.py`, `.env.example`.
- **Requisitos:** RF-09, RF-10, RF-13; RNF-04, RNF-08, RNF-10.
- **ADR:** ADR-002.
- **Teste:** `test_minio_real_le_e_grava_no_bucket_teste` verifica round-trip e metadados ASCII no destino selecionado; teste requer Railway disponível.
- **Contrato:** `test_minio_real_le_e_grava_no_bucket_teste` e `test_proxy_502_repete_put_mesma_chave`; o Railway foi acessado com as credenciais injetadas em memória, sem exibi-las.
- **Correção acoplada:** `load_config()` agora aplica variáveis de ambiente sobre `.env`, permitindo que configuração injetada pelo Railway prevaleça; o teste `test_variaveis_injetadas_sobrescrevem_valores_do_dotenv` falhou antes da correção.
- **Provisionamento autorizado:** bucket `teste` criado no serviço Railway após `head_bucket` indicar HTTP 404.
- **Comando:** `railway run python -c '...'` mapeando credenciais em memória e executando `pytest tests/integration/test_storage_minio.py -q` — 2 passed.
- **Verificação local alternativa:** `TEST_MINIO=1 python -m pytest tests/integration/test_storage_minio.py -q` — 2 passed.
- **Depende de:** T-06, T-18; projeto Railway e bucket `teste` provisionados.

## Matriz requisito → tarefas

| Requisito | Tarefas |
|---|---|
| RF-01 | T-09 |
| RF-02 | T-10 |
| RF-03 | T-01, T-09, T-18 |
| RF-04 | T-11 |
| RF-05 | T-02, T-03, T-09 |
| RF-06 | T-02, T-03, T-04, T-09, T-10, T-18 |
| RF-07 | T-02, T-03, T-12, T-18 |
| RF-08 | T-13 |
| RF-09 | T-05, T-06, T-10, T-11, T-19, T-20 |
| RF-10 | T-05, T-06, T-13, T-19, T-20 |
| RF-11 | T-15, T-16, T-17 |
| RF-12 | T-12, T-15, T-16, T-17 |
| RF-13 | T-07, T-08, T-13, T-14, T-17, T-18, T-19, T-20 |
| RF-14 | T-14, T-17 |
| RF-15 | T-19 |
| RF-16 | T-02, T-03, T-12, T-18 |
| RNF-01 | T-11, T-12, T-14, T-15, T-16, T-17 |
| RNF-02 | T-02, T-03, T-12, T-18 |
| RNF-03 | T-04, T-09, T-10, T-11 |
| RNF-04 | T-05, T-06, T-19, T-20 |
| RNF-05 | T-07, T-08, T-09, T-13, T-14, T-17 |
| RNF-06 | T-03, T-04, T-10, T-12 |
| RNF-07 | T-05, T-06, T-07, T-08, T-13, T-17, T-19 |
| RNF-08 | T-01, T-18, T-20 |
| RNF-09 | T-16 |
| RNF-10 | T-01, T-05, T-06, T-17, T-18, T-19, T-20 |
