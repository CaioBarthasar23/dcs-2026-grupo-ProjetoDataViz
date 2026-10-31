# 01. Objetivos de negócio

> Etapa 2 do SDD. Preenchido pelo prompt 2 a partir de `docs/00_persona.md`.
> Objetivo de negócio descreve resultado para a persona, não tecnologia.

## Objetivos

| ID | Objetivo | Métrica de sucesso | Origem |
|---|---|---|---|
| OBJ-01 | Manter o custo dentro do crédito do trial do Railway. | Uso total do crédito no trial menor ou igual a US$ 5; verificar o consumo apresentado pela plataforma durante o trial. | Enunciado da Aula 01: crédito único de US$ 5 no trial. |
| OBJ-02 | Manter os dados disponíveis entre deploys e reinícios do serviço. | Após deploy ou reinício, todos os objetos gravados antes da operação continuam disponíveis; zero objetos perdidos. Comparar a listagem e o conteúdo antes e depois de cada operação. | Persona: dor atual de os dados coletados sumirem; objetivo definido no pedido. |
| OBJ-03 | Permitir acesso somente autenticado e não versionar segredos no repositório público. | Nenhum acesso sem autenticação é bem-sucedido e nenhum segredo é encontrado nos arquivos versionados. Verificar com tentativas sem autenticação e revisão do conteúdo versionado. | Enunciado da Aula 01: repositório público no GitHub e nenhuma chave de API em arquivo versionado. |
| OBJ-04 | Permitir que qualquer integrante recrie o storage do zero por comandos documentados. | Cada integrante consegue concluir a recriação a partir do zero usando somente os comandos documentados; hipótese: validação pendente quanto à evidência de conclusão. Medir pela execução acompanhada do procedimento por cada integrante e registrar o resultado. | Enunciado da Aula 01: uso pelo grupo nas Aulas 02, 03 e 04 e no projeto final; objetivo definido no pedido. |

## Drivers de negócio

Forças que pressionam a arquitetura (prazo, custo, regulação, equipe, risco).

| ID | Driver | Atributo de qualidade afetado |
|---|---|---|
| DRV-01 | O grupo precisa manter o custo dentro do crédito limitado do trial e considerar o plano após seu término. | Custo |
| DRV-02 | A coleta deve continuar disponível entre deploys e reinícios, para permitir seu reaproveitamento nas aulas seguintes e no projeto final. | Persistência e disponibilidade |
| DRV-03 | O repositório é público, então credenciais não podem ser expostas em arquivos versionados e o acesso deve exigir autenticação. | Segurança |
| DRV-04 | Integrantes diferentes precisam conseguir recriar o storage e reaproveitar dados coletados por colegas. | Reprodutibilidade e operação pelo grupo |

## Restrições

| ID | Restrição | Tipo (técnica, financeira, legal, prazo) | Origem |
|---|---|---|---|
| RES-01 | O trial tem crédito único de US$ 5 por até 30 dias; depois, o plano Free custa US$ 1 por mês. | financeira | Enunciado da Aula 01 (Extras). |
| RES-02 | O projeto dispõe de 1 GB de RAM, vCPU compartilhada e até 5 serviços por projeto. | técnica | Enunciado da Aula 01 (Extras). |
| RES-03 | Volumes de contas trial são apagados 30 dias após o fim dos créditos. | prazo | Enunciado da Aula 01 (Extras). |
| RES-04 | A imagem indicada é `ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z`; a porta 9000 corresponde à API S3 e a 9001 ao console. | técnica | Enunciado da Aula 01 (Extras). |
| RES-05 | O repositório do grupo é público; não se pode incluir chave de API em arquivo versionado. Cada integrante escolhe seu agente de código. | técnica | Enunciado da Aula 01 (Extras). |

## Fora do escopo
- Alta disponibilidade com múltiplos nós.
- Console web público.
- Backup automático agendado.

## Fatos, lacunas e suposições
- Fato: a persona precisa reaproveitar coletas de colegas nas Aulas 03 e 04 e no projeto final. Origem: `docs/00_persona.md`.
- Fato: a gravação da coleta da Aula 02 será horária e armazenará JSON bruto. Origem: enunciado da Aula 01 (Extras).
- Fato: o trial oferece crédito único de US$ 5 por até 30 dias, seguido pelo plano Free de US$ 1 por mês. Origem: enunciado da Aula 01 (Extras).
- Fato: volumes de contas trial são apagados 30 dias após o fim dos créditos. Origem: enunciado da Aula 01 (Extras).
- Lacuna: não está definido se a meta de custo considera somente o crédito do trial ou também os meses restantes do semestre no plano Free. Origem: enunciado da Aula 01 (Extras), que informa ambos os períodos, e OBJ-01 do pedido.
- Lacuna: a forma de evidenciar que cada integrante consegue recriar o storage ainda precisa ser validada. hipótese: validação pendente. Medir acompanhando a execução por cada integrante e registrando se concluiu usando os comandos documentados.

## Perguntas abertas
- A meta de custo deve cobrir apenas o trial de até 30 dias ou também os meses restantes do semestre no plano Free?
- Qual evidência o grupo aceitará para registrar a recriação bem-sucedida por cada integrante?
