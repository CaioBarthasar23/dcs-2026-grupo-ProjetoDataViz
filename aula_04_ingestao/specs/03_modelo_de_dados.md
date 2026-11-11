# Modelo de dados da ingestão

## ClickHouse: `ingestao.db_ingestion`

```sql
CREATE DATABASE IF NOT EXISTS ingestao;

CREATE TABLE IF NOT EXISTS ingestao.db_ingestion
(
    timestamp UInt64,
    data_json JSON,
    data_tag LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(fromUnixTimestamp64Milli(toInt64(timestamp)))
ORDER BY (data_tag, timestamp);
```

`timestamp` é Unix em milissegundos, gerado pelo servidor na ingestão. Milissegundos preservam a resolução do evento de ingestão; segundos descartariam precisão, e `DateTime` acrescentaria semântica de fuso/conversão que não pertence ao valor original do relógio do servidor.

`MergeTree` atende à tabela de pouso append-only e à leitura ordenada por chave. O particionamento mensal deriva o mês de ingestão a partir do timestamp em milissegundos, permitindo poda por período sem criar partições por linha ou por dia. `ORDER BY (data_tag, timestamp)` favorece consultas por domínio e intervalo temporal, que são os filtros usados nas análises desta aula. Como a entrega é pelo menos uma vez, linhas duplicadas podem existir.

`data_json` no tipo `JSON` permite consultar caminhos como subcolunas e aplicar cast no momento da consulta. A conversão de texto para JSON não preserva a representação lexical original, como espaços, ordem das chaves ou formatação dos números. O envelope original continua no raw JSON Lines. Todo INSERT define `input_format_try_infer_dates = 0` e `input_format_try_infer_datetimes = 0`: assim datas e horas dentro de `data_json` permanecem texto, sem conversão para Date/DateTime nem normalização que perca o deslocamento original, como `-03:00`.

### DDL conferido

`sql/001_db_ingestion.sql` já contém os três nomes e tipos, `MergeTree`, particionamento mensal e ordenação descritos acima. Foi conferido e não precisou de alteração.

## Lake

`D` é a data de recebimento no fuso `America/Sao_Paulo`. O lote usa o mesmo trecho `lote_<HHMMSS>_<id>` em raw, bronze e manifesto. O identificador é único por flush e não determinístico: duas tentativas ou reentregas no mesmo segundo não colidem nem sobrescrevem objetos. Isso preserva tentativas distintas da semântica pelo menos uma vez; chaves determinísticas poderiam colidir com um reprocessamento.

| Camada/uso | Chave | Conteúdo |
|---|---|---|
| Raw | `raw/ingestao/data_tag=X/data=D/lote_<HHMMSS>_<id>.jsonl` | Um envelope por linha JSONL, como recebido, com `recebido_em_ms`. Preserva a mensagem original para auditoria e reconstrução. |
| Bronze | `bronze/ingestao/data_tag=X/data=D/lote_<HHMMSS>_<id>.parquet` | Parquet ZSTD; uma linha por objeto de `data`, colunas `timestamp` UBIGINT (ms) e `data_json` VARCHAR. Listas viram várias linhas com o mesmo `timestamp` do envelope; objetos viram uma linha. `data_tag` e `D` ficam no caminho, não nas colunas. |
| Manifesto | `raw/_manifestos/ingestao/data=D/lote_<HHMMSS>_<id>.json` | ID do lote; mensagens e linhas por `data_tag`; chaves gravadas; bytes e SHA-256 de cada arquivo; tempos de cada passo; status. |
| Rejeitados | `raw/ingestao_rejeitados/data=D/rejeitado_<HHMMSS>_<id>.json` | `recebido_em_ms`, motivo da rejeição e corpo recebido. |

A chave de rejeitado usa data e identificador próprios; não integra o trio raw/bronze/manifesto do lote válido.

## Reconstrução

O raw conserva o envelope, incluindo `data_tag`, `data` e o timestamp de recebimento. A reconstrução da bronze desdobra listas de `data`, serializa cada objeto em `data_json` e copia o timestamp do envelope para todas as linhas geradas. A carga no ClickHouse lê Parquet, usa `data_tag` do caminho e converte cada `data_json` VARCHAR para o tipo JSON da tabela, com inferência de datas e datetimes desativada.

Comandos previstos para as etapas de implementação — os scripts/interfaces abaixo ainda não existem nesta etapa:

```sh
python sql/rodar_sql.py sql/raw_para_bronze.sql --var DATA_TAG=<data_tag> --var DATA=<AAAA-MM-DD>
python -m src.clickhouse reprocessar --data-tag <data_tag> --data <AAAA-MM-DD>
```

O primeiro executará SQL DuckDB para reconstruir bronze a partir do raw no RustFS. O segundo lerá o Parquet da bronze e reinserirá as linhas em `ingestao.db_ingestion`. Ambos preservam os artefatos de origem e não implicam deduplicação.
