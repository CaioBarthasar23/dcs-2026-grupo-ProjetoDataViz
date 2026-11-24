# ADR-011 — Valor das carteiras ao longo do tempo

- **Status:** aceito como hipótese, validação pendente.
- **Data:** 24/11/2026.
- **Responsável:** CaioBarthasar23.

## Contexto

A T-18 calcula o valor de liquidação diário das cinco carteiras (`selado`, `cesta_raras`, `propria`, `dolar`, `cdi`), com e sem taxa de venda (RF-13). A composição vem da T-17 (ADR-005, ADR-006) e a taxa vem do ADR-007, mas esses textos não definiam a grade de datas, quando o CDI começa a render, a fórmula da perda máxima nem o que fazer quando faltam dados. O aluno decidiu esses pontos em 24/11/2026, na confirmação do plano da T-18. Implementação: `src/valor_carteiras.py`; evidência: `docs/evidencias/T-18_valor_carteiras.txt`. Relacionados: ADR-005, ADR-006, ADR-007.

## Decisão

1. **Grade de datas.** Uma linha por data distinta de `preco_diario` maior ou igual à data inicial da composição. Datas que existem só em `cambio_diario` ou só em `cdi_diario` não criam linhas. Dia sem coleta é lacuna declarada, nunca preenchido.
2. **CDI.** `taxa_dia` está em percentagem ao dia; o fator do dia é `1 + taxa_dia / 100`. A sobra e a carteira `cdi` rendem apenas as taxas com data maior que a data inicial e menor ou igual à data da linha. A taxa do próprio dia inicial não conta; dia sem taxa publicada (fim de semana, feriado) não rende.
3. **Taxa de venda.** Incide só nas posições de carta e selado, sobre `unidades × market_price × PTAX de compra`. As carteiras `dolar` e `cdi` e a sobra em caixa não pagam taxa; para `dolar` e `cdi` as variantes com e sem taxa dão o mesmo valor (ver adendo ao ADR-007).
4. **Preço ausente.** Só `market_price` nulo ou linha ausente conta como ausente (nulo não é zero). Usa-se o último preço conhecido até o dia e o dia da carteira é marcado como preço carregado. `dias_preco_carregado` conta dias por carteira, no máximo uma vez por dia.
5. **Perda máxima.** Maior queda percentual entre um pico anterior e o vale seguinte da série `valor_brl` da carteira, por variante de taxa, como fração positiva (0 quando não há queda). O módulo `src/retorno_risco.py` calcula retorno e desvio-padrão, não perda máxima, e não foi alterado.
6. **Dados que faltam.** Sem PTAX de compra por ASOF para uma data, sem nenhum preço conhecido para uma posição, sem `data_inicial` na composição ou com `group_id` misto, a função levanta `ValueError`, sem inventar valor.

## Resultado

Conferência com a silver local (somente leitura), de 31/10/2026 (sábado) a 21/11/2026 (sábado), sem dias com preço carregado nas cinco carteiras:

| Carteira | Sem taxa: primeiro → último | Com taxa de 15%: primeiro → último |
|---|---|---|
| selado | R$ 999,93 → R$ 1.069,15 | R$ 902,46 → R$ 961,64 |
| cesta_raras | R$ 999,95 → R$ 1.051,72 | R$ 918,82 → R$ 963,28 |
| propria | R$ 999,92 → R$ 1.079,51 | R$ 891,37 → R$ 959,29 |
| dolar | R$ 999,89 → R$ 1.086,16 | R$ 999,89 → R$ 1.086,16 |
| cdi | R$ 1.000,00 → R$ 1.006,62 | R$ 1.000,00 → R$ 1.006,62 |

O último dia usa a PTAX de compra de 19/11/2026 (5,8883), a última de fechamento conhecida. O fator de CDI acumulado de 03/11 a 19/11 (13 dias úteis, `taxa_dia` de 0,050788 em todos) é 1,0066226. As carteiras `dolar`, `selado` e `cdi` foram refeitas por fora, com consulta direta à silver, e bateram. Os valores do primeiro dia ficam abaixo de R$ 1.000 pelo spread entre PTAX de venda e de compra e, com taxa, pelos 15%. A silver local termina em 21/11; dias posteriores só entram quando a silver for reconstruída.

## Motivo

- Grade só com dias de preço: não inventa dias em que não houve coleta, e câmbio e CDI entram por ASOF e por acumulação.
- CDI sem a taxa do dia inicial: convenção conservadora, o capital começa a render a partir do dia útil seguinte (hipótese, validação pendente).
- Taxa só nas posições: a taxa de venda é cobrada ao vender cartas e selados; `dolar` e `cdi` não vendem nada no TCGplayer.
- Perda máxima como queda de pico a vale: medida usual de pior perda sobre a série, sem exigir outra fórmula que o projeto não define.
- `ValueError` em vez de valor inventado: nulo não é zero e dado ausente não é preenchido.

## Alternativas descartadas

- Grade pela união das datas de preço, câmbio e CDI: criaria linhas sem preço observado.
- Preencher dia sem coleta com o último valor: seria dado inventado.
- Taxa também na sobra ou nas carteiras `dolar` e `cdi`: não há venda nelas.
- Contar a taxa CDI do dia inicial: o capital ainda não esteve aplicado naquele dia.

## Consequências e limites

- Todas as regras acima são hipótese, validação pendente, inclusive a taxa de 15% (ADR-007) e a PTAX e o CDI da silver local, que não foram validados contra o BCB.
- A publicação em `tcg/gold_turma/carteira/` não faz parte da T-18 até aqui; as colunas `excesso_sobre_cdi` e `preco_carregado` são extras ao contrato.
- Arredondamento implementado: `valor_brl` a centavos (ROUND_HALF_UP) e retornos a seis casas decimais; escolhido na implementação, a validar.
