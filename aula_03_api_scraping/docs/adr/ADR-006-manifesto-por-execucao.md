# ADR-006 · Manifesto por execução

**Status:** Proposta

## Contexto

DN-02 requer que P2 identifique etapa, item e motivo de falha. RF-13 exige manifesto próprio por execução, RF-14 exige registrar divergências e RF-15 preserva manifestos anteriores durante reexecução. RNF-05 exige diagnóstico de incompletude; RNF-07 exige reexecução sem apagar histórico.

## Decisão

Criar um manifesto imutável por execução, identificado somente na chave do manifesto. O cabeçalho registra ID, início, fim, data de referência, estado, `robots.txt` e total declarado. Cada item registra URL, estado (`pendente`, `baixando`, `aguardando`, `baixado`, `gravado` ou `falhou`), chave raw quando gravada, status HTTP, tentativas, bytes, SHA-256 e erro. Cada transição relevante atualiza o manifesto da execução, sem incluir o ID da execução nas chaves raw.

## Alternativas

- Registrar somente logs locais sem manifesto persistido.
- Manter um único manifesto mutável por data, sobrescrito a cada reexecução.
- Registrar apenas um resumo de sucesso/falha sem granularidade por item.

## Consequências

- Falhas de rede, gravação e contagem podem ser inspecionadas sem inferência a partir dos objetos finais.
- Execuções distintas permanecem auditáveis, inclusive quando compartilham objetos raw.
- A atualização do manifesto precisa ser consistente com estados finais dos itens; mensagens de erro não podem incluir credenciais.
- O número de manifestos cresce com o número de reexecuções e consome armazenamento.

**Origem:** DN-02; RF-05, RF-08, RF-13, RF-14, RF-15; RNF-05, RNF-07.

**Diagramas da Etapa 08:** [estados do item](../modelagem/dinamica/estados_item.md), [coleta Books](../modelagem/dinamica/coleta_books.md), [coleta PTAX](../modelagem/dinamica/coleta_ptax.md), [reexecução](../modelagem/dinamica/reexecucao.md).

**Referências:** [manifesto no modelo de dados](../../specs/03_modelo_de_dados.md), [RFs](../../specs/01_requisitos_funcionais.md).
