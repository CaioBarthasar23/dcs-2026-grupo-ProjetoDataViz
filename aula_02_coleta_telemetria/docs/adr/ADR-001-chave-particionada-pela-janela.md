# ADR-001 — Chave particionada pelo início da janela em UTC

- **Status:** Aceito.
- **Data:** 2026-11-02.

## Contexto

Cada lote corresponde ao início de uma janela de 15 minutos em
`America/Sao_Paulo`. A mesma janela pode ser retransmitida em outra execução;
portanto, a chave não pode depender do horário de chegada nem do relógio do
coletor. Os lotes também precisam ser localizáveis por data, hora e caminhão.

## Alternativas consideradas

1. Particionar pelo horário em que o arquivo chegou ou foi coletado.
2. Manter a partição na hora local de Brasília.
3. Converter o início da janela de Brasília para UTC e construir uma chave
   determinística por data, hora, caminhão e janela.

## Decisão

Validar o nome `CAM-XXXX_AAAAMMDDTHHMM.txt`, interpretar o início da janela em
`America/Sao_Paulo`, convertê-lo para UTC e usar:

`telemetria/data=AAAA-MM-DD/hora=HH/caminhao=CAM-XXXX/lote_HHMM.txt`

O nome e a janela determinam a mesma chave em qualquer execução. O conteúdo é
preservado separadamente como bytes; o nome não é usado para transformar o
lote.

## Consequências positivas

- Reexecuções da mesma janela apontam à mesma chave e permitem idempotência.
- A partição temporal é explícita e normalizada em UTC, inclusive ao cruzar
  data local/UTC.
- A chave pode ser calculada sem consultar relógio, rede ou conteúdo.

## Consequências negativas

- Um nome repetido para conteúdos diferentes resulta em colisão intencional de
  identidade lógica; a política de hash do ADR-002 deve impedir sobrescrita.
- Uma correção legítima para a mesma janela exige processo de adjudicação, não
  um novo caminho automático.
- A precisão de minutos vem do padrão de nome; arquivos com outra granularidade
  precisam de evolução explícita do formato.

## Requisitos relacionados

RF-03, RF-05, RF-06; OBJ-01, OBJ-02.

## Evidência

- `src/chaves.py::montar_chave`.
- `tests/test_chaves.py::test_chave_usa_inicio_da_janela_em_utc`.
- `tests/test_chaves.py::test_chave_avanca_data_no_limite_utc`.
- A integração local informada validou as chaves dos 80 lotes.

## Condição de revisão

Revisar se o provedor alterar a semântica do timestamp do nome, a zona de
origem, a granularidade da janela ou a necessidade de múltiplas revisões
legítimas do mesmo lote.
