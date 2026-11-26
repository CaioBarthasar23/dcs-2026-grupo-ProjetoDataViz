# ADR-012 — Dashboard da pergunta 1: fonte, alternador US$, ranking e Code Card

* **Status:** confirmado pelo aluno (CaioBarthasar23) em 26/11/2026.
* **Data:** 25/11/2026
* **Decisor:** CaioBarthasar23 (responsável pendente de confirmação do professor)
* **Tarefa e requisitos:** T-20; RF-10, RF-11, RF-12; RNF-01; OBJ-01
* **Origem do código:** `dashboard/` e `tests/test\_dashboard\_q1.py` foram escritos pelo agente Codex (GPT-6-Luna default) no Prompt 41, sob as decisões abaixo; dois testes de borda foram acrescentados pelo agente revisor, sem novo prompt (`docs/evidencias/T-20\_dashboard\_q1.txt`). A ordenação foi corrigida após a revisão de 25/11/2026 pelo agente opencode, DeepSeek V4.1 Flash Free (Prompt 43; o Prompt 42, com outro modelo, foi descartado).

## Contexto

A T-20 entrega a primeira tela: ranking das cartas por variação de valor, decomposição em efeito da carta, do câmbio e cruzado, alternador R$/US$, e para cada carta `product\_id`, imagem e link do TCGplayer. A spec não fixa a fonte local dos dados, o tamanho do ranking nem a semântica do alternador na decomposição. Essas lacunas foram fechadas por decisão do aluno, registradas aqui.

## Decisões

1. **Fonte dos dados (hipótese, validação pendente).** O dashboard lê somente `data\_local/silver` (raiz como parâmetro), com leitura própria em duckdb (`dashboard/common.py`, `carregar\_silver`), converte com `src.fx\_asof.converter\_precos` e calcula com `src.decomposicao.decompor\_variacao`. Não usa `src.gold.build` (que grava) nem função privada. Não há persistência do gold. A fonte em produção fica para a T-27. As pastas `data\_local/silver\_t08\_\*` são cópias de teste e nunca são lidas.
2. **Streamlit 1.67.0** em `requirements-gold.txt`, importado apenas em `dashboard/app.py`. `common.py` e `p1.py` são funções puras, testáveis sem servidor.
3. **Grão e ordenação.** Uma linha por (`product\_id`, `acabamento`). O ranking ordena por **variação percentual** (RF-10 e RF-11 pedem variação percentual em reais), maiores altas em ordem decrescente e maiores quedas pela mais negativa, empate por `product\_id` e depois por `acabamento`; a variação absoluta segue exibida, sem ordenar. **Correção após revisão (26/11/2026):** a primeira versão ordenava por variação absoluta em R$, o que divergia do texto do RF-10/RF-11; o aluno decidiu corrigir (opção B).
4. **Alternador US$ (hipótese, validação pendente).** Em US$, a variação é preço final menos preço inicial em dólar; a percentual é essa variação sobre o preço inicial em dólar; efeito do câmbio e efeito cruzado valem `None`, exibidos como "não se aplica"; o ranking em US$ ordena pela variação percentual em dólar. Em R$ vale a decomposição de `decompor\_variacao`, sem alteração.
5. **Tamanho do ranking (hipótese, validação pendente, sem origem na spec).** 10 maiores altas e 10 maiores quedas; o 10 é parâmetro (`tamanho`), não valor fixo.
6. **Filtro de preço.** Entram só cartas com preço estritamente maior que US$ 1 no primeiro dia (`limite\_usd=1.0`; exatamente US$ 1,00 fica fora, conforme `decomposicao.py`).
7. **Code Card fora.** Constante `RARIDADE\_CODE\_CARD = "Code Card"` em `dashboard/common.py`, com comentário apontando `silver.py:125`, `concentracao\_valor.py:104` e `decomposicao.py:52`. A exclusão é explícita no preparo do dashboard e as excluídas são contadas. Como `decompor\_variacao` também exclui Code Card, existe defesa em duas camadas; o teste exige que a mutação remova as duas.
8. **Nulo não é zero.** Preço inicial ou final ausente exclui a comparação e é contado por motivo (`preco\_inicial\_nulo`, `preco\_final\_nulo`); nunca se usa preço de outra data nem zero. O período é do primeiro ao último dia disponível; não há seleção de datas.

## Resultado (31/10 a 21/11/2026, `data\_local/silver`)

|Item|Valor|
|-|-|
|Comparações elegíveis (acima de US$ 1, sem Code Card)|60|
|Excluídas: filtro de US$ 1 / preço inicial nulo / preço final nulo / Code Card|357 / 0 / 0 / 10|
|Soma dos três efeitos contra a variação total|erro máximo 2,6e-16|
|Efeito do câmbio (todas as cartas, R$)|8,63% (PTAX 5,4206 → 5,8883, conferida à parte)|
|Maior alta (por percentual, em R$)|589983, Holofoil: +R$ 31,13 (+88,22%)|
|Maior queda (por percentual, em R$)|589857, Holofoil: −R$ 6,84 (−17,95%)|
|Mudança em relação ao ranking absoluto anterior|R$: 8 das 20 cartas saíram; US$: 9 das 20|
|Testes|14 do dashboard; suíte com 247 passando|

Contagens e valores acima vêm da saída real em `docs/evidencias/T-20\_dashboard\_q1.txt`; as capturas estão em `docs/evidencias/T-20\_captura\_brl.png` e `T-20\_captura\_usd.png`.

## Motivo 

Ler a silver local mantém a tela reproduzível sem rede nem bucket enquanto a fonte em produção não existe (T-27); o ranking de 10 mantém a tela legível; "não se aplica" evita mostrar zero onde o conceito não existe.

## Alternativas consideradas

* Montar o fato com `src.gold.build`: descartada porque grava e a T-20 não autoriza persistência.
* Mostrar efeito de câmbio igual a zero em US$: descartada, nulo não é zero.
* Ordenar por variação absoluta em R$: foi a primeira versão; descartada após a revisão porque o RF-10/RF-11 pedem variação percentual.

## Limites e pendências conhecidos

* O bloco "Exclusões" aparece como JSON cru e mistura unidades: `filtro\_usd\_1` conta combinações (357) e `code\_card` conta produtos (10).
* No modo R$, uma comparação descartada pela decomposição por falta de conversão some sem ser contada.
* Sem `st.cache\_data`: a silver é relida a cada clique no alternador.
* Com a ordenação percentual e o piso estrito de US$ 1, três cartas baratas (589892, 589911 e 590019, entre US$ 1,03 e US$ 1,50, variações de R$ 1,42 a R$ 1,53) entram nas maiores altas. É consequência da spec; vale perguntar ao professor se o corte de US$ 1 é o desejado.
* Fonte em produção e os números 10 e US$ 1 seguem como **hipótese, validação pendente** até confirmação em spec ou com o professor.

