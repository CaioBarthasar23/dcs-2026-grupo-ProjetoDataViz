-- Dimensão gerada: 731 dias, uma linha por dia, sem reinicialização.
CREATE TABLE IF NOT EXISTS mackenzie.g00_dim_data
(
    data_key UInt32,
    data Date,
    ano UInt16,
    mes UInt8,
    dia UInt8
)
ENGINE = MergeTree
ORDER BY data_key;

INSERT INTO mackenzie.g00_dim_data
SELECT
    toUInt32(formatDateTime(toDate('2026-01-01') + number, '%Y%m%d')),
    toDate('2026-01-01') + number,
    toUInt16(toYear(toDate('2026-01-01') + number)),
    toUInt8(toMonth(toDate('2026-01-01') + number)),
    toUInt8(toDayOfMonth(toDate('2026-01-01') + number))
FROM numbers(731);

-- Dimensão de livro em SCD tipo 2 por versão de UPC.
CREATE TABLE IF NOT EXISTS mackenzie.g00_dim_livro
(
    livro_key UInt64,
    upc String,
    titulo String,
    categoria String,
    url String,
    versao_ms UInt64
)
ENGINE = ReplacingMergeTree(versao_ms)
ORDER BY livro_key;

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_dim_livro
TO mackenzie.g00_dim_livro
AS
SELECT
    cityHash64(data_json.upc::String, timestamp) AS livro_key,
    data_json.upc::String AS upc,
    data_json.titulo::String AS titulo,
    data_json.categoria::String AS categoria,
    data_json.url::String AS url,
    timestamp AS versao_ms
FROM mackenzie.db_ingestion
WHERE data_tag = 'livros';

-- Fato: uma observação de um livro em uma data de coleta.
CREATE TABLE IF NOT EXISTS mackenzie.g00_fato_preco_livro
(
    data_key UInt32,
    upc String,
    preco_gbp Float64,
    qtd_estoque UInt32,
    avaliacao UInt8,
    em_estoque Bool,
    coletado_em DateTime('America/Sao_Paulo'),
    versao_ms UInt64
)
ENGINE = ReplacingMergeTree(versao_ms)
ORDER BY (data_key, upc);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_fato_preco_livro
TO mackenzie.g00_fato_preco_livro
AS
SELECT
    toUInt32OrZero(replaceAll(substring(data_json.coletado_em::String, 1, 10), '-', '')) AS data_key,
    data_json.upc::String AS upc,
    data_json.preco_gbp::Float64 AS preco_gbp,
    data_json.qtd_estoque::UInt32 AS qtd_estoque,
    data_json.avaliacao::UInt8 AS avaliacao,
    data_json.em_estoque::Bool AS em_estoque,
    toDateTimeOrNull(substring(data_json.coletado_em::String, 1, 19), 'America/Sao_Paulo') AS coletado_em,
    timestamp AS versao_ms
FROM mackenzie.db_ingestion
WHERE data_tag = 'livros';

-- Fato PTAX: uma cotação por data, hora, moeda e tipo de boletim.
CREATE TABLE IF NOT EXISTS mackenzie.g00_fato_cotacao_ptax
(
    data_key UInt32,
    moeda String,
    data_hora_cotacao DateTime64(6, 'America/Sao_Paulo'),
    tipo_boletim String,
    cotacao_compra Float64,
    cotacao_venda Float64,
    paridade_compra Float64,
    paridade_venda Float64,
    versao_ms UInt64
)
ENGINE = ReplacingMergeTree(versao_ms)
ORDER BY (data_key, moeda, data_hora_cotacao, tipo_boletim);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_fato_cotacao_ptax
TO mackenzie.g00_fato_cotacao_ptax
AS
SELECT
    toUInt32(formatDateTime(parseDateTimeBestEffortOrNull(data_json.dataHoraCotacao::String, 'America/Sao_Paulo'), '%Y%m%d')) AS data_key,
    data_json.moeda::String AS moeda,
    parseDateTimeBestEffortOrNull(data_json.dataHoraCotacao::String, 'America/Sao_Paulo') AS data_hora_cotacao,
    data_json.tipoBoletim::String AS tipo_boletim,
    data_json.cotacaoCompra::Float64 AS cotacao_compra,
    data_json.cotacaoVenda::Float64 AS cotacao_venda,
    data_json.paridadeCompra::Float64 AS paridade_compra,
    data_json.paridadeVenda::Float64 AS paridade_venda,
    timestamp AS versao_ms
FROM mackenzie.db_ingestion
WHERE data_tag = 'ptax';

-- Fato de leitura: uma posição válida por caminhão e instante.
CREATE TABLE IF NOT EXISTS mackenzie.g00_fato_leitura_telemetria
(
    data_key UInt32,
    caminhao_id String,
    instante_leitura DateTime64(3, 'America/Sao_Paulo'),
    latitude Float64,
    longitude Float64,
    velocidade_kmh UInt16,
    tachometro_codigo String,
    versao_ms UInt64
)
ENGINE = ReplacingMergeTree(versao_ms)
ORDER BY (data_key, caminhao_id, instante_leitura);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_fato_leitura_telemetria
TO mackenzie.g00_fato_leitura_telemetria
AS
WITH
    data_json.linha::String AS linha,
    splitByChar('|', data_json.linha::String) AS partes_barra,
    splitByChar(' ', data_json.linha::String) AS partes_espaco,
    startsWith(data_json.linha::String, 'CAM-') AND position(data_json.linha::String, '|') > 0 AS eh_barra,
    startsWith(data_json.linha::String, 'CAM-') AND position(data_json.linha::String, ' GPS ') > 0 AS eh_espaco
SELECT
    toUInt32(formatDateTime(
        multiIf(
            eh_barra,
            parseDateTimeOrNull(arrayElement(partes_barra, 2), '%d/%m/%y %H:%i:%s', 'America/Sao_Paulo'),
            eh_espaco,
            parseDateTimeOrNull(arrayElement(partes_espaco, 2) || ' ' || arrayElement(partes_espaco, 3), '%d-%m-%Y %H:%i:%s', 'America/Sao_Paulo'),
            NULL
        ),
        '%Y%m%d'
    )) AS data_key,
    multiIf(
        eh_barra,
        arrayElement(partes_barra, 1),
        eh_espaco,
        arrayElement(partes_espaco, 1),
        ''
    ) AS caminhao_id,
    multiIf(
        eh_barra,
        parseDateTimeOrNull(arrayElement(partes_barra, 2), '%d/%m/%y %H:%i:%s', 'America/Sao_Paulo'),
        eh_espaco,
        parseDateTimeOrNull(arrayElement(partes_espaco, 2) || ' ' || arrayElement(partes_espaco, 3), '%d-%m-%Y %H:%i:%s', 'America/Sao_Paulo'),
        NULL
    ) AS instante_leitura,
    multiIf(
        eh_barra,
        toFloat64OrZero(arrayElement(splitByChar(',', arrayElement(partes_barra, 3)), 1)),
        eh_espaco,
        toFloat64OrZero(arrayElement(partes_espaco, 5)),
        0
    ) AS latitude,
    multiIf(
        eh_barra,
        toFloat64OrZero(arrayElement(splitByChar(',', arrayElement(partes_barra, 3)), 2)),
        eh_espaco,
        toFloat64OrZero(arrayElement(partes_espaco, 6)),
        0
    ) AS longitude,
    multiIf(
        eh_barra,
        toUInt16OrZero(extract(arrayElement(partes_barra, 4), '[0-9]+')),
        eh_espaco,
        toUInt16OrZero(extract(arrayElement(partes_espaco, 7), '[0-9]+')),
        0
    ) AS velocidade_kmh,
    multiIf(
        eh_barra,
        extract(linha, 'TAC MOT ([0-9]{2}h[0-9]{2})'),
        eh_espaco,
        '',
        ''
    ) AS tachometro_codigo,
    timestamp AS versao_ms
FROM mackenzie.db_ingestion
WHERE data_tag = 'telemetria'
  AND position(linha, 'ERR SAT') = 0
  AND position(linha, 'RADIO') = 0
  AND (
      (startsWith(linha, 'CAM-') AND position(linha, '|') > 0)
      OR (startsWith(linha, 'CAM-') AND position(linha, ' GPS ') > 0)
  );

-- Fato de alerta: um alerta por caminhão, instante e duração contínua.
CREATE TABLE IF NOT EXISTS mackenzie.g00_fato_alerta_direcao
(
    data_key UInt32,
    caminhao_id String,
    instante_alerta DateTime64(3, 'America/Sao_Paulo'),
    duracao_continua_min UInt32,
    quantidade_alerta UInt32,
    versao_ms UInt64
)
ENGINE = ReplacingMergeTree(versao_ms)
ORDER BY (data_key, caminhao_id, instante_alerta, duracao_continua_min);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_fato_alerta_direcao
TO mackenzie.g00_fato_alerta_direcao
AS
WITH
    data_json.linha::String AS linha,
    splitByChar(';', linha) AS partes
SELECT
    toUInt32(formatDateTime(
        parseDateTimeOrNull(arrayElement(partes, 3), '%Y%m%dT%H%i%s', 'America/Sao_Paulo'),
        '%Y%m%d'
    )) AS data_key,
    arrayElement(partes, 2) AS caminhao_id,
    parseDateTimeOrNull(arrayElement(partes, 3), '%Y%m%dT%H%i%s', 'America/Sao_Paulo') AS instante_alerta,
    toUInt32OrZero(arrayElement(splitByChar(':', arrayElement(splitByChar(' ', arrayElement(partes, 4)), 3)), 1)) * 60
        + toUInt32OrZero(arrayElement(splitByChar(':', arrayElement(splitByChar(' ', arrayElement(partes, 4)), 3)), 2)) AS duracao_continua_min,
    1 AS quantidade_alerta,
    timestamp AS versao_ms
FROM mackenzie.db_ingestion
WHERE data_tag = 'telemetria'
  AND startsWith(linha, 'TAC;')
  AND position(linha, 'DIRECAO CONTINUA') > 0
  AND position(linha, 'ALERTA') > 0
  AND position(linha, 'ERR SAT') = 0
  AND position(linha, 'RADIO') = 0;

-- Dimensão caminhão em cascata, agregando a primeira e a última leitura.
CREATE TABLE IF NOT EXISTS mackenzie.g00_dim_caminhao
(
    caminhao_key String,
    primeira_leitura SimpleAggregateFunction(min, DateTime64(3, 'America/Sao_Paulo')),
    ultima_leitura SimpleAggregateFunction(max, DateTime64(3, 'America/Sao_Paulo'))
)
ENGINE = AggregatingMergeTree
ORDER BY caminhao_key;

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_dim_caminhao
TO mackenzie.g00_dim_caminhao
AS
SELECT
    caminhao_id AS caminhao_key,
    min(instante_leitura) AS primeira_leitura,
    max(instante_leitura) AS ultima_leitura
FROM mackenzie.g00_fato_leitura_telemetria
GROUP BY caminhao_id;
