# ADR-001 · Coleta e extração separadas

**Status:** Proposta

## Contexto

DN-02 exige diagnóstico quando uma etapa falha, e DN-03 exige um bronze consistente para a Aula 04. RF-09/RF-10 determinam preservar a resposta bruta antes da interpretação; RF-11/RF-12 determinam extrair a partir desses brutos. RNF-01 exige correção e completude, enquanto RNF-09 exige extração testável sem rede externa. Misturar requisição, parser e publicação dificultaria repetir apenas a extração e identificar a etapa que falhou.

## Decisão

Separar o pipeline em coleta/preservação e extração/validação/publicação. A coleta grava os bytes no `raw` e os referencia no manifesto. O extrator lê somente os objetos associados ao manifesto, não chama as fontes externas e publica os contratos JSON Lines em `bronze`.

## Alternativas

- Fazer scraping e parsing no mesmo passo, gravando somente os registros extraídos.
- Reconsultar a fonte sempre que for necessário corrigir ou testar o parser.
- Manter extração separada, mas permitir que consulte a rede como fallback.

## Consequências

- É possível testar e reprocessar fixtures ou objetos raw sem rede externa.
- Uma correção de parser não exige nova coleta, desde que os brutos estejam preservados.
- É necessário manter chaves, metadados e manifestos suficientes para associar a extração à execução correta.
- O armazenamento consome espaço adicional e a publicação bronze deve ser validada para não apresentar resultado parcial como completo.

**Origem:** DN-02, DN-03; RF-09, RF-10, RF-11, RF-12; RNF-01, RNF-05, RNF-09.

**Diagramas da Etapa 08:** [extração](../modelagem/dinamica/extracao.md), [coleta Books](../modelagem/dinamica/coleta_books.md), [coleta PTAX](../modelagem/dinamica/coleta_ptax.md).

**Referências:** [componentes](../componentes.md), [classes](../classes.md), [requisitos funcionais](../../specs/01_requisitos_funcionais.md).
