# Contrato do envelope de ingestão

Este contrato valida somente a estrutura externa da mensagem. Os campos dentro de `data` não são validados nesta etapa; o schema de cada domínio fica para a Aula 07.

## Campos do envelope

| Campo | Obrigatório | Tipo e regra |
|---|---|---|
| `data_tag` | Sim | Texto cujo valor consta em `DOMINIOS`: `telemetria`, `livros` ou `ptax`. |
| `data` | Sim | Objeto JSON ou lista não vazia de objetos JSON. O conteúdo interno dos objetos não é validado por este contrato. |

O envelope é fechado: aceita somente `data_tag` e `data`. O produtor não envia `timestamp`; o servidor acrescenta o instante de ingestão em Unix, em milissegundos.

O corpo HTTP deve ter até `HTTP_MAX_BYTES`, configurado como 1 MiB (1.048.576 bytes). Corpo maior recebe 413. A API responde 400 quando o corpo não é JSON, 422 quando o JSON não satisfaz o envelope e 202 quando o envelope válido foi publicado na fila com confirmação do broker.

## Regras verificáveis

| regra | exemplo que viola | resposta |
|---|---|---|
| CT-01 — `data_tag` é obrigatório, texto e membro de `DOMINIOS`. | `invalido_422_sem_data_tag.json`; `invalido_422_data_tag_tipo.json` (número); `invalido_422_data_tag_desconhecida.json` (`vendas`). | 422 com o motivo da ausência, tipo incorreto ou domínio fora de `DOMINIOS`. |
| CT-02 — `data` é obrigatório e deve ser objeto ou lista não vazia de objetos. | `invalido_422_sem_data.json`; `invalido_422_data_texto.json`; `invalido_422_data_lista_vazia.json`; `invalido_422_lista_com_texto.json`. | 422 com o motivo da ausência ou estrutura inválida de `data`. |
| CT-03 — O envelope aceita somente `data_tag` e `data`; campo adicional é recusado. | `invalido_422_campo_extra_timestamp.json`. | 422 com o nome do campo adicional. |
| CT-04 — O corpo não excede `HTTP_MAX_BYTES` (1 MiB). | `invalido_413_corpo_grande_demais.json`. | 413, corpo grande demais. |
| CT-05 — O produtor não envia `timestamp`; esse campo é acrescentado pelo servidor como hora de ingestão Unix em milissegundos. | `invalido_422_campo_extra_timestamp.json`. | 422 com motivo de campo adicional; o servidor gera o timestamp para envelopes aceitos. |
| CT-06 — O corpo da requisição deve ser JSON. | `invalido_400_nao_json.txt`. | 400, corpo que não é JSON. |
## Exemplos

| Arquivo | Resultado esperado |
|---|---|
| `valido_telemetria_linha.json` | 202 |
| `valido_livros_objeto.json` | 202 |
| `valido_ptax_lista.json` | 202 |
| `invalido_422_sem_data_tag.json` | 422 |
| `invalido_422_data_tag_tipo.json` | 422 |
| `invalido_422_data_tag_desconhecida.json` | 422 |
| `invalido_422_data_texto.json` | 422 |
| `invalido_422_data_lista_vazia.json` | 422 |
| `invalido_422_lista_com_texto.json` | 422 |
| `invalido_422_campo_extra_timestamp.json` | 422 |
| `invalido_422_sem_data.json` | 422 |
| `invalido_413_corpo_grande_demais.json` | 413 |
| `invalido_400_nao_json.txt` | 400 |

Os exemplos preservam nomes e campos das fixtures dos domínios sem renomeá-los nem traduzi-los. Nenhum campo dentro de `data` é validado pelo contrato desta etapa.
