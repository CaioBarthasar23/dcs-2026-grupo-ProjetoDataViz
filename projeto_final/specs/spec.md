# Especificação de requisitos

Esta especificação descreve o comportamento esperado, não o estado atual da implementação. A cobertura e o estado real de cada requisito devem ser registrados posteriormente na rastreabilidade.

## Requisitos funcionais

### RF-01 — Coletar diariamente produtos, preços, PTAX e CDI no bruto

O processo deve registrar os dados recebidos das fontes para produtos e preços da coleção, PTAX e CDI, preservando as respostas originais. Cada objeto deve estar associado à coleção e à data da coleta, e identificar sua fonte. A indisponibilidade de PTAX em dia não útil ou de CDI ainda não publicado não deve ser representada como valor zero.

**Origem:** OBJ-07; RES-01 e RES-03; fatos do enunciado sobre TCGCSV e Banco Central.

**Critério de aceite:**

- **Dado** um dia de coleta e as respostas disponíveis das fontes para a coleção SSP (`groupId 23651`),
- **Quando** a coleta diária for executada,
- **Então** os dados originais disponíveis de produtos, preços, PTAX e CDI ficam registrados no bruto com identificação da coleção, data e fonte, e qualquer fonte sem dado disponível permanece ausente, sem valor inventado.

### RF-02 — Preservar o bruto e tornar a coleta idempotente

A coleta deve usar uma chave que identifique a coleção, a fonte e a data. Repetir a execução no mesmo dia não deve criar duplicatas nem sobrescrever objetos existentes; a segunda execução deve terminar com sucesso e registrar que o objeto já existia.

**Origem:** OBJ-07; RES-02; invariantes de dados em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** um objeto bruto já existente para a coleção `group_id=23651`, fonte e data da coleta,
- **Quando** a coleta for executada novamente para a mesma fonte e data,
- **Então** o objeto existente não é regravado, não surge uma duplicata, o processo termina com código zero e o log informa `ja existia`.

### RF-03 — Respeitar as regras de uso do TCGCSV

As chamadas ao TCGCSV devem incluir User-Agent próprio, manter pausa mínima de 100 ms entre chamadas e respeitar o limite de 10.000 requisições por dia. A previsão de chamadas para a coleta desta coleção deve considerar três chamadas por dia.

**Origem:** RES-01; fatos e restrições do enunciado do projeto final.

**Critério de aceite:**

- **Dado** o início da coleta TCGCSV da coleção,
- **Quando** as chamadas forem feitas ao longo do dia,
- **Então** cada chamada contém User-Agent próprio, o intervalo entre chamadas é de pelo menos 100 ms e o total diário não excede 10.000 requisições; a execução da coleção usa três chamadas no dia.

### RF-04 — Declarar dias sem coleta como lacunas

O README deve registrar cada dia sem coleta com a data e o motivo conhecido. A série não deve preencher lacunas com valores estimados ou inventados.

**Origem:** OBJ-07; RES-08; invariantes de dados em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** um dia esperado sem dados de coleta,
- **Quando** a documentação da série for atualizada,
- **Então** o README apresenta a data e o motivo conhecido da lacuna, e não há valor sintético atribuído àquele dia.

### RF-05 — Validar silver e colocar registros inválidos em quarentena

A silver deve respeitar o contrato comum da turma quanto a nomes e tipos das colunas, podendo incluir colunas adicionais. Registros que não passem pela validação devem ser isolados em quarentena com o motivo; o log deve informar a contagem de registros em quarentena. Valores ausentes permanecem nulos.

**Origem:** OBJ-07; RES-02 e RES-08; fato do enunciado sobre o contrato comum da silver.

**Critério de aceite:**

- **Dado** um conjunto bruto com registros válidos e registros incompatíveis com o contrato comum da silver,
- **Quando** a silver for construída,
- **Então** os registros válidos aparecem com nomes e tipos de contrato, os inválidos ficam em quarentena com motivo, o log informa a contagem em quarentena e campos sem valor permanecem nulos.

### RF-06 — Reconstruir silver e gold com um único comando

Deve existir um único comando documentado no README que reconstrua silver e gold a partir do bruto, sem depender de resultados derivados anteriores.

**Origem:** OBJ-07; invariantes de dados em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** o bruto necessário e a ausência das camadas silver e gold derivadas,
- **Quando** for executado o comando único documentado no README para reconstrução,
- **Então** silver e gold são produzidas a partir do bruto e o comando termina sem exigir uma camada derivada anterior.

### RF-07 — Publicar gold em esquema estrela

A gold deve conter um fato de preço diário ligado às dimensões de produto, coleção, data e acabamento, e um fato de câmbio diário. A modelagem deve permitir identificar o produto, a coleção, o dia e o acabamento associados a cada preço.

**Origem:** OBJ-01, OBJ-02, OBJ-03, OBJ-04, OBJ-05 e OBJ-06; contrato comum da turma para consumo de dados compartilhados.

**Critério de aceite:**

- **Dado** silver reconstruída com preços de produtos e dados de câmbio disponíveis,
- **Quando** a gold for reconstruída,
- **Então** ela contém o fato de preço diário relacionado às dimensões de produto, coleção, data e acabamento, além do fato de câmbio diário, e cada preço consultado pode ser relacionado a essas dimensões.

### RF-08 — Converter preços para reais usando PTAX conhecida até a data do preço

A conversão de preço para reais deve associar a cada preço a última PTAX de fechamento conhecida cuja data não seja posterior à data do preço. Cotação futura não pode ser usada.

**Origem:** OBJ-01 a OBJ-06; RES-03; invariante de câmbio em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** um preço em dólar em uma data e cotações PTAX de fechamento anteriores, do mesmo dia ou posteriores,
- **Quando** o preço for convertido para reais,
- **Então** é usada a PTAX de fechamento mais recente cuja data seja igual ou anterior à data do preço, e nenhuma cotação posterior é associada.

### RF-09 — Verificar a conversão PTAX na semana de 09/10 a 13/10/2026

A conversão deve ter um teste de unidade para a semana de 09/10 a 13/10/2026, verificando a associação da cotação válida a cada data de preço e evitando cotação posterior. O ano de 2026 foi definido pelo aluno em 11/11/2026; 12/10/2026 é segunda-feira e feriado nacional, então a semana testa fim de semana e feriado.

**Origem:** OBJ-01 a OBJ-06; RF-08; decisão do aluno em 11/11/2026 sobre o ano da semana de teste.

**Critério de aceite:**

- **Dado** o conjunto de preços e fechamentos PTAX de 09/10 a 13/10/2026,
- **Quando** o teste de unidade de conversão for executado,
- **Então** todas as datas usam a última PTAX de fechamento disponível até a data do preço, e o teste passa sem associar cotação futura.

### RF-10 — Decompor a variação em efeito da carta, do câmbio e cruzado

Para cada carta elegível comparável entre o início e o fim do período, o resultado deve apresentar variação percentual em reais e suas parcelas atribuídas ao efeito do preço da carta, ao efeito do câmbio e ao efeito cruzado, usando `(1+r_brl) = (1+r_usd) × (1+r_cambio)`. Preços ausentes permanecem nulos e não são tratados como zero.

**Origem:** OBJ-01; pergunta 1; persona, dor atual.

**Critério de aceite:**

- **Dado** um preço em dólar e uma PTAX válidos no início e no fim do período para uma carta,
- **Quando** a variação em reais for calculada pela fórmula `(1+r_brl) = (1+r_usd) × (1+r_cambio)`,
- **Então** o resultado apresenta a variação total e os três componentes; a soma dos componentes corresponde à variação total dentro da precisão monetária documentada.

### RF-11 — Apresentar no dashboard as cinco perguntas em reais

O dashboard deve apresentar: (1) variação percentual em reais entre o primeiro e o último dia por carta e acabamento, para cartas acima de US$ 1 no primeiro dia, com decomposição dos efeitos; (2) índice base 100 no primeiro dia, comparando a média dos selados com a soma dos preços das cartas de raridade Double Rare em diante; (3) valor diário da coleção em reais, calculado pela soma de `market_price_brl` de um exemplar de cada carta, com índice base 100 por coleção e PTAX em base 100 no mesmo gráfico; (4) participação de cada raridade no valor total no último dia e número de cartas que somam 80% do valor; e (5) retorno no período contra desvio-padrão dos retornos diários para cartas acima de US$ 5. Períodos, coberturas e quantidades de observações devem ser visíveis para contextualizar comparações.

**Origem:** OBJ-01, OBJ-02, OBJ-03, OBJ-04 e OBJ-05; perguntas 1 a 5 do enunciado; persona.

**Critério de aceite:**

- **Dado** silver das coleções disponíveis e dados suficientes para as perguntas,
- **Quando** o dashboard for consultado,
- **Então** o dashboard apresenta em reais (1) a variação percentual por carta e acabamento para cartas acima de US$ 1 no primeiro dia, com decomposição; (2) os índices base 100 do selado e das cartas Double Rare em diante, agregados conforme definido; (3) o valor diário da coleção e os índices base 100 por coleção e da PTAX no mesmo gráfico; (4) a participação por raridade no último dia e o número de cartas que somam 80% do valor; e (5) retorno e desvio-padrão dos retornos diários para cartas acima de US$ 5. Os períodos e coberturas correspondentes são visíveis.

### RF-12 — Expor chave, imagem e link do produto e aplicar filtros e exclusões definidos

O dashboard deve apresentar valores em reais e oferecer a chave R$/US$ para alternar a exibição dos valores para dólar. `product_id` identifica o produto; imagem da carta e link do produto no TCGplayer devem ser apresentados quando disponíveis. Deve permitir filtros de preço mínimo em dólar, incluindo acima de US$ 1 no primeiro dia para P1 e acima de US$ 5 para P5. Code Card, identificado pela raridade, fica fora das perguntas 1, 3 e 4.

**Origem:** OBJ-01 a OBJ-05; requisito de dashboard do enunciado; restrição de filtros de preço mínimo em dólar e exclusão de Code Card em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** produtos com `product_id`, imagem, link do TCGplayer e preços em dólar disponíveis,
- **Quando** o usuário alternar a chave R$/US$, aplicar os filtros mínimos de preço e consultar as perguntas 1 a 5,
- **Então** os valores são exibidos na moeda selecionada, `product_id` identifica cada produto, imagem e link disponíveis são apresentados, P1 considera cartas acima de US$ 1 no primeiro dia, P5 considera cartas acima de US$ 5, e Code Card não aparece em P1, P3 ou P4.

### RF-13 — Calcular as cinco carteiras e apresentar resultados no contrato comum

O desafio deve calcular cinco carteiras: `selado`, `cesta_raras`, `propria`, `dolar` e `cdi`. `selado` compra unidades inteiras do booster box; se o box não tiver preço no primeiro dia, usa o selado de maior preço, com a escolha detalhada em ADR. `cesta_raras` investe R$ 100 em cada uma das dez cartas com maior `market_price` no primeiro dia, em unidades inteiras. A regra da carteira `propria` será definida pelo aluno em ADR e registrada em commit anterior ao primeiro cálculo (**hipótese: validação pendente**). `dolar` converte R$ 1.000 pela PTAX de venda do primeiro dia. `cdi` corrige R$ 1.000 pelo CDI de cada dia útil, com juros compostos.

O valor de liquidação é unidades × `market_price` × (1 − taxa de venda) × PTAX de compra, mais sobra em caixa rendendo CDI. A taxa de venda é parâmetro; 15% permanece hipótese a declarar em ADR. Produto sem preço no dia usa o último preço observado; o painel marca esses dias e nenhum valor inventado é gravado na silver. As métricas são retorno acumulado, excesso sobre o CDI, perda máxima e dias com preço carregado. O dashboard mostra resultados com e sem a taxa. Os resultados seguem o contrato comum `tcg/gold_turma/carteira/`: `data DATE`, `group_id INTEGER`, `carteira VARCHAR`, `valor_brl DOUBLE`, `retorno_acumulado DOUBLE`, `taxa_venda DOUBLE`.

**Origem:** OBJ-06; RES-03 e RES-05; desafio da carteira e contrato comum do enunciado; invariantes de carteira em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** preços, PTAX e CDI disponíveis para o período e a regra da carteira `propria` registrada em ADR,
- **Quando** as cinco carteiras forem calculadas com uma taxa de venda configurada,
- **Então** `selado`, `cesta_raras`, `propria`, `dolar` e `cdi` seguem as regras descritas, as compras e liquidações usam respectivamente PTAX de venda e de compra, as unidades são inteiras, o CDI é composto em dias úteis, preços carregados são identificados no painel sem gravar valores inventados na silver, as métricas são produzidas, o dashboard mostra resultados com e sem taxa e os registros seguem o caminho e esquema definidos.

### RF-14 — Manter estável a composição da cesta de raras com dados posteriores

A seleção da cesta deve usar somente os dados disponíveis no primeiro dia da janela da carteira; dados incluídos posteriormente na silver não podem alterar a composição selecionada para aquela janela.

**Origem:** OBJ-06; invariante de carteira em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** uma silver inicial e a composição da cesta de raras calculada para uma janela,
- **Quando** forem acrescentados à silver dados de dias posteriores e a composição for calculada novamente para a mesma janela,
- **Então** a cesta selecionada permanece idêntica à composição obtida usando somente o primeiro dia.

### RF-15 — Documentar no README o comando do pipeline e os testes

O README deve informar o comando que executa o pipeline de reconstrução e como executar os testes. A especificação exige que os testes do projeto passem na validação; não declara que passam no estado atual.

**Origem:** OBJ-07; pedido desta etapa; fluxo de validação em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** o README e o ambiente de execução documentado para o projeto,
- **Quando** uma pessoa seguir o comando documentado para executar o pipeline e os testes,
- **Então** o pipeline inicia conforme documentado e os testes terminam com código zero, com a saída real registrada como evidência antes de declarar sucesso.

### RF-16 — Classificar produtos da silver como carta ou selado

A silver deve classificar cada produto como carta ou selado a partir dos campos da fonte: produto com número de carta é carta; produto sem número de carta é selado. Code Card, que tem raridade Code Card, é classificado como carta e excluído das perguntas 1, 3 e 4 pela raridade. O método exato de classificação será confirmado no ADR-005.

**Origem:** decisão do aluno no plano; comportamento do código existente em `src/silver.py`; regra de exclusão de Code Card em `projeto_final/AGENTS.md`. O método exato será confirmado no ADR-005.

**Critério de aceite:**

- **Dado** produtos da fonte com e sem número de carta, incluindo um produto de raridade Code Card,
- **Quando** a silver classificar os produtos,
- **Então** produtos com número de carta são classificados como carta, produtos sem número são classificados como selado, Code Card é classificado como carta, e Code Card é excluído das perguntas 1, 3 e 4 pela raridade.

## Requisitos não funcionais

### RNF-01 — Preservar nulos sem tratá-los como zero

**Atributo:** integridade dos dados.

Campos sem valor na fonte devem permanecer nulos nas camadas derivadas e não devem participar de médias, variações ou comparações como se fossem zero.

**Origem:** OBJ-01 e OBJ-07; RES-08; invariantes de dados em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** um preço ausente na fonte,
- **Quando** silver e gold forem reconstruídas e uma média ou variação for consultada,
- **Então** o preço continua nulo e não é contado como zero nem incluído no cálculo.

### RNF-02 — Tolerar variações no texto da fonte PTAX

**Atributo:** robustez a mudanças de apresentação da fonte.

A identificação do boletim de fechamento PTAX deve tolerar variações no texto de apresentação, incluindo o rótulo `Fechamento PTAX`, sem depender exclusivamente da igualdade com o texto `Fechamento`.

**Origem:** OBJ-07; fato adicional do enunciado sobre a execução real em 07/11/2026, quando o filtro ignorou cinco dias úteis.

**Critério de aceite:**

- **Dado** um retorno da fonte PTAX cujo boletim de fechamento esteja identificado como `Fechamento PTAX`,
- **Quando** os boletins forem interpretados,
- **Então** o fechamento é reconhecido e os dias úteis correspondentes não são descartados por diferença textual em relação ao rótulo `Fechamento`.

### RNF-03 — Restringir escrita ao prefixo da própria coleção

**Atributo:** isolamento de dados entre coleções.

Toda escrita de dados da coleção SSP deve permanecer no prefixo atribuído a `group_id=23651`; nenhum processo pode gravar no prefixo de outra coleção.

**Origem:** RES-02; invariantes de dados em `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** um processo de coleta ou publicação executado para `group_id=23651`,
- **Quando** ele escrever dados,
- **Então** todas as chaves escritas pertencem ao prefixo da coleção 23651 e nenhuma chave de outra coleção é alterada.

### RNF-04 — Manter segredos fora do Git

**Atributo:** proteção de credenciais.

Chaves e credenciais do RustFS devem permanecer fora do Git e não podem aparecer em código, documentação, logs ou evidências.

**Origem:** RES-06; seção “Segredos” de `projeto_final/AGENTS.md`.

**Critério de aceite:**

- **Dado** o conjunto de arquivos versionados e as evidências geradas,
- **Quando** forem revisados para publicação no Git,
- **Então** não há valores de credenciais ou chaves do RustFS nos arquivos, logs ou evidências.

### RNF-05 — Validar a conformidade da silver e registrar quarentena e contagens

**Atributo:** qualidade e auditabilidade dos dados.

A validação da silver deve ser reproduzível e deixar rastros verificáveis dos registros rejeitados, seus motivos e suas contagens.

**Origem:** OBJ-07; RES-02 e RES-08; contrato comum da turma.

**Critério de aceite:**

- **Dado** o mesmo bruto e as mesmas regras de validação,
- **Quando** a reconstrução da silver for executada,
- **Então** os registros inválidos são identificados com motivo e a contagem correspondente aparece no log da execução.

## Fora do escopo

| Item | Motivo | Origem |
|---|---|---|
| Previsão de preço | A série cobre cerca de sete semanas e não sustenta previsão. | `docs/00_persona.md`; `docs/01_objetivos_negocio.md`. |
| Recomendação de compra ou decisão automática de investimento | O dashboard apresenta evidências; a decisão final cabe ao colecionador. | `docs/00_persona.md`; `docs/01_objetivos_negocio.md`. |
| Preço praticado no Brasil, incluindo frete, impostos e spread de cartão | Os preços disponíveis refletem vendas recentes nos Estados Unidos e não incluem esses componentes. | `docs/00_persona.md`; `docs/01_objetivos_negocio.md`. |
| Dados em tempo real | A coleta é diária; a fonte atualiza por volta de 20h UTC e PTAX/CDI têm disponibilidade condicionada a dia útil e publicação. | `docs/01_objetivos_negocio.md`. |
| Scraping que viole `robots.txt` ou termos, ou contorno de bloqueio anti-robô | Não permitido no escopo. | RES-04 em `docs/01_objetivos_negocio.md`. |
