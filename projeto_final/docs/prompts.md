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