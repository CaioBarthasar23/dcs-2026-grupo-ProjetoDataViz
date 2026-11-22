# Views no ClickHouse

## Três formas

### VIEW comum

É uma consulta nomeada; não guarda linhas próprias. Cada `SELECT` recompila sua
consulta sobre os dados atuais das tabelas referenciadas. Custa CPU, memória e
I/O no momento da leitura. Pode usar uma janela temporal, por exemplo:

```sql
WHERE minuto >= now() - INTERVAL 15 MINUTE
```

É adequada para observabilidade corrente e para evitar replicar dados derivados.

### MATERIALIZED VIEW ... TO incremental

Não guarda o resultado do `SELECT` nesta view; guarda e encaminha linhas novas
para uma tabela destino `TO`. O `SELECT` roda durante um `INSERT` na tabela
esquerda, sobre o bloco inserido, não sobre todo o histórico. O destino fica
quase imediato, mas o custo é pago na escrita daquele bloco. Com repetições,
`ReplacingMergeTree(versao_ms)` permite estabilizar leitura com `FINAL`.

Exemplo: um bloco de 40 linhas inserido em `db_ingestion` faz
`g00_mv_fato_leitura_telemetria` executar seu `SELECT` sobre essas 40 linhas,
e somente elas.

### MATERIALIZED VIEW ... REFRESH refreshable

É uma tarefa periódica com período definido. O `SELECT` roda no refresh
programado sobre o estado daquela execução e grava o resultado no destino ou
cache da view. O resultado é tão atual quanto o último refresh concluído; o
custo é pago no refresh conforme tamanho dos dados e a carga do servidor.

É adequada a cubos fechados e agregados que podem tolerar frescor periódico.
No projeto não é criada uma refreshable nesta etapa.

## Quadro comparativo

| Forma | O que guarda | Quando o SELECT roda | Dados consultados | Atualidade | Quando o custo é pago |
|---|---|---|---|---|---|
| `VIEW` comum | Definição da consulta, não linhas | A cada `SELECT` da view | Estado atual das tabelas referenciadas | Atual na leitura | Na consulta |
| `MATERIALIZED VIEW ... TO` | Linhas derivadas na tabela `TO` | Em cada `INSERT` de bloco na tabela esquerda | Apenas linhas do bloco novo | Próxima à origem | Na escrita do bloco |
| `MATERIALIZED VIEW ... REFRESH` | Resultado materializado da última execução | Conforme agenda de refresh | Estado escolhido pelo refresh | Até o último refresh concluído | No período de refresh |

## Consequências da incremental

- Não processa automaticamente o histórico já existente: a carga histórica
  exige `INSERT ... SELECT` separado, como `002_carga_historico.sql`.
- Não vê `UPDATE`, `DELETE` ou merges da origem como eventos completos; para
  corrigir linhas, use versão ou recarga controlada e leia o destino com
  `FINAL` quando o engine suportar deduplicação.
- Agrega por bloco. Uma soma ou contagem pode exigir reparação ou
  reprocessamento para representar o total histórico corretamente.
- Em `JOIN`, só a tabela da esquerda dispara a view incremental. Alterações
  na tabela da direita não disparam o `SELECT`.
- Um erro no `SELECT` da view derruba o `INSERT` na origem. Em
  `mackenzie`, isso pode barrar temporariamente o mesmo canal compartilhado
  usado pela turma.
- Funciona em cascata: uma view escreve uma tabela que pode disparar outra
  view, como `g00_mv_dim_caminhao` lê `g00_fato_leitura_telemetria`.

## Objetos do grupo registrados pelo banco

Consulta usada:

```sql
SELECT name, engine, engine_full, total_rows
FROM system.tables
WHERE database='mackenzie' AND startsWith(name,'g00_')
ORDER BY name;
```

O resultado confirma 15 objetos próprios listados abaixo. `engine_full=''`
em views é consistente com a declaração visual em `system.tables`; o tipo
é identificado por `engine`.

| Nome | Tipo |
|---|---|
| `g00_dim_caminhao` | `AggregatingMergeTree` |
| `g00_dim_data` | `MergeTree` |
| `g00_dim_livro` | `ReplacingMergeTree` |
| `g00_fato_alerta_direcao` | `ReplacingMergeTree` |
| `g00_fato_cotacao_ptax` | `ReplacingMergeTree` |
| `g00_fato_leitura_telemetria` | `ReplacingMergeTree` |
| `g00_fato_preco_livro` | `ReplacingMergeTree` |
| `g00_mv_dim_caminhao` | `MaterializedView` |
| `g00_mv_dim_caminhao_20261029` | `MaterializedView` |
| `g00_mv_dim_livro` | `MaterializedView` |
| `g00_mv_fato_alerta_direcao` | `MaterializedView` |
| `g00_mv_fato_cotacao_ptax` | `MaterializedView` |
| `g00_mv_fato_leitura_telemetria` | `MaterializedView` |
| `g00_mv_fato_preco_livro` | `MaterializedView` |
| `g00_v_dim_caminhao` | `View` |

Outros objetos `g00_tel_*`, `g00_tel_mv_*` e `g00_tel_v_*` também apareceram
no filtro da consulta. Eles pertencem ao conjunto do grupo, mas não fazem
parte da especificação dimensional criada nesta etapa.

## Regras do projeto

- Use incremental para fatos e dimensões derivadas de novos blocos.
- Use refreshable para cubos fechados que toleram latência de refresh.
- Use view comum com janela para observabilidade corrente.
- Não use WINDOW VIEW nesta implementação.
- Não use LIVE VIEW nesta implementação.

## Fora de escopo

WINDOW VIEW é experimental no ClickHouse 25.8 e exige
`allow_experimental_analyzer = 0` na criação e na leitura.

LIVE VIEW é obsoleta e não faz parte da arquitetura.

## EXPLAIN de uma view comum

Pendente. Será completado na Etapa 05, quando
`mackenzie.g00_v_saude_ingestao_15min` existir.
