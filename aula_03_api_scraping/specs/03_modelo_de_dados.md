# Modelo de dados · Monitor de preços

## Premissas

- Os nomes definidos para os campos JSONL são contratos com as Aulas 04 e 05; não devem ser renomeados nem traduzidos.
- Os arquivos JSONL contêm estritamente os campos listados em seus contratos; a data de referência permanece no manifesto e nas chaves dos objetos.
- Chaves de objetos brutos derivam de fonte, data de referência, recurso e SHA-256 do corpo; não contêm ID de execução. O manifesto é o único objeto cuja chave inclui esse ID.
- A mesma resposta na mesma fonte/data/recurso gera a mesma chave e pode ser reutilizada; conteúdo diferente gera chave distinta. Objetos brutos existentes não são alterados.
- Os exemplos de origem, códigos HTTP, tamanhos e SHA-256 correspondem a respostas públicas inspecionadas em 02/11/2026. A observação PTAX é o fechamento de 30/10/2026 para uma janela até 02/11/2026. O ID de execução e instantes explicitamente ilustrativos não descrevem uma execução real.
- `avaliacao` conserva o rótulo original (`One` a `Five`), sem conversão numérica. `qtd_estoque` é nulo se a página não informar quantidade numérica.

## Layout de chaves

| Tipo | Convenção | Exemplo |
|---|---|---|
| Página inicial bruta | `raw/books_toscrape/data=<data_ref>/recurso=inicio/sha256=<sha256>.html` | `raw/books_toscrape/data=2026-11-02/recurso=inicio/sha256=9fdd63da34161ebd13408d7a85105f83ec3c9f351c5d77cd0aa578790e121c1e.html` |
| Página de categoria bruta | `raw/books_toscrape/data=<data_ref>/categoria=<slug>/pagina=<numero>/sha256=<sha256>.html` | `raw/books_toscrape/data=2026-11-02/categoria=mystery_3/pagina=001/sha256=ff899bea5c8806ecd24542d7a195899ad46eeb9a12d4fbfc79a9ed6be9faf2a2.html` |
| Detalhe de livro bruto | `raw/books_toscrape/data=<data_ref>/livro=<slug>/detalhe/sha256=<sha256>.html` | `raw/books_toscrape/data=2026-11-02/livro=sharp-objects_997/detalhe/sha256=41ae9ef1bc17c9984b8e452c61f3370fc6e1868e9b699c803c7336136f57c0ef.html` |
| Resposta de `robots.txt` | `raw/books_toscrape/data=<data_ref>/recurso=robots.txt/sha256=<sha256>.html` | `raw/books_toscrape/data=2026-11-02/recurso=robots.txt/sha256=6ad407809dc8e6d079dfbd21823508dffb897b97a27eb8ae43acbea1b7c8df0d.html` (HTTP 404; corpo da resposta preservado) |
| Resposta bruta PTAX | `raw/ptax/moeda=<moeda>/data=<data_ref>/janela=<inicio>_<fim>/sha256=<sha256>.json` | `raw/ptax/moeda=GBP/data=2026-11-02/janela=10-30-2026_11-02-2026/sha256=62d766ca2186571e1026473571e75fabdcb740ba3c9ae44a51bdf2be97b78cbf.json` |
| Manifesto da execução | `raw/manifestos/data=<data_ref>/execucao=<id>.json` | `raw/manifestos/data=2026-11-02/execucao=<id>.json` (ID ilustrativo; somente esta chave contém ID de execução) |
| Livros extraídos do dia | `bronze/books_toscrape/data=<data_ref>/livros.jsonl` | `bronze/books_toscrape/data=2026-11-02/livros.jsonl` |
| Cotações extraídas do dia | `bronze/ptax/moeda=<moeda>/data=<data_ref>/cotacoes.jsonl` | `bronze/ptax/moeda=GBP/data=2026-11-02/cotacoes.jsonl` |

O nome de recurso, categoria, moeda e data localizam a resposta lógica; `sha256` distingue corpos diferentes e torna a chave content-addressed. O manifesto referencia a chave bruta de cada item. Resultados `bronze` são a visão diária corrente e são substituídos na reexecução conforme RF-15.

## Dicionário do bronze

### `livros.jsonl`

Uma linha representa a observação diária de um livro. Origem do exemplo: livro “Sharp Objects”, UPC `e00eb4fd7b871a48`, observado na categoria Mystery.

| Campo | Tipo | Nulo? | Origem | Exemplo | Regra |
|---|---|---:|---|---|---|
| `upc` | string | Não | Detalhe: `table.table-striped tr` com cabeçalho `UPC`, valor da célula seguinte | `e00eb4fd7b871a48` | RN-01 |
| `url` | string (URL absoluta) | Não | Listagem: `article.product_pod h3 a[href]`; resolver o `href` contra a URL da listagem | `https://books.toscrape.com/catalogue/sharp-objects_997/index.html` | RN-11 |
| `titulo` | string | Não | Listagem: `article.product_pod h3 a[title]`, atributo `title` | `Sharp Objects` | RN-11 |
| `categoria` | string | Não | Detalhe: `ul.breadcrumb li:nth-child(3) a`, texto | `Mystery` | RN-11 |
| `avaliacao` | string (`One`…`Five`) | Não | Listagem: classe de `article.product_pod p.star-rating` | `Four` | RN-11 |
| `preco_gbp` | decimal | Não | Listagem: `article.product_pod p.price_color`, remover símbolo `£` sem conversão cambial | `47.82` | RN-11 |
| `em_estoque` | boolean | Não | Detalhe: `div.product_main p.availability`; verdadeiro se contém `In stock`, falso se informa indisponibilidade | `true` | RN-11 |
| `qtd_estoque` | inteiro | Sim | Detalhe: mesma disponibilidade; extrair o número de `(<n> available)` | `20` | RN-11 |
| `coletado_em` | timestamp ISO 8601 UTC | Não | Instante em que a resposta do detalhe foi recebida, registrado no item do manifesto | `2026-11-02T03:56:00Z` (formato ilustrativo) | RN-03, RN-11 |

### `cotacoes.jsonl`

Uma linha representa a cotação de fechamento selecionada para a data de referência. Os campos mantêm exatamente a grafia do contrato, inclusive `dataHoraCotacao`.

| Campo | Tipo | Nulo? | Origem | Exemplo | Regra |
|---|---|---:|---|---|---|
| `moeda` | string | Não | Parâmetro `moeda` da consulta PTAX; não é retornado em cada item do JSON | `GBP` | RN-02 |
| `dataHoraCotacao` | timestamp conforme JSON PTAX | Não | Campo JSON `value[].dataHoraCotacao` | `2026-10-30 13:04:18.706316` | RN-02 |
| `tipoBoletim` | string | Não | Campo JSON `value[].tipoBoletim`; somente o fechamento elegível é selecionado | `Fechamento` | RN-02 |
| `cotacaoCompra` | decimal | Não | Campo JSON `value[].cotacaoCompra` | `7.2609` | RN-02 |
| `cotacaoVenda` | decimal | Não | Campo JSON `value[].cotacaoVenda` | `7.2633` | RN-02 |

Se não houver fechamento elegível, não se escreve linha de cotação fictícia: a execução fica incompleta e registra a ausência (RF-08, RF-12).

## Manifesto da execução

O manifesto é JSON e possui um cabeçalho por execução e um item por recurso consultado. Horários usam ISO 8601 UTC; `data_ref` usa o calendário local de São Paulo.

| Parte | Campo | Tipo | Nulo? | Significado |
|---|---|---|---:|---|
| Cabeçalho | `id` | string | Não | Identificador único da execução; compõe somente a chave do manifesto |
| Cabeçalho | `inicio` | timestamp ISO 8601 UTC | Não | Início da execução |
| Cabeçalho | `fim` | timestamp ISO 8601 UTC | Não | Término da execução, inclusive incompleta |
| Cabeçalho | `data_ref` | date ISO 8601 | Não | Data de referência local |
| Cabeçalho | `robots_txt` | objeto | Não | `url`, `status_http`, `chave`, `sha256` e `consultado_em`; campos de corpo/hash podem ser nulos se não houve resposta com corpo |
| Cabeçalho | `sources` | lista de strings | Não | Fontes consultadas, sem duplicatas |
| Cabeçalho | `escopo` | objeto | Não | `tipo` (`completo` ou `filtrado`) e categorias solicitadas; lista vazia quando todas as categorias são coletadas |
| Cabeçalho | `total_declarado` | inteiro | Sim | Total informado para o escopo; nulo se a fonte não declarou total |
| Cabeçalho | `estado` | string | Não | `sucesso`, `incompleta` ou `falha` |
| Itens | `url` | string | Não | URL consultada |
| Itens | `estado` | string | Não | Estado atual/final: `pendente`, `baixando`, `aguardando`, `baixado`, `gravado` ou `falhou` |
| Itens | `chave` | string | Sim | Chave do objeto bruto; nula se nenhum corpo foi recebido/preservado |
| Itens | `status_http` | inteiro | Sim | Código HTTP final; nulo se não houve resposta HTTP |
| Itens | `tentativas` | inteiro | Não | Número de tentativas realizadas para o recurso |
| Itens | `bytes` | inteiro | Não | Tamanho do corpo recebido; zero se nenhum corpo foi recebido |
| Itens | `sha256` | string hexadecimal de 64 caracteres | Sim | Hash do corpo bruto; nulo se não houve corpo |
| Itens | `erro` | string | Sim | Erro final em texto sem credenciais; nulo quando não houve erro |

Exemplo abreviado de estrutura:

```json
{
  "id": "execucao-demo-20261102",
  "inicio": "2026-11-02T03:56:00Z",
  "fim": "2026-11-02T04:14:00Z",
  "data_ref": "2026-11-02",
  "sources": ["books.toscrape.com", "PTAX"],
  "escopo": {
    "tipo": "filtrado",
    "categorias": ["mystery_3"]
  },
  "robots_txt": {
    "url": "https://books.toscrape.com/robots.txt",
    "status_http": 404,
    "chave": "raw/books_toscrape/data=2026-11-02/recurso=robots.txt/sha256=6ad407809dc8e6d079dfbd21823508dffb897b97a27eb8ae43acbea1b7c8df0d.html",
    "sha256": "6ad407809dc8e6d079dfbd21823508dffb897b97a27eb8ae43acbea1b7c8df0d",
    "consultado_em": "2026-11-02T03:56:00Z"
  },
  "total_declarado": 1000,
  "estado": "sucesso",
  "itens": [
    {
      "url": "https://books.toscrape.com/catalogue/category/books/mystery_3/index.html",
      "estado": "gravado",
      "chave": "raw/books_toscrape/data=2026-11-02/categoria=mystery_3/pagina=001/sha256=ff899bea5c8806ecd24542d7a195899ad46eeb9a12d4fbfc79a9ed6be9faf2a2.html",
      "status_http": 200,
      "tentativas": 1,
      "bytes": 50388,
      "sha256": "ff899bea5c8806ecd24542d7a195899ad46eeb9a12d4fbfc79a9ed6be9faf2a2",
      "erro": null
    }
  ]
}
```

Os horários e o ID do exemplo são ilustrativos; os códigos HTTP, tamanhos, chaves e hashes correspondem às respostas públicas inspecionadas. O exemplo de manifesto é abreviado.

## Metadados dos objetos brutos

Cada objeto bruto recebe metadados de origem com nomes `x-amz-meta-*`. Chaves e valores são ASCII estrito; texto original do corpo permanece nos bytes do objeto, não nos metadados.

| Metadado | Valor de exemplo | Regra |
|---|---|---|
| `x-amz-meta-source-url` | `https://books.toscrape.com/catalogue/sharp-objects_997/index.html` | URL ASCII/percent-encoded da origem |
| `x-amz-meta-collected-at` | `2026-11-02T03:56:00Z` | Instante ISO 8601 UTC; exemplo de formato |
| `x-amz-meta-data-ref` | `2026-11-02` | Data local de referência |
| `x-amz-meta-sha256` | `41ae9ef1bc17c9984b8e452c61f3370fc6e1868e9b699c803c7336136f57c0ef` | SHA-256 hexadecimal dos bytes gravados |
| `x-amz-meta-http-status` | `200` | Código HTTP decimal em texto; também registra `404` para robots |
| `x-amz-meta-content-type` | `text/html` | Tipo retornado, em valor ASCII |

Medida de conformidade: para cada objeto, codificar estritamente o nome e valor dos metadados como ASCII; qualquer falha reprova RF-09/RF-10 e RNF-04. URLs não ASCII devem ser representadas com percent-encoding antes de armazenar o metadado.

## Modelo lógico em DBML

`execucao_id` nas entidades `livro` e `cotacao` é uma relação lógica interna do modelo, não um campo dos arquivos JSONL nem parte das chaves dos objetos brutos. As linhas de saída representam o resultado diário corrente; o manifesto liga uma execução aos objetos brutos que ela leu ou produziu.

O arquivo importável também está em [`modelo.dbml`](./modelo.dbml).
