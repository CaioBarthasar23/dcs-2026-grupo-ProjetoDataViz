# ADR-001 — Origem do código existente

## Status

Aceito pelo aluno; resposta do professor sobre a aceitação do código anterior à especificação permanece pendente.

## Data

11/11/2026

## Responsável

CaioBarthasar23

## Contexto

O TCGCSV não guarda histórico: cada dia sem coleta é perdido e não pode ser recuperado depois. Por esse motivo, a coleta começou antes da persona e da especificação.

A primeira coleta foi realizada com `data=2026-10-31` no bucket `tcg`, prefixo `group_id=23651`. A coleta diária roda pelo GitHub Actions desde então: primeiro no repositório individual do aluno e, a partir de 11/11/2026, neste repositório (commit `1c45944`).

O arquivo `src/collector.py` foi escrito a partir de 31/10/2026 e ajustado em 07/11/2026 para corrigir o filtro da PTAX pelo rótulo `Fechamento PTAX` e incluir o comando `backfill-ptax`. O arquivo `src/silver.py` foi escrito em 10/11/2026. Ambos foram escritos com ajuda do assistente Claude (Anthropic), em conversas fora do fluxo SDD deste repositório.

A migração para `projeto_final/` ocorreu em 11/11/2026: commit `4e203be` (coletor), `6dc3e03` (silver), `b91faed` (README) e `1c45944` (workflow). A evidência dessa migração está pendente.

Em uma execução real em 11/11/2026, passaram 41 testes: 10 do coletor e 31 da silver. A saída ainda precisa ser guardada em `docs/evidencias/`.

## Decisão

CaioBarthasar23 decidiu iniciar a coleta e escrever `src/collector.py` e `src/silver.py` antes da persona e da especificação, porque o TCGCSV não guarda histórico e cada dia perdido não volta. CaioBarthasar23 também decidiu declarar essa origem neste ADR sem alterar a cronologia.

A especificação descreve o comportamento esperado e não declara nenhum requisito como atendido. O estado real de cada requisito será registrado na rastreabilidade durante a etapa ATAM.

## Alternativas consideradas e descartadas

- **Esperar a persona e a especificação antes de iniciar a coleta:** descartada porque o TCGCSV não guarda histórico e cada dia sem coleta seria perdido sem possibilidade de recuperação.
- **Reescrever a cronologia para indicar que o código foi escrito depois da especificação:** descartada porque ocultaria a origem real dos arquivos e contrariaria o registro honesto exigido em `AGENTS.md`.

## Consequências

- A cronologia da coleta e da escrita de `src/collector.py` e `src/silver.py` permanece explícita neste ADR.
- O ADR registra a origem do código, mas não afirma que qualquer requisito está atendido.
- A saída dos 41 testes e a evidência da migração ainda precisam ser guardadas em `docs/evidencias/`.
- Existe o risco de a disciplina exigir especificação antes do código. CaioBarthasar23 perguntou ao professor se o código anterior é aceito quando declarado em ADR; a resposta permanece pendente e não é tratada como aceitação.

## Requisitos relacionados

- OBJ-07 — manter uma série diária contínua e verificável.
- T-31 — registrar a origem de `src/collector.py` e `src/silver.py` sem reescrever a cronologia.
- `AGENTS.md`, seção “Estado atual (honesto)” — registrar a origem do código em ADR-001 e separar comportamento esperado do estado real.
