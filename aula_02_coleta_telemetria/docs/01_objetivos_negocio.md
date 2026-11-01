# Objetivos de negócio do coletor de telemetria

## Objetivos

### OBJ-01 Preservar evidência da jornada
- Descrição: manter os lotes recebidos sem alteração para consulta posterior sobre a jornada, inclusive em fiscalizações ou processos.
- Personas atendidas: P-01; P-02.

### OBJ-02 Reduzir perda de janelas de telemetria
- Descrição: conservar os lotes recebidos de cada caminhão para apoiar o acompanhamento de jornada e posição e consultas posteriores.
- Personas atendidas: P-01; P-02.

### OBJ-03 Dar visibilidade sobre a coleta
- Descrição: permitir que a mantenedora saiba se uma execução ocorreu, o que permaneceu no pouso e o que falhou.
- Personas atendidas: P-03.

## Métricas de sucesso
- OBJ-01: proporção de janelas com lote preservado e integridade verificável, por caminhão e período. Meta: hipótese, validação pendente.
- OBJ-02: proporção de janelas esperadas com lote recebido e preservado, por caminhão e período. Meta: hipótese, validação pendente.
- OBJ-03: proporção de execuções com resultado identificável, incluindo lotes recebidos, pendentes no pouso e falhas. Meta: hipótese, validação pendente.
- Retransmissões: proporção de lotes retransmitidos identificados sem perder nem sobrescrever o original. Meta: hipótese, validação pendente.
- Frequência do acompanhamento das métricas: hipótese, validação pendente.

## Drivers de negócio
- Integridade verificável: necessária para sustentar o uso dos registros como evidência (P-01).
- Completude das janelas: reduz o risco de não haver registros quando forem consultados (P-01, P-02).
- Rastreabilidade da origem e do recebimento: ajuda a localizar lotes e entender ocorrências de coleta (P-01, P-03).
- Tratamento consistente de retransmissões: evita confusão ou perda de evidência quando o provedor repete um lote.
- Visibilidade de falhas e pendências: apoia a investigação e a decisão de recoleta (P-03; hipótese, validação pendente).
- Custo previsível: operação deve respeitar os limites de orçamento informados.

## Restrições
- Armazenamento em object storage MinIO, com API compatível com S3, no bucket `raw`. Origem: restrição fornecida pelo professor.
- Execução local via docker compose e publicação no MinIO do Railway criado na Aula 01. Origem: restrição fornecida pelo professor.
- Orçamento limitado ao crédito do plano de teste do Railway (US$ 5, até 30 dias) e, depois, ao plano Free (US$ 1/mês). Origem: restrição fornecida pelo professor.
- Fonte: lotes do provedor por satélite, simulados pelo `gerar_lotes.py` na pasta `pouso/`, que faz o papel do SFTP; o provedor não guarda histórico e às vezes retransmite um lote. Origem: restrição fornecida pelo professor.
- Nenhum segredo em arquivo versionado. Origem: restrição fornecida pelo professor.

## Fora de escopo
- Integração com o SFTP real; a pasta `pouso/` faz o papel do SFTP nesta etapa.
- Interpretar ou transformar o conteúdo dos lotes; criar parser.
- Criar painel.
- Definir decisões operacionais além do acompanhamento de jornada e posição informado pela coordenação.
- Definir prazo de retenção legal ou metas de disponibilidade sem validação do cliente.

## Fatos/lacunas/suposições
- Fatos: lotes TXT chegam a cada 15 minutos por caminhão; o provedor não mantém histórico e pode retransmitir lotes. O jurídico precisa consultar registros posteriormente e verificar integridade; a coordenação acompanha jornada e posição.
- Lacunas: meta aceitável de falhas ou janelas ausentes; período de medição; prazo de guarda; como identificar caminhões e janelas; critérios para tratar retransmissões.
- Suposições: métricas agregadas por caminhão e período são úteis para acompanhar os objetivos (hipótese, validação pendente). Nenhuma meta de sucesso foi definida.
