# Objetivos de negócio

## Objetivos

| ID | Objetivo de negócio | Métrica de sucesso verificável | Origem |
|---|---|---|---|
| OBJ-01 | Saber quais cartas da coleção mais valorizaram e mais desvalorizaram em reais desde o início da coleta, separando o efeito da carta, do câmbio e o efeito cruzado (pergunta 1). | Para cada carta elegível, apresentar variação total em R$ entre o primeiro e o último dia com preço comparável e a decomposição em efeito da carta, efeito do câmbio e efeito cruzado; ordenar variações para identificar os maiores ganhos e perdas. A fórmula e o tratamento de dados ausentes são **hipótese: validação pendente**; medir validando a decomposição contra os valores inicial e final e registrando a fórmula adotada. | Pergunta 1 do enunciado do projeto final; persona: dor de não separar a variação da carta e do câmbio. |
| OBJ-02 | Saber se o produto selado guardou valor melhor que as cartas avulsas na coleção (pergunta 2). | Comparar a variação percentual em reais do produto selado e das cartas avulsas no mesmo intervalo observável, informando os valores inicial e final e a quantidade de itens válidos em cada grupo. Critério de agregação dos grupos é **hipótese: validação pendente**; medir validando e documentando o critério antes da comparação. | Pergunta 2 do enunciado do projeto final; persona: quer saber se produto selado preservou valor melhor que cartas avulsas. |
| OBJ-03 | Saber se a coleção valorizou mais ou menos que as outras da turma (pergunta 3). | Comparar a variação percentual em reais da coleção SSP com a de cada coleção da turma no mesmo intervalo comum, indicando período e coleções com dados disponíveis. Métrica de agregação e tratamento de coberturas desiguais são **hipótese: validação pendente**; medir definindo e registrando esses critérios e verificando a disponibilidade de silver das coleções comparadas. | Pergunta 3 do enunciado do projeto final; contrato comum de silver e leitura da silver dos colegas. |
| OBJ-04 | Saber onde está concentrado o valor de cada coleção (pergunta 4). | Para cada coleção, apresentar a participação percentual de cada carta no valor total e identificar as maiores participações; informar data de referência e cobertura. Limiar para caracterizar concentração é **hipótese: validação pendente**; medir consultando o aluno e registrando o limiar, ou reportando apenas participações ordenadas sem classificar concentração. | Pergunta 4 do enunciado do projeto final. |
| OBJ-05 | Saber quais cartas da turma deram mais retorno para o risco assumido (pergunta 5). | Para as cartas comparáveis da turma, apresentar retorno e medida de risco no mesmo período, permitindo ordenar retorno por risco; informar período e número de observações. Definição de retorno, medida de risco e regra de ordenação são **hipótese: validação pendente**; medir consultando o aluno, registrando as definições e recalculando os indicadores sobre a série disponível. | Pergunta 5 do enunciado do projeto final; silver comum da turma. |
| OBJ-06 | Saber se uma carteira de R$ 1.000 em cartas ou selados ganhou do dólar parado e do CDI (desafio da carteira). | Comparar o valor final líquido em reais e o retorno da carteira iniciada com R$ 1.000 com as alternativas dólar parado e CDI, usando a mesma data inicial e final; explicitar itens escolhidos, resultados e taxa aplicada. A regra de seleção e o cálculo das alternativas são **hipótese: validação pendente**; medir validando os critérios e conferindo o cálculo com os dados do período. A taxa de venda de 15% é hipótese e deve ser declarada em ADR. | Desafio da carteira do enunciado do projeto final; persona: decisão entre cartas, selados, dólar parado ou CDI; taxa de venda de 15% indicada como hipótese. |
| OBJ-07 | Manter uma série diária contínua e verificável: bruto imutável, camadas reconstruíveis, lacunas declaradas. | Zero objetos do bruto sobrescritos; silver e gold reconstruíveis a partir do bruto; todo dia sem coleta declarado no README com data e motivo. Para PTAX, considerar sua disponibilidade apenas em dia útil; para CDI de um dia útil, considerar que o dado aparece na manhã seguinte. | Persona: dor “não sei se o dado é confiável” (hipótese: validação pendente); invariantes de dados de `projeto_final/AGENTS.md`; fatos e restrições do enunciado do projeto final. |

## Drivers de negócio

| ID | Driver | Relação com os objetivos | Origem |
|---|---|---|---|
| DR-01 | Apoiar a decisão do colecionador sobre onde aplicar dinheiro entre cartas avulsas, produto selado, dólar parado e CDI. | OBJ-02, OBJ-06 | Persona: decisão que toma; enunciado do projeto final. |
| DR-02 | Explicar a variação em reais separando preço da carta e câmbio, inclusive o efeito cruzado. | OBJ-01 | Persona: dor atual e critério de sucesso; pergunta 1 do enunciado. |
| DR-03 | Permitir comparar itens e coleções em bases temporais e monetárias comparáveis. | OBJ-02, OBJ-03, OBJ-05, OBJ-06 | Perguntas 2, 3 e 5 e desafio da carteira do enunciado do projeto final. |
| DR-04 | Mostrar como o valor está distribuído dentro de cada coleção. | OBJ-04 | Pergunta 4 do enunciado do projeto final. |
| DR-05 | Dar evidência verificável e explicitar limites e lacunas dos dados para apoiar a decisão do colecionador. | OBJ-01 a OBJ-07 | Persona: como saberia que deu certo; fonte sem histórico e série com cerca de sete semanas; invariantes do projeto. |

## Restrições

| ID | Restrição | Tipo | Origem |
|---|---|---|---|
| RES-01 | A fonte principal é TCGCSV, sem chave, atualizada por volta de 20h UTC; exige User-Agent próprio, pausa mínima de 100 ms entre chamadas e limite de 10.000 requisições por dia; uma coleção usa três chamadas por dia. | técnica | Fatos e restrições do enunciado do projeto final. |
| RES-02 | Escrita somente no prefixo da própria coleção; o dashboard lê a silver dos colegas pelo contrato comum da turma. | técnica | Enunciado do projeto final; `projeto_final/AGENTS.md`: “Nunca escrever no prefixo de outra coleção” e contrato comum de silver. |
| RES-03 | PTAX e CDI são do Banco Central e não exigem chave; PTAX só existe em dia útil e o CDI de um dia útil só aparece na manhã seguinte. | técnica | Fatos e restrições do enunciado do projeto final. |
| RES-04 | Scraping só é permitido se `robots.txt` e os termos permitirem; contornar bloqueio anti-robô não faz parte do trabalho. | legal | Fatos e restrições do enunciado do projeto final. |
| RES-05 | A taxa de venda de 15% é hipótese e deve ser declarada em ADR. | financeira | Fatos e restrições do enunciado do projeto final. |
| RES-06 | A chave do RustFS deve permanecer fora do Git. | técnica | Fatos e restrições do enunciado do projeto final; `projeto_final/AGENTS.md`, seção “Segredos”. |
| RES-07 | A mentoria ocorre em 05/12/2026 e a entrega deve ocorrer até 12/12/2026, às 23h59. | prazo | Fatos e restrições do enunciado do projeto final. |
| RES-08 | Nulo não é zero; dias sem coleta devem ser declarados como lacunas e não preenchidos com dados inventados. | técnica | `projeto_final/AGENTS.md`, invariantes de dados; persona e enunciado do projeto final. |

## Fora do escopo

| Item | Motivo | Origem |
|---|---|---|
| Previsão de preço | A série cobre cerca de sete semanas e não sustenta previsão. | Persona, fatos e lacunas. |
| Recomendação de compra ou decisão automática de investimento | O dashboard apresenta evidências; a decisão final é do colecionador. A série não sustenta recomendação de compra. | Persona, fatos e lacunas. |
| Preço praticado no Brasil, incluindo frete, impostos e spread de cartão | Os preços disponíveis refletem vendas recentes nos Estados Unidos e não incluem esses componentes. | Persona, fatos e lacunas; enunciado do projeto final. |
| Dados em tempo real | A fonte principal atualiza por volta de 20h UTC e a coleta é diária; PTAX e CDI também têm disponibilidade condicionada a dia útil e horário de publicação. | Fatos e restrições do enunciado do projeto final. |
| Scraping que viole `robots.txt` ou termos, ou contorno de bloqueio anti-robô | Não permitido no escopo do projeto. | Fatos e restrições do enunciado do projeto final. |
