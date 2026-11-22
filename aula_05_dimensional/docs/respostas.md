# Respostas de negócio

## P1

**Resposta:** New Adult tem o maior preço médio em BRL entre categorias com pelo menos 5 livros: 333,4915 BRL.
**Número:** 6 livros; 333,4915 BRL. **Origem:** `g00_rel_preco_categoria_dia`. **Medida:** preço não aditivo; média.

```sql
WITH totais AS (
  SELECT categoria, sum(livros) AS livros, avg(preco_medio_brl) AS preco_medio_brl
  FROM mackenzie.g00_rel_preco_categoria_dia GROUP BY categoria
)
SELECT categoria, livros, preco_medio_brl FROM totais
WHERE livros >= 5 ORDER BY preco_medio_brl DESC LIMIT 1;
```

## P2

**Resposta:** Default lidera o estoque no último dia: 1.345 exemplares.
**Número:** 1.345. **Origem:** `g00_fato_preco_livro FINAL` e `g00_dim_livro FINAL`. **Medida:** semiaditiva por dia; soma entre livros.

```sql
SELECT l.categoria, sum(f.qtd_estoque) AS exemplares_estoque
FROM mackenzie.g00_fato_preco_livro AS f FINAL
INNER JOIN mackenzie.g00_dim_livro AS l FINAL ON f.upc=l.upc
WHERE f.data_key=(SELECT max(data_key) FROM mackenzie.g00_fato_preco_livro FINAL)
GROUP BY l.categoria ORDER BY exemplares_estoque DESC;
```

## P3

**Resposta:** A hora 0 teve a maior velocidade média observada: 78,3675 km/h.
**Número:** 78,3675 km/h. **Origem:** `g00_fato_leitura_telemetria FINAL`. **Medida:** velocidade não aditiva; média.

```sql
SELECT toHour(instante_leitura) AS hora, avg(velocidade_kmh) AS velocidade_media
FROM mackenzie.g00_fato_leitura_telemetria FINAL
GROUP BY hora ORDER BY velocidade_media DESC LIMIT 1;
```

## P4

**Resposta:** CAM-5707 acumulou o maior tempo sem pausa: 4.076 minutos.
**Número:** 4.076 minutos; 12 alertas. **Origem:** `g00_fato_alerta_direcao FINAL`. **Medida:** duração semiaditiva por evento; soma entre eventos não simultâneos.

```sql
SELECT caminhao_id, sum(duracao_continua_min) AS tempo_sem_pausa_min, count() AS alertas
FROM mackenzie.g00_fato_alerta_direcao FINAL
GROUP BY caminhao_id ORDER BY tempo_sem_pausa_min DESC LIMIT 1;
```

## P5

**Resposta:** A venda do GBP subiu entre o primeiro e o último fechamento.
**Número:** de 6,7072 para 7,1899; variação de 0,4827. **Origem:** `g00_fato_cotacao_ptax FINAL`. **Medida:** cotação não aditiva; primeiro e último valor.

```sql
WITH m AS (
  SELECT argMin(cotacao_venda,data_hora_cotacao) AS venda_primeiro,
         argMax(cotacao_venda,data_hora_cotacao) AS venda_ultimo
  FROM mackenzie.g00_fato_cotacao_ptax FINAL
  WHERE moeda='GBP' AND tipo_boletim IN ('Fechamento','Fechamento PTAX')
)
SELECT venda_primeiro,venda_ultimo,venda_ultimo-venda_primeiro AS variacao,
  if(venda_ultimo>venda_primeiro,'subiu',if(venda_ultimo<venda_primeiro,'caiu','igual')) AS tendencia
FROM m;
```
