# Contrato de eventos - Rede Tatame

## Identidade e contexto informado

Fonte: contexto fornecido pelo professor. São 240 academias: sa-saopaulo 96,
us-virginia 72, eu-estocolmo 48 e ap-sydney 24. Média informada: 150 alunos
por academia. Os tipos de evento são app_aberto, video_assistido,
reserva_aula, checkin, cobranca_aprovada, cobranca_falhou,
aula_experimental, matricula, graduacao, cancelamento e heartbeat.

Taxa de eventos, proporção entre tipos e distribuição temporal são
**hipótese, validação pendente**. O gerador recebe semente, taxa e proporções
por parâmetro, sem usar a origem como fato.

## Campos comuns

| Campo | Obrigatório | Formato | Exemplo válido |
|---|---:|---|---|
| event_id | todos | UUID | `7f3b1c9e-52a4-4d0e-9c1b-6a2f8e4d7b10` |
| tipo | todos | enum de tipos | `checkin` |
| ocorrido_em | todos | UTC ISO 8601 com milissegundos | `2026-11-14T11:02:07.412Z` |
| regiao | todos | slug da região | `eu-estocolmo` |
| academia | todos | código `XX-CID-###` | `SE-STO-014` |
| origem | todos | app, catraca, gestao ou dispositivo | `catraca` |

## Campos por tipo

| Tipo | Obrigatórios | Opcionais |
|---|---|---|
| app_aberto | comum, aluno | turma, faixa |
| video_assistido | comum, aluno, turma | faixa |
| reserva_aula | comum, aluno, turma | faixa |
| checkin | comum, aluno, turma, faixa | nenhum |
| cobranca_aprovada | comum, aluno | valor?* |
| cobranca_falhou | comum, aluno | motivo |
| aula_experimental | comum, aluno, turma | faixa |
| matricula | comum, aluno, turma, faixa | nenhum |
| graduacao | comum, aluno, turma, faixa | nenhum |
| cancelamento | comum, aluno, motivo | turma, faixa |
| heartbeat | comum, dispositivo_id | aluno, turma, faixa |

`* valor` não é definido pelo contexto; por isso não é emitido nesta versão.

Campo `aluno` tem exatamente 16 caracteres hexadecimais: os primeiros 16
caracteres hexadecimais de `HMAC-SHA-256(ANON_CHAVE, identificador_interno)`.
O identificador interno nunca sai do gerador.

## Exemplos válidos e inválidos

Válido:
`{"event_id":"...","tipo":"checkin","ocorrido_em":"2026-11-14T11:02:07.412Z","regiao":"eu-estocolmo","academia":"SE-STO-014","aluno":"a8f3c1d9e2b47f60","turma":"adulto-fundamentos","faixa":"branca","origem":"catraca"}`

Inválido: evento sem `event_id`, timestamp sem `Z`, aluno com menos de 16
caracteres hexadecimais, origem desconhecida, região fora das quatro informadas
ou `tipo=cancelamento` sem `motivo`.

## Campos proibidos

Nunca emitir `nome`, `documento`, `email`, `e-mail`, `telefone` ou equivalente
identificado em mapa cadastral. Identificadores internos não são campos públicos.

## Evolução do contrato

Compatível: adicionar campo opcional, ampliar enum de origem com consumidores
preparados para desconhecidos e adicionar tipo novo com processamento explícito.
Incompatível: remover campo obrigatório, mudar tipo ou formato, reutilizar
significado do campo ou remover enum conhecido sem versão.
