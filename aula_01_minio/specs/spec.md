# Especificação

> Etapa 3 do SDD. Preenchido pelo prompt 3 a partir da persona e dos objetivos.
> A spec diz O QUE o sistema faz e com qual qualidade. Não escolha tecnologia aqui,
> exceto quando uma restrição de `docs/01_objetivos_negocio.md` já a impuser.

## Contexto e escopo
O storage do grupo será usado nas Aulas 02, 03 e 04 e no projeto final para manter e
reaproveitar dados coletados. Os requisitos cobrem os ambientes local e publicado,
verificações, persistência, segurança, custo e recriação. Docker Compose é incluído
por autorização explícita do pedido do Prompt 3, embora ainda não conste como restrição
em `docs/01_objetivos_negocio.md`.

## Requisitos funcionais

### RF-01: API S3 publicada por HTTPS no domínio do Railway

O serviço publicado oferece a API compatível com S3 por HTTPS no domínio do Railway.

- Origem: RES-01, RES-04; pedido do Prompt 3.
- Critério de aceite:
  - Dado o serviço publicado e credenciais válidas fornecidas fora do repositório
  - Quando um teste automatizado fizer uma operação pela API S3 usando HTTPS no domínio do Railway
  - Então a operação será concluída com sucesso e a resposta virá pelo endpoint HTTPS esperado

### RF-02: buckets da arquitetura medalhão

O storage oferece os buckets `raw`, `bronze`, `silver` e `gold`.

- Origem: OBJ-04; pedido do Prompt 3.
- Critério de aceite:
  - Dado o serviço no ar e credenciais válidas fornecidas fora do repositório
  - Quando a etapa documentada de criação de buckets for executada duas vezes seguidas
  - Então as duas execuções terminarão com sucesso e a listagem conterá exatamente os quatro buckets definidos

### RF-03: ambiente local equivalente ao publicado

O ambiente local é executado por Docker Compose e usa a mesma imagem MinIO e a mesma tag fixada do ambiente publicado.

- Origem: RES-04; pedido do Prompt 3 (autorização para Docker Compose).
- Critério de aceite:
  - Dado os arquivos de configuração dos ambientes local e publicado
  - Quando um teste automatizado comparar a imagem e a tag configuradas
  - Então ambos usarão `ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z`

### RF-04: verificação automatizada nos dois ambientes

Uma verificação automatizada valida saúde, acesso anônimo, buckets e gravação e leitura de um objeto de teste no ambiente local e no Railway.

- Origem: OBJ-03, OBJ-04; pedido do Prompt 3.
- Critério de aceite:
  - Dado cada ambiente inicializado e credenciais válidas disponíveis fora do repositório
  - Quando a verificação automatizada for executada contra o ambiente local e, separadamente, contra o Railway
  - Então ambos passarão na verificação de saúde, negarão acesso anônimo, listarão exatamente os quatro buckets e devolverão na leitura o mesmo conteúdo gravado no objeto de teste

### RF-05: recriação documentada do zero

Os comandos necessários para recriar o storage do zero são documentados e executáveis por qualquer integrante.

- Origem: OBJ-04, DRV-04.
- Critério de aceite:
  - Dado um ambiente vazio e credenciais fornecidas fora do repositório
  - Quando um integrante seguir os comandos documentados para recriar o storage
  - Então o ambiente ficará pronto e passará pela verificação definida em RF-04; a evidência será registrada em `docs/evidencias/`

### RF-06: persistência entre deploys

Os objetos gravados permanecem disponíveis após deploys e reinícios do serviço publicado.

- Origem: OBJ-02, DRV-02, RES-03.
- Critério de aceite:
  - Dado um objeto de verificação gravado antes de um deploy ou reinício
  - Quando a operação terminar e a verificação de leitura for executada novamente
  - Então o objeto e seu conteúdo continuarão disponíveis, sem objetos perdidos

### RF-07: acesso autenticado e segredos fora do Git

O acesso aos dados exige autenticação e nenhum segredo é incluído no conteúdo versionado do repositório público.

- Origem: OBJ-03, DRV-03, RES-05.
- Critério de aceite:
  - Dado o endpoint publicado e o repositório versionado
  - Quando um teste acessar a API sem credenciais e uma verificação inspecionar os arquivos versionados
  - Então o acesso anônimo será negado e nenhum segredo será encontrado nos arquivos versionados

## Requisitos não funcionais (atributos de qualidade)

### RNF-01: custo acompanhado dentro do crédito do trial

- Atributo: custo
- Origem: OBJ-01, RES-01.
- Critério de aceite mensurável:
  - Dado o projeto durante o trial do Railway
  - Quando o consumo acumulado do crédito for verificado no registro de uso da plataforma
  - Então o consumo não ultrapassará US$ 5; a verificação será registrada como evidência

### RNF-02: imagem fixada por tag, sem `latest`

- Atributo: reprodutibilidade e controle de mudança
- Origem: RES-04; pedido do Prompt 3.
- Critério de aceite mensurável:
  - Dado os arquivos versionados de configuração dos ambientes local e publicado
  - Quando uma verificação automatizada inspecionar as referências de imagem
  - Então ambos usarão a tag `RELEASE.2025-10-15T17-29-55Z` e nenhuma referência usará `latest`

### RNF-03: tolerância a 502 e idempotência

- Atributo: disponibilidade e idempotência
- Origem: DRV-02; fato adicional do enunciado do Prompt 3 sobre o proxy do Railway.
- Critério de aceite mensurável:
  - Dado que o proxy devolva 502 durante uma gravação, inclusive quando o resultado da primeira tentativa for desconhecido
  - Quando o cliente repetir a gravação da mesma chave com espera crescente
  - Então a chave esperada conterá um único objeto com o conteúdo esperado; o número máximo de tentativas é hipótese: validação pendente, a medir por testes com respostas 502 repetidas e registro das tentativas necessárias para concluir sem duplicação

### RNF-04: evidências de verificação rastreáveis

- Atributo: rastreabilidade
- Origem: DRV-04; gate de qualidade do `AGENTS.md`; pedido do Prompt 3.
- Critério de aceite mensurável:
  - Dado que uma verificação de requisito tenha sido executada em qualquer ambiente
  - Quando o resultado for registrado
  - Então a evidência correspondente estará em `docs/evidencias/`, identificará ambiente e verificação e não conterá segredos

## Fora do escopo
- Alta disponibilidade com múltiplos nós.
- Console web público.
- Backup automático agendado.

## Perguntas abertas
- A restrição de uso de Docker Compose no ambiente local ainda não consta em `docs/01_objetivos_negocio.md`; foi incluída nesta spec por autorização do pedido do Prompt 3, sem alterar aquele arquivo.
- A meta de custo cobre somente o trial de até 30 dias ou também os meses restantes do semestre no plano Free? Origem: lacuna registrada em `docs/01_objetivos_negocio.md`.
- Qual evidência o grupo aceitará para confirmar a recriação bem-sucedida por cada integrante? Origem: lacuna registrada em `docs/01_objetivos_negocio.md`.
- Qual será o número máximo de tentativas para lidar com respostas 502? hipótese: validação pendente; medir com testes de falhas repetidas e registrar a quantidade de tentativas necessárias.
