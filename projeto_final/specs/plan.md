# Plano de arquitetura — projeto final SSP

## Escopo e premissas

Este plano descreve a arquitetura pretendida para a coleção SSP (`groupId 23651`). Ele não declara componentes ou requisitos como implementados. A ordem dos ADRs preserva a decisão do `AGENTS.md`: ADR-001 fica reservado para registrar a origem do código já existente em `src/collector.py` e `src/silver.py`; as novas decisões começam em ADR-002.

Decisões já tomadas pelo aluno e refletidas aqui:

- Agendador no GitHub Actions, com execução diária às 18h30 de Brasília e tentativas de reserva. Quantidade, horários e condição das tentativas de reserva ainda precisam ser definidos.
- Coletor e transformação silver em Python, usando `requests`, `boto3`, Pydantic e Parquet.
- Gold em DuckDB, lendo arquivos Parquet do RustFS.
- Dashboard em Streamlit.
- Credenciais no `.env` local e em GitHub Secrets; nenhum segredo em arquivo versionado.
- Classificação carta/selado derivada dos dados da fonte. Code Card é classificado como carta e fica excluído das perguntas 1, 3 e 4 conforme a regra de raridade definida pelo aluno.
- Backfill da PTAX permitido por se tratar de registro público organizado por data; o bruto continua imutável e o backfill não sobrescreve objetos existentes.

Os elementos nomeados nos diagramas são: Colecionador, Projeto final SSP, Plataforma de dados SSP, Agendador GitHub Actions, Coletor, Processador silver, Gold DuckDB, Dashboard Streamlit, TCGCSV, API PTAX do Banco Central, SGS do Banco Central, RustFS da turma e Silver dos colegas. Os mesmos nomes são usados nas seções de arquitetura e fluxo abaixo.

A execução diária às 18h30 de Brasília ocorre após a atualização esperada do TCGCSV por volta das 17h de Brasília (cerca de 20h UTC, conforme RES-01). As tentativas de reserva não alteram a regra de lacuna declarada quando a coleta não obtiver dados.

## C4 nível 1 — Contexto

```mermaid
C4Context
    title C4 nível 1 — Contexto do projeto final SSP
    Person(colecionador, "Colecionador", "Consulta evidências de valor em reais para apoiar suas decisões")
    System_Boundary(projeto, "Projeto final SSP") {
        System(plataforma, "Plataforma de dados SSP", "Coleta, transforma e apresenta dados da coleção")
    }
    System_Ext(tcgcsv, "TCGCSV", "Produtos e preços de mercado em dólar")
    System_Ext(ptax, "API PTAX do Banco Central", "Cotações PTAX de compra e venda")
    System_Ext(sgs, "SGS do Banco Central", "Série diária do CDI")
    System_Ext(rustfs, "RustFS da turma", "Armazena bruto e silver no prefixo da coleção")
    System_Ext(silvers, "Silver dos colegas", "Dados das demais coleções no contrato comum da turma")
    Rel(colecionador, plataforma, "Consulta o dashboard")
    Rel(plataforma, tcgcsv, "Obtém produtos e preços")
    Rel(plataforma, ptax, "Obtém cotações e registros históricos públicos")
    Rel(plataforma, sgs, "Obtém CDI publicado")
    Rel(plataforma, rustfs, "Escreve no prefixo SSP e lê Parquet")
    Rel(plataforma, silvers, "Lê silver para comparações da turma")
```

## C4 nível 2 — Contêineres

```mermaid
C4Container
    title C4 nível 2 — Contêineres do projeto final SSP
    Person(colecionador, "Colecionador", "Consulta evidências no dashboard")
    System_Boundary(projeto, "Projeto final SSP") {
        Container(coletor, "Coletor", "Python, requests e boto3", "Obtém dados das fontes e grava o bruto no prefixo SSP")
        Container(silver, "Processador silver", "Python, Pydantic e Parquet", "Reconstrói e valida silver a partir do bruto")
        Container(gold, "Gold DuckDB", "DuckDB", "Lê Parquet do RustFS e constrói o esquema estrela")
        Container(dashboard, "Dashboard Streamlit", "Streamlit", "Apresenta perguntas de negócio e desafio da carteira")
    }
    Container_Ext(actions, "Agendador GitHub Actions", "GitHub Actions", "Dispara a execução diária às 18h30 de Brasília e tentativas de reserva")
    System_Ext(tcgcsv, "TCGCSV", "Produtos e preços em dólar")
    System_Ext(ptax, "API PTAX do Banco Central", "Cotações de compra e venda")
    System_Ext(sgs, "SGS do Banco Central", "CDI")
    System_Ext(rustfs, "RustFS da turma", "Armazena raw e silver no prefixo SSP")
    System_Ext(silvers, "Silver dos colegas", "Dados no contrato comum da turma")
    Rel(colecionador, dashboard, "Consulta")
    Rel(actions, coletor, "Dispara coleta diária e tentativas de reserva")
    Rel(actions, silver, "Dispara após a coleta concluir")
    Rel(actions, gold, "Dispara após a silver concluir")
    Rel(coletor, tcgcsv, "Obtém produtos e preços respeitando RF-03")
    Rel(coletor, ptax, "Obtém PTAX e backfill histórico")
    Rel(coletor, sgs, "Obtém CDI disponível")
    Rel(coletor, rustfs, "Escreve objetos raw por coleção, fonte e data")
    Rel(silver, rustfs, "Lê raw e escreve silver Parquet no prefixo SSP")
    Rel(gold, rustfs, "Lê Parquet silver SSP")
    Rel(gold, silvers, "Lê silver das demais coleções")
    Rel(gold, dashboard, "Disponibiliza fatos e dimensões gold")
```

A chave da gold e seu local persistente não estão definidos na spec nem nas decisões recebidas. O diagrama representa Gold DuckDB como o contêiner que constrói e disponibiliza a gold; o modo de persistência fica como pergunta aberta, sem introduzir outro serviço ou banco.

## Fluxo de dados e responsabilidades de escrita

| Etapa | Entrada | Operação | Quem escreve | Destino e regra |
|---|---|---|---|---|
| Coleta | TCGCSV, API PTAX do Banco Central e SGS do Banco Central | Coleta produtos e preços diariamente; obtém PTAX e CDI disponíveis; permite backfill histórico público da PTAX. | Coletor | Escreve as respostas originais em raw no prefixo `group_id=23651`, identificadas por coleção, fonte e data. Verifica a existência da chave antes de gravar; não sobrescreve nem duplica. |
| Silver | Raw da coleção SSP | Valida o contrato comum; separa inválidos em quarentena com motivo e contagem no log; preserva nulos; deriva classificação carta/selado a partir da fonte. Code Card é carta e sua exclusão das perguntas 1, 3 e 4 segue a regra de raridade. | Processador silver | Lê raw e escreve silver Parquet somente no prefixo SSP no RustFS da turma. |
| Gold | Silver Parquet SSP e silver dos colegas | DuckDB lê os Parquets; converte preços pela última PTAX de fechamento até a data do preço; produz fatos e dimensões do esquema estrela e cálculos exigidos pela spec. | Gold DuckDB | Produz a gold para consumo pelo Dashboard Streamlit. Local e forma de persistência da gold ainda não definidos. |
| Apresentação | Gold e silver dos colegas no contrato comum, conforme a visualização | Apresenta as cinco perguntas em reais, identificadores, imagens e links disponíveis, filtros definidos e desafio da carteira. | Dashboard Streamlit | Leitura para apresentação; não escreve em prefixos de colegas. |

O Agendador GitHub Actions inicia a execução diária às 18h30 de Brasília e pode disparar tentativas de reserva. Horários, quantidade e condição de repetição ficam pendentes de decisão. A coleta das três chamadas diárias do TCGCSV e os limites de uso seguem RF-03. Falha ou ausência de dados é registrada como lacuna no README; não há preenchimento sintético.

A reconstrução de silver e gold deve continuar disponível por um único comando documentado no README (RF-06). A forma exata de invocar esse comando em GitHub Actions e localmente será consolidada na implementação e documentação, sem permitir que a reconstrução dependa de camadas derivadas anteriores.

## Escolhas técnicas

| Escolha | Alternativas consideradas e motivo do descarte | Requisito ou restrição que justifica | ADR previsto |
|---|---|---|---|
| Chave de objeto raw por coleção, fonte e data, sem sobrescrita | Chave somente por data poderia colidir entre coleções ou fontes; sobrescrever o objeto do dia viola a imutabilidade. | RF-02, RNF-03, OBJ-07 e RES-02. | ADR-002 — chave por coleção e data (incluir fonte na identificação para separar origens). |
| Camadas raw, silver e gold reconstruíveis | Manter somente a última camada derivada impediria reconstrução; editar silver ou gold manualmente perderia a rastreabilidade a partir do bruto. | RF-02, RF-06, OBJ-07 e invariantes de `AGENTS.md`. | ADR-003 — camadas derivadas e reconstruíveis. |
| Gold em esquema estrela construída com DuckDB sobre Parquet do RustFS | Uma tabela plana não representa as dimensões exigidas; cálculo diretamente no dashboard mistura transformação e apresentação e não atende à gold requerida. | RF-06, RF-07, RF-08 e RF-10. DuckDB e Parquet são escolhas do aluno; a spec exige a gold e suas relações, não estas ferramentas específicas. | ADR-004 — esquema estrela na gold. |
| Coletor e processador silver em Python com `requests`, `boto3`, Pydantic e Parquet | Coleta manual não garante a série diária; validação sem contrato explícito não assegura nomes e tipos da silver; outro formato de arquivo não foi escolhido pelo aluno. | RF-01, RF-03, RF-05 e RF-06; RES-01, RES-02 e RES-06. As bibliotecas e o formato específicos são decisões do aluno, sem requisito correspondente que os torne obrigatórios. | Sem ADR previsto além da decisão de camadas no ADR-003; detalhamento adicional sem requisito correspondente. |
| Agendador no GitHub Actions, execução diária às 18h30 de Brasília e tentativas de reserva | Execução manual não garante frequência diária; executar somente próximo das 17h poderia coincidir com a atualização aproximada do TCGCSV. O horário e o agendador foram decididos pelo aluno; a quantidade e os horários de reserva seguem pendentes. | RF-01 e RF-03 justificam coleta diária e respeito à fonte; horário e produto GitHub Actions: sem requisito correspondente específico. | ADR-008 — agenda diária e tentativas de reserva. |
| Dashboard em Streamlit | Relatórios estáticos não atendem ao dashboard consultável; construir interface dentro do processamento mistura apresentação e transformação. Streamlit foi escolhido pelo aluno; outra ferramenta específica não é exigida. | RF-11 e RF-12 justificam dashboard, conteúdo e filtros; Streamlit: sem requisito correspondente específico. | Sem ADR previsto; tecnologia específica sem requisito correspondente. |
| Classificação carta/selado derivada da fonte; Code Card classificado como carta e excluído das perguntas 1, 3 e 4 segundo raridade | Classificação manual não se atualizaria com os dados da fonte; tratar Code Card como produto selado contraria a decisão do aluno; inclusão nas perguntas 1, 3 e 4 contraria a regra existente. | RF-11 e RF-12; invariante de filtros e Code Card em `AGENTS.md`. O método exato para derivar categoria por raridade ainda precisa ser validado contra os campos disponíveis. | ADR-005 — classificação carta/selado e regra de Code Card. |
| Carteira própria com seleção usando apenas o primeiro dia | Selecionar com dias posteriores introduziria informação futura na composição; usar a cesta compartilhada da turma substituiria a decisão de carteira própria. | RF-13 e RF-14; OBJ-06 e invariante de carteira em `AGENTS.md`. | ADR-006 — regra da carteira própria, antes do primeiro cálculo. |
| Taxa de venda parametrizada; 15% tratado como hipótese | Fixar permanentemente 15% impede avaliar outros valores; assumir taxa zero omite custo de venda. A taxa exata permanece hipótese declarada em ADR. | RF-13, OBJ-06 e RES-05. | ADR-007 — taxa de venda como parâmetro e hipótese de 15%. |
| Credenciais em `.env` local e GitHub Secrets, nunca em arquivo versionado | Credencial embutida no código ou committada expõe acesso; variável sem proteção não atende à restrição de segredo fora do Git. | RNF-04 e RES-06; confirmação do aluno de que “variáveis do GitHub” significa GitHub Secrets. | Sem ADR previsto; restrição de segurança vigente. |
| Backfill da PTAX por data, preservando a imutabilidade do bruto | Não recuperar registros públicos históricos reduziria a cobertura disponível; alterar objetos existentes violaria RF-02. | RF-01, RF-02, RF-08 e RES-03; permissão expressa do aluno para backfill da PTAX pública. | Sem ADR previsto; decisão de coleta alinhada à imutabilidade. |

ADR-001 permanece reservado ao registro da origem histórica do código de `src/collector.py` e `src/silver.py`, conforme `AGENTS.md`. A tabela começa os ADRs arquiteturais em ADR-002 para evitar colisão.

## Riscos técnicos iniciais

| Risco | Efeito possível | Requisito ou restrição relacionada | Mitigação ou observação para a etapa seguinte |
|---|---|---|---|
| Atualização do TCGCSV pode atrasar ou falhar após o horário esperado. | Coleta do dia ausente ou incompleta. | RF-01, RF-03, RF-04; RES-01. | Definir política de tentativas de reserva; preservar a lacuna declarada quando não houver coleta válida. |
| Tentativas de reserva sem horário e quantidade definidos podem gerar chamadas em excesso ou não recuperar a execução. | Violação de limite ou falta de dados. | RF-03; RES-01. | Decidir quantidade, intervalo e condição de acionamento sem exceder a pausa e o limite diário. |
| Mudança no texto ou formato do boletim PTAX. | Fechamentos descartados, como os cinco dias úteis observados no fato adicional. | RNF-02, RF-08 e RF-09. | Testar variantes do texto de fechamento e manter teste com a semana solicitada, após confirmar o ano. |
| CDI ainda não publicado na manhã seguinte ou indisponível em feriados. | Retorno de caixa incompleto ou incorreto. | RF-01, RF-13; RES-03. | Tratar ausência como indisponibilidade, sem zero inventado, e aplicar CDI somente quando publicado para dia útil. |
| Silver de colegas ausente, atrasada ou incompatível com o contrato comum. | Comparações de turma incompletas ou inválidas. | RF-05, RF-07, RF-11, RF-13; RES-02. | Validar contrato, colocar inválidos em quarentena e apresentar cobertura das coleções disponíveis. |
| Nomes, tipos ou campos das fontes mudarem. | Erro de validação ou classificação de produtos incorreta. | RF-05, RF-12; contrato comum da silver. | Registrar motivos e contagens; confirmar quais campos da fonte determinam carta, selado e raridade. |
| Escrita em prefixo incorreto ou vazamento de credencial. | Alteração de dados de colegas ou exposição de acesso. | RNF-03, RNF-04; RES-02 e RES-06. | Restringir escrita ao prefixo SSP e usar apenas GitHub Secrets e `.env` local, nunca versionado. |
| História disponível curta e lacunas na coleta. | Comparações de risco e retorno podem ter cobertura insuficiente para conclusão. | OBJ-05 a OBJ-07; persona. | Exibir período, cobertura, contagens e lacunas; não extrapolar a série. |
| Hipóteses de agregação, risco, decomposição e carteira não validadas. | Resultados diferentes conforme a regra escolhida. | OBJ-01, OBJ-02, OBJ-03, OBJ-05 e OBJ-06. | Validar definições antes de interpretar resultados e registrá-las nos ADRs pertinentes. |
| Destino persistente da gold e acesso pelo dashboard ainda não definidos. | Reprodução de resultados pode depender do processo ou ambiente de execução. | RF-06, RF-07, RF-11. | Definir a persistência e o ciclo de vida da gold sem introduzir serviço não aprovado. |

## Perguntas abertas

- Quantas tentativas de reserva haverá, em quais horários e sob qual condição de falha? A regra deve caber no limite diário de chamadas e respeitar a pausa mínima do TCGCSV.
- Qual é o local e o ciclo de vida da gold produzida pelo DuckDB, e como o Dashboard Streamlit a consultará?
- Quais são as cinco carteiras e os critérios exatos para dólar parado e CDI?
- Qual ano deve ser usado no teste de conversão PTAX da semana de 09/10 a 13/10?
- Quais fórmulas e critérios serão validados para a decomposição do OBJ-01, agregações dos OBJ-02 e OBJ-03, medida de risco do OBJ-05 e seleção/retorno do OBJ-06?
- Quais campos específicos da fonte determinam categoria carta/selado e a regra de raridade aplicada à exclusão de Code Card?
- A classificação da gold será publicada como dado acessível no contrato comum ou aplicada apenas às análises do dashboard? A spec exige resultados comuns, mas não detalha esse atributo.
