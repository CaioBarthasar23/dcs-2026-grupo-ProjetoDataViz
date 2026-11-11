# ADR-003 · Retry com backoff exponencial, full jitter e Retry-After

**Status:** Proposta

## Contexto

DN-02 requer falhas transitórias diagnosticáveis e recuperação controlada. RF-05, RF-06, RF-07 e RF-16 dependem de requisições HTTP; RNF-02 exige timeout explícito e RNF-06 permite retries apenas para falhas transitórias, limitados por configuração. Clientes que repetem uma falha ao mesmo tempo podem voltar a concentrar chamadas; para este monitor, a coleta do site é sequencial, mas retries ainda precisam respeitar limites e instruções do servidor.

## Decisão

Repetir timeout, erro de conexão e respostas 408, 429 e 5xx até `HTTP_MAX_TENTATIVAS`. Para a tentativa k, usar full jitter uniforme entre 0 e `min(teto, base × 2^k)`, com k iniciando em 0. Quando houver `Retry-After` válido, respeitar o tempo indicado pelo servidor. Outros 4xx não são repetidos. Timeout, base, teto e máximo de tentativas permanecem configuráveis e, conforme RNF-02/RNF-06, números sem validação são hipóteses pendentes.

## Alternativas

- Intervalo fixo entre retries.
- Backoff exponencial sem jitter.
- Não repetir falhas.
- Repetir qualquer código HTTP, inclusive erros permanentes.

## Consequências

- O atraso aleatório reduz sincronização entre tentativas, e `Retry-After` respeita a orientação do servidor.
- O limite evita retry infinito, mas uma falha persistente termina a execução com erro registrado no manifesto.
- A duração da coleta varia e pode aumentar com retries.
- É preciso testar limites, classificação de erros e tratamento de `Retry-After` com relógio e aleatoriedade controláveis.
- Não se assume redução quantitativa de pico sem ensaio com carga representativa; volume concorrente é especialmente limitado pela coleta sequencial.

**Origem:** DN-02; RF-05, RF-06, RF-07, RF-16; RNF-02, RNF-06.

**Diagramas da Etapa 08:** [coleta Books](../modelagem/dinamica/coleta_books.md), [coleta PTAX](../modelagem/dinamica/coleta_ptax.md), [gravação raw](../modelagem/dinamica/gravacao_raw.md).

**Referências:** [RNFs](../../specs/02_requisitos_nao_funcionais.md), [cliente HTTP e classes](../classes.md).
