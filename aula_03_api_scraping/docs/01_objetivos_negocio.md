# Direcionadores e objetivos de negócio

## Direcionadores

### DN-01 · Comparação diária sem referência de preço e câmbio
- **Força:** reduzir o trabalho manual para analisar títulos e preços em libras com a cotação GBP/BRL do ciclo.
- **Quem sente:** P1.
- **Sem o sistema:** P1 compara dados coletados em momentos diferentes e pode priorizar títulos com informação desatualizada.

### DN-02 · Falhas de coleta sem diagnóstico oportuno
- **Força:** tornar verificável se a coleta diária chegou às zonas de armazenamento.
- **Quem sente:** P2.
- **Sem o sistema:** P2 pode descobrir tarde que scraping, PTAX ou gravação falhou e não saber qual etapa investigar.

### DN-03 · Bronze difícil de consumir na Aula 04
- **Força:** entregar registros extraídos legíveis e consistentes para a transformação posterior.
- **Quem sente:** P3.
- **Sem o sistema:** P3 pode precisar corrigir registros ou não conseguir associá-los ao ciclo de coleta.

## Objetivos

### OBJ-01 · Disponibilizar o snapshot diário de livros e câmbio
- **Direcionador:** DN-01.
- **Métrica:** quantidade de registros de livros em JSON Lines comparada ao total declarado pela página inicial capturada no mesmo ciclo; presença do registro GBP/BRL desse ciclo.
- **Como medir:** `mc cat local/bronze/CHAVE_LIVROS.jsonl | wc -l`; comparar com o total “N results” no HTML correspondente em `raw`. Confirmar a presença da cotação com `mc stat local/bronze/CHAVE_PTAX.jsonl`.
- **Meta:** uma coleta por dia com livros e cotação PTAX disponíveis — hipótese — validação pendente.

### OBJ-02 · Detectar ausência de dados do ciclo
- **Direcionador:** DN-02.
- **Métrica:** proporção de ciclos esperados com os objetos definidos para o ciclo presentes em `raw` e `bronze`.
- **Como medir:** para cada ciclo, executar `mc stat local/raw/CHAVE_RAW` e `mc stat local/bronze/CHAVE_BRONZE`; contar os ciclos em que ambos retornam sucesso e dividir pelo total de ciclos esperados.
- **Meta:** identificar toda ausência de dados antes do consumo por P1/P3 — hipótese — validação pendente. Alerta automático e prazo de atendimento não estão definidos.

### OBJ-03 · Entregar JSON Lines válido para a Aula 04
- **Direcionador:** DN-03.
- **Métrica:** proporção de linhas de livros e PTAX em `bronze` que são JSON válidos.
- **Como medir:** `mc cat local/bronze/CHAVE.jsonl | jq -R -e 'fromjson' >/dev/null`; o comando valida cada linha de entrada como um valor JSON. Repetir para cada objeto JSON Lines do ciclo.
- **Meta:** 100% das linhas válidas — hipótese — validação pendente.

## Restrições

| Restrição | Origem |
|---|---|
| Sem custo de API; execução em Codespace com Docker. | Ajustes do solicitante: restrições da disciplina. |
| MinIO local e MinIO no Railway (trial, 1 GB de RAM). | Ajustes do solicitante: restrições da disciplina. |
| Scraping educado: User-Agent identificável, intervalo entre requisições, sem paralelismo e consulta a `robots.txt`. | Ajustes do solicitante: restrições da disciplina. |
| Nenhum segredo versionado. | Ajustes do solicitante: restrições da disciplina. |

## Fora de escopo

- Parquet, DuckDB, camadas silver/gold e conversão de preços para reais (Aula 04).
- Agendamento em produção, painéis e tratamento de dados pessoais.

## Hipóteses

- Horário da coleta, metas, chaves e esquema dos objetos ainda precisam de validação.
- “1.000 livros” e “50 categorias” são fatos observados em 03/10/2026, não constantes nem metas permanentes.
- Comandos de medição usam `local` e nomes de chave ilustrativos; confirmar alias, chaves e formato ao definir o contrato de dados.
