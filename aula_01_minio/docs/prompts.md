# Histórico de prompts

> Registro contínuo dos prompts CREATE efetivamente enviados ao agente, na ordem.
> Cole o texto exatamente como foi enviado, inclusive as correções. Não reescreva
> prompts antigos para parecerem melhores: o histórico real mostra como o projeto
> foi conduzido. Nunca cole chave, senha ou token aqui.

## P01: Persona

- Data e hora: 2026-10-31, 19:19 (horário de Brasília, UTC-03:00)
- Quem enviou: CaioBarthasar23
- Agente e modelo usados: GitHub Copilot Chat (modo Agent) no Codespaces; modelo: GPT-6 Luna
- Arquivos alterados: docs/00_persona.md
- Resultado da revisão ("Revise antes de seguir"): aceito. As 5 perguntas passaram. A persona descreve decisão e dor; nenhum número sem origem (a frequência de acesso ficou marcada como "hipótese: validação pendente"); a tabela de fatos tem 4 fatos e 1 lacuna, todos com origem; nenhum produto na dor nem no sucesso; o git status mostrou só docs/00_persona.md.

[C] Personagem
Você é um analista de requisitos de engenharia de dados que trabalha com um grupo de alunos de MBA. Nesta etapa você só descreve pessoas e problemas. Você não propõe tecnologia, não escreve código e não executa comandos.

[R] Pedido
Preencha docs/00_persona.md para o projeto aula_01_minio: um object storage próprio do grupo, compatível com a API S3, que será usado nas Aulas 02, 03 e 04 da disciplina (coleta de JSON, APIs e scraping, lakehouse) e no projeto final. Descreva uma persona principal: o engenheiro de dados do grupo, que precisa de um object storage próprio, barato e reprodutível para o semestre. Use a tabela que já existe no arquivo.

[E] Exemplos
Linha bem escrita:
| Dor atual | Cada integrante guarda arquivos no próprio Codespace; quando o Codespace é apagado, os dados coletados somem e ninguém consegue reproduzir a coleta do colega. |
Linha mal escrita (não faça assim):
| Dor atual | Precisa de uma solução escalável e robusta na nuvem. |

[A] Ajustes
- Use somente as informações deste prompt, de AGENTS.md e dos fatos listados em Extras.
- Não invente números (volume de dados, quantidade de arquivos, custo, tempo). Onde faltar um valor, escreva "hipótese: validação pendente".
- Não cite produtos ou ferramentas nas linhas de dor e de sucesso; a persona fala do problema dela.
- Preencha "Fatos, lacunas e suposições" com pelo menos três linhas, cada fato com a origem.
- Não crie nem altere outros arquivos.

[T] Tipo de saída
Somente docs/00_persona.md, em Markdown, com no máximo uma página. Antes de editar, mostre em tópicos o que vai escrever e espere minha confirmação.

[E] Extras
Leia antes: AGENTS.md e docs/00_persona.md.
Fatos do contexto (origem: enunciado da Aula 01):
- o grupo tem um único repositório público no GitHub e cada integrante trabalha no próprio Codespace;
- a plataforma de publicação é o Railway, com crédito único de US$ 5 no trial de até 30 dias;
- volumes de contas trial são apagados 30 dias após o fim dos créditos;
- a coleta da Aula 02 será horária e gravará JSON bruto.
Se faltar informação para uma linha, pergunte antes de supor. Ao terminar, liste as perguntas abertas e pare.

## P02: Objetivos de negócio

- Data e hora: 2026-10-31, 19:33 (horário de Brasília, UTC-03:00)
- Quem enviou: CaioBarthasar23
- Agente e modelo usados: GitHub Copilot Chat (modo Agent) no Codespaces; modelo: modelo: GPT-6 Luna
- Arquivos alterados: docs/01_objetivos_negocio.md
- Resultado da revisão ("Revise antes de seguir"): aceito. As 5 perguntas passaram: métricas verificáveis nos quatro objetivos (OBJ-04 com evidência marcada como hipótese e forma de medir); valores do enunciado copiados sem alteração; drivers ligados a cada objetivo; fora do escopo com os três itens; persona sem alteração. Duas perguntas abertas mantidas (escopo da meta de custo e evidência de recriação).

[C] Personagem
Você é um product owner técnico de uma equipe de dados. Você traduz a dor da persona em objetivos de negócio mensuráveis, drivers e restrições. Você não escreve requisitos técnicos nem código.

[R] Pedido
Preencha docs/01_objetivos_negocio.md a partir de docs/00_persona.md. Escreva exatamente estes quatro objetivos, cada um com métrica de sucesso e origem:
OBJ-01 custo dentro do crédito de US$ 5 do trial do Railway;
OBJ-02 dados persistem entre deploys e reinícios do serviço;
OBJ-03 acesso somente autenticado, sem segredo versionado no repositório público;
OBJ-04 storage recriável do zero por comandos documentados, por qualquer integrante.
Liste também os drivers de negócio, as restrições e o que fica fora do escopo.

[E] Exemplos
| OBJ-02 | Objetos gravados continuam disponíveis depois de um novo deploy ou reinício do serviço. | Um objeto de verificação gravado antes do redeploy aparece na listagem depois dele; zero objetos perdidos. | Persona: dor "os dados somem" |
| RES-02 | Imagem do MinIO: ghcr.io/coollabsio/minio, tag fixada | técnica | MinIO comunitário em manutenção, sem imagens oficiais (enunciado da Aula 01) |

[A] Ajustes
- Cada objetivo precisa de uma métrica verificável. Se o valor não estiver nos fatos abaixo, escreva "hipótese: validação pendente" e diga como medir.
- Restrições têm tipo (técnica, financeira, legal, prazo) e origem.
- Fora do escopo, inclua pelo menos: alta disponibilidade com múltiplos nós, console web público, backup automático agendado.
- Preserve a persona; não altere docs/00_persona.md.
- Não escolha tecnologia além das que estão nas restrições.

[T] Tipo de saída
Somente docs/01_objetivos_negocio.md, em Markdown, com as tabelas do modelo. Mostre o plano antes de editar e espere confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md.
Fatos e restrições (origem: enunciado da Aula 01):
- Railway trial: crédito único de US$ 5, até 30 dias; depois, plano Free com US$ 1 por mês; 1 GB de RAM, vCPU compartilhada, até 5 serviços por projeto; volumes de contas trial apagados 30 dias após o fim dos créditos.
- MinIO: imagem ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z; porta 9000 = API S3, 9001 = console.
- Repositório do grupo público no GitHub.
- Agente de código: o de preferência de cada integrante, sem chave de API em arquivo versionado.
- O storage será usado pelas Aulas 02, 03 e 04 e pelo projeto final.
Se faltar informação, pergunte. Ao terminar, liste perguntas abertas e pare.

## P03: Especificação

- Data e hora: 2026-10-31, 19:44 (horário de Brasília, UTC-03:00)
- Quem enviou: CaioBarthasar23
- Agente e modelo usados: GitHub Copilot Chat (modo Agent) no Codespaces; modelo: GPT-6 Luna
- Arquivos alterados: specs/spec.md
- Resultado da revisão ("Revise antes de seguir"): aceito. Os 11 itens do pedido viraram RF-01 a RF-07 e RNF-01 a RNF-04; critérios em Dado/Quando/Então e verificáveis; todo requisito com origem; único número fora de docs/ (tentativas máximas) marcado como hipótese; sem tecnologia fora das restrições. Houve uma rodada de esclarecimento: o agente perguntou se o Docker Compose podia ser citado; autorizado pelo pedido e registrado como pergunta aberta, sem alterar docs/.

[C] Personagem
Você é um engenheiro de requisitos de dados. Você escreve requisitos funcionais e não funcionais com critérios de aceite verificáveis. Você não escreve código e só cita tecnologia quando ela já é uma restrição em docs/01_objetivos_negocio.md.

[R] Pedido
Escreva specs/spec.md para o projeto aula_01_minio, derivando os requisitos de docs/00_persona.md e docs/01_objetivos_negocio.md. Cubra no mínimo:
- API compatível com S3 publicada por HTTPS num domínio do Railway;
- buckets raw, bronze, silver e gold;
- ambiente local equivalente por docker compose, com a mesma imagem e tag;
- verificação automatizada (saúde, acesso anônimo negado, buckets, gravação e leitura de objeto de teste), local e no Railway;
- recriação documentada do zero;
- persistência entre deploys;
- acesso autenticado e segredos fora do Git;
- custo acompanhado dentro do crédito;
- imagem fixada por tag, nunca latest;
- tolerância a 502 do proxy com nova tentativa e operações idempotentes;
- evidências de verificação registradas em docs/evidencias/.

[E] Exemplos
### RF-02: buckets da arquitetura medalhão
O storage do grupo oferece os buckets raw, bronze, silver e gold.
- Origem: OBJ-04
- Critério de aceite:
  - Dado o MinIO no ar e credenciais válidas no .env
  - Quando scripts/criar_buckets.sh railway for executado duas vezes seguidas
  - Então as duas execuções terminam com código 0 e mc ls lista exatamente os quatro buckets

### RNF-05: tolerância a 502 do proxy
- Atributo: disponibilidade e idempotência
- Origem: DRV-xx (proxy do Railway devolve 502 esporádico)
- Critério de aceite:
  - Dado um 502 numa gravação
  - Quando o cliente repetir a operação com espera crescente
  - Então o objeto existe uma única vez na chave esperada; número máximo de tentativas: hipótese: validação pendente

[A] Ajustes
- Numere RF-01, RF-02... e RNF-01, RNF-02...; cada requisito tem origem (OBJ, DRV ou RES).
- Todo critério de aceite usa Dado/Quando/Então e pode ser verificado por um comando ou teste.
- Não invente números de latência, disponibilidade ou volume. Valor ausente = "hipótese: validação pendente".
- Hipóteses de docs/ continuam hipóteses aqui; não as transforme em fato.
- Inclua "Fora do escopo" coerente com docs/01_objetivos_negocio.md.

[T] Tipo de saída
Somente specs/spec.md, em Markdown, com no máximo duas páginas. Mostre a lista de RF e RNF (só títulos) antes de escrever e espere confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md.
Fato adicional (origem: experiência do professor com serviços no Railway): o proxy do Railway devolve 502 esporádico; reenviar uma escrita às cegas pode duplicar dados se a operação não for idempotente.
Se algum objetivo não gerar requisito, explique por quê. Ao terminar, liste perguntas abertas e pare.

## P04: Plano e Arquitetura

- Data e hora: 2026-10-31, [hora do envio da correção] (horário de Brasília, UTC-03:00)
- Quem enviou: CaioBarthasar23
- Agente e modelo usados: GitHub Copilot Chat (modo Agent) no Codespaces; modelo: GPT-6 Luna
- Arquivos alterados: specs/plan.md
- Resultado da revisão ("Revise antes de seguir"): refeito. Primeira versão reprovada nas perguntas 1, 2 e 5 do quadro: restos do modelo (blocos de exemplo, tabela vazia, cabeçalho duplicado), rótulos ambíguos no nível 2 e ADR-003 a ADR-008 numerados além do previsto; origem do fato do 502 também corrigida (Prompt 3, não Prompt 4). Segunda versão aceita após uma rodada de correção pelo agente.

[C] Personagem
Você é um arquiteto de software de dados. Você transforma a spec em arquitetura, justificando cada escolha por um requisito ou restrição. Você não escreve código nesta etapa.

[R] Pedido
Escreva specs/plan.md com:
1. C4 nível 1 (contexto), nível 2 (contêineres) e nível 3 (componentes do script de verificação), em blocos Mermaid;
2. tabela de escolhas técnicas: escolha, alternativas consideradas, requisito ou restrição, ADR previsto;
3. ambientes local (docker compose no Codespace) e publicado (Railway), lado a lado;
4. riscos técnicos iniciais e perguntas abertas.
O plano deve conter estas decisões, já tomadas pelo grupo:
- Dockerfile em minio_railway/ com FROM ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z e CMD server /data --console-address ":9001";
- volume do Railway montado em /data;
- domínio público do Railway apenas para a porta 9000; console 9001 só no ambiente local;
- credenciais como variáveis do serviço no Railway e no .env local, nunca em arquivo versionado;
- docker-compose.yml com a mesma imagem e tag, portas 9000 e 9001, volume nomeado e healthcheck com "mc ready local" (a imagem não tem curl nem wget);
- cliente mc para operar e verificar; scripts em scripts/ carregam o .env sem imprimir valores.

[E] Exemplos
flowchart LR
  subgraph rw["Railway: projeto minio-grupo-xx"]
    dom["Domínio público HTTPS"]
    svc["Serviço minio"]
    vol[("Volume em /data")]
  end
  dom -->|"porta 9000"| svc
  svc --- vol

| Escolha | Alternativas | Requisito/restrição | ADR |
| Imagem coolLabs com tag fixada | imagem minio/minio antiga; latest da coolLabs; compilar do código-fonte | RNF-xx (imagem fixada), RES-02 | ADR-001 |

[A] Ajustes
- Os nomes usados nos diagramas são exatamente os nomes usados no texto.
- Toda escolha técnica aponta para RF, RNF ou RES; escolha sem origem fica marcada "sem requisito correspondente".
- Para cada decisão relevante, liste pelo menos duas alternativas descartadas e o motivo.
- Não acrescente componentes que a spec não pede (proxy reverso, orquestrador, banco de dados).

[T] Tipo de saída
Somente specs/plan.md, em Markdown com blocos ```mermaid. Mostre a lista de seções antes de escrever e espere confirmação.

[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md, specs/plan.md.
Os ADRs serão escritos na etapa 7; aqui apenas indique o número previsto (ADR-001 para a imagem, ADR-002 para a exposição de portas).
Se uma decisão acima contradisser a spec, aponte a contradição e pergunte. Pare ao final.

## P05: Tarefas

- Data e hora: 2026-10-31, 20:22 (horário de Brasília, UTC-03:00)
- Quem enviou: CaioBarthasar23
- Agente e modelo usados: GitHub Copilot Chat (modo Agent) no Codespaces; modelo: GPT-6 Luna
- Arquivos alterados: specs/tasks.md
- Resultado da revisão ("Revise antes de seguir"): refeito. A primeira versão cobria todos os RF e RNF e separava as tarefas manuais, mas o T-06 dependia do T-04 e o T-04 do T-06 (ciclo), o T-07 não trazia comandos executáveis e o T-09 estava fora da seção de manuais. O agente também propôs `railway up` no T-07, rejeitado porque o redeploy é manual no painel. Segunda versão aceita após correção pelo agente. Antes da escrita, foram pedidos três ajustes: tarefa de acompanhamento de custo (RNF-01), T-04 sem retry e T-08 com falha simulada.

[C] Personagem
Você é o líder técnico do grupo. Você quebra o plano em tarefas pequenas, cada uma com requisito, verificação executável e evidência esperada.

[R] Pedido
Escreva specs/tasks.md a partir de specs/spec.md e specs/plan.md. Inclua no mínimo:
T-01 docker-compose.yml do MinIO local;
T-02 minio_railway/Dockerfile;
T-03 scripts/criar_buckets.sh (local e railway, idempotente);
T-04 scripts/verificar.sh (local e railway: saúde, 403 anônimo, buckets, ida e volta de objeto, saída salva em docs/evidencias/);
T-05 README.md da pasta com recriação do zero;
T-06 deploy no Railway (executado pelo prompt 8);
T-07 teste de persistência com redeploy.
Separe as tarefas manuais do grupo (login no Railway, geração e cadastro da senha, cópia do domínio para o .env).

[E] Exemplos
| T-03 | Criar scripts/criar_buckets.sh que cria raw, bronze, silver e gold com mc mb --ignore-existing | RF-02 | bash scripts/criar_buckets.sh local, executado duas vezes | segunda execução termina com código 0; mc ls local lista 4 buckets | [ ] |

[A] Ajustes
- Cada tarefa cabe num único prompt de implementação e toca poucos arquivos.
- Cada RF e RNF é coberto por pelo menos uma tarefa, ou aparece em "sem tarefa" com o motivo.
- Marque as tarefas que criam recursos no Railway ou consomem crédito.
- Indique a ordem de execução e as dependências.
- Todas as tarefas começam com status [ ].

[T] Tipo de saída
Somente specs/tasks.md, em Markdown, com a tabela do modelo. Mostre a lista de tarefas antes de escrever e espere confirmação.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md.
Os scripts devem funcionar com o mc instalado no Codespace e ler as variáveis MINIO_ROOT_USER, MINIO_ROOT_PASSWORD (local) e MINIO_RAILWAY_ENDPOINT, MINIO_RAILWAY_USER, MINIO_RAILWAY_PASSWORD (Railway) do .env, conforme .env.example.
Pare ao final.

## P06: Implementação, uma tarefa por vez

- Data e hora: 2026-10-31, 20:40 (horário de Brasília, UTC-03:00)
- Quem enviou: CaioBarthasar23
- Agente e modelo usados: GitHub Copilot Chat (modo Agent) no Codespaces; modelo: GPT-6 Luna
- Arquivos alterados: docker-compose.yml, docs/evidencias/T-01_compose.txt, specs/tasks.md (apenas o status da T-01)
- Resultado da revisão ("Revise antes de seguir"): refeito. A primeira versão passou na verificação (healthy), mas o healthcheck usava `mc alias set` com credenciais e faltavam `name: minio_local` e os parâmetros de intervalo; correção pedida com base no gabarito. Segunda versão aceita: `mc ready local` sem alias chegou a healthy; contêiner antigo removido sem `-v`; volume minio_data preservado. Diferenças restantes do gabarito: comentários, ausência de `restart: unless-stopped` e `name: minio_data` fixo no volume.

[C] Personagem
Você é um engenheiro de dados que implementa com disciplina de testes. Você executa uma única tarefa, prova que ela funciona com a saída real do terminal e para.

[R] Pedido
Implemente a tarefa T-01 de specs/tasks.md. Siga esta ordem:
1. mostre o plano: arquivos que vai criar ou alterar e o comando de verificação;
2. espere minha confirmação;
3. crie ou altere os arquivos;
4. execute a verificação indicada na tarefa e mostre a saída real;
5. se passou, salve a saída em docs/evidencias/T-xx_<nome>.txt, marque a tarefa como [x] em specs/tasks.md e proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].

[E] Exemplos
Evidência bem registrada (docs/evidencias/T-01_compose.txt):
$ docker compose ps
NAME                  IMAGE                                                   STATUS
minio_local-minio-1   ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z   Up 20 seconds (healthy)
$ curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9000/minio/health/live
200
Mensagem de commit: feat(T-01): MinIO local com healthcheck e volume nomeado [RF-03]

[A] Ajustes
- Faça somente a tarefa pedida. Não adiante outras tarefas.
- Use a imagem ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z; nunca latest.
- Scripts em bash começam com set -euo pipefail, carregam o .env com "set -a; . ./.env; set +a" e nunca imprimem senha (não use set -x, não ecoe variáveis de credencial).
- Não leia nem imprima o arquivo .env. Use docker compose config --quiet, que não mostra valores.
- Operações repetíveis devem ser idempotentes (mc mb --ignore-existing; objeto de verificação com chave fixa raw/_verificacao/teste.json).
- No compose: portas 9000 e 9001, volume nomeado minio_data, healthcheck com mc ready local, variáveis com ${MINIO_ROOT_USER:?} e ${MINIO_ROOT_PASSWORD:?}.
- Não execute docker compose down -v nem apague buckets.
- Se a verificação falhar, mostre o erro e tente corrigir no máximo duas vezes; depois disso, pare e explique.
- Não declare sucesso sem mostrar a saída do comando.

[T] Tipo de saída
Os arquivos da tarefa, a atualização de specs/tasks.md, o arquivo de evidência e um resumo de até cinco linhas com o que mudou e a mensagem de commit proposta.

[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md e .env.example (só os nomes das variáveis).
O .env local já foi criado pelo grupo a partir do .env.example. O cliente mc está instalado no Codespace (mc --version).
Pare ao final da tarefa.

