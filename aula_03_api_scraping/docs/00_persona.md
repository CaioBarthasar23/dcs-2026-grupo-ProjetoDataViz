# Personas · Monitor diário de preços de livros

> **Domínio didático:** o site Books to Scrape informa que preços e avaliações
> são aleatórios; portanto, os dados não representam ofertas comerciais reais.

## P1 · Analista de compras da livraria importadora

- **Papel:** consumidor do negócio que acompanha o catálogo observado.
- **Decisão:** selecionar títulos e categorias para a lista diária de análise
  de reposição, considerando os preços em libras e a cotação coletada; a
  conversão para reais será feita na Aula 04.
- **Pergunta típica:** quais livros de Mystery em estoque têm menor preço em
  libras e qual cotação GBP/BRL foi coletada no mesmo ciclo diário?
- **Frequência:** diária, antes das 10h — hipótese — validação pendente.
- **Dor atual:** comparar manualmente preços em libras com uma cotação cambial.
- **Consequência de dado errado ou atrasado:** priorização inadequada ou análise
  diária feita com preços ou cotação desatualizados.
- **Nível técnico:** intermediário em análise de dados — hipótese — validação
  pendente.

## P2 · Operador(a) do pipeline de coleta

- **Papel:** opera a coleta diária por scraping e pela API PTAX; é acionado(a)
  quando a execução falha ou os dados esperados não chegam.
- **Decisão:** iniciar a investigação e decidir se e quando reexecutar a coleta
  para disponibilizar os dados do dia.
- **Pergunta típica:** qual etapa falhou e quais dados do ciclo diário faltam
  em `raw` ou `bronze`?
- **Frequência:** diária; plantão ou alerta noturno por falha — hipótese —
  validação pendente.
- **Dor atual:** identificar se a falha ocorreu no site, na API cambial ou na
  gravação no MinIO — hipótese — validação pendente.
- **O que pode acordá-lo(a) de madrugada:** alerta de falha na coleta diária ou
  de ausência dos dados esperados em `raw`/`bronze` — hipótese — validação
  pendente; horário de execução e política de alertas não foram definidos.
- **Consequência de dado errado ou atrasado:** dados indisponíveis para a
  análise diária ou reexecução desnecessária — hipótese — validação pendente.
- **Nível técnico:** intermediário em operação de pipelines e MinIO — hipótese
  — validação pendente.

## P3 · Engenheiro(a) de dados da Aula 04

- **Papel:** consumidor técnico dos registros JSON Lines persistidos no bucket
  `bronze`.
- **Decisão:** selecionar e validar os registros JSON Lines de `bronze` que
  serão transformados na conversão para reais da Aula 04.
- **Pergunta típica:** quais registros de livros e qual cotação GBP/BRL foram
  extraídos e estão disponíveis no bronze para o ciclo diário?
- **Frequência:** por ciclo de processamento da Aula 04 — hipótese —
  validação pendente.
- **Dor atual:** depender de registros extraídos consistentes e da cotação
  associada ao ciclo — hipótese — validação pendente.
- **Consequência de dado errado ou atrasado:** transformação incorreta ou
  processamento incompleto na Aula 04 — hipótese — validação pendente.
- **Nível técnico:** avançado em engenharia de dados — hipótese — validação
  pendente.

## Fato | Lacuna | Suposição

| Fato | Lacuna | Suposição |
|---|---|---|
| A coleta roda uma vez por dia; scraping obtém preços em libras de Books to Scrape; a API PTAX fornece GBP/BRL; `raw` guarda bytes brutos e `bronze`, JSON Lines; a conversão ocorre na Aula 04. | Horário, responsáveis, critérios de sucesso, formato dos registros e cotação PTAX escolhida não foram definidos. | Horário antes das 10h, níveis técnicos, dores operacionais e frequências além da coleta diária são hipóteses — validação pendente. |
