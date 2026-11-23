# ADR-007 — Taxa de venda de 15% na liquidação das carteiras

- **Status:** aceito como hipótese, validação pendente.
- **Data:** 22/11/2026.
- **Responsável:** CaioBarthasar23.

## Contexto

A liquidação das carteiras (RF-13 e RF-14, tarefa T-30) aplica uma taxa de venda ao valor de mercado dos itens. O aluno decidiu em 22/11/2026 manter 15%. Relacionado: ADR-005 (seleção das carteiras).

## Decisão
A taxa de venda é o parâmetro `taxa_venda`, com valor padrão de 0,15 (15%), aplicado ao valor de mercado dos itens na liquidação: `unidades × market_price × (1 − taxa_venda) × PTAX de compra + caixa`. O valor usado vai na coluna `taxa_venda` do contrato da gold.

## Origem do número (hipótese, validação pendente)
Os 15% são uma aproximação, não uma taxa observada. Base: tabela de taxas do TCGplayer, página https://help.tcgplayer.com/hc/en-us/articles/201357836-Fees, consultada em 22/11/2026:
- Vendedor Marketplace (níveis 1–4): comissão de 10,75% do subtotal, limitada a US$ 75 por produto.
- Vendedor Pro: comissão de 9,25% mais taxa Pro de 2,5%.
- Processamento do pagamento (doméstico): 2,5% do total do pedido mais US$ 0,30 por pedido.

Taxa efetiva calculada sobre o preço dos itens (sem frete e sem imposto), para o que as carteiras compram:
- ETB de US$ 119,88: 13,5% (nível 1–4) e 14,5% (Pro).
- Cesta de 10 cartas (US$ 99,78) vendida num único pedido: 13,6% e 14,6%.
- Cada carta em pedido separado: de 15,5% a 17,1% (nível 1–4), por causa dos US$ 0,30 fixos.

Os 15% ficam no meio dessa faixa (13,5% a 18%) e servem como valor redondo conservador.

## Limites
- A leitura da página foi automática; conferir os números na página antes de citá-los como fonte.
- A página registra mudanças de taxas em junho de 2026 sem informar os valores novos.
- Não está definido se o vendedor seria nível 1–4 ou Pro.
- Frete e comissão sobre frete, imposto de renda sobre ganho de capital e custos de câmbio no Brasil não estão no modelo.
- Não está confirmado que um vendedor no Brasil teria estas taxas.

## Consequências
- A taxa é parâmetro: o resultado das carteiras muda com ela. Prevê-se rodar a análise também com 10% e 20% para mostrar a sensibilidade.
