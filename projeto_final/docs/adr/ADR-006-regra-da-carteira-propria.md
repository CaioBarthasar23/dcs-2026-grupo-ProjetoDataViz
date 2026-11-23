# ADR-006 — Regra da carteira `propria`

- **Status:** aceito como hipótese, validação pendente.
- **Data:** 23/11/2026.
- **Responsável:** CaioBarthasar23.

## Contexto

Requisitos: RF-13 e RF-14; tarefa T-29. A spec exige que a regra da carteira `propria` seja definida pelo aluno em ADR e registrada em commit anterior ao primeiro cálculo da carteira. Nenhuma composição nem retorno da `propria` foi calculado antes deste ADR. Relacionados: ADR-005 (classificação carta/selado, Code Card, PTAX de venda por ASOF e seleção de `selado` e `cesta_raras`) e ADR-007 (taxa de venda). Persona: `docs/00_persona.md` (decisão sobre onde aplicar o dinheiro entre cartas avulsas, selado, dólar parado ou CDI).

## Decisão

Hipótese, validação pendente. A carteira `propria` divide os R$ 1.000 do primeiro dia (31/10/2026) em duas metades iguais:

1. **Preço e câmbio.** Só preços do primeiro dia e a PTAX de venda por ASOF (a última de fechamento conhecida, nunca posterior ao dia do preço), como no ADR-005.
2. **Metade selado (R$ 500).** Entre os produtos com `tipo_produto = selado` e `market_price > 0`, escolhe-se o de maior `market_price` em US$ tal que `market_price × PTAX de venda ≤ R$ 500`; desempate pelo menor `product_id`; compra-se o máximo de unidades inteiras dentro de R$ 500.
3. **Metade carta (R$ 500).** Entre as cartas com `tipo_produto = carta` e `market_price > 0`, **excluídas as Code Cards** (`raridade == "Code Card"`), escolhe-se a de maior `market_price` tal que `market_price × PTAX de venda ≤ R$ 500`; desempate pelo menor `product_id`; compra-se 1 unidade.
4. **Sobras.** A sobra de cada metade rende CDI.
5. **Metade sem candidato.** Se nenhum produto couber em R$ 500 em uma das metades, essa metade fica em caixa rendendo CDI (hipótese, validação pendente).
6. **Liquidação.** Segue as regras gerais de RF-13 e a taxa de venda do ADR-007.

A divisão em R$ 500 e R$ 500 é hipótese do aluno, sem origem em dado.

## Motivo (a partir da persona)

A persona decide onde aplicar o dinheiro entre cartas avulsas, produto selado, dólar parado e CDI. As carteiras `selado` e `cesta_raras` testam cada alternativa isolada; a `propria` representa a decisão de dividir o mesmo orçamento entre as duas, em vez de escolher só uma, e permite comparar a estratégia mista com as puras. A Code Card fica fora da metade carta porque, pelos nomes, é código digital de produto selado, e a persona compra para guardar.

## Alternativas consideradas

- **Quatro partes iguais (carta, selado, dólar, CDI):** não escolhida; as partes de dólar e CDI repetiriam as carteiras `dolar` e `cdi`, e o cálculo misturaria quatro tipos de posição.
- **Carta-troféu (a carta de maior preço que cabe em R$ 1.000):** não escolhida; não compara carta com selado.
- **Code Card dentro da metade carta:** não escolhida (motivo acima).

## Consequências

- A metade selado, limitada a R$ 500, não repete a ETB da carteira `selado` (R$ 649,89 no primeiro dia, conforme a evidência do ADR-005).
- A composição será calculada na T-17 e registrada em `docs/evidencias/`; ela não é conhecida neste ADR.
- A `propria` é uma carteira mista: ela não separa o efeito de cada metade. A comparação entre selado e cartas avulsas continua sendo feita pelas carteiras `selado` e `cesta_raras`.

## Limites

- A frequência de consulta da persona é hipótese, validação pendente.
- O aluno já conhece outras evidências do projeto com preços de dias posteriores (T-14 a T-16). A regra não usa esses dados, mas isso não elimina o risco de viés de retrospecto.
