# Aula 06 - Gerador de eventos

Gera eventos sintéticos, anonimizados na borda e armazenados em JSONL local.

```bash
export ANON_CHAVE='chave-sintetica-local'
python -m src.gerador.cli --quantidade 1000 --semente 42
python -m src.gerador.cli --quantidade 1000 --semente 42
python -m pytest -q
```

O arquivo padrão é `outbox/eventos.jsonl`. Cada linha contém `estado`:
`pendente` ou `enviado`, e o evento. Nenhum nome ou identificador cadastral real
é armazenado. A execução define uma taxa e proporções parametrizáveis; os
valores padrão são hipóteses sem fonte.

## Kafka local

```bash
docker compose up -d
docker compose ps
python -m pip install -r requirements-kafka.txt
python src/kafka/criar_topico.py
python -m src.kafka.produtor --outbox outbox/eventos.jsonl
python -m src.kafka.verificador --maximo 10
docker exec tatame-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --describe --topic tatame.eventos
docker exec tatame-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group verificacao
python -m pytest -q
```

O broker usa `apache/kafka:4.1.2`, tópico `tatame.eventos` com 6 partições,
fator de replicação 1 e retenção de 604800000 ms (7 dias). Vazão não foi
medida neste ambiente; qualquer meta de vazão fica como
`hipótese, validação pendente`.

## CEP

```bash
python -m src.cep.consumidor
python -m pytest -q
```

O consumidor usa o grupo `cep`, lê `tatame.eventos` e publica complexos em
`tatame.alertas`. Quantidades e janelas são hipótese, validação pendente.

## Sink InfluxDB

```bash
docker compose up -d
python -m src.sink_influxdb.consumidor
python src/sink_influxdb/cardinalidade.py
python -m pytest -q
```

O sink usa o grupo `sink-influxdb`, agrega por minuto no measurement `eventos`,
com tags `regiao`, `academia` e `tipo`. `aluno` nunca é tag.

## Elasticsearch

```bash
docker compose up -d elasticsearch
python -m src.indexador.indexador
python -m src.indexador.indexador
python -m pytest -q
```

Índices: `tatame-eventos-AAAA.MM`. Template com 3 shards primários.
A busca por motivos usa BM25; pontuações dependem das estatísticas por shard.
A janela de deduplicação é hipótese, validação pendente.

## Sink lake

```bash
docker compose up -d
python -m src.sink_lake.consumidor
python -m src.sink_lake.conferir_lotes --inicio 0 --fim 100
python -m src.sink_lake.medir_compressao
```

Os lotes JSONL gzip são gravados em `tatame-bruto` no padrão
`regiao=<regiao>/data=<AAAA-MM-DD>/hora=<HH>/lote-<n>.jsonl.gz`.
