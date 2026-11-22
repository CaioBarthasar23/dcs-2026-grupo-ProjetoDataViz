# ADR-009 — Perda do cluster e carga retroativa do raw

## Status

Aceito pelo aluno; autorização do professor por mensagem em 14/11/2026.

## Data

14/11/2026

## Responsável

CaioBarthasar23

## Contexto

Em 14/11/2026 o cluster antigo do RustFS caiu e o endpoint mudou. No endpoint novo, `python -m src.collector check` informou que o prefixo `group_id=23651` estava livre: o raw de 31/10 a 13/11/2026 não existe no servidor novo. A única cópia própria é a captura local do dia 12/11/2026 (`data_local/raw`, 4 arquivos), guardada também em arquivo compactado. A coleta de 14/11/2026 foi gravada no servidor novo pelo GitHub Actions (execução #13).

O professor respondeu por mensagem em 14/11/2026: "Foi perdido, pode recarregar à vontade, agora não vai mais dar nenhum problema". A mensagem autoriza a recarga; não define como declarar os dias recarregados.

O FAQ do TCGCSV descreve arquivos diários de preços desde 08/02/2024 (padrão `prices-AAAA-MM-DD.ppmd.7z`). Em 14/11/2026 os arquivos de 31/10, 01/11, 06/11, 12/11 e 13/11/2026 responderam `200`.

## Decisão

CaioBarthasar23 decidiu recarregar o raw de 31/10 a 13/11/2026:

- dia 12/11/2026: subir a captura local original com `upload`, sem sobrescrever;
- PTAX: recarregar com `backfill-ptax`;
- preços do TCGplayer dos demais dias: recarregar a partir do arquivo diário do TCGCSV, sem gravar `products.json` nos dias retroativos, e declarar esses dias como retroativos no README e neste ADR.

CDI: a recarga fica pendente e depende da data inicial das carteiras.

Hipótese, validação pendente: o preço do arquivo público do TCGCSV equivale ao preço que o coletor teria gravado depois das 18h BRT. O horário em que o arquivo é gerado não é informado pela fonte. A validação será feita comparando o arquivo do dia 12/11/2026 com a captura própria do mesmo dia.

## Alternativas consideradas e descartadas

- **Declarar a lacuna e seguir só com os dias coletados a partir de 14/11/2026:** descartada porque o professor autorizou a recarga e o período curto inviabilizaria as perguntas de evolução.
- **Recarregar um período maior que o perdido (o arquivo cobre desde 08/02/2024):** não adotada por ora; muda o escopo do projeto e exige justificativa própria.

## Consequências

- Os dias retroativos são identificados no README e neste ADR; o preço retroativo é o instantâneo do arquivo público, não a coleta própria do dia.
- Nenhum objeto existente do raw é sobrescrito ou apagado, e a escrita fica no prefixo `group_id=23651`.
- A premissa do ADR-001 de que o TCGCSV não guarda histórico foi registrada como imprecisa em nota de atualização desse ADR.

## Requisitos relacionados

- OBJ-07 — manter uma série diária contínua e verificável.
- RNF-06 — declarar e preservar a carga retroativa do histórico.
- RNF-03 — restringir escrita ao prefixo da própria coleção.
- T-33 e T-34.

## Atualização de 14/11/2026

A PTAX de 30/10/2026 (último fechamento anterior ao primeiro dia de preços) foi acrescentada à recarga, porque a conversão de 31/10 a 02/11/2026 usa o último fechamento conhecido (ASOF) e ficaria nula sem ela. O texto original deste ADR não foi alterado.

## Atualização de 19/11/2026

Em 19/11/2026 a conferência do bucket mostrou que os preços do TCGplayer e a PTAX de 17/11/2026 não foram coletados: a lista de execuções do GitHub Actions não tem nenhuma execução depois das 18h (horário de Brasília) nesse dia. A PTAX de 17/11/2026 foi recarregada com `backfill-ptax`, e os preços de 17/11/2026 entram na carga retroativa dos preços (T-33 e T-34), com o dia declarado como retroativo no README e neste ADR. O texto original deste ADR não foi alterado.

## Atualização de 22/11/2026

Estado final da recarga retroativa, conforme a evidência `docs/evidencias/T-34_recarga_retroativa.txt` (listagens de 22/11/2026, antes e depois da gravação):

- **Preços do TCGplayer carregados do arquivo público do TCGCSV (15 dias):** 31/10 a 11/11, 13/11, 17/11 e 20/11. Os dias 12/11 (captura própria enviada pelo aluno) e 14/11 a 16/11, 18/11, 19/11 e 21/11 foram gravados pela coleta diária.
- **Motivo por dia:** 31/10 a 11/11 e 13/11, perda do cluster; 17/11, ausência da execução da noite; 20/11, falha de TLS no endpoint do RustFS.
- **`products.json`:** ausente nos 15 dias retroativos, por decisão do aluno de 14/11/2026.
- **PTAX:** 30/10 a 13/11 e 17/11 recarregadas pelo backfill; 20/11 gravada como "sem boletim no dia" (feriado nacional). Sem lacuna de PTAX de 30/10 a 21/11.
- **CDI:** o objeto diário não existe em 30/10 a 11/11 nem em 13/11. O arquivo de 12/11 traz a janela de 03/11 a 11/11, então a série tem valores a partir de 03/11; o valor de 30/10 (sexta-feira) não está no bucket, e 31/10, 01/11 e 02/11 não têm CDI. Hipótese, validação pendente na silver. O tratamento do CDI de 30/10 na carteira CDI será decidido no ADR da carteira.
- **Hipótese mantida:** o arquivo público equivale ao que o coletor teria gravado depois das 18h BRT. Verificada por conteúdo idêntico apenas em 12/11; hipótese, validação pendente nos demais dias.
- **Pendente:** teste da reconstrução da silver em dias sem `products.json`.
