# Avaliação ATAM

> Etapa 7 do SDD. Avaliação baseada em `specs/spec.md`, `specs/plan.md`,
> `specs/tasks.md` e nas evidências disponíveis em `docs/evidencias/`.
> Esta análise registra trade-offs e lacunas; não é certificação de segurança,
> disponibilidade ou custo.

## 1. Drivers de negócio e abordagens arquiteturais

- **DRV-01 — custo:** crédito único de US$ 5 no trial e plano Free informado
  como US$ 1/mês após o trial. O acompanhamento de consumo está em T-09 e
  ainda não tem evidência.
- **DRV-02 — persistência e disponibilidade:** reutilizar dados entre deploys e
  reinícios. O serviço Railway usa volume em `/data`; o objeto verificado
  sobreviveu a um redeploy.
- **DRV-03 — segurança:** API autenticada e segredos fora do repositório
  público. A verificação anônima retornou HTTP 403; uma varredura de segredos
  no histórico Git não está evidenciada.
- **DRV-04 — reprodutibilidade:** recriar e verificar o storage por comandos.
  README e scripts existem; a recriação por outro integrante em ambiente vazio
  ainda não foi demonstrada.

Abordagens avaliadas: imagem/tag fixadas (ADR-001), exposição pública somente
da API na porta 9000 (ADR-002), Compose local (ADR-003), volume persistente em
`/data` (ADR-004), credenciais em variáveis externas ao Git (ADR-005), operação
por `mc` e scripts (ADR-006), retry idempotente planejado para 502 (ADR-007),
evidências em arquivos (ADR-008) e acompanhamento manual do crédito (ADR-009).

## 2. Utility tree

| Atributo | Refinamento | Cenário (resumo) | Importância | Dificuldade |
|---|---|---|---|---|
| Persistência/disponibilidade | recuperar estado após troca de contêiner | CEN-01 redeploy não perde dados | Alta | Média |
| Segurança | detectar e conter exposição de credencial | CEN-02 senha commitada no repositório público | Alta | Média |
| Custo | acompanhar consumo e evitar ultrapassar o crédito | CEN-03 crédito do trial acabando | Alta | Alta |
| Disponibilidade/integridade | concluir escrita de resultado ambíguo após falha do proxy | CEN-04 HTTP 502 durante gravação | Alta | Alta |
| Retenção/recuperabilidade | reconhecer e mitigar expiração do volume trial | CEN-05 volume apagado 30 dias após fim dos créditos | Alta | Alta |

As classificações de importância e dificuldade são avaliações qualitativas,
não métricas de desempenho. Dificuldade alta indica dependência de operação
manual, comportamento externo ou experimento ainda não realizado.

## 3. Cenários de qualidade

### CEN-01: redeploy não perde dados

| Parte | Conteúdo |
|---|---|
| Fonte | Integrante do grupo que opera o serviço |
| Estímulo | Executa um redeploy do serviço MinIO |
| Ambiente | Operação normal, com `raw/t07-persistencia.txt` gravado antes do redeploy |
| Artefato | Serviço MinIO e volume Railway montado em `/data` |
| Resposta | O contêiner novo monta o volume existente e o objeto continua acessível |
| Métrica | Para o objeto de teste: `persistencia-t07` lido após o redeploy igual ao conteúdo gravado antes; zero perda desse objeto. Medição: comparação do conteúdo antes/depois registrada em `docs/evidencias/T-07_persistencia.txt`. Generalização para todos os objetos: hipótese: validação pendente; medir inventários e checksums antes/depois. |

- **Decisão/tática (Len Bass):** ADR-004, separar dados persistentes do
  contêiner substituível; disponibilidade — recuperação/reintrodução do
  serviço usando o volume existente.
- **Evidência existente:** `docs/evidencias/T-07_persistencia.txt`; o conteúdo
  `persistencia-t07` em `raw/t07-persistencia.txt` foi lido após o redeploy.
  A primeira leitura retornou 502; a repetição manual após 10 segundos teve
  sucesso.
- **Lacuna:** o teste confirma um objeto específico, mas não comprova a
  retenção de todos os objetos nem a recuperação de inventário completo.

### CEN-02: credencial commitada no repositório público

| Parte | Conteúdo |
|---|---|
| Fonte | Integrante, agente de código ou automação que publica uma alteração |
| Estímulo | Uma credencial é incluída acidentalmente em um commit |
| Ambiente | Repositório público, antes ou depois de o commit ser publicado |
| Artefato | Histórico Git, credenciais do serviço e API S3 |
| Resposta | O incidente deve ser tratado como exposição: revogar/rotacionar a credencial no provedor, atualizar o `.env` local e verificar/remediar o histórico; o processo atual não automatiza detecção ou rotação |
| Métrica | Alvo: zero credenciais válidas presentes nas referências Git publicadas; medir com varredura de segredos sobre árvore e histórico completo. Após incidente, confirmar que a credencial exposta não autentica. Prazo de detecção e revogação: hipótese: validação pendente; medir um exercício controlado sem publicar segredo real. |

- **Decisão/tática (Len Bass):** ADR-005 e ADR-002; segurança — resistir por
  não versionar credenciais e limitar a superfície exposta; reagir revogando
  a credencial comprometida.
- **Evidência existente:** `docs/evidencias/verificar_railway.txt`
  demonstra HTTP 403 sem autenticação; isso comprova uma parte do controle de
  acesso, não a ausência de segredos no histórico.
- **Lacuna:** não há evidência de varredura do repositório/histórico, alerta de
  segredo ou ensaio de revogação. Durante o primeiro startup Railway foi
  observado um aviso de credenciais padrão; logs posteriores, após ação do
  grupo, não mostraram esse aviso. Os valores não são reproduzidos aqui.

### CEN-03: crédito do trial acabando

| Parte | Conteúdo |
|---|---|
| Fonte | Integrante responsável por acompanhar o trial |
| Estímulo | O consumo acumulado se aproxima do crédito único de US$ 5 |
| Ambiente | Projeto Railway durante o trial, com serviço e volume ativos |
| Artefato | Conta de cobrança e processo manual de acompanhamento T-09 |
| Resposta | O grupo consulta o consumo na plataforma e decide parar, reduzir ou manter o uso antes de exceder o crédito; não há alerta automático documentado |
| Métrica | Consumo acumulado no trial menor ou igual a US$ 5; medir pelo painel/registro de uso Railway e salvar a consulta em evidência. Frequência de consulta e limite preventivo de alerta: hipótese: validação pendente. |

- **Decisão/tática (Len Bass):** ADR-009; disponibilidade/custo — limitar
  demanda de recursos e acompanhar o estado operacional por observação manual.
- **Evidência existente:** nenhuma evidência de consumo; T-09 continua pendente.
  `docs/evidencias/T-06_deploy.txt` documenta o deploy, não o gasto.
- **Lacuna:** consumo atual, periodicidade de consulta e procedimento quando
  o limite se aproxima não foram registrados. O valor informado para o trial
  é US$ 5; o plano Free e seu custo têm período e escopo distintos.

### CEN-04: HTTP 502 do proxy durante uma gravação

| Parte | Conteúdo |
|---|---|
| Fonte | Proxy Railway |
| Estímulo | Retorna HTTP 502 durante uma gravação, cujo resultado pode ser desconhecido |
| Ambiente | Serviço publicado, durante operação de escrita |
| Artefato | Cliente de gravação e chave do objeto |
| Resposta | A abordagem planejada é repetir a mesma chave e conteúdo com espera crescente; essa lógica ainda precisa ser implementada e testada |
| Métrica | Em teste controlado com 502 simulado: um objeto final na chave esperada e conteúdo igual ao esperado. Medir tentativas e resultado no teste. Máximo de tentativas: hipótese: validação pendente. |

- **Decisão/tática (Len Bass):** ADR-007; disponibilidade — retry para falha
  transitória e recuperação; integridade — tornar repetição idempotente usando
  a mesma chave e conteúdo.
- **Evidência existente:** nenhuma evidência de teste controlado de 502;
  T-08 permanece pendente.
- **Lacuna:** estratégia, limite de tentativas e comportamento sob resultado
  ambíguo não foram validados. O sucesso do `mc pipe` sem 502 não demonstra
  tolerância a essa falha.

### CEN-05: volume apagado 30 dias após o fim dos créditos

| Parte | Conteúdo |
|---|---|
| Fonte | Ciclo de vida de conta trial da plataforma Railway |
| Estímulo | A janela informada de 30 dias após o fim dos créditos termina e o volume é apagado |
| Ambiente | Conta trial após o encerramento do crédito |
| Artefato | Volume montado em `/data` e todos os objetos armazenados nele |
| Resposta | A arquitetura atual não oferece cópia de recuperação; sem ação do grupo, o serviço perde os dados quando o volume é apagado. Recomenda-se exportar os objetos para armazenamento independente antes do prazo, sujeito à decisão de custo e retenção do grupo. |
| Métrica | Alvo derivado de OBJ-02: 100% dos objetos necessários ao semestre com cópia independente antes do prazo; medir inventários/checksums entre volume e cópia. Viabilidade, destino e custo dessa cópia: hipótese: validação pendente. |

- **Decisão/tática (Len Bass):** ADR-004; disponibilidade — preparação para
  recuperação e armazenamento persistente durante o ciclo de vida do serviço.
  Não existe tática de backup implementada; backup automático está fora do
  escopo.
- **Evidência existente:** `docs/evidencias/T-06_deploy.txt` registra o volume
  em `/data`; `docs/evidencias/T-07_persistencia.txt` cobre somente redeploy.
- **Lacuna:** não existe evidência de exportação, recuperação após exclusão,
  aviso de prazo ou retenção além do ciclo trial. Persistência entre redeploys
  não protege contra a exclusão do volume.

## 4. Descobertas

| Tipo | Descrição | Cenário | Decisão |
|---|---|---|---|
| Ponto de sensibilidade | A persistência depende do volume estar montado exatamente em `/data`, caminho usado pelo processo MinIO. Divergência entre montagem e diretório de dados invalida a tática. | CEN-01, CEN-05 | ADR-004 |
| Ponto de trade-off | Volume e serviço publicados ajudam a disponibilidade, mas consomem recursos sob crédito limitado; cópia independente melhora recuperação, mas pode acrescentar custo e operação. | CEN-03, CEN-05 | ADR-004, ADR-009 |
| Risco confirmado | A plataforma informa exclusão do volume trial 30 dias após o fim dos créditos; não há cópia/recuperação demonstrada. | CEN-05 | ADR-004 |
| Risco confirmado | O proxy pode produzir 502 e T-08, que deveria validar repetição idempotente, continua pendente. | CEN-04 | ADR-007 |
| Risco confirmado | T-09 não tem registro de consumo do trial; não há evidência de que o uso permaneça abaixo de US$ 5. | CEN-03 | ADR-009 |
| Risco confirmado | Um startup inicial mostrou alerta de credenciais padrão; embora os logs posteriores após ação do grupo não tenham repetido o alerta, faltam varredura de histórico e teste de revogação. | CEN-02 | ADR-005 |
| Não-risco observado | Na consulta de domínios do serviço `minio`, foi listado somente o domínio de porta 9000; não foi observado domínio público para o console 9001. Essa observação ainda não foi salva como evidência versionada. | CEN-02 | ADR-002 |
| Tema de risco | Ciclo de vida, propriedade e recuperabilidade dos dados em um serviço trial: prazo de exclusão, custo de cópias, monitoramento e ação do grupo precisam ser tratados em conjunto. | CEN-03, CEN-05 | ADR-004, ADR-009 |

**Distinção:** os fatos de exclusão do volume e ocorrência esporádica de 502
são riscos confirmados pela restrição/fato de entrada. O custo atual, a
possibilidade de comprometimento e a taxa de falhas não foram medidos; são
dúvidas não investigadas, não ocorrências confirmadas.

## 5. Matriz de rastreabilidade

A matriz completa, com um estado para cada RF e RNF, está em
`docs/rastreabilidade.md`.

## 6. Riscos aceitos, riscos residuais e próximos experimentos

### Riscos aceitos

Não há aceitação formal de risco registrada pelo grupo. Alta disponibilidade
com múltiplos nós e backup automático agendado estão fora do escopo de produto,
mas a consequência de perda de dados permanece risco residual — não se presume
que o grupo aceitou essa perda.

### Riscos residuais

- Exclusão do volume trial após o prazo informado, sem cópia independente
  comprovada (CEN-05).
- Consumo do crédito sem evidência ou alerta preventivo (CEN-03).
- Falha 502 durante escrita sem tratamento implementado/testado (CEN-04).
- Credencial exposta sem varredura do histórico ou procedimento de revogação
  exercitado (CEN-02).
- Evidência de persistência comprova um objeto após redeploy, mas não a
  retenção de todos os objetos (CEN-01).
- Recriação a partir de ambiente vazio por outro integrante não foi observada
  (RF-05).

### Próximos experimentos

1. Comparar inventários/checksums antes e depois de um redeploy para avaliar a
   persistência além do objeto único de T-07.
2. Executar T-08 com 502 controlado, incluindo resultado inicial ambíguo;
   registrar tentativas e conteúdo final.
3. Executar T-09: consultar consumo Railway, registrar valor e data sem dados
   de credenciais; definir periodicidade e limiar preventivo.
4. Fazer varredura aprovada pelo grupo sobre arquivos e histórico Git; se houver
   credencial, revogá-la/rotacioná-la antes de qualquer republicação.
5. Ensaiar a recriação local por outro integrante em ambiente vazio, sem apagar
   volumes que contenham dados do grupo.
6. Definir e testar como preservar os objetos antes da expiração do volume trial;
   medir inventários/checksums e custo antes de escolher o destino.
