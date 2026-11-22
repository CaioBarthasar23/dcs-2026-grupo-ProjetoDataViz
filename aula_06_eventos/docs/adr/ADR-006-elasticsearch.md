# ADR-006 - Elasticsearch do índice operacional

- **Data:** 2026-11-22
- **Imagem:** `docker.elastic.co/elasticsearch/elasticsearch`
- **Tag fixa:** `8.17.0`
- **Lingua de consulta:** Query DSL e API REST do Elasticsearch 8.
- **Fonte oficial:** documentação Docker e mapping/cardinality da Elastic.

Plano de ciclo de vida pretendido: fases hot, warm, cold, frozen e delete.
Prazos por fase são `hipótese, validação pendente` até haver origem e
configuração definida pelo grupo.

A instância local usa `discovery.type=single-node`. Isso não verifica replicas,
shards distribuídos, consistência entre nós, relocação de shards ou alta
disponibilidade. O template fixa 3 shards primários; replica count fica como
zero neste ambiente.

Pontuações BM25 dependem das estatísticas de índice por shard. Com poucos
documentos distribuídos em vários shards, o resultado pode diferir do cálculo
manual ou de uma única partição. Métodos exclusivos: busca por motivo com
match text e cancelamentos filtrados por tipo.

Plágio ou vazamento para serviço externo não ocorre neste módulo. Todo contexto
é montado localmente a partir de trechos e agregações autorizadas.
