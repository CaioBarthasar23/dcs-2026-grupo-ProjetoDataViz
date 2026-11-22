# ADR-005 - Sink bruto no object storage

- **Data:** 2026-11-22
- **Armazenamento:** RustFS compatível com S3, cliente `boto3`, reaproveitando
  o padrão S3 já usado nas aulas anteriores.
- **Imagem:** `rustfs/rustfs:1.0.0-alpha.68`
- **Motivo:** essa tag fixa identifica uma release específica do MinIO e evita
  atualização invisível por `latest`. A atualização deve ser registrada nesta
  decisão após validar compatibilidade S3.

## Lote

Os valores padrão são hipótese, validação pendente:
`FECHAR_LOTE_MINUTOS=10` e `FECHAR_LOTE_BYTES=5242880`.
Fechar cedo reduz atraso de consulta, mas cria mais objetos e aumenta custo de
gerenciamento. Fechar tarde reduz objetos e melhora compressão, mas aumenta
tempo até disponibilidade no bucket.

## Particionamento

`PARTICIONAR_POR=evento` usa `ocorrido_em`: eventos atrasados podem escrever em
uma partição antiga, útil para reconstituição histórica e menos previsível para
carteiras de chegada recente. `chegada` usa a hora em que o sink lê o evento:
produz partições próximas ao processamento, mas separa eventos antigos da hora
original e dificulta reconstrução histórica cronológica.

## Imutabilidade

Cada lote usa `particao+primeiro_offset` em `lote-<n>.jsonl.gz`. Regravação
produz a mesma chave. O sink compara o objeto existente: bytes iguais permitem
nenhuma alteração; bytes diferentes são recusados.

Credenciais ficam em `.env`, fora do Git.
