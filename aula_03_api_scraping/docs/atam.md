# ATAM · Monitor de preços

## Escopo e método

Análise baseada em `docs/`, `specs/`, `src/`, `tests/` e no manifesto local mais recente consultado em 02/11/2026. Esta revisão registra também as correções implementadas para as três ações prioritárias; nenhuma especificação foi alterada. Prioridades usam **Importância** e **Dificuldade** alta (A), média (M) ou baixa (B); dificuldade alta significa que cumprir ou demonstrar o atributo é difícil. Métricas sem execução ou observação suficiente são explicitamente **evidência pendente**.

## Drivers arquiteturais

| Driver | Interesse | Implicação e consequência |
|---|---|---|
| DN-01 · Comparação diária sem referência de preço e câmbio | P1 precisa relacionar observações de livros a um fechamento GBP/BRL elegível na data de referência. | Escopo diário comum, filtragem de categorias, seleção temporal PTAX e dados extraídos com origem preservada. |
| DN-02 · Falhas de coleta sem diagnóstico oportuno | P2 precisa localizar ausência, falha HTTP/armazenamento e divergência de contagem. | Manifesto por execução, estados por item, tentativas, status, bytes, hashes e erros sanitizados. |
| DN-03 · Bronze difícil de consumir na Aula 04 | P3 precisa de registros JSON Lines rastreáveis e consistentes. | Separar bytes raw de parsing, validar contratos e publicar saídas diárias. |

Fontes: [objetivos de negócio](./01_objetivos_negocio.md), [regras de negócio](./02_regras_de_negocio.md), [RFs](../specs/01_requisitos_funcionais.md), [RNFs](../specs/02_requisitos_nao_funcionais.md).

## Utility tree

```text
Adequação funcional
├── Correção dos registros e vínculo livro/cotação (A/A)
└── Fechamento PTAX correto ou ausência explicitamente incompleta (A/M)
Confiabilidade
├── Falhas transitórias recuperáveis com tentativas limitadas (A/M)
├── Reexecução diária sem duplicar bronze e sem perder raw (A/M)
└── Diagnóstico íntegro no manifesto (A/A)
Eficiência e operação
├── Respeito a intervalo e paralelismo (A/M)
└── Coleta completa de aproximadamente 1.000 detalhes no limite de duração (M/A)
Compatibilidade e evolução
├── Mudança de HTML sem publicação falsa de dados incompletos (A/A)
└── Escrita e metadados compatíveis em MinIO local e Railway (A/A)
Confidencialidade
└── Credenciais ausentes dos artefatos versionados e de diagnóstico (A/M)
```

| Qualidade / estímulo | Importância | Dificuldade | Justificativa da prioridade |
|---|:---:|:---:|---|
| Correção e completude de livros e PTAX | A | A | Erro ou dado incompleto compromete P1/P3; dependência de páginas externas e parsing. |
| Diagnóstico e manifesto verificável | A | A | Operação depende do estado por etapa; o manifesto real observado omite fontes. |
| Retry de HTTP e MinIO | A | M | Falhas transitórias são esperadas, mas limites e caminho real de gravação precisam ser verificados em integração. |
| Reexecução e consistência raw/bronze | A | M | Uma execução deve substituir bronze sem apagar histórico bruto nem duplicar UPC. |
| Evolução do HTML de origem | A | A | Seletores de estrutura são rígidos e fixtures não representam mudanças futuras do site. |
| Intervalo e ausência de paralelismo | A | M | Obrigação da coleta; configuração permite intervalo zero e a trava é por instância de cliente. |
| Duração/custo da coleta completa | M | A | A linha de base indica 1.081 requisições e cerca de 18 min de espera a 1 s; desempenho integral não foi medido nesta análise. |
| Compatibilidade local/Railway | A | A | O ambiente remoto tem proxy, limites e comportamento distintos; teste remoto não demonstra o caminho completo da CLI. |
| Sigilo de configuração e logs | A | M | Credenciais são necessárias ao S3 e erros/manifestos são persistidos; há sanitização e `.env` ignorado, mas não análise adversarial. |

## Cenários de qualidade

Cada cenário explicita as seis partes ATAM. Medidas-alvo sem execução correspondente são identificadas como evidência pendente.

| Parte | C1 · Site muda o HTML |
|---|---|
| Fonte | Books to Scrape |
| Estímulo | Um deploy altera os seletores ou a estrutura dos cartões, breadcrumbs, detalhe ou paginação. |
| Artefato | `ColetorBooks`, parsing em `books.py`, `Extrator` e publicação bronze. |
| Ambiente | Coleta diária, HTML válido segundo o servidor mas incompatível com os seletores atuais. |
| Resposta | Detectar alteração estrutural em listagem e interromper antes de seguir para extração/publicação; os bytes da página permanecem no raw. |
| Medida | `PYTHONPATH=. .venv/bin/pytest tests/test_books.py::test_coletor_detecta_mudanca_na_estrutura_html_da_listagem -q` — 1 passed; o teste comprova erro explícito, bytes raw preservados e ausência de página parseada. Mudanças em detalhes, breadcrumbs, paginação e persistência do erro no manifesto: **evidência pendente**. |

| Parte | C2 · PTAX sem cotação na data |
|---|---|
| Fonte | API PTAX / Banco Central |
| Estímulo | A janela retorna HTTP 200 com `value` vazio ou sem `Fechamento` elegível até a data D. |
| Artefato | `ColetorPtax`, manifesto e extração da cotação. |
| Ambiente | Data de referência em fim de semana/feriado, janela operacional atual de 30 dias. |
| Resposta | Preservar bytes PTAX; não criar cotação; marcar a execução `incompleta` e guardar a causa. |
| Medida | `quote is None`, estado `incompleta`, objeto raw preservado e erro no item. `python -m pytest tests/test_ptax.py::test_janela_vazia_preserva_json_e_marca_incompleta -q` — 1 passed. Os 30 dias não garantem cobertura de qualquer feriado: cobertura universal é **evidência pendente**. |

| Parte | C3 · 429 ou timeout HTTP |
|---|---|
| Fonte | Books to Scrape ou API PTAX |
| Estímulo | Resposta 429 com `Retry-After`, timeout de conexão/leitura ou 5xx transitório. |
| Artefato | `ClienteHttp`, coletores e item do manifesto. |
| Ambiente | Execução diária, falha transitória recuperável ou persistente. |
| Resposta | Aguardar `Retry-After` válido ou full jitter, repetir apenas transitórios até o limite e registrar resultado final sem expor segredo. |
| Medida | O caminho PTAX da CLI usa tentativa HTTP única por chamada e um retry externo limitado: `PYTHONPATH=. .venv/bin/pytest tests/test_ptax.py::test_ptax_tem_quatro_tentativas_totais_com_cliente_http -q` — 1 passed, exatamente quatro chamadas com três 503 transitórios. O helper também mantém cobertura de `Retry-After` e timeout; limite de quatro foi verificado no coletor com cliente HTTP. |

| Parte | C4 · Reexecução no mesmo dia |
|---|---|
| Fonte | Operador P2 inicia nova execução para a mesma data. |
| Estímulo | Repetir coleta/extrator quando existem objetos raw, manifesto e JSON Lines diários anteriores. |
| Artefato | Chaves determinísticas, manifestos por execução e publicação bronze. |
| Ambiente | Mesmo MinIO e mesma data; bytes podem ser iguais ou novos. |
| Resposta | Criar manifesto novo; reutilizar raw idêntico, preservar histórico e substituir bronze somente após validação, sem UPC duplicado. |
| Medida | Igualdade da chave raw, IDs de manifesto distintos, manifesto anterior legível e zero UPC duplicado. `TEST_MINIO=1 python -m pytest tests/integration/test_pipeline.py -q` — 1 passed segundo o registro de T-19. O manifesto local atual está em estado `sucesso`; quantidade de reexecuções não é inferida dele. |

| Parte | C5 · Configuração agressiva: intervalo zero ou paralelismo |
|---|---|
| Fonte | Operador ou ambiente fornece configuração de coleta agressiva. |
| Estímulo | `HTTP_INTERVALO_MINIMO=0` ou tentativa de executar múltiplas coletas em paralelo. |
| Artefato | `Config`, `ClienteHttp` e coordenador da execução. |
| Ambiente | Uma instância ou múltiplos processos/instâncias usando a mesma origem. |
| Resposta | Rejeitar configuração que viole a política aprovada e garantir no máximo uma chamada ativa; registrar configuração inválida sem iniciar scraping. |
| Medida | Zero inícios abaixo do intervalo aprovado e concorrência máxima 1 por execução; teste existente usa intervalo de 1 s em uma instância. `Config` aceita zero e a trava é local a cada `ClienteHttp`; teste de zero/múltiplos processos é **evidência pendente**. |

| Parte | C6 · Custo de cerca de 1.000 detalhes por execução |
|---|---|
| Fonte | Catálogo Books to Scrape |
| Estímulo | Coleta sem filtro precisa visitar cerca de 1.000 páginas de detalhe, além de páginas e PTAX. |
| Artefato | `ColetorBooks`, `ClienteHttp`, `GravadorS3`, volume raw e duração da execução. |
| Ambiente | Execução completa sequencial; Codespace/Docker ou Railway trial de 1 GB de RAM. |
| Resposta | Fazer chamadas sequenciais com intervalo; persistir os bytes; terminar dentro do orçamento operacional ou produzir estado/diagnóstico de falha. |
| Medida | Linha de base documental: 1.081 requisições e cerca de 18 min de espera com intervalo de 1 s; limite de 30 min é hipótese. O manifesto local consultado representa escopo filtrado (52 extraídos), não prova custo da execução completa. Tempo, memória e bytes de uma execução completa: **evidência pendente**. |

| Parte | C7 · 502 do Railway durante PUT |
|---|---|
| Fonte | Proxy do Railway |
| Estímulo | `PutObject` recebe HTTP 502 transitório; o proxy pode responder antes ou depois de encaminhar a gravação. |
| Artefato | `GravadorS3`, objeto raw e item do manifesto. |
| Ambiente | Escrita raw em MinIO no Railway durante coleta. |
| Resposta | Repetir apenas falhas transitórias com limite de quatro tentativas, backoff com full jitter e os mesmos bytes/chave determinística; a camada automática do SDK S3 está desabilitada para evitar multiplicação; gravar tentativas totais no item do manifesto. |
| Medida | `PYTHONPATH=. .venv/bin/pytest tests/test_books.py::test_502_no_gravador_repite_put_na_mesma_chave_e_contabiliza_tentativa -q` — 1 passed; o fluxo do coletor usa `GravadorS3`, repete a mesma chave/corpo e registra duas tentativas. MinIO/Railway real permanece **evidência pendente**. |

## Riscos

| ID | Risco | Evidência / consequência | Prioridade |
|---|---|---|---|
| R-01 | Retry raw ainda precisa de confirmação em destino MinIO/Railway real. | `GravadorS3` agora repete falhas transitórias de PUT e o teste do fluxo do coletor verifica chave, bytes e tentativas no manifesto com backend simulado. Falha remota e comportamento do proxy permanecem **evidência pendente**. | M |
| R-02 | Limite de retry PTAX ainda depende de integração do caminho configurado. | Quatro chamadas totais são verificadas com `ClienteHttp.get_once` e o retry único de `ColetorPtax`; o teste de rede é simulado, não exercita o serviço PTAX real. | M |
| R-03 | Mudança de HTML fora da estrutura de cartões pode produzir campos incompletos. | Listagem agora falha explicitamente quando cartões/estrutura não correspondem; não há cobertura de deriva nos seletores de detalhes, breadcrumbs e paginação, nem persistência da causa no manifesto. | A |
| R-04 | O último manifesto observado não lista fontes nem escopo. | O objeto histórico `raw/manifestos/data=2026-10-24/execucao=e7189d5c-db61-4fc4-a982-b811d76b4455.json` não contém os dados corrigidos. Novas coletas registram `books.toscrape.com`, `PTAX`, tipo de escopo e categorias selecionadas; teste unitário da CLI verifica o JSON persistido. Ainda não foi gerado manifesto real após a correção. | M |
| R-05 | Política de intervalo pode ser desabilitada ou contornada. | Configuração permite intervalo zero; trava protege apenas chamadas pela mesma instância `ClienteHttp`. Processos concorrentes não compartilham limite. | A |
| R-06 | Janela PTAX de 30 dias não é garantia para qualquer feriado/indisponibilidade. | ADR-007 declara que 30 dias é escolha operacional, não garantia. Ausência legítima mantém ciclo incompleto. | M |
| R-07 | `Content-Type` do raw não está definido como HTML/JSON. | No MinIO o objeto HTML observado retornou `binary/octet-stream`; `gravar_raw` não envia `ContentType`. Ferramentas downstream podem não reconhecer formato sem inferir pela extensão. | M |
| R-08 | Orçamento de execução completa e capacidade não foram provados no caminho CLI. | RNF-03 tem duração de 30 min como hipótese; teste mede `run_collection`, mas `run_command` não o usa para aplicar limite. 1.000 detalhes e Railway trial podem ultrapassar o orçamento. | A |
| R-09 | Cobertura agregada esconde módulos pouco exercitados. | `src/coletar.py` e `src/extrair.py` têm 0%; `storage.py` 64%, `cli.py` 69% e `manifest.py` 75% no comando medido. O total não demonstra cobertura dos fluxos externos nem do caminho 502 em Railway. | M |

## Não riscos (evidência limitada ao escopo observado)

| ID | Afirmação delimitada | Evidência |
|---|---|---|
| NR-01 | A janela PTAX vazia não inventa cotação no teste contratual. | `test_janela_vazia_preserva_json_e_marca_incompleta` passa e verifica `quote is None`, raw gravado e manifesto incompleto. |
| NR-02 | A mensagem de falha da CLI não imprime a exceção detalhada no teste disponível. | `test_cli_extrair_data_ref_e_propaga_falha_sem_segredos` passa e verifica ausência da mensagem/traceback. Isso não prova que todo segredo em qualquer URL/metadado será sanitizado. |
| NR-03 | No manifesto local consultado, não houve item em estado falho nem HTTP diferente de 200/404. | O manifesto teve 57 itens: 56 HTTP 200 e 1 HTTP 404 (robots); todos `gravado`; total declarado e extraído 52/52. Evidência pontual, não garantia de outras execuções. |
| NR-04 | Os testes unitários de extração bloqueiam ou não utilizam rede externa. | `test_le_so_minio_sem_chamada_http` e `test_extrator_le_raw_sem_cliente_http_e_produz_registros` verificam que o extrator usa bytes raw. |

## Pontos de sensibilidade

| Parâmetro/decisão | Sensibilidade | Observação |
|---|---|---|
| `HTTP_INTERVALO_MINIMO` | Alta | Afeta ética/carga e duração; zero é aceito apesar de a especificação exigir intervalo mínimo. |
| `HTTP_MAX_TENTATIVAS`, timeout, backoff e `Retry-After` | Alta | Alteram número de chamadas e prazo; PTAX agora usa uma única camada de retry, mas a integração externa segue pendente. |
| `SCRAPER_CATEGORIAS` | Alta | Determina escopo e denominador da contagem; slug selecionado vira nome legível no caminho da chave. Manifesto deve conservar escopo/fontes para auditoria. |
| Janela PTAX de 30 dias | Alta | Janela maior aumenta payload e parsing; menor pode não conter o último fechamento. |
| Seletores HTML | Alta | Mudança de marcação afeta contagem, campos, categoria e UPC. |
| Estratégia de escrita/retry S3 | Alta | PUT raw tem retry explícito limitado e chave idempotente; resultado remoto ainda não foi ensaiado. |
| Metadados e MIME raw | Média | Origem/hash estão disponíveis, mas `ContentType` genérico foi observado no objeto HTML. |
| Limite de 1 GB e volume de raw | Média | Baseline indica cerca de 21,5 MiB de raw por coleta completa; histórico e respostas alteradas aumentam armazenamento. |
| Manifesto por execução | Média | Facilita auditoria, mas cresce a cada reexecução; o manifesto histórico permanece sem fontes/escopo, embora o fluxo novo preencha ambos. |

## Trade-offs

| Decisão | Ganho | Custo / risco residual |
|---|---|---|
| Coleta sequencial com intervalo | Evita pico de concorrência na origem. | Cerca de 1.000 detalhes tornam o tempo dependente do intervalo e dos retries. |
| Raw imutável, endereçado por hash | Permite reprocessar e auditar respostas originais. | Crescimento do armazenamento, especialmente em execuções com conteúdo alterado. |
| Janela PTAX histórica | Permite selecionar fechamento anterior em fim de semana. | Sem limite validado, janela fixa pode ser insuficiente; aumento de janela eleva payload. |
| Retry de falhas transitórias | Recupera instabilidade sem repetir indefinidamente; HTTP PTAX tem uma camada e PUT raw repete na mesma chave. | Mais espera/carga; integração remota e resultado posterior ao encaminhamento do proxy ainda não foram observados. |
| Bronze diário substituível | Consumidor lê a versão corrente sem juntar execuções. | Falha entre os dois PUTs bronze pode deixar livros e cotações de versões diferentes. |
| Manifesto por execução | Mantém diagnóstico e histórico; novas execuções preenchem fontes, escopo e tentativas de PUT. | O manifesto histórico não é retroativamente corrigido; acumula objetos. |
| Mesmo adaptador para MinIO local/Railway | Evita bifurcar interfaces. | Não elimina diferenças de proxy, timeout, permissão e metadados. |

## Medição de cobertura

Comando executado: `PYTHONPATH=. .venv/bin/pytest --cov=src`.

**57 passed, 3 skipped.** O relatório mediu 942 statements cobertos de 1.161 (`1.161 - 219 = 942`), razão exata **942/1161 = 314/387**; o resumo do pytest-cov exibe 81%. A fração preserva a medição sem arredondar.

## Três ações mais urgentes

1. Executar teste de integração de PUT com falha injetada em MinIO/Railway e confirmar manifesto/tentativas.
2. Cobrir mudanças dos seletores de detalhe, breadcrumbs e paginação; registrar a falha de parsing no manifesto.
3. Executar uma nova coleta real e confirmar fontes, escopo e tentativas no manifesto persistido.
