# ADR-002 · Chaves determinísticas para objetos brutos

**Status:** Proposta

## Contexto

DN-02 precisa de rastreabilidade entre coleta e objeto persistido. RF-09/RF-10 exigem chave determinística e preservação do raw; RF-15 exige reexecução diária sem duplicar resultados, e RNF-07 exige manter objetos brutos e manifestos anteriores. Uma chave com horário ou ID de execução mudaria a cada retry ou reexecução, mesmo para o mesmo conteúdo.

## Decisão

Formar a chave do objeto raw com fonte, data de referência, recurso lógico consultado e SHA-256 dos bytes. O recurso identifica a página inicial, a categoria/página, o detalhe ou a janela PTAX. A chave não inclui horário de coleta nem ID da execução. Cada execução mantém seu próprio manifesto e referencia a chave calculada. Conteúdo diferente produz chave distinta; conteúdo idêntico para o mesmo recurso pode reutilizar o mesmo objeto imutável.

## Alternativas

- Chave com timestamp ou ID de execução, criando cópia para cada tentativa.
- Chave somente por fonte/data/recurso, sobrescrevendo conteúdo diferente.
- Uma chave baseada somente no hash, sem caminho lógico da fonte e do recurso.

## Consequências

- Reexecuções com os mesmos bytes convergem para a mesma chave e evitam sobrescrita de conteúdo.
- O manifesto é necessário para identificar quais objetos uma execução usou.
- Alterações de resposta no mesmo dia geram objetos raw adicionais, aumentando armazenamento.
- O SHA-256 distingue conteúdos, mas não garante por si só que o conteúdo recebido é correto; validação continua necessária.
- A semântica exata de recurso/página deve permanecer estável entre versões do coletor.

**Origem:** DN-02; RF-09, RF-10, RF-13, RF-15; RNF-07.

**Diagramas da Etapa 08:** [gravação raw](../modelagem/dinamica/gravacao_raw.md), [reexecução](../modelagem/dinamica/reexecucao.md), [estados do item](../modelagem/dinamica/estados_item.md).

**Referências:** [layout de chaves](../../specs/03_modelo_de_dados.md), [RFs](../../specs/01_requisitos_funcionais.md).
