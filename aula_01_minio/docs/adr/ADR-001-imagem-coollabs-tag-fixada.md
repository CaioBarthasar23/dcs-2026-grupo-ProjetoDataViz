# ADR-001: imagem CoolLabs com tag fixada

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

Os ambientes local e publicado precisam ser reprodutíveis e usar a imagem
indicada em RES-04. Uma tag mutável pode alterar o serviço sem revisão.

## Requisitos e cenários relacionados

RF-03, RNF-02.

## Alternativas consideradas

1. Usar `latest`: descartada por não fixar a versão e dificultar a reprodução.
2. Usar outra imagem MinIO: descartada por não corresponder à imagem definida em
   RES-04.
3. Compilar MinIO do código-fonte: descartada porque não é necessária para os
   requisitos e cria manutenção adicional.

## Decisão

Usar `ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z` no Dockerfile e no
Compose. Tática de modificabilidade/reprodutibilidade: fixar a versão para
reduzir mudanças não controladas.

## Consequências

- Positivas: imagem e versão verificáveis nos ambientes local e Railway.
- Negativas (o trade-off): atualizações de segurança e correções não chegam
  automaticamente; o grupo precisa avaliar e alterar a tag deliberadamente.

## Riscos

A imagem comunitária pode mudar de manutenção ou disponibilidade; a tag fixada
não elimina vulnerabilidades existentes nessa versão.

## Evidência necessária

Comparar referências de imagem no Compose e Dockerfile e confirmar a versão nos
logs do serviço. Evidências existentes: `docs/evidencias/T-01_compose.txt`,
`docs/evidencias/T-02_dockerfile.txt` e `docs/evidencias/T-06_deploy.txt`.

## Condição de revisão

Reabrir se a imagem/tag deixar de estar disponível, receber vulnerabilidade que
exija atualização, ou uma restrição do grupo exigir outra distribuição.
