# ADR-002 - Imagem e confiabilidade do Kafka

- **Data:** 2026-11-22
- **Imagem:** `apache/kafka`
- **Tag fixa:** `4.1.2`
- **Motivo:** a documentação oficial do Apache Kafka informa imagens JVM
  disponíveis a partir da versão 3.7.0 e fornece a tag `4.1.2`; a tag fixa
  evita alterações invisíveis de `latest`.
- **Fonte consultada:** https://kafka.apache.org/41/getting-started/docker/
- **Atualização:** substituir a tag deliberadamente após consultar a documentação
  da versão desejada, validar o compose e registrar o motivo nesta decisão.

O ambiente local usa um único broker: fator de replicação 1 e
`min.insync.replicas` não é uma meta operacional verificável neste ambiente.
A meta de produção é fator de replicação 3 e `min.insync.replicas=2`, sujeita
a validação em cluster de produção.
