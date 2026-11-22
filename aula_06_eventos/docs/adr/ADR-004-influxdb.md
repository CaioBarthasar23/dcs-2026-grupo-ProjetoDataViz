# ADR-004 - InfluxDB do painel tatico

- **Data:** 2026-11-22
- **Imagem:** `influxdb`
- **Tag fixa:** `2.10.1`
- **Lingua de consulta:** Flux
- **Motivo:** a tag oficial fixa oferece InfluxDB OSS v2, inclui Flux e permite
  inicializacao por Docker Compose; evita alterações invisíveis de `latest`.
- **Fontes consultadas:** documentação oficial do Docker Hub da imagem InfluxDB
  e documentação de instalação via Docker Compose do InfluxDB OSS v2.
- **Atualizacao:** alterar a tag deliberadamente, consultar o suporte da versão,
  validar migração e atualizar esta decisão.

Tags gravadas: `regiao`, `academia` e `tipo`. `aluno` não é tag nem campo
derivado; nunca entra em uma série. Os números de série são limitados pelas
240 academias e pelos tipos informados no contrato.

O bucket `tatico` usa retenção de 30 dias. A janela de deduplicação de
`event_id` é **hipótese, validação pendente**. Nesta implementação o padrão
configurável é 24 horas.
