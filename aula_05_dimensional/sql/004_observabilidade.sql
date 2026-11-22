-- Contadores incrementais de ingestao: sem carga historica.
CREATE TABLE IF NOT EXISTS mackenzie.g00_obs_ingestao_minuto
(
    minuto DateTime('America/Sao_Paulo'),
    data_tag LowCardinality(String),
    linhas UInt64
)
ENGINE = SummingMergeTree
ORDER BY (minuto, data_tag);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_obs_ingestao_minuto
TO mackenzie.g00_obs_ingestao_minuto
AS
SELECT
    toStartOfMinute(fromUnixTimestamp64Milli(timestamp, 'America/Sao_Paulo')) AS minuto,
    data_tag,
    toUInt64(count()) AS linhas
FROM mackenzie.db_ingestion
GROUP BY minuto, data_tag;

-- Contadores incrementais de descarte de telemetria.
CREATE TABLE IF NOT EXISTS mackenzie.g00_obs_telemetria_descartes_minuto
(
    minuto DateTime('America/Sao_Paulo'),
    motivo LowCardinality(String),
    linhas UInt64
)
ENGINE = SummingMergeTree
ORDER BY (minuto, motivo);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_obs_telemetria_descartes_minuto
TO mackenzie.g00_obs_telemetria_descartes_minuto
AS
WITH
    data_json.linha::String AS linha
SELECT
    toStartOfMinute(fromUnixTimestamp64Milli(timestamp, 'America/Sao_Paulo')) AS minuto,
    multiIf(
        position(linha, 'ERR SAT') > 0, 'ERR SAT',
        position(linha, '#RADIO') > 0, 'RADIO',
        'outro'
    ) AS motivo,
    toUInt64(count()) AS linhas
FROM mackenzie.db_ingestion
WHERE data_tag = 'telemetria'
  AND (
      position(linha, 'ERR SAT') > 0
      OR position(linha, '#RADIO') > 0
      OR NOT (
          startsWith(linha, 'TAC;')
          OR (startsWith(linha, 'CAM-') AND position(linha, '|') > 0)
          OR (startsWith(linha, 'CAM-') AND position(linha, ' GPS ') > 0)
      )
  )
GROUP BY minuto, motivo;

-- Saude de ingestao nos ultimos 15 minutos.
CREATE VIEW IF NOT EXISTS mackenzie.g00_v_saude_ingestao_15min
AS
WITH
    now64(3, 'America/Sao_Paulo') AS hora_atual
SELECT
    data_tag,
    sum(linhas) AS linhas,
    max(minuto) AS ultimo_minuto,
    greatest(
        0,
        toUInt64(dateDiff('second', max(minuto), hora_atual))
    ) AS segundos_desde_entao
FROM mackenzie.g00_obs_ingestao_minuto
WHERE minuto >= toStartOfMinute(hora_atual - INTERVAL 15 MINUTE)
GROUP BY data_tag;

-- Caminhoes que transmitiram nos ultimos 5 minutos, direto da origem.
CREATE VIEW IF NOT EXISTS mackenzie.g00_v_caminhoes_5min
AS
SELECT DISTINCT
    multiIf(
        position(data_json.linha::String, '|') > 0,
        arrayElement(splitByChar('|', data_json.linha::String), 1),
        position(data_json.linha::String, ' GPS ') > 0,
        arrayElement(splitByChar(' ', data_json.linha::String), 1),
        ''
    ) AS caminhao_id
FROM mackenzie.db_ingestion
WHERE data_tag = 'telemetria'
  AND timestamp >= toUnixTimestamp64Milli(now64(3, 'America/Sao_Paulo') - INTERVAL 5 MINUTE)
  AND caminhao_id != '';

-- Descartes da telemetria na ultima hora e participacao no total.
CREATE VIEW IF NOT EXISTS mackenzie.g00_v_descartes_telemetria_1h
AS
WITH
    now64(3, 'America/Sao_Paulo') AS hora_atual,
    toUnixTimestamp64Milli(now64(3, 'America/Sao_Paulo') - INTERVAL 1 HOUR) AS inicio_ms,
    (SELECT count() FROM mackenzie.db_ingestion WHERE data_tag='telemetria' AND timestamp >= inicio_ms) AS total_telemetria
SELECT
    motivo,
    sum(linhas) AS linhas,
    if(total_telemetria = 0, 0.0, 100.0 * sum(linhas) / total_telemetria) AS parte_total_pct
FROM mackenzie.g00_obs_telemetria_descartes_minuto
WHERE minuto >= toStartOfMinute(hora_atual - INTERVAL 1 HOUR)
  AND motivo IN ('ERR SAT', 'RADIO', 'outro')
GROUP BY motivo, total_telemetria;
