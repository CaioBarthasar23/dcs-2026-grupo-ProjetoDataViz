# Registro de prompts

## Etapa CEP

- Data: 2026-11-22
- Prompt: implementar quatro regras CEP, estado persistente,
  timers, atrasados e consumidor do grupo cep.
- Comandos executados:

```bash
python -m pytest -q
python src/kafka/criar_topico.py
python -m src.cep.consumidor
docker exec tatame-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic tatame.alertas --from-beginning
```

- Validação: 28 testes aprovados.
- Live gate: par isolado `cep-pair-a` e `cep-pair-b` produziu
  `cobranca_reincidente` com os dois IDs em `eventos_origem`.
- Grupo `cep`: lag zero em todas as partições após o dreno.
- Estado persistido em `estado/cep.json`.

## Etapa Kafka

- Data: 2026-11-22
- Prompt: adicionar broker KRaft, tópico, produtor, verificador e ADR.
- Imagem: `apache/kafka:4.1.2`.
- Comandos executados:

```bash
docker compose up -d
docker compose ps
python -m pip install -r requirements-kafka.txt
python src/kafka/criar_topico.py
python -m pytest -q tests/test_integracao_kafka.py
python -m pytest -q
python -m src.kafka.verificador --maximo 10
```

- Broker: saudável em `docker compose ps`.
- Tópico: 6 partições, RF=1, `retention.ms=604800000`.
- Integração: 1 teste aprovado.
- Suíte: 15 testes aprovados.
- Grupo `verificacao`: lag zero após dez mensagens consumidas.
- Gate de lag: com o verificador parado, `CURRENT-OFFSET=10`,
  `LOG-END-OFFSET=110`, `LAG=100`.

## Etapa InfluxDB

- Data: 2026-11-22
- Prompt: adicionar InfluxDB OSS v2, sink por minuto,
  consultas Flux e deduplicação por event_id.
- Imagem: `influxdb:2.10.1`.
- Bucket: `tatico`, retenção 720 horas.
- Comandos executados:

```bash
docker compose up -d
python -m pytest -q
python src/sink_influxdb/cardinalidade.py
docker exec tatame-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group sink-influxdb
```

- Suíte: 33 testes aprovados.
- Cardinalidade observada após carga sintética:
  `122` combinações aproximadas de região, academia e tipo.
- Limite teórico observado: menor que `240 * tipos`.
- Reprocessamento: reset para earliest; cardinalidade permaneceu 122
  e o grupo terminou com lag zero em todas as partições.
- Janela de deduplicação: `24h`, hipótese, validação pendente.

## Etapa Elasticsearch

- Data: 2026-11-22
- Prompt: indexar lotes JSONL.gz em índices mensais, entregar consultas,
  comparação de cardinalidade exata/estimada e contexto local.
- Imagem: `docker.elastic.co/elasticsearch/elasticsearch:8.17.0`.
- Template: índice `tatame-eventos-*`, 3 shards primários,
  replica count 0 no nó único.
- Busca: motivo `preço` em cancelamentos; 1 documento,
  `_score=0.2876821`.
- Contagens: bucket distinto 145; índice 145.
- Alunos únicos: exato 2, estimativa 2, diferença 0%.
- Contexto gerado em `docs/contexto_pergunta.md` sem modelo ou rede externa.

## Etapa Lake

- Imagem object storage: `rustfs/rustfs:1.0.0-alpha.68`.
- Bucket: `tatame-bruto`.
- Chaves observadas em todas as regiões:
  `sa-saopaulo`, `us-virginia`, `eu-estocolmo`, `ap-sydney`.
- Compressao medida em 100 eventos sinteticos:
  antes `15090` bytes, gzip `441` bytes,
  taxa `0.029225`.
- Conferencia: 146 eventos validos no topico e 146 no bucket no intervalo,
  com IDs anteriores de teste repetidos registrados como evidência.
- Dedupe persistente: implementado por `event_id` em estado local.

- Resultado de conferência: `topico_linhas=146`,
  `bucket_linhas=146`, `iguais=True`.
- Resultados históricos dos IDs `gate-cobranca-1` e
  `gate-cobranca-2` estavam duplicados no bucket antigo;
  a deduplicação persistente foi adicionada para reprocessamentos futuros.
- Compressão: 100 eventos: antes `15090` bytes, gzip `441` bytes,
  taxa `0.029225`.
- Grupo `sink-lake`: lag zero em todas as partições após o dreno final.

## Etapa Lake bruto

- Data: 2026-11-22
- Prompt: adicionar sink S3 bruto, lotes gzip e conferência de integridade.
- Armazenamento: RustFS `rustfs/rustfs:1.0.0-alpha.68`.
- Bucket: `tatame-bruto`.
- Padrão: `regiao=<regiao>/data=<AAAA-MM-DD>/hora=<HH>/lote-<n>.jsonl.gz`.
- Comandos executados:

```bash
docker compose up -d
python -m pytest -q
python -m src.sink_lake.conferir_lotes --inicio 0 --fim 100
python -m src.sink_lake.medir_compressao
```

- Lotes: fechados por tempo ou tamanho; valores padrão marcados como
  hipótese, validação pendente.
