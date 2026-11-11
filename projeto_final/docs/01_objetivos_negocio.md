# Objetivos de negócio

## Objetivos

| ID | Objetivo de negócio | Métrica de sucesso verificável | Origem |
|---|---|---|---|
| OBJ-01 | Saber quais cartas da coleção mais valorizaram e mais desvalorizaram em reais desde o início da coleta, separando o efeito da carta, do câmbio e o efeito cruzado (pergunta 1). | Por carta e acabamento, apresentar a variação percentual em reais entre o primeiro e o último dia, considerando apenas cartas com preço acima de US$ 1 no primeiro dia, e ordenar os maiores ganhos e perdas. Decompor a variação por `(1+r_brl) = (1+r_usd) × (1+r_cambio)`, com efeito da carta, do câmbio e cruzado; excluir Code Card. O dashboard apresenta valores em reais, com chave para dólar, imagem das cartas e link do produto no TCGplayer. | Pergunta 1 do enunciado do projeto final (variação em reais, elegibilidade, decomposição e Code Card); requisito de dashboard do enunciado. |
| OBJ-02 | Saber se o produto selado guardou valor melhor que as cartas avulsas na coleção (pergunta 2). | Apresentar índice base 100 no primeiro dia, comparando a média dos produtos selados com a soma dos preços das cartas de raridade Double Rare em diante. O dashboard apresenta valores em reais, com chave para dólar, e filtro de preço mínimo em dólar. | Pergunta 2 do enunciado do projeto final (índice base 100 e critérios de agregação); requisito de dashboard do enunciado. |
| OBJ-03 | Saber se a coleção valorizou mais ou menos que as outras da turma (pergunta 3). | Calcular diariamente o valor da coleção em reais como a soma de `market_price_brl` de um exemplar de cada carta; apresentar índice base 100 por coleção e PTAX também em base 100 no mesmo gráfico. Excluir Code Card. O dashboard apresenta valores em reais, com chave para dólar e filtro de preço mínimo em dólar. | Pergunta 3 do enunciado do projeto final (valor, índices e Code Card); requisito de dashboard do enunciado. |
| OBJ-04 | Saber onde está concentrado o valor de cada coleção (pergunta 4). | No último dia, apresentar a participação de cada raridade no valor total e o número de cartas que somam 80% desse valor. Excluir Code Card. O dashboard apresenta valores em reais, com chave para dólar, imagem das cartas e link do produto no TCGplayer. | Pergunta 4 do enunciado do projeto final (participação por raridade, concentração e Code Card); requisito de dashboard do enunciado. |
| OBJ-05 | Saber quais cartas da turma deram mais retorno para o risco assumido (pergunta 5). | Comparar retorno no período com volatilidade, medida pelo desvio-padrão dos retornos diários, para cartas com preço acima de US$ 5. O dashboard permite filtrar por preço mínimo em dólar. | Pergunta 5 do enunciado do projeto final (retorno, volatilidade e elegibilidade); requisito de dashboard do enunciado. |
| OBJ-06 | Saber se uma carteira de R$ 1.000 em cartas ou selados ganhou do dólar parado e do CDI (desafio da carteira). | Comparar cinco carteiras — `selado`, `cesta_raras`, `propria`, `dolar` e `cdi` — pelas métricas de retorno acumulado, excesso sobre o CDI, perda máxima e dias com preço carregado. O valor de liquidação é unidades × `market_price` × (1 − taxa de venda) × PTAX de compra, mais sobra em caixa rendendo CDI. A regra de seleção da carteira `propria` é **hipótese: validação pendente**. O dashboard mostra resultados com e sem a taxa; a diferença entra no ATAM como ponto de sensibilidade. A taxa de venda de 15% permanece hipótese e deve ser declarada em ADR. | Desafio da carteira do enunciado do projeto final (cinco carteiras, métricas, liquidação e sensibilidade da taxa); taxa de venda de 15% e regra da carteira `propria`: hipóteses sem origem definida. |
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
