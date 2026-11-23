# ADR-010 — Cadastro retroativo na silver

- **Status:** aceito como hipótese, validação pendente.
- **Data:** 22/11/2026.
- **Responsável:** CaioBarthasar23.

## Contexto

Os preços de 31/10 a 11/11/2026 foram carregados do arquivo público do TCGCSV sem `products.json` (ADR-009). A silver (`src/silver.py`) processa os dias em ordem cronológica, sem consultar dias posteriores, e manda para a quarentena o preço cujo `product_id` não tem produto conhecido. Pela análise do código, os preços de 31/10 a 11/11 ficam todos em quarentena e a silver válida começa em 12/11, o que impede as perguntas 1 a 5 e as carteiras, que dependem do primeiro dia. O ensaio de reconstrução confirmará isso (hipótese, validação pendente).

## Decisão

Para as datas anteriores ao primeiro `products.json` disponível (hoje, 12/11/2026), a silver usa o cadastro mais antigo disponível apenas para associar nome, tipo e raridade ao `product_id`. Nenhum preço, câmbio ou outro valor é criado. As linhas associadas por esse cadastro levam a coluna extra `cadastro_retroativo` verdadeira; as demais, falsa, e o log informa a contagem. Preço cujo `product_id` não está nesse cadastro continua em quarentena, com o mesmo motivo de hoje. O raw não é alterado; a silver continua derivada e reconstruível. A informação é tratada como cadastro conhecido posteriormente, não como retrato do catálogo no dia. Hipótese, validação pendente.

## Alternativas consideradas

- **Deixar a lacuna:** rejeitada; perde 12 dias e deixa o primeiro dia da carteira sem dados.
- **Recuperar `products.json` dos dias passados:** rejeitada; o arquivo diário público só contém preços e o ADR-009 excluiu `products.json` dos dias retroativos.
- **Tratar o cadastro de 12/11 como retrato presumido do dia:** rejeitada; afirmaria uma observação que não existiu.

## Consequências

- Nome, tipo e raridade de 31/10 a 11/11 vêm de um cadastro observado depois; produto que mudou de nome ou raridade nesse intervalo, ou que deixou de existir, aparece com o cadastro posterior ou fica em quarentena. A marca `cadastro_retroativo` torna isso visível.
- Mudança pequena em `src/silver.py` (código existente, ADR-001), com teste novo (T-35). O contrato comum da turma continua válido, porque colunas extras são permitidas.
- A declaração dos dias retroativos e da marca entra no README.

## Requisitos relacionados

RNF-06 e RNF-01; T-35.
