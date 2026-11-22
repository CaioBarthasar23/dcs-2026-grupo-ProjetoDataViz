-- Cubos fechados: somente data_key anterior ao dia atual.
-- As tabelas são MergeTree e não são atualizadas por ETL incremental.

CREATE TABLE IF NOT EXISTS mackenzie.g00_rel_preco_categoria_dia
(
    categoria String,
    data_key UInt32,
    livros UInt32,
    preco_medio_gbp Float64,
    cotacao_venda_ptax Float64,
    data_ptax_key UInt32,
    preco_medio_brl Float64
)
ENGINE = MergeTree
ORDER BY (categoria, data_key);

CREATE TABLE IF NOT EXISTS mackenzie.g00_rel_telemetria_caminhao_dia
(
    caminhao_id String,
    data_key UInt32,
    leituras UInt32,
    velocidade_media Float64,
    velocidade_maxima UInt16,
    primeira_leitura DateTime64(3, 'America/Sao_Paulo'),
    ultima_leitura DateTime64(3, 'America/Sao_Paulo'),
    parte_formato_espaco_pct Float64
)
ENGINE = MergeTree
ORDER BY (caminhao_id, data_key);

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_rel_preco_categoria_dia
REFRESH EVERY 1 DAY OFFSET 1 HOUR
TO mackenzie.g00_rel_preco_categoria_dia
AS
WITH
    p AS
    (
        SELECT
            data_key,
            moeda,
            cotacao_venda,
            tipo_boletim
        FROM mackenzie.g00_fato_cotacao_ptax FINAL
        WHERE tipo_boletim IN ('Fechamento', 'Fechamento PTAX')
          AND moeda = 'GBP'
          AND data_key < toYYYYMMDD(today())
    ),
    base AS
    (
        SELECT
            l.categoria AS categoria,
            f.data_key AS data_key,
            'GBP' AS moeda,
            toUInt32(count()) AS livros,
            avg(f.preco_gbp) AS preco_medio_gbp
        FROM mackenzie.g00_fato_preco_livro AS f FINAL
        INNER JOIN mackenzie.g00_dim_livro AS l FINAL
            ON f.upc = l.upc
        WHERE f.data_key < toYYYYMMDD(today())
        GROUP BY categoria, f.data_key
    )
SELECT
    base.categoria AS categoria,
    base.data_key AS data_key,
    base.livros AS livros,
    base.preco_medio_gbp AS preco_medio_gbp,
    p.cotacao_venda AS cotacao_venda_ptax,
    p.data_key AS data_ptax_key,
    base.preco_medio_gbp * p.cotacao_venda AS preco_medio_brl
FROM base
ASOF LEFT JOIN p
    ON base.moeda = p.moeda
   AND base.data_key >= p.data_key;

CREATE MATERIALIZED VIEW IF NOT EXISTS mackenzie.g00_mv_rel_telemetria_caminhao_dia
REFRESH EVERY 1 DAY OFFSET 1 HOUR
TO mackenzie.g00_rel_telemetria_caminhao_dia
AS
SELECT
    caminhao_id AS caminhao_id,
    data_key AS data_key,
    toUInt32(count()) AS leituras,
    avg(velocidade_kmh) AS velocidade_media,
    max(velocidade_kmh) AS velocidade_maxima,
    min(instante_leitura) AS primeira_leitura,
    max(instante_leitura) AS ultima_leitura,
    if(count() = 0, 0.0,
       100.0 * countIf(tachometro_codigo = '') / count()
    ) AS parte_formato_espaco_pct
FROM mackenzie.g00_fato_leitura_telemetria FINAL
WHERE data_key < toYYYYMMDD(today())
GROUP BY caminhao_id, data_key;
