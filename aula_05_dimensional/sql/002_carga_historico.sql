-- Carga histórica idêntica às quatro views de fato e à dimensão de livro.
-- Reexecutar mantém o estado observado com FINAL graças ao ReplacingMergeTree.
INSERT INTO mackenzie.g00_dim_livro
SELECT
    cityHash64(data_json.upc::String, timestamp) AS livro_key,
    data_json.upc::String AS upc,
    data_json.titulo::String AS titulo,
    data_json.categoria::String AS categoria,
    data_json.url::String AS url,
    timestamp AS versao_ms
FROM mackenzie.db_ingestion
WHERE data_tag = 'livros';

INSERT INTO mackenzie.g00_fato_preco_livro
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

INSERT INTO mackenzie.g00_fato_cotacao_ptax
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

INSERT INTO mackenzie.g00_fato_leitura_telemetria
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

INSERT INTO mackenzie.g00_fato_alerta_direcao
WITH
    data_json.linha::String AS linha,
    splitByChar(';', data_json.linha::String) AS partes
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

-- Alimenta a dimensão caminhão em cascata a partir do fato consolidado.
INSERT INTO mackenzie.g00_dim_caminhao
SELECT
    caminhao_id AS caminhao_key,
    min(instante_leitura) AS primeira_leitura,
    max(instante_leitura) AS ultima_leitura
FROM mackenzie.g00_fato_leitura_telemetria FINAL
GROUP BY caminhao_id;
