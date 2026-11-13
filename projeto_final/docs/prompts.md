# Registro de prompts

**Data:** 2026-11-10.
- **Quem enviou: CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/00_persona.md`.
- **Confirmação do plano:**

Prompt 1: persona
[C] Personagem
Você é um analista de requisitos de engenharia de dados que trabalha com um aluno de MBA. Nesta etapa você só descreve pessoas e problemas. Você não propõe tecnologia, não escreve código e não executa comandos.
[R] Pedido
Preencha docs/00_persona.md para o projeto_final: uma base de preços diários de cartas Pokémon TCG e de produtos selados da coleção SSP (SV08: Surging Sparks, groupId 23651), que alimenta um dashboard em reais. Descreva uma persona principal: o colecionador brasileiro que compra cartas e produtos selados em dólar para guardar e quer saber onde o dinheiro dele rende mais. Use a tabela que já existe no arquivo. Se o arquivo não tiver tabela, crie uma com as linhas: Quem é; Decisão que toma; Frequência de consulta; Dor atual; O que o impede hoje de decidir com dado; Como saberia que deu certo.
[E] Exemplos
Linha bem escrita:
| Dor atual | Vê o preço de hoje em dólar, mas não sabe se a carta que comprou subiu por causa da carta ou do câmbio, nem se o selado guardou valor melhor que as cartas avulsas. |
Linha mal escrita (não faça assim):
| Dor atual | Precisa de uma solução escalável de análise de preços. |
[A] Ajustes
Use somente as informações deste prompt, de AGENTS.md e dos fatos listados em Extras.
Não invente números (quantidade de cartas, valor investido, frequência, tempo). Onde faltar um valor, escreva "hipótese: validação pendente".
Não cite produtos ou ferramentas nas linhas de dor e de sucesso; a persona fala do problema dela.
Preencha "Fatos, lacunas e suposições" com pelo menos três linhas, cada fato com a origem.
Não crie nem altere outros arquivos.
[T] Tipo de saída
Somente docs/00_persona.md, em Markdown, com no máximo uma página. Antes de editar, mostre em tópicos o que vai escrever e espere minha confirmação.
[E] Extras
Leia antes: AGENTS.md e docs/00_persona.md.
Fatos do contexto (origem: enunciado do projeto final):
o colecionador mora no Brasil e os preços do TCGplayer chegam em dólar, uma vez por dia, sem histórico na fonte;
o valor em reais mistura o que veio da carta e o que veio do dólar;
a decisão em jogo é onde aplicar dinheiro: cartas avulsas, produto selado, dólar parado ou CDI;
a série cobre cerca de sete semanas, o que descreve o período mas não sustenta previsão nem recomendação de compra;
o preço de mercado vem de vendas recentes nos Estados Unidos e não inclui frete, taxas nem preço no Brasil;
o dashboard mostra evidência; quem decide é o colecionador.
Se faltar informação para uma linha, pergunte antes de supor. Ao terminar, liste as perguntas abertas e pare.

**Data:** 2026-11-10.
- **Quem enviou: CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/01_objetivos_negocio.md`.
- **Confirmação do plano:** Confirmado pelo aluno.

Prompt 2: objetivos de negócio
[C] Personagem
Você é um product owner técnico de uma equipe de dados. Você traduz a dor da persona em objetivos de negócio mensuráveis, drivers e restrições. Você não escreve requisitos técnicos nem código.
[R] Pedido
Preencha docs/01_objetivos_negocio.md a partir de docs/00_persona.md. Escreva exatamente estes sete objetivos, cada um com métrica de sucesso e origem:
OBJ-01 saber quais cartas da coleção mais valorizaram e mais desvalorizaram em reais desde o início da coleta, separando o efeito da carta, do câmbio e o efeito cruzado (pergunta 1);
OBJ-02 saber se o produto selado guardou valor melhor que as cartas avulsas na coleção (pergunta 2);
OBJ-03 saber se a coleção valorizou mais ou menos que as outras da turma (pergunta 3);
OBJ-04 saber onde está concentrado o valor de cada coleção (pergunta 4);
OBJ-05 saber quais cartas da turma deram mais retorno para o risco assumido (pergunta 5);
OBJ-06 saber se uma carteira de R$ 1.000 em cartas ou selados ganhou do dólar parado e do CDI (desafio da carteira);
OBJ-07 manter uma série diária contínua e verificável: bruto imutável, camadas reconstruíveis, lacunas declaradas.
Liste também os drivers de negócio, as restrições e o que fica fora do escopo.
[E] Exemplos
| OBJ-07 | A série diária de preços, de PTAX e de CDI não tem buracos escondidos e pode ser reconstruída. | Zero objetos do bruto sobrescritos; todo dia sem coleta aparece no README com data e motivo. | Persona: dor "não sei se o dado é confiável" (hipótese: validação pendente) |
| RES-02 | Escrita só no prefixo da própria coleção | técnica | Enunciado: "Cada aluno escreve somente nos prefixos da própria coleção" |
[A] Ajustes
Cada objetivo precisa de uma métrica verificável. Se o valor não estiver nos fatos abaixo, escreva "hipótese: validação pendente" e diga como medir.
Restrições têm tipo (técnica, financeira, legal, prazo) e origem.
Fora do escopo, inclua pelo menos: previsão de preço, recomendação de compra, preço praticado no Brasil (frete, impostos, spread de cartão) e dados em tempo real.
Preserve a persona; não altere docs/00_persona.md.
Não escolha tecnologia além das que estão nas restrições.
[T] Tipo de saída
Somente docs/01_objetivos_negocio.md, em Markdown, com tabelas. Mostre o plano antes de editar e espere confirmação.
[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md.
Fatos e restrições (origem: enunciado do projeto final):
Fonte principal: TCGCSV, sem chave, atualizado por volta de 20h UTC; exige User-Agent próprio, pausa mínima de 100 ms entre chamadas e no máximo 10.000 requisições por dia; uma coleção usa três chamadas por dia.
PTAX e CDI do Banco Central, sem chave; a PTAX só existe em dia útil; o CDI de um dia útil só aparece na manhã seguinte.
Scraping só vale se robots.txt e termos permitirem; contornar bloqueio anti-robô está fora do escopo.
Silver no contrato comum da turma; o dashboard lê a silver dos colegas.
Mentoria em 05/12/2026; entrega até 12/12/2026, 23h59.
Taxa de venda de 15% é hipótese a declarar em ADR.
Chave do RustFS fora do Git.
Se faltar informação, pergunte. Ao terminar, liste perguntas abertas e pare.



**Data:** 2026-11-11.
- **Quem enviou: CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/spec.md`.
- **Confirmação do plano:** confirmado pelo aluno.

Prompt 3: especificação
[C] Personagem
Você é um engenheiro de requisitos de dados. Você escreve requisitos funcionais e não funcionais com critérios de aceite verificáveis. Você não escreve código e só cita tecnologia quando ela já é uma restrição em docs/01_objetivos_negocio.md.
[R] Pedido
Escreva specs/spec.md para o projeto_final, derivando os requisitos de docs/00_persona.md e docs/01_objetivos_negocio.md. Cubra no mínimo:
coleta diária de produtos, preços, PTAX e CDI no bruto, com chave por coleção e data, sem sobrescrever, e repetida no mesmo dia sem duplicar;
respeito às regras de uso do TCGCSV (User-Agent próprio, pausa mínima, limite diário);
dia sem coleta declarado como lacuna, sem preencher com dado inventado;
silver no contrato comum da turma, com validação, quarentena com motivo e contagem no log; nulo não é zero;
silver e gold reconstruíveis a partir do bruto com um único comando;
gold em esquema estrela com fato de preço diário e dimensões de produto, coleção, data e acabamento, e fato de câmbio diário;
conversão para reais pela última PTAX conhecida, sem usar cotação posterior ao dia do preço, com teste de unidade para a semana de 09/10 a 13/10;
decomposição da variação em efeito da carta, do câmbio e cruzado;
dashboard com as cinco perguntas em reais e chave para dólar, imagem e link do produto, filtros de preço mínimo em dólar e Code Card fora das perguntas 1, 3 e 4;
desafio da carteira com cinco carteiras, compra pela PTAX de venda, venda pela PTAX de compra, unidades inteiras, sobra em caixa rendendo CDI, taxa de venda como parâmetro, último preço observado marcado, CDI só em dia útil e resultado no contrato comum;
teste de que a composição da cesta de raras não muda quando dias posteriores entram na silver;
escrita somente no prefixo da própria coleção e segredos fora do Git;
README com o comando que roda o pipeline, e testes que passam.
[E] Exemplos
RF-02: bruto imutável e idempotente
O coletor grava a resposta original de cada fonte sem alterá-la e sem sobrescrever objetos existentes.
Origem: OBJ-07
Critério de aceite:
Dado um objeto raw/tcgplayer/group_id=23651/data=AAAA-MM-DD/prices.json já existente
Quando o coletor for executado de novo no mesmo dia
Então a segunda execução termina com código 0, não regrava o objeto e o log diz "ja existia"
RNF-03: nulo não é zero
Atributo: integridade dos dados
Origem: OBJ-01
Critério de aceite:
Dado um preço de mercado ausente na fonte
Quando a silver for reconstruída
Então o campo market_price fica nulo e o produto não entra em média nem em variação
[A] Ajustes
Numere RF-01, RF-02... e RNF-01, RNF-02...; cada requisito tem origem em um OBJ, restrição ou fato do enunciado.
Todo critério de aceite usa Dado/Quando/Então e pode ser verificado por um comando ou teste.
Não invente números. Valor ausente = "hipótese: validação pendente". Hipóteses de docs/ continuam hipóteses aqui.
Inclua "Fora do escopo" coerente com docs/01_objetivos_negocio.md.
Estado atual: src/collector.py e src/silver.py já existem, escritos antes desta especificação. A spec descreve o comportamento esperado, sem declarar nada como atendido; o estado real vai para a rastreabilidade.
[T] Tipo de saída
Somente specs/spec.md, em Markdown. Mostre a lista de RF e RNF (só títulos) antes de escrever e espere confirmação.
[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md.
Fato adicional (origem: execução real em 07/11/2026): a PTAX devolve o último boletim como "Fechamento PTAX", e um filtro que esperava o texto "Fechamento" ignorou cinco dias úteis. Considere um RNF de tolerância a variação no texto da fonte.
Se algum objetivo não gerar requisito, explique por quê. Ao terminar, liste perguntas abertas e pare.

**Data:** 2026-11-11.
- **Quem enviou: CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/plan.md`.
- **Confirmação do plano:** “pode seguir com o sugerido”; interpretação de “variáveis do GitHub” como GitHub Secrets confirmada pelo aluno.

Prompt 4: plano e arquitetura
[C] Personagem
Você é um arquiteto de software de dados. Você transforma a spec em arquitetura, justificando cada escolha por um requisito ou restrição. Você não escreve código nesta etapa.
[R] Pedido
Escreva specs/plan.md com:
C4 nível 1 (contexto) e nível 2 (contêineres), em blocos Mermaid, com o RustFS da turma e as silvers dos colegas como sistemas externos;
tabela de escolhas técnicas: escolha, alternativas consideradas, requisito ou restrição, ADR previsto;
fluxo de dados do bruto ao dashboard, com as camadas raw, silver e gold e quem as escreve;
riscos técnicos iniciais e perguntas abertas.
O plano deve conter estas decisões, já tomadas pelo aluno:
agendador no GitHub Actions, uma execução diária às 18h30 de Brasília, com tentativas de reserva (o TCGCSV atualiza por volta das 17h);
coletor e silver em Python, com requests, boto3, Pydantic e Parquet;
gold em DuckDB lendo o Parquet do RustFS;
dashboard em Streamlit;
credenciais em variáveis do GitHub e no .env local, nunca em arquivo versionado;
classificação carta/selado derivada da fonte (Code Card como carta, excluída por raridade);
coleta retroativa da PTAX permitida por ser registro público por data.
Os sistemas externos são TCGCSV, API PTAX do Banco Central, SGS do Banco Central, RustFS da turma e a silver dos colegas.
[E] Exemplos
flowchart LR
tcg["TCGCSV"] --> col["Coletor diário"]
col --> raw[("raw no RustFS")]
| Escolha | Alternativas | Requisito/restrição | ADR |
| Chave de objeto por coleção e data | chave só por data; sobrescrever o arquivo do dia | RF-02, OBJ-07 | ADR-001 |
[A] Ajustes
Os nomes usados nos diagramas são exatamente os nomes usados no texto.
Toda escolha técnica aponta para RF, RNF ou restrição; escolha sem origem fica marcada "sem requisito correspondente".
Para cada decisão relevante, liste pelo menos duas alternativas descartadas e o motivo.
Não acrescente componentes que a spec não pede (streaming, fila, banco de dados extra).
[T] Tipo de saída
Somente specs/plan.md, em Markdown com blocos ```mermaid. Mostre a lista de seções antes de escrever e espere confirmação.
[E] Extras
Leia antes: AGENTS.md, docs/00_persona.md, docs/01_objetivos_negocio.md, specs/spec.md, specs/plan.md.
Os ADRs serão escritos na etapa 7; aqui apenas indique o número previsto: ADR-001 chave por coleção e data, ADR-002 camadas derivadas e reconstruíveis, ADR-003 esquema estrela na gold; acrescente os que encontrar (classificação carta/selado, regra da carteira própria, taxa de venda).
Se uma decisão acima contradisser a spec, aponte a contradição e pergunte. Pare ao final.

**Data:** 2026-11-11.
- **Quem enviou: CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/tasks.md`.
- **Confirmação do plano:** confirmado pelo aluno.

Prompt 5: tarefas
[C] Personagem
Você é o líder técnico do aluno. Você quebra o plano em tarefas pequenas, cada uma com requisito, verificação executável e evidência esperada.
[R] Pedido
Escreva specs/tasks.md a partir de specs/spec.md e specs/plan.md. Inclua no mínimo tarefas para:
coletor diário idempotente; agendamento no GitHub Actions; silver no contrato comum com quarentena; coleta retroativa da PTAX; gold em esquema estrela; conversão para reais com ASOF JOIN e teste de 09/10 a 13/10; decomposição carta/câmbio; as cinco carteiras e as métricas; dashboard das perguntas 1, 2 e 4; dashboard das perguntas 3 e 5; painel da carteira e placar da turma; README com o comando do pipeline.
Separe as tarefas manuais do aluno (criar o .env, cadastrar os secrets no GitHub, conferir as pastas no bucket).
[E] Exemplos
| T-03 | Silver reconstruída por um único comando | RF-05, RNF-03 | python -m src.silver rebuild --fonte local --destino local, duas vezes | as duas execuções produzem os mesmos arquivos; quarentena contada no log | [ ] |
[A] Ajustes
Cada tarefa cabe num único prompt de implementação e toca poucos arquivos.
Cada RF e RNF é coberto por pelo menos uma tarefa, ou aparece em "sem tarefa" com o motivo.
Tarefas que descrevem código já existente (coletor, silver) ficam [ ] com a nota "código existente; evidência pendente".
Marque as tarefas que gravam no bucket compartilhado.
Indique a ordem de execução e as dependências. Todas começam com status [ ].
[T] Tipo de saída
Somente specs/tasks.md, em Markdown, com a tabela do modelo. Mostre a lista de tarefas antes de escrever e espere confirmação.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md, specs/plan.md, specs/tasks.md.
Os scripts leem S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY e S3_BUCKET do .env, conforme .env.example. Pare ao final.

**Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/01_objetivos_negocio.md`.
- **Confirmação do plano:** confirmado pelo aluno.

Prompt 2b: ajuste dos objetivos com as definições do enunciado

[C] Personagem
Você é um product owner técnico. Está corrigindo docs/01_objetivos_negocio.md, que marcou como "hipótese" definições que o enunciado já traz.
[R] Pedido
Atualize os objetivos OBJ-01 a OBJ-06 com as definições abaixo (origem: enunciado do projeto final, seção das cinco perguntas e do desafio da carteira). Troque "hipótese: validação pendente" por essas definições, com origem, e mantenha a marca de hipótese só no que continuar sem origem (taxa de venda de 15%, regra da carteira propria).
Fatos:
- P1: variação percentual em reais entre o primeiro e o último dia, por carta e acabamento, só cartas acima de US$ 1 no primeiro dia; decomposição (1+r_brl) = (1+r_usd) × (1+r_cambio): efeito da carta, do câmbio e cruzado; Code Card fora.
- P2: índice base 100 no primeiro dia: média dos selados contra a soma do preço das cartas de raridade Double Rare em diante.
- P3: valor da coleção no dia em reais (soma do market_price_brl de um exemplar de cada carta), índice base 100 por coleção, com a PTAX em base 100 no mesmo gráfico; Code Card fora.
- P4: participação de cada raridade no valor total no último dia e número de cartas que somam 80% do valor; Code Card fora.
- P5: retorno no período contra volatilidade (desvio-padrão dos retornos diários), cartas acima de US$ 5.
- Dashboard: valores em reais e chave para ver em dólar; imagem das cartas e link do produto no TCGplayer; filtros de preço mínimo em dólar.
- Carteiras (cinco): selado, cesta_raras, propria, dolar, cdi. Métricas: retorno acumulado, excesso sobre o CDI, perda máxima, dias com preço carregado. Valor de liquidação = unidades × market_price × (1 − taxa de venda) × PTAX de compra + sobra em caixa rendendo CDI. O dashboard mostra o resultado com e sem a taxa; a diferença entra no ATAM como ponto de sensibilidade.
[A] Ajustes
Preserve os IDs, os drivers, as restrições e o fora do escopo. Não altere outros arquivos.
[T] Tipo de saída
Somente docs/01_objetivos_negocio.md. Mostre em tópicos o que vai mudar e espere minha confirmação antes de editar.
[E] Extras
Leia antes: AGENTS.md e docs/01_objetivos_negocio.md. Ao terminar, liste perguntas abertas e pare.

**Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/spec.md`.
- **Confirmação do plano:** "Confirmado. Pode editar. Escreva a chave como R$/US$. Em RF-11, a P3 deve citar a PTAX em base 100 no mesmo gráfico e a P4 o número de cartas que somam 80% do valor."

Prompt 3b: ajuste da especificação com as definições do enunciado
[C] Personagem
Você é um engenheiro de requisitos de dados. Está corrigindo specs/spec.md, que tratou como hipótese definições que o enunciado já traz e leu "chave para dólar" como identificador do produto.
[R] Pedido
Ajuste specs/spec.md com os fatos abaixo (origem: enunciado do projeto final e docs/01_objetivos_negocio.md já corrigido). Preserve os IDs RF-01 a RF-15 e RNF-01 a RNF-05; novos requisitos entram no fim, como RF-16.
Mudanças:
1. RF-11: reescreva as cinco perguntas com as definições de OBJ-01 a OBJ-05 (P1 variação percentual em reais por carta e acabamento, cartas acima de US$ 1 no primeiro dia; P2 índice base 100, média dos selados contra soma das cartas Double Rare em diante; P3 valor da coleção em reais, índice base 100 por coleção, com a PTAX em base 100 no mesmo gráfico; P4 participação de cada raridade no último dia e número de cartas que somam 80% do valor; P5 retorno contra desvio-padrão dos retornos diários, cartas acima de US$ 5). Remova as hipóteses de agregação, retorno e risco.
2. RF-10: a fórmula é (1+r_brl) = (1+r_usd) × (1+r_cambio): efeito da carta, do câmbio e cruzado. Remova a hipótese da fórmula; o tratamento de preço ausente segue a regra nulo não é zero.
3. RF-12: "chave" é o alternador para ver os valores em dólar, não identificador. O dashboard tem valores em reais e a chave R$/US$; imagem da carta e link do produto no TCGplayer; product_id como identificador. Filtros de preço mínimo em dólar: P1 acima de US$ 1 no primeiro dia e P5 acima de US$ 5. Code Card fica fora das perguntas 1, 3 e 4. Reescreva o critério de aceite.
4. RF-13: as cinco carteiras são selado, cesta_raras, propria, dolar e cdi (dólar parado e CDI são duas das cinco, não referências extras). Regras: selado = unidades inteiras do booster box, ou o selado de maior preço se o box não tiver preço no primeiro dia (escolha em ADR); cesta_raras = R$ 100 em cada uma das dez cartas de maior market_price no primeiro dia, em unidades inteiras; propria = regra do aluno em ADR com commit anterior ao primeiro cálculo (hipótese: validação pendente); dolar = R$ 1.000 pela PTAX de venda do primeiro dia; cdi = R$ 1.000 corrigidos pelo CDI de cada dia útil, juros compostos. Valor de liquidação = unidades × market_price × (1 − taxa de venda) × PTAX de compra + sobra em caixa rendendo CDI. Produto sem preço no dia usa o último preço observado; o painel marca esses dias e nada inventado é gravado na silver. Métricas: retorno acumulado, excesso sobre o CDI, perda máxima, dias com preço carregado. O dashboard mostra o resultado com e sem a taxa. Resultado no contrato comum tcg/gold_turma/carteira/: data DATE, group_id INTEGER, carteira VARCHAR, valor_brl DOUBLE, retorno_acumulado DOUBLE, taxa_venda DOUBLE. A taxa de 15% continua hipótese a declarar em ADR.
5. RF-09: o ano da semana de 09/10 a 13/10 é 2026 (decisão do aluno em 11/11/2026; 12/10/2026 é segunda-feira e feriado nacional, então a semana testa fim de semana e feriado). Remova a hipótese do ano e ajuste a origem para OBJ-01 a OBJ-06 e RF-08.
6. RF-16 (novo): a silver classifica cada produto como carta ou selado a partir dos campos da fonte; produto com número de carta é carta e sem número é selado; Code Card (raridade) é carta e fica excluído das perguntas 1, 3 e 4 pela raridade. Origem: decisão do aluno no plano, comportamento do código existente em src/silver.py; o método exato será confirmado no ADR-005. Escreva Dado/Quando/Então.
[A] Ajustes
Todo critério de aceite usa Dado/Quando/Então verificável. Hipótese só onde falta origem. Não toque em docs/ nem em outros arquivos. Não declare nada como atendido.
[T] Tipo de saída
Somente specs/spec.md. Mostre em tópicos o que vai mudar e espere minha confirmação antes de editar.
[E] Extras
Leia antes: AGENTS.md, docs/01_objetivos_negocio.md e specs/spec.md. Ao terminar, liste perguntas abertas e pare.

**Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/plan.md`.
- **Confirmação do plano:** confirmado pelo aluno.

Prompt 4b: ajuste do plano com as decisões já definidas
[C] Personagem
Você é um arquiteto de software de dados. Está corrigindo specs/plan.md depois que docs/01_objetivos_negocio.md e specs/spec.md foram ajustados com as definições do enunciado. Você não escreve código.
[R] Pedido
Ajuste specs/plan.md. Preserve as seções, os nomes dos elementos nos diagramas, os ADRs previstos (ADR-001 reservado à origem do código; ADR-002 a ADR-008) e os riscos que continuam válidos.
Mudanças:
1. C4 nível 2 e fluxo de dados: remova as relações em que o Agendador GitHub Actions dispara a silver e a gold. A decisão do aluno é o agendador disparar a coleta; silver e gold rodam pelo comando único de RF-06. Quando e onde ele roda continua pergunta aberta.
2. Tentativas de reserva: registre o estado do workflow existente: execuções às 21:30, 22:30 e 23:30 UTC (18:30, 19:30 e 20:30 de Brasília); o coletor é idempotente e recusa gravar preço do TCGCSV e fechamento da PTAX antes das 18h de Brasília; no máximo nove chamadas ao TCGCSV por dia, abaixo do limite de 10.000. Origem: workflow coleta-diaria.yml existente; ADR-008 confirma.
3. Perguntas abertas já respondidas: tire da lista o ano do teste (2026, RF-09), as cinco carteiras (selado, cesta_raras, propria, dolar, cdi, RF-13), as fórmulas e agregações dos OBJ-01 a OBJ-05 (definidas no enunciado), a quantidade de reservas (item 2) e a classificação no contrato comum (o contrato permite colunas extras; categoria_selado existe em src/silver.py). Mantenha abertas: local e ciclo de vida da gold e como o dashboard a consulta; regra da carteira propria e taxa de 15% (hipóteses); campos exatos da classificação (ADR-005).
4. Tabela de escolhas: cada decisão relevante com pelo menos duas alternativas reais descartadas e o motivo, em vez de alternativas sem substância. Para DuckDB, Streamlit, Parquet e Pydantic liste alternativas reais (por exemplo: pandas, banco relacional; Dash, Metabase; CSV, JSON; validação manual). Sem requisito que as torne obrigatórias, marque "sem requisito correspondente" e não invente justificativa. Não acrescente componentes que a spec não pede.
5. Aponte RF-16 (classificação) na escolha de ADR-005 e RF-12 (chave R$/US$) no dashboard.
6. Riscos: remova "hipóteses de agregação, risco e decomposição não validadas"; mantenha só regra da propria e taxa de venda como hipóteses.
[A] Ajustes
Use somente docs/, specs/spec.md e AGENTS.md. Não altere outros arquivos. Os nomes nos diagramas e no texto continuam idênticos.
[T] Tipo de saída
Somente specs/plan.md, em Markdown com blocos mermaid. Mostre em tópicos o que vai mudar e espere minha confirmação antes de editar.
[E] Extras
Leia antes: AGENTS.md, docs/01_objetivos_negocio.md, specs/spec.md e specs/plan.md. Ao terminar, liste perguntas abertas e pare.

**Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/tasks.md`.
- **Confirmação do plano:** confirmado

Prompt 5b: ajuste das tarefas com as definições do enunciado
[C] Personagem
Você é o líder técnico do aluno. Está corrigindo specs/tasks.md depois que docs/01_objetivos_negocio.md, specs/spec.md e specs/plan.md foram ajustados com as definições do enunciado.
[R] Pedido
Ajuste specs/tasks.md. Preserve os IDs T-01 a T-28, as duas tabelas e a tabela de cobertura; todas as tarefas continuam [ ]. Mudanças:
1. Definições já dadas pelo enunciado: remova de T-12 a T-16 as dependências "validar antes a fórmula/critério/definição de OBJ-0x" e use as definições de OBJ-01 a OBJ-05 e RF-10/RF-11 da spec. Em T-10, tire a dependência de T-09 (o teste usa dados fixos) e fixe 09/10 a 13/10/2026 (RF-09).
2. Dashboard (T-20 a T-24): inclua a chave R$/US$ (alternador da moeda), imagem, link do produto no TCGplayer e product_id. Filtros: P1 acima de US$ 1 no primeiro dia; P5 acima de US$ 5; P2 só cartas Double Rare em diante; P3 e P4 sem filtro de preço. Code Card fora de P1, P3 e P4. P3 mostra a PTAX em base 100 no mesmo gráfico; P4 mostra a participação por raridade e o número de cartas que somam 80%.
3. Carteiras (T-17, T-18, T-25): as cinco são selado, cesta_raras, propria, dolar e cdi (dólar parado e CDI são duas das cinco). T-18 calcula valor de liquidação com e sem taxa e as métricas retorno acumulado, excesso sobre o CDI, perda máxima e dias com preço carregado, no contrato tcg/gold_turma/carteira/ (data, group_id, carteira, valor_brl, retorno_acumulado, taxa_venda). T-26 (placar): em quantas coleções o selado ganhou do CDI, em quantas a cesta_raras ganhou do dolar, e qual coleção teve a carteira com menor perda máxima.
4. Tarefas manuais novas, na tabela do aluno: T-29 escrever e commitar o ADR-006 (regra da carteira propria) antes de T-17; T-30 escrever o ADR-007 (taxa de venda, hipótese de 15%) antes de T-18; T-31 escrever o ADR-001 (origem do código de src/collector.py e src/silver.py, escritos antes da spec). Ajuste as dependências de T-17 e T-18.
5. Código existente, nota "código existente; evidência pendente": mantenha em T-06 e T-08 e acrescente em T-07 (workflow coleta-diaria.yml existente), T-09 (backfill-ptax existente) e T-10 (reconhecimento do rótulo "Fechamento PTAX" existente no coletor; o ASOF JOIN ainda não existe). Em T-02 registre que os três secrets foram criados no repositório do grupo em 11/11/2026, com evidência pendente (gh secret list).
6. Verificação das tarefas de código existente: use os testes que já existem (tests/test_collector.py para T-06, tests/test_silver.py para T-08; 41 testes passaram em 11/11/2026 numa execução real, a saída entra em docs/evidencias/). Crie arquivos de teste novos só onde falta cobertura; diga qual é qual.
7. T-08: inclua RF-16 (classificação carta/selado, Code Card como carta) e a coluna extra categoria_selado. T-07: troque "definir quantidade e horários" pelo estado do workflow existente (21:30, 22:30 e 23:30 UTC; ADR-008 confirma). T-27: registre que o comando src.pipeline precisa ser acrescentado à lista de comandos permitidos de AGENTS.md por decisão do aluno.
8. Atualize a tabela de cobertura com RF-09, RF-16 e as novas tarefas; cada RF e RNF coberto por pelo menos uma tarefa.
[A] Ajustes
Cada tarefa cabe num prompt de implementação e toca poucos arquivos. Todas começam [ ]; não declare nada como atendido. Não toque em outros arquivos. Não invente números.
[T] Tipo de saída
Somente specs/tasks.md. Mostre em tópicos o que vai mudar e espere minha confirmação antes de editar.
[E] Extras
Leia antes: AGENTS.md, docs/01_objetivos_negocio.md, specs/spec.md, specs/plan.md e specs/tasks.md. Ao terminar, liste perguntas abertas e pare.

**Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/adr/ADR-001-origem-do-codigo-existente.md`.
- **Confirmação do plano:** confirmado pelo aluno, com ajuste na seção Decisão.

Prompt 6 (T-31): ADR-001, origem do código existente
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-31 (specs/tasks.md): escrever o ADR-001 sobre a origem do código existente. Você só escreve documentação; não altera código, testes, workflow nem outros ADRs.
[R] Pedido
Escreva docs/adr/ADR-001-origem-do-codigo-existente.md. Leia a linha da T-31 em specs/tasks.md e siga a verificação dela. Estrutura do ADR: título, status, data, responsável, contexto, decisão, alternativas consideradas e descartadas (pelo menos duas, com motivo), consequências, requisitos relacionados.
Fatos (origem: histórico real do aluno, não invente nada além deles):
- O TCGCSV não guarda histórico: cada dia sem coleta é perdido e não pode ser recuperado depois. Por isso a coleta começou antes da persona e da especificação.
- A primeira coleta está em data=2026-10-31 no bucket tcg, prefixo group_id=23651. A coleta diária roda pelo GitHub Actions desde então, primeiro no repositório individual do aluno e, a partir de 11/11/2026, neste repositório (commit 1c45944).
- src/collector.py foi escrito a partir de 31/10/2026 e ajustado em 07/11/2026 (correção do filtro da PTAX "Fechamento PTAX", comando backfill-ptax). src/silver.py foi escrito em 10/11/2026. Ambos foram escritos com ajuda do assistente Claude (Anthropic), em conversas fora do fluxo SDD deste repositório.
- Migração para projeto_final/: commits 4e203be (coletor), 6dc3e03 (silver), b91faed (README) e 1c45944 (workflow), em 11/11/2026, com a evidência pendente. Numa execução real em 11/11/2026, 41 testes passaram (10 do coletor e 31 da silver); a saída ainda precisa ser guardada em docs/evidencias/.
- A spec descreve o comportamento esperado e não declara nada como atendido; o estado real vai para a rastreabilidade (etapa ATAM).
- Risco: a disciplina pode exigir especificação antes do código. O aluno perguntou ao professor se o código anterior é aceito quando declarado em ADR; a resposta está pendente (registre como pendente, não como aceita).
- Responsável: CaioBarthasar23.
[A] Ajustes
Não reescreva a cronologia nem esconda que o código veio antes. Não afirme que o código atende a algum requisito. Sem segredos, sem valores de credenciais. Não crie outros arquivos nem altere os existentes.
[T] Tipo de saída
Somente docs/adr/ADR-001-origem-do-codigo-existente.md, em Markdown. Mostre em tópicos o que vai escrever e espere minha confirmação antes de criar o arquivo.
[E] Extras
Leia antes: AGENTS.md (seção "Estado atual"), specs/tasks.md (T-31) e specs/plan.md (nota sobre ADR-001). Se faltar informação, pergunte. Ao terminar, mostre o resultado da verificação da T-31 e pare.

**Data:** 2026-11-11.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `src/prefixo.py`, `src/collector.py`, `tests/test_prefix_isolation.py`, `tests/test_collector.py` e `docs/evidencias/T-04_prefixo.txt`.
- **Confirmação do plano:** confirmado pelo aluno. Depois da implementação, o aluno autorizou ajustar somente as chaves de dois testes antigos (`test_nao_sobrescreve_objeto_existente` e `test_upload_nao_sobrescreve`), que gravavam chaves sem `group_id` e passaram a ser recusadas pela nova regra.

Prompt 7 (T-04): proteger a escrita para aceitar somente o prefixo da coleção SSP
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-04 (specs/tasks.md): proteger a escrita para aceitar somente o prefixo da coleção SSP. Requisitos: RNF-03 e RF-02. Uma tarefa, um prompt: não mexa em mais nada.
[R] Pedido
Implemente a proteção e o teste, nesta ordem: primeiro o teste que falha, depois o código que o faz passar.
1. Crie src/prefixo.py, um módulo pequeno com a constante do prefixo próprio (group_id=23651, fixa no código, independente da variável de ambiente GROUP_ID) e uma função que recebe uma chave de objeto e levanta erro claro se a chave não pertencer a esse prefixo. Regra: a chave precisa conter o segmento group_id=23651 e nenhum outro segmento group_id=<outro número>. Chave sem group_id também é recusada.
2. Em src/collector.py, aplique a função em todo ponto que grava: LocalStorage.put, S3Storage.put e a rotina que sobe do disco para o bucket (subir_local). A recusa acontece antes de qualquer gravação ou chamada ao bucket. Se GROUP_ID do ambiente for diferente de 23651, o coletor recusa e termina com código diferente de zero, com mensagem clara, sem gravar nada.
3. Crie tests/test_prefix_isolation.py com, no mínimo: chave própria aceita; chave de outra coleção (por exemplo group_id=24269) recusada em LocalStorage e em S3Storage (com cliente falso, comprovando que o cliente nunca é chamado); subir_local não envia chave de outra coleção; GROUP_ID de outra coleção no ambiente faz o coletor recusar. Use cliente falso e pasta temporária; nenhum teste usa rede nem o bucket real.
4. Não altere src/silver.py (a proteção da silver entra na T-08, que reutiliza src/prefixo.py). Não altere o workflow nem outros testes.
[E] Exemplos
Linha de log ao recusar: ERRO escrita recusada: raw/tcgplayer/group_id=24269/data=2026-11-11/prices.json fora do prefixo group_id=23651
[A] Ajustes
Não leia nem imprima .env. Não rode collect, upload, backfill-ptax nem rebuild --destino s3. Comandos permitidos: python -m pytest e python -m src.collector check. Sem segredos em código, testes ou evidências. Todos os 41 testes existentes devem continuar passando. Não faça git commit nem git push: proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivos: src/prefixo.py (novo), src/collector.py (alterado), tests/test_prefix_isolation.py (novo). Mostre o plano em tópicos e espere minha confirmação antes de editar. Depois de implementar, rode python -m pytest tests/test_prefix_isolation.py e python -m pytest, e salve a saída real em docs/evidencias/T-04_prefixo.txt, incluindo o caso que rejeita o prefixo de outra coleção. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RNF-03, RF-02), specs/tasks.md (T-04) e src/collector.py. Ao terminar, liste perguntas abertas e pare.

Resposta do aluno ao plano do Codex:
Confirmado. Pode seguir. Na mensagem de commit proposta, cite os dois requisitos: feat(T-04): restringe escrita ao prefixo SSP [RNF-03][RF-02].

Resposta do aluno à pergunta do Codex sobre os dois testes antigos que falharam:
Autorizo ajustar somente esses dois testes antigos, e só o valor das chaves: troque raw/x.json, raw/a.json e raw/b.json por chaves SSP válidas (por exemplo raw/tcgplayer/group_id=23651/data=2026-11-11/x.json). Não altere as verificações nem o comportamento testado, e não toque em nenhum outro teste. Depois refaça a execução completa e regrave docs/evidencias/T-04_prefixo.txt com a saída real (esperado: 48 passed). Na mensagem de commit proposta, mencione o ajuste: feat(T-04): restringe escrita ao prefixo SSP, ajusta chaves de 2 testes [RNF-03][RF-02].

**Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `tests/test_secrets_not_versioned.py` e `docs/evidencias/T-05_segredos.txt`.
- **Confirmação do plano:** confirmado pelo aluno. O teste parou duas vezes com achados que o aluno avaliou como falsos positivos e orientou o ajuste do detector: placeholder em pasta de aula fora do escopo e referência a variável de ambiente no workflow; depois, o nome do parâmetro `aws_secret_access_key` recebendo uma variável em `src/collector.py`.

Prompt 8 (T-05): impedir que credenciais ou .env sejam versionados ou impressos
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-05 (specs/tasks.md): impedir que credenciais ou .env sejam versionados ou impressos em evidências e logs. Requisitos: RNF-04 e RES-06. Uma tarefa, um prompt: não mexa em mais nada.
[R] Pedido
Crie tests/test_secrets_not_versioned.py. Escreva o teste primeiro e rode-o; se algum caso falhar por um problema real, pare e me mostre o achado: não corrija em silêncio e não altere src/ nem o workflow.
Casos mínimos:
1. O .env de projeto_final está ignorado pelo Git (git check-ignore -q projeto_final/.env, que funciona mesmo se o arquivo não existir) e não consta em git ls-files.
2. Arquivos rastreados (git ls-files, só texto; exclua o próprio arquivo de teste) não contêm credencial: atribuição não vazia a S3_ACCESS_KEY, S3_SECRET_KEY ou nomes com SECRET, PASSWORD ou TOKEN; padrão de chave AWS (AKIA seguido de 16 caracteres); linhas aws_secret_access_key. No workflow, S3_ACCESS_KEY, S3_SECRET_KEY e S3_ENDPOINT só podem aparecer como ${{ secrets.NOME }}.
3. .env.example só tem nomes: toda variável com KEY, SECRET, PASSWORD ou TOKEN no nome tem valor vazio.
4. Verificação estática em src/: nenhuma linha com log.*, logging.* ou print( referencia S3_SECRET_KEY, S3_ACCESS_KEY ou as variáveis que guardam esses valores.
5. docs/evidencias/ (arquivos rastreados e novos) passa na mesma varredura do caso 2.
Os casos de varredura devem ser testados também contra texto de exemplo com uma credencial falsa embutida no próprio teste (por exemplo SEGREDO-FALSO-123), para provar que o detector detecta; essa credencial falsa não pode ser um valor real.
[A] Ajustes
Não leia, não imprima e não abra o .env, nem para comparar valores. Rode os testes com PYTHON_DOTENV_DISABLED=true. Não rode collect, upload, backfill-ptax nem rebuild --destino s3. Comandos permitidos: python -m pytest e git status, git diff, git log, git ls-files, git check-ignore. Não faça git commit nem git push: proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivos: tests/test_secrets_not_versioned.py (novo) e docs/evidencias/T-05_segredos.txt (saída real de python -m pytest tests/test_secrets_not_versioned.py e de python -m pytest, sem nenhum valor secreto). Mostre o plano em tópicos e espere minha confirmação antes de editar. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md (seção Segredos), specs/spec.md (RNF-04), specs/tasks.md (T-05) e .env.example. Ao terminar, liste perguntas abertas e pare.

Respostas do aluno ao Codex:
1. Confirmado. Pode seguir. Mantenha a credencial falsa claramente fictícia (por exemplo SEGREDO-FALSO-123) e evite que o próprio arquivo de teste dispare a varredura dos outros casos.
2. Respostas: (1) Não aceite placeholders. Restrinja a varredura de arquivos rastreados a projeto_final/ e ao workflow .github/workflows/coleta-diaria.yml; pastas de aula ficam fora do escopo (AGENTS.md proíbe alterá-las). Dentro de projeto_final, o .env.example continua exigindo valores vazios nas variáveis sensíveis. (2) Sim, permita referências ao nome da variável após a atribuição, como $S3_ENDPOINT no shell, mas toda atribuição de S3_ENDPOINT, S3_ACCESS_KEY e S3_SECRET_KEY no workflow deve ser exatamente ${{ secrets.NOME }}; um valor literal reprova. Ajuste só o teste, sem alterar src/ nem o workflow, rode de novo o teste dedicado e, se passar, rode a suíte completa e grave docs/evidencias/T-05_segredos.txt. Mantenha a prova de detecção com credencial falsa: ela deve mostrar que um valor literal no workflow reprova. Mensagem de commit: feat(T-05): teste impede segredos versionados ou impressos [RNF-04].
3. O achado em src/collector.py:97 (aws_secret_access_key=secret_key) é falso positivo: o argumento

**Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `tests/test_tcgcsv_limits.py`, `docs/evidencias/T-06_testes.txt` e `docs/evidencias/T-06_coleta_duas_execucoes.txt`.
- **Confirmação do plano:** confirmado pelo aluno, incluindo as duas execuções reais de `collect` no prefixo `group_id=23651`, sem `--forcar`, conforme a autorização expressa do próprio prompt. A primeira tentativa de execução falhou por DNS antes de a rede ser liberada e não escreveu nada; foi refeita com rede.

Prompt 9 (T-06): evidência do coletor diário existente
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-06 (specs/tasks.md): dar evidência ao coletor diário existente (código existente; evidência pendente): idempotência, bruto preservado e regras de uso do TCGCSV. Requisitos: RF-01, RF-02, RF-03 e RNF-03. Uma tarefa, um prompt.
[R] Pedido
Não altere src/. Se algo reprovar por problema real do coletor, pare e me mostre o achado.
1. Rode PYTHON_DOTENV_DISABLED=true python -m pytest tests/test_collector.py e mapeie, na evidência, qual teste existente cobre qual critério de aceite de RF-01 e RF-02, apontando lacunas.
2. Crie tests/test_tcgcsv_limits.py (RF-03): toda chamada leva User-Agent próprio (diferente do padrão da biblioteca requests); a pausa mínima entre chamadas é de pelo menos 100 ms; uma execução de coletar faz no máximo 3 chamadas ao TCGCSV (registre a contagem real, que deve ser 2: products e prices); o pior caso diário com as três tentativas do workflow fica abaixo de 10.000. Use cliente falso e relógio simulado; sem rede.
3. AUTORIZAÇÃO EXPRESSA: autorizo executar python -m src.collector collect duas vezes seguidas, gravando no bucket compartilhado SOMENTE no prefixo group_id=23651, sem --forcar. Não rode upload, backfill-ptax nem rebuild. Para estas duas execuções NÃO use PYTHON_DOTENV_DISABLED (o coletor lê o .env sozinho); você não deve ler, abrir nem imprimir o .env. Confirme: código de saída zero nas duas, nenhuma chave de outra coleção, e na segunda execução todos os objetos com o log "ja existia".
[A] Ajustes
Sem segredos em testes ou evidências; não imprima endpoints nem credenciais, e se um log os contiver, remova-os da evidência e me avise. Não faça git commit nem git push: proponha as mensagens no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivos: tests/test_tcgcsv_limits.py (novo), docs/evidencias/T-06_testes.txt (saída real dos testes e o mapa de cobertura) e docs/evidencias/T-06_coleta_duas_execucoes.txt (logs reais das duas execuções e os códigos de saída). Mostre o plano em tópicos e espere minha confirmação antes de editar. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RF-01, RF-02, RF-03, RNF-03), specs/tasks.md (T-06) e src/collector.py. Ao terminar, liste perguntas abertas e pare.

Resposta do aluno ao plano do Codex:
Confirmado. Pode seguir, incluindo as duas execuções reais de collect, conforme a autorização expressa do prompt (somente prefixo group_id=23651, sem --forcar). Se algum log contiver endpoint ou credencial, remova da evidência e me avise.

**Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `specs/tasks.md` e `specs/plan.md`.
- **Confirmação do plano:** "Confirmado. Pode editar. Mantenha todas as tarefas como [ ] e os valores dos tempos limite como hipótese: validação pendente."

Prompt 10: registrar o achado do tempo limite do cliente S3 como T-32 e risco
[C] Personagem
Você é o líder técnico do aluno. Está registrando nos documentos um achado de operação observado em 11/11/2026, antes de qualquer código. Você só edita documentação.
[R] Pedido
Ajuste specs/tasks.md e specs/plan.md, nada mais.
Fato (origem: execução real #4 do workflow coleta-diaria, 11/11/2026): o passo Coletar ficou 10 minutos sem nenhum log do coletor e foi cancelado pelo timeout-minutes do workflow. As execuções normais levam entre 17 e 25 segundos. Causa provável, a confirmar: o cliente S3 do coletor (boto3) sem tempos limite explícitos aguardou o RustFS. Não houve perda de dado, porque a coleta do dia já estava completa.
1. specs/tasks.md: acrescente a tarefa T-32, com ID, tarefa, requisitos, dependências, verificação executável, evidência esperada e status [ ]. Conteúdo: definir tempos limite curtos e número limitado de tentativas no cliente S3 do coletor. Requisito: RF-01 (coleta diária confiável). Dependência: T-06. Verificação: python -m pytest tests/test_s3_timeouts.py, que confere a configuração do cliente S3 (tempo de conexão, tempo de leitura e tentativas). Os valores exatos são hipótese: validação pendente, a decidir pelo aluno no ADR-008. Evidência: saída real do teste em docs/evidencias/. Nota: código existente; mudança pequena em src/collector.py.
2. specs/tasks.md: em T-07, acrescente que revisa também o timeout-minutes do workflow (valor hipótese: validação pendente) e registre o fato de que as execuções agendadas tiveram atrasos de 36 a 56 minutos em 11/11/2026, a considerar na decisão sobre as tentativas de reserva. Inclua T-32 como dependência de T-07 quando fizer sentido. Atualize a tabela de cobertura (RF-01 passa a incluir T-32).
3. specs/plan.md: acrescente em Riscos técnicos a linha "Cliente S3 sem tempo limite pode travar a coleta", com o fato acima como origem, requisito RF-01 e mitigação T-32/T-07. Em ADR-008, acrescente a observação dos atrasos do agendador.
[A] Ajustes
Todas as tarefas continuam [ ]; não declare nada como atendido. Não invente números além dos fatos acima. Não toque em outros arquivos.
[T] Tipo de saída
Somente specs/tasks.md e specs/plan.md. Mostre em tópicos o que vai mudar e espere minha confirmação antes de editar.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RF-01), specs/tasks.md e specs/plan.md. Ao terminar, liste perguntas abertas e pare.

**Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `src/collector.py`, `tests/test_s3_timeouts.py` e `docs/evidencias/T-32_timeouts.txt`.
- **Confirmação do plano:** "Confirmado. Pode seguir. Mantenha os valores (5 s, 15 s e 2 tentativas) como hipótese: validação pendente nas constantes, com um comentário curto que aponte para o ADR-008."

Prompt 11 (T-32): tempos limite e tentativas do cliente S3
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-32 (specs/tasks.md): definir tempos limite curtos e número limitado de tentativas no cliente S3 do coletor. Requisito: RF-01 (coleta diária confiável). Origem: execução #4 do workflow em 11/11/2026, cancelada após 10 minutos sem log. Uma tarefa, um prompt.
[R] Pedido
Implemente o teste e o ajuste, nesta ordem: primeiro o teste que falha, depois o código.
1. Crie tests/test_s3_timeouts.py: construa o S3Storage do coletor com endpoint e credenciais falsos (sem rede; o cliente boto3 não conecta ao ser criado) e confira na configuração do cliente: tempo de conexão 5 s, tempo de leitura 15 s e 2 tentativas máximas no modo standard. Acrescente um teste de que um erro de tempo limite do cliente (por exemplo, ReadTimeoutError simulado) em exists() não é tratado como "objeto não existe": o erro sobe, e o coletor existente já o registra como falha da fonte sem gravar nada.
2. Em src/collector.py, ajuste somente a criação do cliente em S3Storage, mantendo as opções atuais (signature_version s3v4, addressing_style path): acrescente connect_timeout=5, read_timeout=15 e retries com max_attempts=2 e mode standard. Não altere mais nada no coletor.
3. Os valores são hipótese: validação pendente, a confirmar no ADR-008. Deixe-os em constantes nomeadas no topo de src/collector.py, para o ADR poder citá-las.
[A] Ajustes
Não altere o workflow, src/silver.py, src/prefixo.py nem outros testes. Todos os 59 testes existentes devem continuar passando. Não leia nem imprima o .env. Rode os testes com PYTHON_DOTENV_DISABLED=true. Não rode collect, upload, backfill-ptax nem rebuild. Comandos permitidos: python -m pytest e git status, git diff, git log. Não faça git commit nem git push: proponha a mensagem de commit no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivos: tests/test_s3_timeouts.py (novo), src/collector.py (alterado) e docs/evidencias/T-32_timeouts.txt (saída real de python -m pytest tests/test_s3_timeouts.py e de python -m pytest). Mostre o plano em tópicos e espere minha confirmação antes de editar. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RF-01), specs/tasks.md (T-32) e src/collector.py. Ao terminar, liste perguntas abertas e pare.

Resposta do aluno ao plano do Codex:
Confirmado. Pode seguir. Mantenha os valores (5 s, 15 s e 2 tentativas) como hipótese: validação pendente nas constantes, com um comentário curto que aponte para o ADR-008.

**Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `.github/workflows/coleta-diaria.yml`, `tests/test_workflow_schedule.py`, `tests/test_s3_timeouts.py` (correção de regressão autorizada pelo aluno) e `docs/evidencias/T-07_agenda.txt`.
- **Confirmação do plano:** confirmado pelo aluno, com a edição autorizada do workflow. Valores `timeout-minutes` 5 e a faixa 01:30 UTC como hipótese: validação pendente. Na suíte completa, o teste de segredos reprovou `tests/test_s3_timeouts.py` (valores fictícios atribuídos a `access_key` e `secret_key`); o aluno autorizou corrigir só esse teste passando os valores de forma posicional a partir de variáveis neutras, sem afrouxar o detector.

Prompt 12 (T-07): agenda do workflow com faixa de reserva e timeout de 5 minutos
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-07 (specs/tasks.md): registrar e verificar o agendamento diário do workflow coleta-diaria.yml (código existente; evidência pendente), com tentativas de reserva, e revisar o timeout-minutes. Requisitos: RF-01 e RF-03. Uma tarefa, um prompt.
[R] Pedido
Escreva o teste primeiro e rode-o para falhar; depois ajuste o workflow.
1. Crie tests/test_workflow_schedule.py, que lê .github/workflows/coleta-diaria.yml (na raiz do repositório) como TEXTO, sem biblioteca nova de YAML, e verifica: as faixas de cron são exatamente "30 21 * * *", "30 22 * * *", "30 23 * * *" e "30 1 * * *" (21:30, 22:30, 23:30 e 01:30 UTC, ou seja 18:30, 19:30, 20:30 e 22:30 de Brasília, todas no mesmo dia de Brasília, depois das 18h); workflow_dispatch presente; concurrency com cancel-in-progress falso; timeout-minutes igual a 5; S3_ENDPOINT, S3_ACCESS_KEY e S3_SECRET_KEY atribuídos somente via ${{ secrets.NOME }}; o pior caso diário de chamadas ao TCGCSV (4 execuções × 2 chamadas = 8) fica abaixo de 10.000.
2. AUTORIZAÇÃO DE ESCOPO: você pode editar .github/workflows/coleta-diaria.yml, e somente ele fora de projeto_final/. Acrescente a faixa "30 1 * * *", ajuste timeout-minutes de 10 para 5 e atualize os comentários: a faixa das 18h30 é a principal; as outras três são reservas; o GitHub atrasou execuções agendadas de 36 a 56 minutos em 11/11/2026; os valores timeout-minutes 5 e a quarta faixa são hipótese: validação pendente, a confirmar no ADR-008. Não altere mais nada no workflow.
[A] Ajustes
Não altere src/, outros testes nem outros arquivos. Todos os 61 testes existentes devem continuar passando. Não leia nem imprima o .env. Rode os testes com PYTHON_DOTENV_DISABLED=true. Não rode collect, upload, backfill-ptax nem rebuild. Comandos permitidos: python -m pytest e git status, git diff, git log. Não faça git commit nem git push: proponha as mensagens no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivos: tests/test_workflow_schedule.py (novo), .github/workflows/coleta-diaria.yml (alterado) e docs/evidencias/T-07_agenda.txt (saída real de python -m pytest tests/test_workflow_schedule.py e de python -m pytest). Mostre o plano em tópicos e espere minha confirmação antes de editar. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RF-01, RF-03), specs/tasks.md (T-07) e o workflow atual. Ao terminar, liste perguntas abertas e pare.

Respostas do aluno ao Codex:
1. Confirmado. Pode seguir, com a edição autorizada do workflow coleta-diaria.yml. Mantenha os valores timeout-minutes 5 e a faixa 01:30 UTC como hipótese: validação pendente nos comentários.
2. Autorizo alterar somente tests/test_s3_timeouts.py para corrigir a regressão: os valores fictícios devem ser passados com nomes neutros (por exemplo, valor_falso_a e valor_falso_b), sem atribuição a nomes com SECRET, KEY ou TOKEN e sem formato de credencial real. Mantenha as verificações do teste exatamente como estão. Não afrouxe o detector em tests/test_secrets_not_versioned.py. Depois: (1) rode a suíte completa e confirme que fica toda verde (esperado: 64 passed); (2) regrave docs/evidencias/T-07_agenda.txt com a saída COMPLETA, sem resumir nem omitir linhas; (3) proponha duas mensagens de commit separadas: uma para a correção do teste (fix(T-32): ...) e outra para a T-07.
Observação: access_key e secret_key são nomes da assinatura do S3Storage, então passe os valores fictícios de forma posicional, a partir de variáveis neutras, e não como argumentos nomeados.

**Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/evidencias/T-08_silver_dados_reais.txt`.
- **Confirmação do plano:** confirmado pelo aluno, com a autorização expressa de `rebuild --fonte s3 --destino local` (lê o bucket, não escreve nele). O Codex parou ao encontrar `data_local/` já existente; o aluno orientou usar destinos novos por execução via `LOCAL_ROOT`. A primeira resposta do aluno foi recusada pelo agente por um filtro de segurança indevido e foi reenviada em versão curta. Uma tentativa terminou por erro de DNS e deixou saída parcial em `data_local/silver_t08_a`; o aluno autorizou os destinos `silver_t08_a_retry` e `silver_t08_b_retry`.

Prompt 13 (T-08, parte 1): evidência da silver existente sobre dados reais
[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano. Hoje é a T-08, parte 1 (specs/tasks.md): dar evidência à silver existente (código existente; evidência pendente) no contrato comum, com quarentena, motivo e contagem. Requisitos: RF-05, RF-06, RF-16, RNF-01 e RNF-05. Uma tarefa, um prompt.
[R] Pedido
Não altere src/. Se algo reprovar por problema real da silver, pare e me mostre o achado, sem corrigir.
1. Rode PYTHON_DOTENV_DISABLED=true python -m pytest tests/test_silver.py e mapeie, na evidência, qual teste existente cobre qual critério de aceite de RF-05, RF-16 (carta, selado, Code Card como carta, coluna extra categoria_selado) e RNF-01 (nulo não é zero), apontando as lacunas.
2. AUTORIZAÇÃO EXPRESSA: autorizo executar python -m src.silver rebuild --fonte s3 --destino local duas vezes. Isso LÊ o bucket compartilhado (raw, prefixo group_id=23651) e grava somente em disco local (data_local/, ignorada pelo Git). NÃO grave no bucket: não use --destino s3 e não rode collect, upload nem backfill-ptax. Para estas execuções NÃO use PYTHON_DOTENV_DISABLED (a leitura do bucket precisa das credenciais); você não deve ler, abrir nem imprimir o .env.
3. Registre, para cada execução: código de saída, contagem por tabela (colecao, produto, preco_diario, cambio_diario, cdi_diario), contagem em quarentena com os motivos, e a soma de verificação (sha256) de cada arquivo gerado. Compare as duas execuções: os mesmos arquivos e o mesmo conteúdo derivado. Se os bytes dos Parquets diferirem só por metadados, compare o conteúdo das tabelas (por exemplo, com pyarrow) e explique.
4. Confira com dados reais: cambio_diario só tem dia útil com PTAX de fechamento; cdi_diario sem duplicata por data; preços nulos continuam nulos (nenhum zero inventado); Code Card classificado como carta. Se PTAX ou CDI forem para a quarentena por nome de campo diferente do esperado, esse é um achado: pare e mostre o motivo.
[A] Ajustes
Sem segredos em evidências: não imprima endpoints nem credenciais, e se um log os contiver, remova da evidência e me avise. Não faça git commit nem git push: proponha as mensagens no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivo: docs/evidencias/T-08_silver_dados_reais.txt (saídas reais dos testes, do mapa de cobertura e das duas reconstruções, com contagens, quarentena, somas de verificação e a comparação). Mostre o plano em tópicos e espere minha confirmação antes de executar. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RF-05, RF-06, RF-16, RNF-01, RNF-05), specs/tasks.md (T-08) e src/silver.py. Ao terminar, liste perguntas abertas e pare.

Respostas do aluno ao Codex:
1. Confirmado. Pode executar, incluindo as duas reconstruções autorizadas (--fonte s3 --destino local, sem escrever no bucket). Acréscimo: confirme que a pasta local de destino não existia antes da primeira execução (registre isso) e remova SOMENTE essa pasta local de destino entre as duas execuções, para provar que a silver se reconstrói do bruto sem depender de camada anterior. Não apague nada fora dela.
2. Não apague nada. Use um destino novo e vazio por execução, via variável LOCAL_ROOT: primeira reconstrução com LOCAL_ROOT=data_local/silver_t08_a e segunda com LOCAL_ROOT=data_local/silver_t08_b (ambas dentro de data_local/, que o Git ignora). Antes de cada execução, confirme e registre que a pasta ainda não existe. Não toque em nada que já esteja em data_local/. Mantenha o restante da autorização: python -m src.silver rebuild --fonte s3 --destino local, duas vezes, sem escrever no bucket, sem PYTHON_DOTENV_DISABLED nas reconstruções. Compare os resultados das pastas a e b (arquivos, somas de verificação e, se os bytes diferirem, o conteúdo das tabelas). Ajuste o texto da evidência: a pré-condição agora é "a pasta de destino de cada execução não existia".
3. Use silver_t08_a_retry e silver_t08_b_retry.

D*Data:** 2026-11-12.
- **Quem enviou:** CaioBarthasar23.
- **Agente e modelo:** Codex, GPT-6.
Arquivos alterados: docs/evidencias/T-06_coleta_duas_execucoes.txt (nota ao final) e docs/evidencias/T-06_coleta_bucket_real.txt (novo)
Confirmação do plano: “Confirmado. Execute o plano.”
Resultado: as duas coletas e o check falharam por NameResolutionError; a idempotência no bucket não foi comprovada

[C] Personagem
Você é o engenheiro que executa uma única tarefa do plano: corrigir a evidência da T-06 (specs/tasks.md). Requisitos: RF-02 e RNF-03.
[R] Pedido
Não altere src/. Fato: as duas execuções de collect da T-06 foram feitas com STORAGE=local (valor do .env do Codespace) e gravaram em data_local/, não no bucket. Prova: a execução agendada de 12/11 às 22:15 UTC registrou "gravado" para as mesmas quatro chaves, que não existiam no bucket.
1. Acrescente ao FINAL de docs/evidencias/T-06_coleta_duas_execucoes.txt, sem apagar nem reescrever o que já está lá, uma nota de correção datada: as duas execuções acima foram em armazenamento local (STORAGE=local); não comprovam a idempotência no bucket; a evidência no bucket está em docs/evidencias/T-06_coleta_bucket_real.txt.
2. AUTORIZAÇÃO EXPRESSA: autorizo executar duas vezes seguidas STORAGE=s3 python -m src.collector collect (a variável na linha de comando prevalece sobre o .env), gravando no bucket compartilhado SOMENTE no prefixo group_id=23651, sem --forcar. Não rode upload, backfill-ptax nem rebuild. Não use PYTHON_DOTENV_DISABLED nessas execuções (precisam das credenciais). Você não deve ler, abrir nem imprimir o .env.
3. Grave em docs/evidencias/T-06_coleta_bucket_real.txt: o comando de cada execução (com STORAGE=s3), o código de saída, os logs com o status por chave, a confirmação de que todas as chaves estão em group_id=23651 e, depois, a saída de python -m src.collector check (somente leitura).
[A] Ajustes
Sem segredos em evidências: não imprima endpoints nem credenciais; se um log os contiver, remova da evidência e me avise. Não faça git commit nem git push: proponha as mensagens no formato tipo(T-xx): descrição [RF-yy].
[T] Tipo de saída
Arquivos: docs/evidencias/T-06_coleta_duas_execucoes.txt (nota ao final) e docs/evidencias/T-06_coleta_bucket_real.txt (novo). Mostre o plano em tópicos e espere minha confirmação antes de executar. Não declare sucesso sem mostrar a saída.
[E] Extras
Leia antes: AGENTS.md, specs/spec.md (RF-02, RNF-03), specs/tasks.md (T-06) e docs/evidencias/T-06_coleta_duas_execucoes.txt. Ao terminar, liste perguntas abertas e pare.