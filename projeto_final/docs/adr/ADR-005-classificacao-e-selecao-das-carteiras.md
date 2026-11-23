# ADR-005 — Classificação carta/selado, Code Card e seleção das carteiras `selado` e `cesta_raras`

- **Status:** aceito; hipóteses marcadas, validação pendente.
- **Data:** 22/11/2026 (decisão); seleção calculada em 23/11/2026.
- **Responsável:** CaioBarthasar23.

## Contexto

Requisitos: RF-13 e RF-14 (carteiras e seleção só com dados do primeiro dia). Relacionados: ADR-006 (carteira `propria`) e ADR-007 (taxa de venda). Evidência: `docs/evidencias/ADR-005_selecao_primeiro_dia.txt` (leitura da silver local, reconstruída do bucket na T-35).

A especificação descreve `selado` como unidades de booster box ("Surging Sparks Booster Box", product_id 565606) e `cesta_raras` como R$ 100 em cada uma das 10 cartas de maior `market_price`, no primeiro dia (31/10/2026), com unidades inteiras e PTAX de venda por ASOF. No primeiro dia a PTAX de venda é 5,4212 (fechamento de 30/10).

Com esses preços, o texto literal da spec não compra nada:
- A Booster Box custa US$ 298,42 = R$ 1.617,79, acima dos R$ 1.000 (0 unidades).
- As 10 cartas de maior preço custam, cada uma, mais de R$ 100 (12 cartas passam desse valor), então nenhuma unidade inteira cabe em R$ 100.
- As duas carteiras ficariam 100% em caixa e seriam iguais à carteira `cdi`. Isso é uma consequência dos preços da SSP em 31/10, não um erro de cálculo.

## Decisão
1. **Classificação (método confirmado).** A função `classificar` de `src/silver.py` (linhas 125–131, ADR-001) decide: produto com o campo `Number` preenchido é `carta`; produto com `Rarity == "Code Card"` também é `carta`, mesmo sem número; os demais são `selado` (os selados recebem `categoria_selado` pelo nome). Conferência na silver local em 23/11/2026 (evidência): 252 cartas com número, 10 cartas sem número, todas com raridade Code Card e nenhuma de outra raridade, e 27 selados sem número; nenhum produto de raridade Code Card fora de `carta`. As 10 Code Cards são códigos de produtos selados (pelos nomes). *Hipótese, validação pendente:* a classificação não foi conferida produto a produto contra o site do TCGplayer.
2. **Code Card.** É a carta com `raridade == "Code Card"` (mesmo critério de `src/concentracao_valor.py`). Fica fora das perguntas 1, 3 e 4 do dashboard (AGENTS.md) e **dentro** da `cesta_raras`. Em 31/10 nenhuma das 10 cartas escolhidas é Code Card.
3. **`selado`.** Entre os produtos com `tipo_produto = selado` e `market_price > 0` no primeiro dia, escolhe-se o de maior `market_price` em US$ tal que `market_price × PTAX de venda ≤ R$ 1.000`; desempate pelo menor `product_id`. Compra-se o máximo de unidades inteiras e a sobra rende CDI.
4. **`cesta_raras`.** Entre as cartas (`tipo_produto = carta`, com Code Card) com preço no primeiro dia e `market_price × PTAX de venda ≤ R$ 100`, escolhem-se as 10 de maior `market_price`; desempate pelo menor `product_id`. Uma unidade de cada; a sobra rende CDI.
5. A escolha usa só preços e câmbio do primeiro dia (RF-14), verificada no teste da T-19.

## Resultado em 31/10/2026 (PTAX de venda 5,4212)
**`selado`:** Surging Sparks Elite Trainer Box (565630), US$ 119,88 = R$ 649,89; 1 unidade; sobra R$ 350,11 em CDI. Não existe selado entre US$ 119,88 e US$ 194,71. O mais barato que não cabe é a Half Booster Box (646039), R$ 1.055,56.

**`cesta_raras`** (custo R$ 540,92, soma dos valores arredondados por carta; sobra R$ 459,08):

| # | product_id | Carta | Raridade | US$ | R$ |
|---|---|---|---|---|---|
| 1 | 590003 | Mesprit - 204/191 | Illustration Rare | 13,33 | 72,26 |
| 2 | 589869 | Archaludon ex - 241/191 | Special Illustration Rare | 11,80 | 63,97 |
| 3 | 593855 | Alolan Exeggutor ex - 248/191 | Hyper Rare | 10,90 | 59,09 |
| 4 | 593857 | Gravity Mountain - 250/191 | Hyper Rare | 10,90 | 59,09 |
| 5 | 590057 | Slakoth - 212/191 | Illustration Rare | 10,52 | 57,03 |
| 6 | 590063 | Spheal - 199/191 | Illustration Rare | 9,58 | 51,94 |
| 7 | 593859 | Night Stretcher - 251/191 | Hyper Rare | 8,70 | 47,16 |
| 8 | 590024 | Phanpy - 205/191 | Illustration Rare | 8,19 | 44,40 |
| 9 | 589984 | Latias ex - 220/191 | Ultra Rare | 8,09 | 43,86 |
| 10 | 589865 | Appletun - 211/191 | Illustration Rare | 7,77 | 42,12 |

Não houve empate entre a 10ª e a 11ª carta; o empate entre a 3ª e a 4ª (US$ 10,90) não afeta a seleção.

## Motivo (declarado pelo aluno)
- **`selado`:** a regra literal não compra nada; a regra escolhida foge do "booster box" da spec, mas mantém o espírito de "selado" (o produto fechado de maior preço que o capital permite).
- **`cesta_raras`:** a regra literal resulta na carteira `cdi`; a regra escolhida mantém a ideia de cartas raras de maior preço, dentro do orçamento de R$ 100 por carta.

## Alternativas consideradas
- **Regra literal da spec nas duas carteiras:** rejeitada, porque as carteiras seriam idênticas à `cdi` e não diferenciariam a estratégia.

## Consequências
- Esta decisão diverge do texto de RF-13; a spec e a `tasks.md` (T-17 a T-19) serão ajustadas em commit próprio, e os testes verificam a regra escolhida.
- A `cesta_raras` não contém as 10 cartas mais caras: as 12 mais caras passam de R$ 100 e ficam de fora. Cerca de 46% do capital fica em caixa rendendo CDI, e o `selado` deixa cerca de 35%.
- O `selado` concentra o capital em um produto (1 ETB).
- Os valores em reais dependem da PTAX de 30/10 (5,4212); a reconstrução a partir do raw reproduz a seleção.

## Adendo de 23/11/2026 — unidade de seleção, primeiro dia e arredondamento

Decisão do aluno CaioBarthasar23, tomada durante a implementação da T-17 (`src/selecao_carteiras.py`, evidência em `docs/evidencias/T-17_selecao_carteiras.txt`). O ADR original não definia esses pontos.

1. **Unidade de seleção (opção c).** Uma carta ou um selado é um `product_id`. Para cada carteira, consideram-se as linhas `(product_id, acabamento)` do primeiro dia com `market_price > 0`, `tipo_produto` correto e `market_price × PTAX de venda ≤ limite`; por `product_id` fica a linha de maior `market_price` entre as elegíveis (empate de preço entre acabamentos do mesmo produto: menor nome do acabamento, hipótese, validação pendente). Um `product_id` aparece no máximo uma vez em cada carteira; depois ordena-se por `market_price` decrescente e `product_id` crescente. Motivo: coerente com "10 cartas" e evita excluir um produto por causa de um acabamento caro que não cabe no limite.
2. **Primeiro dia.** É a menor data com pelo menos um `market_price` não nulo. Se não houver nenhum `market_price` não nulo, a seleção falha com erro, e não devolve carteiras vazias, para não esconder uma coleta quebrada.
3. **Arredondamento.** A elegibilidade e o número de unidades usam o valor exato (Decimal, convertido de float por `str()`). O `custo_brl` de cada posição é `unidades × market_price × PTAX de venda` arredondado a centavos (ROUND_HALF_UP) e o caixa é o capital menos a soma dos custos arredondados; é o que reproduz os valores acima (cesta R$ 540,92 e sobra R$ 459,08).
4. **Menos de 10 cartas elegíveis na `cesta_raras`.** Compram-se as que houver e o resto fica em caixa (hipótese, validação pendente).
