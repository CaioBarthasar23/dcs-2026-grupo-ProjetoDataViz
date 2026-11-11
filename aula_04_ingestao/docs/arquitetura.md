# Arquitetura da ingestão

## Componentes

```mermaid
flowchart LR
  PH["Produtor HTTP"] -->|POST /ingest| API["API"]
  API -->|publica mensagem persistente| Q[("Fila ingestao")]
  PA["Produtor AMQP"] -->|publica mensagem persistente| Q
  Q -->|entrega| C["Consumidor"]
  C --> B["Buffer de micro-lote"]
  B --> GR["Gravador do raw"]
  B --> GB["Gravador do bronze DuckDB"]
  B --> GC["Gravador do ClickHouse"]
  B --> GM["Gravador do manifesto"]
  GR -->|JSON Lines| R[("RustFS")]
  GB -->|Parquet| R
  GM -->|manifesto| R
  GC --> CH[("ClickHouse")]
  B -->|ack após gravações| Q
```

HTTP publica pela API; o produtor AMQP publica na fila. O consumidor valida mensagens e acumula envelopes no buffer. No flush, os gravadores persistem raw, bronze, ClickHouse e manifesto nessa ordem. O consumidor confirma as mensagens após as gravações.

## Sequência: caminho feliz

```mermaid
sequenceDiagram
  participant PH as Produtor HTTP
  participant API as API
  participant PA as Produtor AMQP
  participant Q as Fila ingestao
  participant C as Consumidor
  participant B as Buffer de micro-lote
  participant GR as Gravador do raw
  participant GB as Gravador do bronze DuckDB
  participant GC as Gravador do ClickHouse
  participant GM as Gravador do manifesto
  participant R as RustFS
  participant CH as ClickHouse
  PH->>API: POST /ingest
  API->>Q: publicar mensagem persistente
  API-->>PH: 202 após confirmação do broker
  PA->>Q: publicar mensagem persistente
  Q->>C: entregar mensagem
  C->>C: validar envelope
  C->>B: acumular envelope
  Note over B: flush quando atingir FLUSH_N ou FLUSH_SEGUNDOS
  B->>GR: gravar envelope do lote
  GR->>R: raw JSON Lines
  B->>GB: gravar objetos de data
  GB->>R: bronze Parquet
  B->>GC: inserir lote
  GC->>CH: INSERT
  B->>GM: gravar manifesto status ok
  GM->>R: manifesto
  C->>Q: ack após todas as gravações
```

## Sequência: falha do ClickHouse no meio do lote

```mermaid
sequenceDiagram
  participant Q as Fila ingestao
  participant C as Consumidor
  participant B as Buffer de micro-lote
  participant GR as Gravador do raw
  participant GB as Gravador do bronze DuckDB
  participant GC as Gravador do ClickHouse
  participant GM as Gravador do manifesto
  participant R as RustFS
  participant CH as ClickHouse
  Q->>C: entregar mensagens sem ack
  C->>B: acumular e validar
  B->>GR: gravar raw
  GR->>R: JSON Lines
  B->>GB: gravar bronze
  GB->>R: Parquet
  B->>GC: inserir lote
  GC->>CH: INSERT do lote
  CH-->>GC: falha durante o lote
  GC-->>B: reportar erro
  B->>GM: gravar manifesto status erro
  GM->>R: manifesto de falha
  Note over C,Q: sem ack para permitir nova entrega
```

## Decisões registradas

| Decisão | ADR | Requisitos relacionados |
|---|---|---|
| API HTTP publica na fila | ADR-001 | RF-01, RF-02, RF-03 |
| Persistir raw e bronze antes do ClickHouse | ADR-002 | RF-06, RF-07, RF-08, RNF-04 |
| Manifesto depois do ClickHouse e ack só após tudo gravado | ADR-003 | RF-09, RF-10, RF-11, RNF-02 |
| Buffer com flush por tamanho ou tempo | ADR-004 | RF-06 a RF-10, RNF-01 |
| Tabela comum de três colunas com `data_json JSON` | ADR-005 | RF-07, RF-08, RNF-03, RNF-04 |
