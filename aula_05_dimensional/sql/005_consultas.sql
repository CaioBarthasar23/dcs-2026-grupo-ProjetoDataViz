-- 1. Teste do grão: sem FINAL e com FINAL, comparando linhas e uniqExact.
SELECT 'g00_fato_preco_livro' AS fato, 'sem FINAL' AS modo,
       count() AS linhas,
       uniqExact(tuple(data_key, upc)) AS chaves
FROM mackenzie.g00_fato_preco_livro
UNION ALL
SELECT 'g00_fato_preco_livro', 'com FINAL',
       count(), uniqExact(tuple(data_key, upc))
FROM mackenzie.g00_fato_preco_livro FINAL
UNION ALL
SELECT 'g00_fato_cotacao_ptax', 'sem FINAL',
       count(), uniqExact(tuple(data_key, moeda, data_hora_cotacao, tipo_boletim))
FROM mackenzie.g00_fato_cotacao_ptax
UNION ALL
SELECT 'g00_fato_cotacao_ptax', 'com FINAL',
       count(), uniqExact(tuple(data_key, moeda, data_hora_cotacao, tipo_boletim))
FROM mackenzie.g00_fato_cotacao_ptax FINAL
UNION ALL
SELECT 'g00_fato_leitura_telemetria', 'sem FINAL',
       count(), uniqExact(tuple(data_key, caminhao_id, instante_leitura))
FROM mackenzie.g00_fato_leitura_telemetria
UNION ALL
SELECT 'g00_fato_leitura_telemetria', 'com FINAL',
       count(), uniqExact(tuple(data_key, caminhao_id, instante_leitura))
FROM mackenzie.g00_fato_leitura_telemetria FINAL
UNION ALL
SELECT 'g00_fato_alerta_direcao', 'sem FINAL',
       count(), uniqExact(tuple(data_key, caminhao_id, instante_alerta, duracao_continua_min))
FROM mackenzie.g00_fato_alerta_direcao
UNION ALL
SELECT 'g00_fato_alerta_direcao', 'com FINAL',
       count(), uniqExact(tuple(data_key, caminhao_id, instante_alerta, duracao_continua_min))
FROM mackenzie.g00_fato_alerta_direcao FINAL;

-- 2. Rotear cada linha de telemetria para leitura barra, leitura espaço, alerta ou descarte.
SELECT
    multiIf(
        position(data_json.linha::String, 'ERR SAT') > 0,
        'descarte ERR SAT',
        position(data_json.linha::String, 'RADIO') > 0,
        'descarte RADIO',
        startsWith(data_json.linha::String, 'TAC;')
            AND position(data_json.linha::String, 'DIRECAO CONTINUA') > 0,
        'alerta',
        startsWith(data_json.linha::String, 'CAM-')
            AND position(data_json.linha::String, '|') > 0,
        'leitura barra',
        startsWith(data_json.linha::String, 'CAM-')
            AND position(data_json.linha::String, ' GPS ') > 0,
        'leitura espaço',
        'descarte outro'
    ) AS destino,
    count() AS linhas
FROM mackenzie.db_ingestion
WHERE data_tag = 'telemetria'
GROUP BY destino
ORDER BY destino;

-- 3. Estrela: preco medio por categoria e dia da semana.
SELECT
    l.categoria AS categoria,
    d.dia AS dia,
    d.dia_da_semana AS dia_da_semana,
    avg(f.preco_gbp) AS preco_medio_gbp
FROM mackenzie.g00_fato_preco_livro AS f FINAL
INNER JOIN mackenzie.g00_dim_livro AS l FINAL ON f.upc = l.upc
INNER JOIN (
    SELECT
        data_key,
        toDate(parseDateTimeOrNull(concat(substring(toString(data_key), 1, 4), '-', substring(toString(data_key), 5, 2), '-', substring(toString(data_key), 7, 2)), '%Y-%m-%d')) AS dia,
        toDayOfWeek(toDate(parseDateTimeOrNull(concat(substring(toString(data_key), 1, 4), '-', substring(toString(data_key), 5, 2), '-', substring(toString(data_key), 7, 2)), '%Y-%m-%d'))) AS dia_da_semana
    FROM mackenzie.g00_dim_data
) AS d ON f.data_key = d.data_key
GROUP BY categoria, d.dia, d.dia_da_semana
ORDER BY preco_medio_gbp DESC;

-- 4. Alertas por caminhao com velocidade media do dia.
SELECT
    a.caminhao_id,
    a.data_key,
    count() AS alertas,
    r.velocidade_media,
    r.velocidade_maxima
FROM mackenzie.g00_fato_alerta_direcao AS a FINAL
LEFT JOIN mackenzie.g00_rel_telemetria_caminhao_dia AS r
    ON a.caminhao_id = r.caminhao_id
   AND a.data_key = r.data_key
GROUP BY a.caminhao_id, a.data_key, r.velocidade_media, r.velocidade_maxima
ORDER BY alertas DESC, a.caminhao_id
SETTINGS join_use_nulls = 1;

-- 5. Views do grupo e seus tipos.
SELECT name, engine
FROM system.tables
WHERE database = 'mackenzie'
  AND startsWith(name, 'g00_')
  AND engine IN ('View', 'MaterializedView')
ORDER BY name;

-- 6. EXPLAIN da view comum de saude.
EXPLAIN SELECT * FROM mackenzie.g00_v_saude_ingestao_15min;

-- 7. Estado das refreshable do grupo.
SELECT
    view,
    status,
    last_success_time,
    last_refresh_time,
    next_refresh_time,
    exception,
    total_rows,
    written_rows
FROM system.view_refreshes
WHERE database = 'mackenzie'
  AND startsWith(view, 'g00_mv_rel_')
ORDER BY view;

-- 8. Tres views em janela.
SELECT * FROM mackenzie.g00_v_saude_ingestao_15min;
SELECT * FROM mackenzie.g00_v_caminhoes_5min;
SELECT * FROM mackenzie.g00_v_descartes_telemetria_1h;

-- P1. Categoria com pelo menos 5 livros e maior preco medio em BRL.
SELECT
    r.categoria,
    r.livros,
    r.preco_medio_brl
FROM
(
    SELECT
        categoria,
        sum(livros) AS livros,
        avg(preco_medio_brl) AS preco_medio_brl
    FROM mackenzie.g00_rel_preco_categoria_dia
    GROUP BY categoria
) AS r
WHERE r.livros >= 5
ORDER BY r.preco_medio_brl DESC
LIMIT 1;

-- P2. Exemplares em estoque por categoria.
SELECT
    l.categoria,
    sum(f.qtd_estoque) AS exemplares_estoque
FROM mackenzie.g00_fato_preco_livro AS f FINAL
INNER JOIN mackenzie.g00_dim_livro AS l FINAL ON f.upc = l.upc
WHERE f.data_key = (SELECT max(data_key) FROM mackenzie.g00_fato_preco_livro FINAL)
GROUP BY l.categoria
ORDER BY exemplares_estoque DESC;

-- P3. Hora do dia com maior velocidade media.
SELECT
    toHour(instante_leitura) AS hora,
    avg(velocidade_kmh) AS velocidade_media
FROM mackenzie.g00_fato_leitura_telemetria FINAL
GROUP BY hora
ORDER BY velocidade_media DESC
LIMIT 1;

-- P4. Caminhao com mais tempo acumulado ao volante sem pausa.
SELECT
    caminhao_id,
    sum(duracao_continua_min) AS tempo_sem_pausa_min,
    count() AS alertas
FROM mackenzie.g00_fato_alerta_direcao FINAL
GROUP BY caminhao_id
ORDER BY tempo_sem_pausa_min DESC
LIMIT 1;

-- P5. Venda do GBP no primeiro e ultimo Fechamento.
SELECT
    argMin(cotacao_venda, data_hora_cotacao) AS venda_primeiro,
    argMax(cotacao_venda, data_hora_cotacao) AS venda_ultimo,
    venda_ultimo - venda_primeiro AS variacao,
    if(venda_ultimo > venda_primeiro, 'subiu', if(venda_ultimo < venda_primeiro, 'caiu', 'igual')) AS tendencia
FROM mackenzie.g00_fato_cotacao_ptax FINAL
WHERE moeda = 'GBP'
  AND tipo_boletim IN ('Fechamento', 'Fechamento PTAX');
