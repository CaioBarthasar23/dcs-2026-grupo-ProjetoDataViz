# Registro de prompts

## Revisão dos critérios de aceite e dos testes

> [R] Pedido: revisar se há um cenário por critério, se os testes falham
> pelo motivo correto e se algum teste depende da ordem; corrigir os
> problemas encontrados nos cenários, fixtures e testes.
>
> [A] Ajustes: preservar `src/` como stubs `NotImplementedError`, não
> acessar fontes externas, medir espera de retry, cobrir PTAX sem
> fechamento elegível e HTTP 500, timeout e duração total, e usar MinIO
> real somente com ativação explícita e bucket `teste`.

## Testes de aceitação antes da implementação

> [C] Personagem: engenheiro de testes que deriva testes de critérios Dado,
> Quando e Então antes da implementação.
>
> [R] Pedido: criar features Gherkin por módulo (coleta, gravação,
> extração, execução), com tags RF/RNF por cenário; criar um teste pytest
> por cenário, função em snake_case e comentário de rastreabilidade.
>
> [A] Ajustes: nenhum teste acessa rede; usar fixtures e função `get`
> injetada; testes de gravação têm marca `minio` e bucket `teste`; em
> `src/`, somente assinaturas/stubs com `NotImplementedError`.
>
> [T] Saída: `features/`, `tests/` e resultado de `pytest -q`, mostrando
> falhas causadas pela implementação ausente.
>
> [E] Extras: ler `specs/` e `docs/modelagem/`, registrar prompt e parar.

## Plano de implementação e tarefas

> [C] Personagem: líder técnico que decompõe a arquitetura em tarefas de
> até 30 minutos.
>
> [R] Pedido: criar `specs/plan.md` com bibliotecas e RNFs justificadores,
> estrutura de `src/` e `tests/`, comandos local/Railway. Criar
> `specs/tasks.md` com tarefas T-01... em ordem nas Etapas 12 a 15:
> configuração/HTTP, gravador/manifesto, coletores, extrator/CLI. Cada
> tarefa inclui objetivo, arquivos, RF/RNF, ADR, teste nomeado e objetivo,
> comando e dependências.
>
> [A] Ajustes: usar `requests`, `beautifulsoup4`, `boto3`,
> `python-dotenv` e `pytest`; outra dependência requer RNF justificadora.
> Testes de parser e HTTP não usam rede; integração de gravação usa MinIO
> local, bucket `teste`.
>
> [T] Saída: `specs/plan.md` e `specs/tasks.md`, com matriz final
> requisito | tarefas e nenhuma linha vazia.
>
> [E] Extras: ler `docs/` e `specs/`, registrar este prompt e parar.

## Arquitetura e ADRs de qualidade

> [C] Personagem: arquiteto responsável pelas decisões, registrando cada
> tática de qualidade em um ADR com alternativas e consequências.
>
> [R] Pedido: criar `docs/arquitetura.md` com drivers DN/RNF, pipeline em
> lotes, implantação Codespace/MinIO local/Railway, mapa
> tática-qualidade-RNF, trade-offs e riscos. Criar ADRs para separação
> coleta/extração, chaves determinísticas, retry com backoff/full jitter/
> Retry-After, coleta sequencial, bytes brutos, manifesto por execução e
> janela PTAX.
>
> [A] Ajustes: cada ADR cita RNF e RF de origem e diagramas da Etapa 08;
> todos têm status `Proposta`, sem status `Aceita`.
>
> [T] Saída: `arquitetura.md` e sete ADRs com contexto, decisão,
> alternativas, consequências e links.
>
> [E] Extras: ler `docs/` e `specs/`, registrar o prompt e parar.

## Fluxos dinâmicos e estados do manifesto

> [C] Personagem: arquiteto de software de dados que descreve como os
> componentes conversam no tempo, incluindo falhas.
>
> [R] Pedido: criar um arquivo Markdown por fluxo com sequenceDiagram
> Mermaid para coleta PTAX por janela, coleta de categoria com paginação
> e detalhes, gravação raw com 502 do proxy Railway e retry na mesma
> chave, extração MinIO para JSON Lines e reexecução no mesmo dia. Criar
> `estados_item.md` com stateDiagram-v2 para pendente, baixando,
> aguardando, baixado, gravado e falhou, indicando o evento das
> transições.
>
> [A] Ajustes: participantes seguem os nomes de `classes.md`; todos os
> diagramas têm caminho de erro explícito com `alt`/`else`; não usar ponto
> e vírgula nas mensagens.
>
> [T] Saída: cinco arquivos de fluxo e `estados_item.md`, com matriz
> final fluxo | RF | RNF.
>
> [E] Extras: ler `specs/` e `docs/modelagem/estatica/`, validar sintaxe
> Mermaid, registrar este prompt e parar.

> Revisão posterior: tornar explícito o estado terminal `falhou` por item
> no contrato do manifesto e no DBML, incluindo persistência do estado e
> da causa do erro quando um retry ou gravação falha definitivamente.

## Arquitetura de componentes e classes

> [C] Personagem: arquiteto de software de dados que desenha a estrutura
> antes da implementação.
>
> [R] Pedido: criar `docs/componentes.md` com diagrama Mermaid flowchart,
> responsabilidades, interfaces públicas e rastreabilidade RF/RNF de
> fontes, configuração, cliente HTTP, coletores, gravador S3, manifesto,
> extrator e destinos MinIO local/Railway. Criar `docs/classes.md` com
> diagrama Mermaid classDiagram para Config, ClienteHttp, Resposta,
> ColetorBooks, ColetorPtax, GravadorS3, Manifesto, ItemManifesto,
> Extrator, Livro e Cotacao, incluindo atributos tipados, assinaturas e
> dependências.
>
> [A] Ajustes: coletores recebem GravadorS3 e não conhecem MinIO; Extrator
> lê apenas do MinIO e não importa requests; nomes do diagrama serão os
> nomes previstos para `src/`; não usar ponto e vírgula nos rótulos Mermaid.
>
> [T] Saída: dois arquivos Markdown com Mermaid e tabela componente | RF |
> RNF.
>
> [E] Extras: ler `specs/`, registrar este prompt e parar. Nenhuma
> implementação de código nesta etapa.

## Personas do monitor diário de preços

> [C] Personagem: analista de produto de dados da Aula 03, em etapa de
> descrição de pessoas e seguindo Spec-Driven Development.
>
> [R] Pedido: criar `docs/00_persona.md` para monitor diário de preços de
> livros. A coleta usa scraping em `https://books.toscrape.com` para preços em
> libras, a API PTAX do Banco Central para GBP/BRL, grava bytes brutos no
> MinIO (`raw`) e registros extraídos em JSON Lines (`bronze`). A conversão
> para reais ocorre na Aula 04. Descrever papel, decisão, pergunta típica,
> frequência, dor atual, consequência de dado errado ou atrasado e nível
> técnico.
>
> [A] Ajustes: três personas — P1 consumidor do negócio, P2 operador do
> pipeline acionado em falhas, P3 engenheiro de dados da Aula 04 que lê o
> bronze. Declarar no topo que o domínio é didático, pois o site avisa que
> preços e avaliações são aleatórios. Valores sem origem devem ser marcados
> como "hipótese — validação pendente". Apenas o arquivo solicitado, sem
> código.
>
> [T] Saída: Markdown com até 80 linhas, uma seção por persona e tabela
> "Fato | Lacuna | Suposição".
>
> [E] Extras: ler `AGENTS.md`, mostrar o plano e aguardar confirmação antes
> de escrever; registrar o prompt aqui e parar.

## Direcionadores e objetivos de negócio

> [C] Personagem: gerente de produto de dados que transforma dores de persona
> em direcionadores de negócio e objetivos mensuráveis.
>
> [R] Pedido: criar `docs/01_objetivos_negocio.md` com direcionadores
> DN-01... (força, personas afetadas P1/P2/P3, consequência de nada fazer),
> objetivos OBJ-01... vinculados a direcionadores (métrica, comando ou
> consulta para medir, meta ou “hipótese — validação pendente”), restrições
> com origem e itens fora de escopo.
>
> [A] Ajustes: restrições da disciplina: sem custo de API; Codespace com
> Docker; MinIO local e MinIO no Railway (trial, 1 GB RAM); scraping educado
> (User-Agent identificável, intervalo, sem paralelismo, consulta a
> robots.txt); nenhum segredo versionado. Fora de escopo: Parquet, DuckDB,
> silver/gold e conversão para reais (Aula 04), agendamento em produção,
> painéis e dado pessoal. 1.000 livros e 50 categorias são fatos de
> 03/10/2026, não constantes. Preservar P1, P2 e P3.
>
> [T] Saída: Markdown até 90 linhas, seções Direcionadores, Objetivos,
> Restrições (tabela restrição | origem), Fora de escopo e Hipóteses.
>
> [E] Extras: ler `AGENTS.md` e `docs/00_persona.md`; dor sem objetivo
> precisa de justificativa. Registrar o prompt e parar.

## Regras de negócio do monitor

> [C] Personagem: analista de negócio que transforma decisões e restrições
> em regras numeradas, sem falar de tecnologia.
>
> [R] Pedido: criar `docs/02_regras_de_negocio.md` com regras RN-01...; cada
> regra contém enunciado de uma frase, origem (DN, OBJ, P ou restrição),
> exemplo concreto e contraexemplo.
>
> [A] Ajustes: cobrir identidade do livro pelo UPC da página de detalhe;
> cotação GBP/BRL pelo último boletim “Fechamento” com data menor ou igual
> à referência, mostrando a data da cotação; data de coleta em
> America/Sao_Paulo; coleta educada (robots.txt, User-Agent, intervalo,
> sequencial); preservação do bruto antes de interpretar e sem alteração;
> reexecução no mesmo dia substitui sem duplicar; divergência entre
> quantidade extraída e declarada resulta em falha registrada. Sem nomes de
> biblioteca, bucket ou função. Regras atômicas e preservar IDs anteriores.
>
> [T] Saída: Markdown com regras e tabela final RN | origem.
>
> [E] Extras: ler `docs/`, perguntar se houver conflito entre regras,
> registrar este prompt e parar.

## Requisitos funcionais do monitor

> [C] Personagem: engenheiro de dados responsável pela especificação, que
> escreve requisitos testáveis sem escolher bibliotecas.
>
> [R] Pedido: criar `specs/01_requisitos_funcionais.md` com RF-01...; cada
> requisito tem descrição, origem RN/OBJ/P e ao menos um critério
> Dado/Quando/Então. Cobrir descoberta de categorias, paginação por próxima
> página, detalhe de cada livro (UPC e estoque), filtro
> `SCRAPER_CATEGORIAS`, HTML bruto com chave determinística e metadados de
> origem, consulta/registro de robots.txt, consulta PTAX GBP em janela e
> gravação JSON bruta, janela sem fechamento, manifesto por execução,
> extração somente do MinIO para `livros.jsonl` e `cotacoes.jsonl`, e
> reexecução sem duplicação.
>
> [A] Ajustes: apenas funcional; desempenho e segurança ficam para a Etapa
> 05. Não fixar total de livros ou páginas; comparar com totais declarados.
> Terminar com matriz RN → RF, cobrindo toda RN.
>
> [T] Saída: Markdown com contexto em cinco linhas, requisitos agrupados em
> descoberta, coleta, gravação, extração e execução, e matriz de rastreabilidade.
>
> [E] Extras: ler `docs/`, apresentar o índice antes da redação completa,
> confirmar os fatos fornecidos antes de usá-los, registrar este prompt e parar.
>
> **Fatos fornecidos para confirmação:** em 03/10 e 16/10/2026, Books to
> Scrape teria 50 categorias, 1.000 livros e 20 por página; cartões
> `article.product_pod`; título em `h3 > a[title]`; preço em
> `p.price_color`; próxima página em `li.next > a`; robots.txt 404; detalhe
> com UPC em `table.table-striped`, estoque em
> `div.product_main p.availability` e categoria no terceiro link de
> `ul.breadcrumb`; Content-Type sem charset. A PTAX usa
> `CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)`,
> datas `MM-DD-AAAA` e `$format=json`; sábado e data ISO respondem 200 sem
> valores, `DD-MM-AAAA` responde 500 e o boletim final é “Fechamento”.
> **Verificação ao elaborar:** consulta atual confirmou 50 links de categoria,
> 1.000 resultados declarados, 20 itens na página inicial, detalhe com UPC,
> disponibilidade e categoria no breadcrumb, `robots.txt` 404 e cabeçalho
> HTTP `Content-Type: text/html` sem charset. A API consultada para 23/10/2026
> retornou boletins até “Fechamento”; 24/10 e data ISO retornaram 200 vazios,
> enquanto `DD-MM-AAAA` retornou 500. Os valores observados agora não provam
> independentemente o estado histórico em 03/10 e 16/10.
>
> **Decisões após revisão do índice:** preservar brutos por execução e
> substituir os JSON Lines diários na reexecução; janela PTAX sem fechamento
> resulta em cotação indisponível e execução incompleta; categoria ausente ou
> vazia em `SCRAPER_CATEGORIAS` significa todas as categorias descobertas.
> Para resolver o conflito entre filtragem e contagem geral, RN-10 mantém seu
> ID e compara o total declarado do escopo selecionado: total da página
> inicial na coleta completa e soma dos totais das categorias filtradas.

## Modelo de dados do monitor

> [C] Personagem: modelador de dados responsável por definir chaves,
> contratos de arquivo e manifesto do monitor.
>
> [R] Pedido: criar `specs/03_modelo_de_dados.md` e `specs/modelo.dbml`.
> Documentar layouts de chaves `raw`/`bronze`, dicionários de
> `livros.jsonl` e `cotacoes.jsonl`, manifesto (cabeçalho e itens),
> metadados `x-amz-meta-*` ASCII e entidades DBML `execucao`,
> `item_manifesto`, `objeto_raw`, `livro` e `cotacao`, com relações lógicas.
>
> [A] Ajustes: preservar nomes dos campos fornecidos como contrato com as
> Aulas 04/05; não incluir silver, Parquet ou conversão para reais. Chaves
> brutas derivam de fonte, data, recurso e SHA-256, sem ID de execução; ID
> de execução aparece somente na chave do manifesto. `avaliacao` preserva
> o rótulo original `One` a `Five`. Revisão posterior confirmou contratos
> JSONL estritos: nove campos em `livros.jsonl` e cinco em `cotacoes.jsonl`,
> sem `data_ref`; a data fica no manifesto e nas chaves dos objetos.
>
> [T] Saída: Markdown com tabelas e DBML importável no dbdiagram.io.
>
> [E] Extras: ler `docs/` e `specs/`; registrar o prompt e parar.

## Requisitos não funcionais do monitor

> [C] Personagem: engenheiro de confiabilidade de dados que escreve
> requisitos de qualidade mensuráveis e ligados aos RFs.
>
> [R] Pedido: criar `specs/02_requisitos_nao_funcionais.md` com RNF-01...,
> organizados pelos oito eixos da ISO/IEC 25010: adequação funcional,
> eficiência de desempenho, compatibilidade, usabilidade, confiabilidade,
> segurança, manutenibilidade e portabilidade. Cada RNF inclui critério de
> aceite numérico, forma de medir, RFs relacionados, personas e componente
> provável. Se um eixo não tiver requisito pertinente, explicar.
>
> [A] Ajustes: cobrir timeout explícito; retry apenas transitório com
> backoff exponencial, full jitter, Retry-After e limite; intervalo mínimo
> entre requisições, zero paralelismo e duração da coleta; reexecução sem
> duplicar; metadados ASCII; segredos fora do Git; extração testável sem
> rede; mesmo código para MinIO local e Railway alterando só `.env`.
> Números sem origem são “hipótese — validação pendente”.
>
> [T] Saída: Markdown com premissas, uma seção por eixo e matriz RF → RNF.
>
> [E] Extras: ler `docs/` e `specs/01_requisitos_funcionais.md`; usar as
> medidas de 16/10/2026 apenas como linha de base, não como metas; registrar
> o prompt e parar.

## Implementação T-01 a T-04 · Configuração e cliente HTTP

> [C] Personagem: engenheiro de dados Python. Implementa as tarefas indicadas de
> `specs/tasks.md`, uma por vez, com os testes da Etapa 11 como contrato.
>
> [R] Pedido: implementar T-01 a T-04 (Etapa 12 · Configuração e cliente HTTP).
> Para cada tarefa, mostrar o plano, rodar seu teste (vermelho), implementar o
> mínimo, rodar `pytest -q` (verde), marcar a tarefa em `specs/tasks.md` com o
> comando de verificação e só então avançar.
>
> [E] Exemplos: `T-02 · verde · pytest tests/test_http.py -q · 4 passed · src/http.py`.
>
> [A] Ajustes: não alterar testes; parar e explicar se um teste estiver errado.
> Configuração somente pelo `.env` com `python-dotenv`; nenhum segredo em código,
> teste, log, manifesto ou metadado. Toda requisição com timeout; retry somente
> para falhas transitórias, com limite. Enviar bytes ao parser e ao MinIO.
> Seguir os nomes de `docs/modelagem/estatica/classes.md`.
>
> [T] Saída: código em `src/`, saída do pytest e resumo de até dez linhas.
>
> [E] Extras: ler `AGENTS.md`, `specs/` e `docs/adr/`; usar somente comandos
> permitidos; registrar o prompt e parar ao fim das tarefas indicadas.

## Implementação T-05 a T-08 · Gravador e manifesto

> [C] Personagem: engenheiro de dados Python. Implementa as tarefas indicadas de
> `specs/tasks.md`, uma por vez, com os testes da Etapa 11 como contrato.
>
> [R] Pedido: implementar T-05 a T-08 (Etapa 13 · Gravador e manifesto). Para
> cada tarefa, mostrar o plano, executar o teste em vermelho, implementar o
> mínimo, executar `pytest -q` em verde, marcar a tarefa em `specs/tasks.md`
> com o comando de verificação e só então avançar.
>
> [E] Exemplos: `T-02 · verde · pytest tests/test_http.py -q · 4 passed · src/http.py`.
>
> [A] Ajustes: não alterar testes; parar e explicar se um teste estiver errado.
> Configuração somente pelo `.env` com `python-dotenv`; nenhum segredo em código,
> teste, log, manifesto ou metadado. Toda requisição com timeout; retry somente
> para falhas transitórias, com limite. Enviar bytes ao parser e ao MinIO.
> Seguir os nomes de `docs/modelagem/estatica/classes.md`.
>
> [T] Saída: código em `src/`, saída do pytest e resumo de até dez linhas.
>
> [E] Extras: ler `AGENTS.md`, `specs/` e `docs/adr/`; usar somente comandos
> permitidos; registrar o prompt e parar ao fim das tarefas indicadas.

## Implementação T-09 a T-14 · Coletores

> [C] Personagem: engenheiro de dados Python. Implementa as tarefas indicadas de
> `specs/tasks.md`, uma por vez, com os testes da Etapa 11 como contrato.
>
> [R] Pedido: implementar T-09 a T-14 (Etapa 14 · Coletores). Para cada tarefa,
> mostrar o plano, executar seu teste em vermelho, implementar o mínimo, executar
> `pytest -q` em verde, marcar a tarefa em `specs/tasks.md` com o comando de
> verificação e só então avançar.
>
> [E] Exemplos: `T-02 · verde · pytest tests/test_http.py -q · 4 passed · src/http.py`.
>
> [A] Ajustes: não alterar testes; parar e explicar se um teste estiver errado.
> Configuração somente pelo `.env` com `python-dotenv`; nenhum segredo em código,
> teste, log, manifesto ou metadado. Toda requisição com timeout; retry somente
> para falhas transitórias, com limite. Enviar bytes ao parser e ao MinIO.
> Seguir os nomes de `docs/modelagem/estatica/classes.md`.
>
> [T] Saída: código em `src/`, saída do pytest e resumo de até dez linhas.
>
> [E] Extras: ler `AGENTS.md`, `specs/` e `docs/adr/`; usar somente comandos
> permitidos; registrar o prompt e parar ao fim das tarefas indicadas.

## Implementação T-15 a T-20 · Extrator e linha de comando

> [C] Personagem: engenheiro de dados Python. Implementa as tarefas indicadas de
> `specs/tasks.md`, uma por vez, com os testes da Etapa 11 como contrato.
>
> [R] Pedido: implementar T-15 a T-20 (Etapa 15 · Extrator e linha de comando).
> Para cada tarefa, mostrar o plano, executar seu teste em vermelho, implementar
> o mínimo, executar `pytest -q` em verde, marcar a tarefa em `specs/tasks.md`
> com o comando de verificação e só então passar à próxima.
>
> [E] Exemplos: `T-02 · verde · pytest tests/test_http.py -q · 4 passed · src/http.py`.
>
> [A] Ajustes: não alterar testes para fazê-los passar; se o teste estiver errado,
> parar e explicar. Configuração somente pelo `.env` com `python-dotenv`; nenhum
> segredo em código, teste, log, manifesto ou metadado. Toda requisição com
> timeout; retry somente para transitórios e com limite. Bytes ao parser e ao
> MinIO. Seguir os nomes de `docs/modelagem/estatica/classes.md`.
>
> [T] Saída: código em `src/`, resultados do pytest e resumo de até dez linhas.
>
> [E] Extras: ler `AGENTS.md`, `specs/` e `docs/adr/`; usar comandos permitidos;
> registrar este prompt e parar ao fim das tarefas indicadas.

## Análise ATAM e matriz de rastreabilidade

> [C] Personagem: facilitador de ATAM; procurar riscos, sem elogiar a arquitetura.
>
> [R] Pedido: criar `docs/atam.md` com drivers DN-xx, utility tree com
> importância/dificuldade, cenários de qualidade nas seis partes, riscos,
> não riscos, pontos de sensibilidade e trade-offs. Cobrir mudança de HTML,
> PTAX sem cotação, 429/timeout, reexecução diária, configuração agressiva,
> custo de aproximadamente 1.000 detalhes e 502 do Railway. Criar
> `docs/rastreabilidade.md` com matriz P → DN → OBJ → RN → RF → RNF → ADR →
> tarefa → teste → evidência.
>
> [A] Ajustes: evidência não medida deve ser "evidência pendente"; não alterar
> código nem specs; registrar divergências como risco. Ler todos os arquivos
> de `docs/`, `specs/`, `src/` e `tests/`, além do último manifesto local.
> Executar `pytest --cov=src` e registrar o número medido sem arredondar.
>
> [T] Saída: dois arquivos Markdown com tabelas.
>
> [E] Extras: registrar este prompt, listar as três ações mais urgentes e parar.
