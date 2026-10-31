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

git add specs/spec.md docs/prompts.md
git commit -m "docs(T-00): spec do projeto aula_01_minio"
git push
git status --short