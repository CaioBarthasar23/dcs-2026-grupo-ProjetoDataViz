# ADR-005 · Bytes originais no bruto e decodificação no parser

**Status:** Proposta

## Contexto

DN-02 exige investigação de falhas com evidência, e DN-03 depende de extração corrigível. RF-09/RF-10 exigem gravar bytes originais antes de interpretar; RF-11/RF-12 exigem ler raw para formar JSON Lines. RNF-01 exige correção e RNF-09 exige testar extração sem rede. A origem HTML pode não declarar charset no cabeçalho HTTP.

## Decisão

Persistir o corpo recebido como bytes inalterados em `raw`. Só depois da gravação, o parser interpreta uma cópia e determina a decodificação a partir das informações disponíveis no conteúdo/cabeçalhos e das regras de parsing. O valor decodificado nunca substitui o objeto raw. O hash e os metadados referem-se aos bytes efetivamente persistidos.

## Alternativas

- Decodificar e normalizar o corpo antes de persistir.
- Persistir apenas o texto decodificado.
- Fazer parsing diretamente durante a requisição e descartar os bytes.

## Consequências

- Os bytes podem ser auditados e reprocessados com outra versão do parser.
- O corpo original pode ser interpretado novamente sem nova chamada à fonte.
- É necessário testar charset e decodificação para evitar texto corrompido.
- O armazenamento ocupa mais espaço do que guardar somente os campos extraídos; os bytes não podem conter transformações ocultas de normalização.

**Origem:** DN-02, DN-03; RF-09, RF-10, RF-11, RF-12; RN-08; RNF-01, RNF-07, RNF-09.

**Diagramas da Etapa 08:** [coleta Books](../modelagem/dinamica/coleta_books.md), [coleta PTAX](../modelagem/dinamica/coleta_ptax.md), [extração](../modelagem/dinamica/extracao.md).

**Referências:** [contratos do modelo de dados](../../specs/03_modelo_de_dados.md), [classes](../classes.md).
