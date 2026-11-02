# Avaliação ATAM do coletor de telemetria

## Escopo e disciplina de evidência

Esta avaliação considera as personas e objetivos de negócio, a especificação,
o plano, as tarefas e o código atual em `src/`. Evidência fornecida em
conversa é identificada como tal; não é tratada como artefato versionado.
Resultados ausentes ou ambíguos permanecem lacunas, não confirmações.

**Fatos usados:** o teste completo foi informado como `56 passed`; o teste de
integração local, `1 passed`. A saída informada de `mc` mostra 80 arquivos,
80 listagens com `--versions` e `80KiB 80 objects raw/telemetria`. Também foi
informada uma listagem do alias `railway` contendo somente os prefixos
`_manifestos/` e `telemetria/`, ambos com `0B`. Os comandos e saídas foram
colados na conversa, não encontrados em arquivo do repositório.

**Limite importante:** não é possível atribuir com segurança os resultados de
80 objetos e 80 KiB ao Railway: o texto alterna aliases e o prefixo de
`mc du` é `raw/telemetria`, sem o alias explícito. A saída de `mc version
enable` também informa que `SetVersion` não é suportado pelo destino testado.
Logo, não há evidência de versionamento ativo nem de contagem de versões antes
e depois de uma retransmissão.

## Drivers de negócio e prioridades

| Prioridade | Driver / atributo | Origem | Consequência arquitetural |
|---|---|---|---|
| Alta | Integridade verificável da evidência | OBJ-01; P-01 | Preservar bytes, calcular SHA-256 e registrar procedência; não sobrescrever um objeto divergente. |
| Alta | Completude e recuperação das janelas | OBJ-02; P-01, P-02; provedor não mantém histórico | Manter arquivos não confirmados no pouso e tornar falhas observáveis. |
| Alta | Rastreabilidade e visibilidade operacional | OBJ-03; P-03 | Uma linha por arquivo no manifesto e código de saída não zero em falhas/conflitos. |
| Alta | Tratamento consistente de retransmissões | OBJ-01; contexto do provedor | HEAD e comparação de SHA-256 antes de PUT; primeira gravação prevalece no conflito. |
| Alta | Custo previsível | Restrição de crédito Railway descrita em `docs/01_objetivos_negocio.md` | Medir volume real e comparar com preço/fatura; preço de armazenamento não foi fornecido. |
| Alta | Segredos fora de arquivos versionados | RNF-05 | Obter endpoint e credenciais do ambiente; revisar diff e controlar exposição de credenciais. |
| Média | Evolução do formato de lote | RF-04; firmware prevê `TEMP_BAU` | Tratar conteúdo como bytes opacos; evitar parser acoplado aos formatos de linha. |

As prioridades refletem o impacto nos objetivos de negócio, não uma meta
quantitativa: metas de sucesso, retenção e tolerância a falhas continuam
“hipótese, validação pendente”.

## Utility tree

| Atributo | Refinamento | Cenários | Importância e justificativa | Dificuldade e justificativa |
|---|---|---|---|---|
| Integridade da evidência | Bytes originais, hash/metadados e preservação do primeiro objeto | C-02, C-07 | **Alta** — OBJ-01 e uso jurídico dependem de integridade verificável. | **Alta** — testes verificam repetição serial, mas não execuções concorrentes nem prova operacional com retenção/versionamento. |
| Completude / recuperabilidade | Falha de storage e PUT ambíguo | C-01, C-03 | **Alta** — o provedor não guarda histórico; falha pode perder uma janela. | **Alta** — existe reconciliação em código, mas não há retry configurado no CLI e o manifesto também depende do storage. |
| Observabilidade / auditabilidade | Manifesto, status por arquivo e saída do processo | C-01, C-03 | **Alta** — OBJ-03 exige saber o que falhou e ficou pendente. | **Média** — código e testes existem, mas falha de PUT do manifesto não tem recuperação. |
| Consistência / idempotência | Deduplicação serial e concorrente | C-02, C-07 | **Alta** — uma retransmissão não pode substituir evidência já recebida. | **Alta** — corrida HEAD-404/PUT não é protegida por lock ou escrita condicional. |
| Custo / capacidade | Projeção de bytes para 30 dias, comparação com crédito | C-04 | **Alta** — limite financeiro foi explicitado como restrição. | **Alta** — volume local medido; Railway e tarifa de armazenamento não confirmados, retenção e overhead desconhecidos. |
| Evolutibilidade | Firmware com campo adicional, sem interpretação do lote | C-05 | **Média** — há formato futuro previsto, mas o objetivo é preservar bytes. | **Média** — caminho de gravação é opaco a formatos, porém falta teste específico do firmware novo. |
| Segurança | Segredos, diffs e credenciais de storage | C-06 | **Alta** — RNF-05 proíbe credenciais versionadas; houve valor de credencial visível no contexto compartilhado. | **Média** — configuração por ambiente e `.env*` ignorado; não foi apresentada varredura automatizada do diff. |

## Cenários de qualidade

### C-01 — MinIO fora do ar durante a coleta

- **Fonte do estímulo:** mantenedora ou processo agendador.
- **Estímulo:** MinIO fica indisponível enquanto existem lotes no pouso.
- **Ambiente:** coleta normal, endpoint S3 recusando conexão.
- **Artefato:** `src/coletor.py`, `src/gravacao.py`, arquivos do pouso e bucket `raw`.
- **Resposta:** falhas de lote retornam status `erro`, não autorizam a remoção e levam a código diferente de zero. O coletor tenta publicar o manifesto ao final; se o próprio endpoint estiver fora, esse PUT falha e a execução termina com traceback, sem manifesto durável.
- **Medida da resposta:** arquivos não confirmados continuam no pouso; código de saída não zero; disponibilidade do manifesto verificada separadamente.
- **Decisão relacionada:** RF-07 mantém arquivo após falha; RF-09 publica manifesto ao final; RF-10 continua nos outros lotes.
- **Evidência existente:** `tests/test_limpeza.py::test_put_falha_mantem_arquivo_no_pouso_e_presente_durante_put` e `tests/test_coletor.py::test_falha_em_lote_nao_interrompe_demais`. Também foi colado um teste manual após `docker compose stop minio`: `ConnectionRefusedError` durante PUT do manifesto, código `1` e arquivo no pouso.
- **Lacuna:** não há política de manifesto local/spool nem recuperação do manifesto após indisponibilidade. O resultado manual confirma falha de publicação, não a disponibilidade de um manifesto alternativo.
- **Evidência executável adicional:** `python -m pytest -q tests/test_limpeza.py tests/test_coletor.py`; teste operacional com MinIO parado deve verificar arquivo remanescente, exit code e ausência/recuperação do manifesto, e depois reiniciar o serviço.

### C-02 — Os mesmos lotes chegam duas vezes

- **Fonte do estímulo:** provedor, agendador duplicado ou operador.
- **Estímulo:** os 80 lotes idênticos são coletados novamente.
- **Ambiente:** storage disponível; execução serial; objetos originais permanecem no bucket.
- **Artefato:** `src/gravacao.py`, `src/limpeza.py`, manifesto e bucket `raw`.
- **Resposta:** `ja_existia` por lote; nenhum novo PUT de lote; arquivo removido somente após HEAD confirmar hash igual.
- **Medida da resposta:** os mesmos 80 nomes/chaves antes e depois; segunda execução com 80 statuses `ja_existia`; comparação do conjunto de versões, se versionamento estiver ativo.
- **Decisão relacionada:** ADR-002 — primeira gravação da chave prevalece; igualdade do SHA-256 é idempotente.
- **Evidência existente:** `tests/test_idempotencia.py::test_duas_execucoes_identicas_fazem_um_put_e_status_ja_existia`; teste de integração local informado como `1 passed`, que regenera e coleta duas vezes, verifica 80 chaves e `ja_existia` na segunda. Saídas `mc` coladas informam 80 arquivos e 80 listagens com `--versions`.
- **Lacuna:** a saída de `mc` não contém uma comparação antes/depois. Além disso, `mc version enable` retornou `SetVersion is not supported`; a contagem 80 não prova ausência de versões adicionais em um bucket versionado. A atribuição dos 80 objetos/80 KiB ao alias local ou Railway não está inequívoca.
- **Evidência executável adicional:** `python -m pytest -q -m integracao tests/test_integracao_minio.py`; registrar saída de `mc find` antes/depois e comparar contagens/version IDs no mesmo alias.

### C-03 — MinIO Railway devolve 502 no PUT

- **Fonte do estímulo:** proxy ou serviço MinIO Railway.
- **Estímulo:** PUT do lote termina com HTTP 502, possivelmente após o servidor ter persistido o objeto.
- **Ambiente:** endpoint Railway corretamente apontado à porta da API S3.
- **Artefato:** `gravar_lote`, HEAD de reconciliação, retry e pouso.
- **Resposta:** primeiro consultar HEAD; hash igual resulta em `ja_existia`; hash diferente em `conflito_hash`; só após ausência confirmada pode haver novo PUT com política explícita; estado inconclusivo resulta em `erro`, sem remover o arquivo.
- **Medida da resposta:** ordem `PUT → HEAD → (novo PUT somente após 404)`; estado final coerente com hash; arquivo removido apenas após confirmação.
- **Decisão relacionada:** RNF-01 a RNF-03; retries do SDK estão desativados para que não contornem a reconciliação.
- **Evidência existente:** `tests/test_retry.py` cobre 502 com HEAD igual, diferente, ausente e inconclusivo, e retry com atrasos/sleeper injetados. Também houve erro operacional `S3 API Requests must be made to API port`, evidência de endpoint/porta inadequados, não de um 502 tratado com sucesso.
- **Lacuna:** `src/coletor.py` chama `gravar_lote` sem `atrasos` e `dormir`; portanto, o caminho CLI não repete o PUT após o primeiro 502, mesmo com HEAD confirmando ausência. Não há evidência colada de um 502 real do Railway nem de sucesso após retry na Railway.
- **Evidência executável adicional:** `python -m pytest -q tests/test_retry.py`; para integração Railway, primeiro confirmar endpoint API e executar teste controlado com observação do status/manifesto, sem reutilizar dados de produção.

### C-04 — Crescimento do bucket em 30 dias versus crédito Railway

- **Fonte do estímulo:** chegada contínua do provedor e limite financeiro.
- **Estímulo:** armazenar todos os lotes por 30 dias.
- **Ambiente:** hipótese de 20 caminhões, lote a cada 15 minutos, sem retenção/expurgo; crédito de US$ 5 por até 30 dias conforme `docs/01_objetivos_negocio.md`.
- **Artefato:** objetos `raw/telemetria/`, manifestos e medição de armazenamento.
- **Resposta:** medir payload e overhead, projetar volume e comparar com tarifa documentada antes de afirmar custo.
- **Medida da resposta:** medição observada (não memória): a saída colada de `mc du` informa **80 KiB em 80 objetos** para `raw/telemetria/`; a saída separada do gerador informa **81.987 bytes em 80 lotes**. A atribuição do `mc du` ao alias/ambiente permanece ambígua, portanto esses valores são medições da execução reportada, não uma medição confirmada do Railway. Projeção separada, derivada do valor medido de 80 KiB por hora e da premissa de 20 caminhões × 4 janelas/h: **1.920 lotes/dia**, **57.600 lotes/30 dias** e **57.600 KiB ≈ 56,25 MiB de payload/30 dias**. A projeção não é medição de memória nem medição real de 30 dias e exclui manifestos, overhead, versões, requisições e tráfego.
- **Decisão relacionada:** OBJ-02 e restrição de crédito; um objeto bruto por lote (RF-04).
- **Evidência existente:** saída `mc du` colada (`80KiB 80 objects raw/telemetria`) e gerador informou 80 lotes/81.987 bytes em uma execução de uma hora em conversa anterior.
- **Lacuna:** alias/ambiente da medição não está inequívoco e não há medição identificada como Railway. Não foi fornecida fonte oficial de preço por armazenamento, requisição, rede ou política de cobrança; comparar os 56,25 MiB com US$ 5 não permite concluir custo. A retenção real, o volume dos manifestos e o comportamento de versionamento também não estão definidos. **Preço: hipótese, validação pendente.**
- **Evidência executável adicional:** executar `mc du --depth 0 railway/raw/telemetria/` no alias confirmado e guardar saída datada; obter a tarifa aplicável em fonte oficial do Railway, citando URL/data; incluir manifestos e versões na projeção.

### C-05 — Firmware novo acrescenta `TEMP_BAU` ao formato 3

- **Fonte do estímulo:** fornecedor do firmware/provedor.
- **Estímulo:** linhas do formato 3 passam a terminar com `TEMP_BAU nn.n`.
- **Ambiente:** arquivos válidos do período de firmware novo; storage disponível.
- **Artefato:** leitura binária, hash, metadados, alerta e gravação.
- **Resposta:** armazenar exatamente os bytes recebidos; não rejeitar nem reinterpretar o novo campo; contar apenas linhas `TAC;...;ALERTA`.
- **Medida da resposta:** bytes e SHA-256 no objeto iguais aos do arquivo de origem; status final conforme HEAD/PUT.
- **Decisão relacionada:** RF-04 e escopo “sem parser”; formato é conteúdo opaco para o coletor.
- **Evidência existente:** `tests/test_gravacao.py::test_put_preserva_bytes_sha256_e_metadados` usa UTF-8, CRLF e `ç`, comprovando preservação geral de bytes. A especificação e `gerar_lotes.py` descrevem `TEMP_BAU` a partir do firmware novo.
- **Lacuna:** teste e integração de aceitação citados não usam explicitamente um lote com `TEMP_BAU`; compatibilidade é inferida do caminho binário, não medida para esse formato.
- **Evidência executável adicional:** gerar em diretório temporário lote de data posterior ao firmware, coletar em MinIO local e comparar `Path.read_bytes()`, corpo do objeto e SHA-256.

### C-06 — Credencial aparece em diff ou contexto compartilhado

- **Fonte do estímulo:** pessoa contribuinte, ferramenta de edição ou log.
- **Estímulo:** valor de `S3_ACCESS_KEY`/`S3_SECRET_KEY` aparece em diff, commit ou material compartilhado.
- **Ambiente:** revisão de mudança antes/depois de publicação.
- **Artefato:** `.env*`, configuração do processo, Git e credenciais S3.
- **Resposta:** bloquear publicação do segredo; revogar/rotacionar a credencial exposta; remover histórico conforme procedimento aprovado; manter configuração por ambiente e verificar novamente.
- **Medida da resposta:** nenhum segredo nos arquivos/diffs versionados; credencial antiga recusada após rotação; nova credencial não exibida em logs.
- **Decisão relacionada:** RNF-04/RNF-05; configuração via ambiente; `.env*` consta no `.gitignore`.
- **Evidência existente:** `src/config.py` carrega variáveis de ambiente; `tests/test_config.py::test_config_carrega_variaveis_de_ambiente`; `.gitignore` ignora `.env*`. A saída `git status` informada não listou `.env`. Um valor de credencial foi visível em material compartilhado nesta conversa; nenhum valor é reproduzido neste documento.
- **Lacuna:** não foi apresentada varredura do diff/objetos Git por segredo, nem evidência de rotação após a exposição. Estar ignorado pelo Git não desfaz compartilhamento externo. Tratar a credencial exposta como comprometida e rotacioná-la.
- **Evidência executável adicional:** executar scanner de segredos aprovado no diff e histórico; validar rotação pela recusa da credencial antiga sem imprimir valores. A revisão `git diff --cached` isolada não é detector completo.

### C-07 — Provedor retransmite o mesmo nome com conteúdo diferente

- **Fonte do estímulo:** provedor.
- **Estímulo:** mesmo `caminhao/janela` e nome de arquivo, mas SHA-256 divergente.
- **Ambiente:** objeto original já existe e HEAD retorna seus metadados.
- **Artefato:** `gravar_lote`, objeto original e arquivo retransmitido no pouso.
- **Resposta:** `conflito_hash`, nenhum PUT do lote, objeto original intocado e retransmissão mantida no pouso.
- **Medida da resposta:** zero PUT para a chave conflitante; SHA original continua no storage; bytes retransmitidos continuam no pouso; manifesto registra conflito.
- **Decisão relacionada:** ADR-002 — primeira gravação prevalece; conteúdo diferente nunca sobrescreve automaticamente.
- **Evidência existente:** `tests/test_conflito_hash.py::test_mesma_chave_conteudo_diferente_registra_conflito_sem_put_e_mantem_pouso`; `tests/test_limpeza.py::test_conflito_hash_mantem_arquivo_no_pouso`; `tests/test_retry.py::test_502_head_diferente_registra_conflito_sem_repetir`.
- **Lacuna:** não há procedimento operacional aprovado para revisar, adjudicar ou substituir uma retransmissão conflitante; qualquer correção manual precisa preservar a evidência original e trilha de auditoria.
- **Evidência executável adicional:** `python -m pytest -q tests/test_conflito_hash.py tests/test_limpeza.py`; em storage controlado, verificar hash/bytes antes e depois e a linha JSONL.

## Sensibilidade, trade-offs e riscos

### Pontos de sensibilidade

| Ponto | Efeito se variar |
|---|---|
| Nome do arquivo e instante de início da janela | Muda a chave determinística; colisões ou nome inválido afetam idempotência e partição. |
| SHA-256 nos metadados do HEAD | Metadado ausente causa erro deliberado; não há fallback para baixar e recalcular o objeto. |
| Disponibilidade do endpoint S3 | Afeta HEAD/PUT dos lotes e também PUT do manifesto; falha do manifesto pode tornar a execução sem registro durável. |
| Política de retry injetada | Sem `atrasos`, o CLI não repete após 502/timeout; com valores, muda duração e recuperação. Valores acordados permanecem hipótese, validação pendente. |
| Horário/precisão do nome de manifesto | Nome tem precisão de segundos; execuções simultâneas no mesmo segundo podem usar a mesma chave e sobrescrever manifesto. |
| Tamanho e retenção dos objetos | Determinam custo; política de retenção e tarifas não estão definidas. |
| Concorrência do coletor | Duas instâncias podem observar ausência e competir por PUT; HEAD-then-PUT não é operação atômica. |
| Momento da remoção do pouso | O gravador remove após confirmação do lote antes do PUT final do manifesto; falha do manifesto pode deixar lote apagado sem resultado durável. O plano registra decisão pendente. |

### Pontos de trade-off

| Escolha | Benefício | Custo / risco aceito |
|---|---|---|
| **Primeira gravação vale** (decisão) versus **última gravação vale** (alternativa) | Preserva o primeiro conteúdo confirmado; hash divergente vira `conflito_hash` para investigação, sem sobrescrita silenciosa. | A retransmissão divergente não é aceita automaticamente, mesmo se for uma correção legítima; requer adjudicação. A alternativa “última gravação vale” simplificaria atualização, mas substituiria a evidência anterior sem política aprovada. |
| **Parar em `conflito_hash`** (decisão) versus **aceitar retransmissão divergente** (alternativa) | Mantém o arquivo no pouso e sinaliza divergência. | Pode exigir intervenção e atrasar a completude da janela; aceitar automaticamente arrisca sobrescrever o objeto original. |
| Um objeto por lote e bytes originais | Preserva identidade e permite hash por janela. | Muitos objetos e operações S3; custo real não medido. |
| HEAD antes do PUT | Evita sobrescrita serial de conteúdo divergente. | Latência e janela de corrida com outro escritor entre HEAD e PUT. |
| Remover do pouso logo após confirmação do lote | Evita reprocessar conteúdo confirmado. | Manifesto final pode falhar depois da remoção; recuperação não definida. |
| Manifesto JSONL ao fim da execução | Registro consolidado por execução. | Manifesto depende do mesmo storage indisponível e timestamp em segundos pode colidir. |
| Não interpretar formatos de linha | Compatível com mudanças como `TEMP_BAU`; preserva lote bruto. | Métricas semânticas/validação de formato não são fornecidas. |
| Repetições com parâmetros injetados | Testável sem sleeps reais e sem números presumidos. | CLI não fornece política; operação não obtém retry até definir e configurar esses parâmetros. |

### Riscos confirmados e dúvidas não investigadas

| ID | Tipo | Risco / descoberta | Evidência e ação |
|---|---|---|---|
| R-01 | Confirmado | Com MinIO parado, a publicação do manifesto gera exceção de conexão após o processamento; não há manifesto durável dessa execução. | Traceback manual informado e fluxo de `executar`; definir spool/retry ou registrar explicitamente o limite operacional. |
| R-02 | Confirmado no código, não reproduzido em teste concorrente | HEAD seguido de PUT não é atômico; execuções simultâneas com bytes diferentes podem sobrescrever a primeira gravação. | `src/gravacao.py`; adicionar coordenação/PUT condicional ou aceitar/documentar risco após teste de corrida. |
| R-03 | Confirmado no código e no plano | Arquivo é removido após confirmação do lote antes de o manifesto ser enviado; a própria documentação chama a ordem de decisão pendente. | `src/gravacao.py`, `src/limpeza.py`, risco em `specs/plan.md`; decisão operacional ainda necessária. |
| R-04 | Confirmado no CLI | `src/coletor.py` não injeta atrasos/sleeper em `gravar_lote`; retries com espera existem nos testes mas não no caminho CLI. | `tests/test_retry.py` versus `src/coletor.py`; definir parâmetros após validação e cobrir CLI. |
| R-05 | Confirmado em saída operacional | `mc version enable` retornou `SetVersion is not supported`; versionamento não está comprovado no destino. | Saída colada; escolher storage que suporte versionamento ou não depender dele. |
| R-06 | Confirmado como exposição fora do repositório | Credencial foi visível no contexto compartilhado; isso não demonstra que entrou em commit, mas exige rotação. | Material compartilhado nesta conversa; rotacionar e executar scanner aprovado. |
| R-07 | Dúvida não investigada | 80 objetos/80 KiB e manifestos listados não têm associação inequívoca de alias e execução; não são evidência confiável do estado Railway. | Saídas `mc` coladas; repetir com alias explícito em cada comando e registrar antes/depois. |
| R-08 | Dúvida não investigada | Custo mensal real e margem para crédito não conhecidos. | Falta preço oficial, uso de rede/operações, retenção e tamanho Railway; obter fonte tarifária e medição identificada. |
| R-09 | Dúvida não investigada | Impacto de manifestos concorrentes com timestamps no mesmo segundo. | `caminho_manifesto` tem formato com precisão de segundos; criar teste concorrente ou aumentar unicidade. |

### Não-riscos no escopo avaliado

- `TEMP_BAU` não exige parser para gravar: o objeto é enviado como bytes; a ausência de teste específico é uma lacuna de evidência, não indicação de incompatibilidade no código atual.
- Um conflito serial com HEAD e metadado SHA-256 válido não sobrescreve o objeto pelo fluxo atual, conforme testes. Isso não elimina a corrida entre instâncias.
- Endpoint e credenciais são lidos do ambiente no `src/config.py`; isso reduz a necessidade de segredo em código, mas não prova que todos os diffs/históricos estejam limpos.
- O fato de `mc ls --recursive --versions` retornar 80 não demonstra versionamento habilitado nem ausência de versões extras sem comparação temporal.

### Temas de risco e decisões para revisão

1. Concorrência: lock distribuído, escrita condicional ou política explícita de escritor único.
2. Atomicidade operacional entre PUT do lote, remoção do pouso e PUT do manifesto.
3. Política executável de retry no CLI e sua compatibilidade com 502/timeout do Railway.
4. Evidência de retenção/versionamento, custo, limites e tarifa do Railway com fonte citada.
5. Rotação das credenciais que apareceram em contexto compartilhado e scanner no fluxo de revisão.
6. Unicidade do nome do manifesto e recuperação de execuções repetidas no mesmo segundo.

## Matriz de rastreabilidade — requisitos, decisões, componentes e evidências

| Requisito | Decisão arquitetural relacionada | Componente | Evidência disponível |
|---|---|---|---|
| RF-01 | Avaliar cada arquivo visível do pouso individualmente e registrar no manifesto. | `leitura.py`, `coletor.py`, `manifesto.py` | `test_lista_arquivos_visiveis_diretos_incluindo_nome_invalido`; `test_manifesto_tem_uma_linha_por_arquivo`; integração local informada: 1 passed. |
| RF-02 | Nome inválido não gera chave/PUT e permanece no pouso. | `leitura.py`, `coletor.py` | `test_nome_invalido_permanece_no_pouso`; `test_manifesto_invalido_e_ilegivel_tem_campos_corretos`. |
| RF-03 | Particionar pela janela local convertida para UTC, chave determinística. | `chaves.py` | `test_chave_usa_inicio_da_janela_em_utc`; `test_chave_avanca_data_no_limite_utc`; ADR-001. |
| RF-04 | Preservar corpo como bytes e calcular SHA-256 sobre esses bytes. | `gravacao.py` | `test_put_preserva_bytes_sha256_e_metadados`; integração local informada verifica lote de aceitação. |
| RF-05 | HEAD e hash igual significam `ja_existia`, sem novo PUT do lote. | `gravacao.py`, `limpeza.py` | `test_duas_execucoes_identicas_fazem_um_put_e_status_ja_existia`; integração local informada; ADR-002. |
| RF-06 | Hash diferente gera `conflito_hash`; preservar primeiro objeto e retransmissão. | `gravacao.py`, `limpeza.py` | `test_mesma_chave_conteudo_diferente_registra_conflito_sem_put_e_mantem_pouso`; ADR-002. |
| RF-07 | Remover apenas após PUT confirmado ou `ja_existia` com hash igual. | `gravacao.py`, `limpeza.py` | `test_put_falha_mantem_arquivo_no_pouso_e_presente_durante_put`; `test_conflito_hash_mantem_arquivo_no_pouso`. |
| RF-08 | Metadados ASCII de procedência acompanham o objeto. | `metadados.py`, `gravacao.py` | `test_metadados_em_ascii`; `test_put_preserva_bytes_sha256_e_metadados`; integração local informada. |
| RF-09 | Manifesto JSONL por execução, caminho com início UTC. | `manifesto.py`, `coletor.py` | `test_caminho_manifesto_converte_inicio_para_utc`; `test_manifesto_tem_uma_linha_por_arquivo`; integração local informada verifica manifesto. |
| RF-10 | Falha por lote não interrompe os seguintes. | `coletor.py` | `test_falha_em_lote_nao_interrompe_demais`. |
| RF-11 | Código de saída diferente de zero para `erro`/`conflito_hash`. | `coletor.py` | `test_codigo_de_saida_sinaliza_erro_ou_conflito`. |
| RNF-01 | Repetir falha transitória com espera crescente quando política for fornecida. | `gravacao.py`, `coletor.py` | `test_502_head_ausente_reenvia_put_apos_espera_crescente`; CLI não configura política. |
| RNF-02 | Não repetir 403. | `gravacao.py` | `test_403_nao_faz_nova_tentativa_nem_reconciliacao`. |
| RNF-03 | HEAD reconcilia PUT ambíguo antes de qualquer novo PUT. | `gravacao.py` | `test_502_head_igual_registra_ja_existia_sem_repetir`; `test_502_head_diferente_registra_conflito_sem_repetir`; `test_502_head_inconclusivo_retorna_erro_sem_repetir`. |
| RNF-04 | Endpoint, credenciais, região, bucket e pouso vêm do ambiente. | `config.py`, `coletor.py` | `test_config_carrega_variaveis_de_ambiente`; `test_main_configura_cliente_s3_sem_retry_automatico`. |
| RNF-05 | Não versionar credenciais; revisar diff e rotacionar segredo exposto. | Configuração, `.gitignore`, processo Git | `.env*` ignorado; saída `git status` colada não listou `.env`; credencial compartilhada exige rotação. Scanner não evidenciado. |
| RNF-06 | Usar API S3 e gravar no bucket configurado `raw`. | `coletor.py`, cliente boto3 | `test_main_configura_cliente_s3_sem_retry_automatico`; integração MinIO local informada: 1 passed. Evidência Railway não confirmada. |

## Evidências e referências

- Documentos de contexto: `docs/00_persona.md`, `docs/01_objetivos_negocio.md`.
- Requisitos e arquitetura: `specs/spec.md`, `specs/plan.md`, `specs/tasks.md`.
- Código avaliado: módulos em `src/`; testes citados em `tests/`.
- Saídas de pytest e `mc`: informadas pelo usuário na conversa em 2026-11-02; não armazenadas no repositório. As evidências Railway permanecem ambíguas.
