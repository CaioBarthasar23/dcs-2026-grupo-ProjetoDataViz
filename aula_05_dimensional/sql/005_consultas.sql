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
