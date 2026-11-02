# Tarefas de implementação do coletor

Ordem de execução: dependências indicadas em cada tarefa. As esperas, timeout e
limite de tentativas do retry são hipótese, validação pendente (RNF-01, RNF-03).

## T-01 Estruturar pacote e testes
- Status: concluída.
- Requisitos: RF-01, RNF-04.
- Arquivos: `src/__init__.py`, `tests/test_estrutura.py`, `pytest.ini`.
- Teste que prova: `test_pacote_src_importavel`.
- Pronto quando: `pytest.ini` registra o marcador `integracao` e
  `python -m pytest -q tests/test_estrutura.py` passa.
- Depende de: nenhuma.

## T-02 Carregar configuração e validar o pouso
- Status: concluída.
- Requisitos: RF-01, RF-02, RNF-04, RNF-05; OBJ-02, OBJ-03.
- Arquivos: `src/config.py`, `src/leitura.py`, `tests/test_config.py`,
  `tests/test_leitura.py`.
- Teste que prova: `test_config_carrega_variaveis_de_ambiente`,
  `test_lista_todos_os_arquivos_do_pouso`,
  `test_nome_invalido_e_mantido_no_pouso`.
- Pronto quando: `python -m pytest -q tests/test_config.py tests/test_leitura.py`
  passa e a revisão de `git diff --staged` não encontra credenciais.
- Depende de: T-01.

## T-03 Construir chave UTC e metadados
- Status: concluída.
- Requisitos: RF-03, RF-08; OBJ-01, OBJ-02, OBJ-03.
- Arquivos: `src/chaves.py`, `src/metadados.py`, `tests/test_chaves.py`,
  `tests/test_metadados.py`.
- Teste que prova: `test_chave_usa_inicio_da_janela_em_utc`,
  `test_chave_avanca_data_no_limite_utc`, `test_metadados_em_ascii`.
- Pronto quando: estes testes passam com
  `python -m pytest -q tests/test_chaves.py tests/test_metadados.py` e os sete
  metadados correspondem ao formato da spec.
- Depende de: T-01.

## T-04 Gravar bytes e metadados no MinIO
- Status: concluída.
- Requisitos: RF-04, RF-08, RNF-06; OBJ-01.
- Arquivos: `src/gravacao.py`, `tests/fakes.py`, `tests/test_gravacao.py`.
- Teste que prova: `test_put_preserva_bytes_sha256_e_metadados`.
- Pronto quando: o armazenamento falso recebe os bytes originais sem
  decodificação ou reserialização, e
  `python -m pytest -q tests/test_gravacao.py` passa.
- Depende de: T-02, T-03.

## T-05 Reconhecer retransmissão idêntica
- Requisitos: RF-05, RF-07; OBJ-01.
- Arquivos: `src/gravacao.py`, `src/limpeza.py`, `tests/fakes.py`,
  `tests/test_idempotencia.py`.
- Teste que prova: `test_duas_execucoes_identicas_fazem_um_put_e_status_ja_existia`.
- Pronto quando: duas execuções sobre o mesmo lote no armazenamento falso
  fazem um único PUT, a segunda registra `ja_existia` e
  `python -m pytest -q tests/test_idempotencia.py` passa.
- Depende de: T-04.

## T-06 Detectar retransmissão com conteúdo divergente
- Requisitos: RF-06, RF-07; OBJ-01.
- Arquivos: `src/gravacao.py`, `src/limpeza.py`, `tests/fakes.py`,
  `tests/test_conflito_hash.py`.
- Teste que prova: `test_mesma_chave_conteudo_diferente_registra_conflito_sem_put_e_mantem_pouso`.
- Pronto quando: mesmo nome com conteúdo diferente resulta em
  `conflito_hash`, nenhum PUT é feito e o arquivo continua no pouso;
  `python -m pytest -q tests/test_conflito_hash.py` passa.
- Depende de: T-04.

## T-07 Reconciliar e repetir falhas transitórias
- Requisitos: RNF-01, RNF-02, RNF-03, RF-05, RF-06, RF-07; OBJ-01, OBJ-02,
  OBJ-03.
- Arquivos: `src/gravacao.py`, `tests/fakes.py`, `tests/test_retry.py`.
- Teste que prova: `test_502_head_ausente_reenvia_put_apos_espera_crescente`,
  `test_403_nao_faz_nova_tentativa`,
  `test_502_head_igual_registra_ja_existia_sem_repetir`,
  `test_502_head_diferente_registra_conflito_sem_repetir`,
  `test_502_head_inconclusivo_registra_erro_sem_repetir`.
- Pronto quando: o falso responde 502 e depois sucesso após HEAD confirmar
  ausência, 403 não gera nova tentativa e os demais estados de HEAD têm o
  desfecho especificado; `python -m pytest -q tests/test_retry.py` passa.
- Depende de: T-04.

## T-08 Remover somente após confirmação
- Requisitos: RF-07; OBJ-01, OBJ-02.
- Arquivos: `src/limpeza.py`, `tests/fakes.py`, `tests/test_limpeza.py`.
- Teste que prova: `test_put_falha_mantem_arquivo_no_pouso`,
  `test_remove_apos_put_confirmado_ou_ja_existia_identico`.
- Pronto quando: a falha simulada de PUT mantém o arquivo no pouso, e a
  remoção só ocorre após PUT confirmado ou `ja_existia` com hash igual;
  `python -m pytest -q tests/test_limpeza.py` passa.
- Depende de: T-05, T-06, T-07.

## T-09 Gerar manifesto e concluir a execução
- Requisitos: RF-01, RF-02, RF-09, RF-10, RF-11; OBJ-01, OBJ-02, OBJ-03.
- Arquivos: `src/manifesto.py`, `src/coletor.py`, `tests/test_manifesto.py`,
  `tests/test_coletor.py`.
- Teste que prova: `test_manifesto_tem_uma_linha_por_arquivo`,
  `test_manifesto_invalido_e_ilegivel_tem_campos_corretos`,
  `test_falha_em_lote_nao_interrompe_demais`,
  `test_codigo_de_saida_sinaliza_erro_ou_conflito`.
- Pronto quando: o manifesto JSONL segue caminho UTC e formato da spec,
  inclui os resultados por arquivo, a execução continua após falha individual
  e termina com o código de saída previsto; os testes listados passam com
  `python -m pytest -q tests/test_manifesto.py tests/test_coletor.py`.
- Depende de: T-02, T-04, T-05, T-06, T-07, T-08.

## T-10 Validar integração contra o MinIO local
- Requisitos: RF-01, RF-04, RF-05, RF-07, RF-08, RF-09, RNF-04, RNF-06;
  OBJ-01, OBJ-02, OBJ-03.
- Arquivos: `tests/test_integracao_minio.py`.
- Teste que prova: `test_integracao_80_lotes_hash_de_aceitacao_e_segunda_execucao`.
- Pronto quando: com MinIO local e variáveis de ambiente configurados, o teste
  executa `python gerar_lotes.py --inicio 2026-10-17T09:00`, confirma os 80
  objetos, bytes e metadados, manifesto e remoção confirmada; verifica que
  `CAM-0451_20261017T0900.txt` tem 983 bytes e SHA-256
  `6789b712602d1985d24df7b48370a1190da3db4e2576a74b07b5520d28601b12`, e
  confirma `ja_existia` na segunda execução. Passa com
  `python -m pytest -q -m integracao tests/test_integracao_minio.py`.
- Depende de: T-09.

## Cobertura de requisitos

| Requisito | Objetivo relacionado | Tarefa | Teste ou validação |
|---|---|---|---|
| RF-01 | OBJ-02, OBJ-03 | T-02, T-09, T-10 | `test_lista_todos_os_arquivos_do_pouso`; `test_manifesto_tem_uma_linha_por_arquivo`; `test_integracao_80_lotes_hash_de_aceitacao_e_segunda_execucao` |
| RF-02 | OBJ-03 | T-02, T-09 | `test_nome_invalido_e_mantido_no_pouso`; `test_manifesto_invalido_e_ilegivel_tem_campos_corretos` |
| RF-03 | OBJ-01, OBJ-02 | T-03 | `test_chave_usa_inicio_da_janela_em_utc`; `test_chave_avanca_data_no_limite_utc` |
| RF-04 | OBJ-01 | T-04, T-10 | `test_put_preserva_bytes_sha256_e_metadados`; `test_integracao_80_lotes_hash_de_aceitacao_e_segunda_execucao` |
| RF-05 | OBJ-01 | T-05, T-07, T-10 | `test_duas_execucoes_identicas_fazem_um_put_e_status_ja_existia`; `test_502_head_igual_registra_ja_existia_sem_repetir` |
| RF-06 | OBJ-01 | T-06, T-07 | `test_mesma_chave_conteudo_diferente_registra_conflito_sem_put_e_mantem_pouso`; `test_502_head_diferente_registra_conflito_sem_repetir` |
| RF-07 | OBJ-01, OBJ-02 | T-05, T-06, T-07, T-08, T-10 | `test_put_falha_mantem_arquivo_no_pouso`; `test_remove_apos_put_confirmado_ou_ja_existia_identico` |
| RF-08 | OBJ-01, OBJ-03 | T-03, T-04, T-10 | `test_metadados_em_ascii`; `test_put_preserva_bytes_sha256_e_metadados` |
| RF-09 | OBJ-01, OBJ-03 | T-09, T-10 | `test_manifesto_tem_uma_linha_por_arquivo`; `test_manifesto_invalido_e_ilegivel_tem_campos_corretos` |
| RF-10 | OBJ-02, OBJ-03 | T-09 | `test_falha_em_lote_nao_interrompe_demais` |
| RF-11 | OBJ-03 | T-09 | `test_codigo_de_saida_sinaliza_erro_ou_conflito` |
| RNF-01 | OBJ-02, OBJ-03 | T-07 | `test_502_head_ausente_reenvia_put_apos_espera_crescente` |
| RNF-02 | OBJ-01, OBJ-03 | T-07 | `test_403_nao_faz_nova_tentativa` |
| RNF-03 | OBJ-01, OBJ-02 | T-07 | Testes de 502 com HEAD igual, diferente, ausente e inconclusivo |
| RNF-04 | OBJ-01, OBJ-02, OBJ-03 | T-01, T-02, T-10 | `test_pacote_src_importavel`; `test_config_carrega_variaveis_de_ambiente`; teste de integração local |
| RNF-05 | OBJ-01, OBJ-03 | T-02 | `git diff --staged` sem valores de credenciais |
| RNF-06 | OBJ-01 | T-04, T-10 | `test_put_preserva_bytes_sha256_e_metadados`; teste de integração local |

### Lacunas registradas na especificação

- RNF-01 e RNF-03: número de tentativas, esperas e timeout permanecem
  hipótese, validação pendente; os testes verificam espera crescente sem fixar
  valores.
- RF-05 e RF-06: tratamento de objeto existente sem metadado `sha256`
  utilizável não está definido.
- RF-09: recuperação após falha no PUT do manifesto não está definida.
