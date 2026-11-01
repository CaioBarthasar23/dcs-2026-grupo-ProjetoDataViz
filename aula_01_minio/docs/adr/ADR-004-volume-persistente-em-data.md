# ADR-004: volume persistente montado em /data

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

RF-06/OBJ-02 requerem que objetos sobrevivam a deploys e reinícios. O contêiner
Railway pode ser substituído; RES-03 informa que volumes trial são apagados
30 dias após o fim dos créditos.

## Requisitos e cenários relacionados

RF-06, CEN-01, CEN-05.

## Alternativas consideradas

1. Manter objetos somente no filesystem do contêiner: descartada por não
   oferecer persistência após substituição do contêiner.
2. Montar volume em caminho diferente de `/data`: descartada porque o comando
   do MinIO usa `/data`.
3. Adicionar backup automático agendado: fora do escopo atual e sem requisito
   de destino/custo definido.

## Decisão

Montar o volume Railway em `/data`, mantendo os dados fora do ciclo de vida do
contêiner. Tática de disponibilidade: recuperar/reintroduzir o serviço usando
armazenamento persistente após falha ou redeploy.

## Consequências

- Positivas: os objetos podem continuar acessíveis quando o contêiner é
  substituído, conforme o teste de redeploy.
- Negativas (o trade-off): volume único cria ponto único de perda; a persistência
  não protege contra exclusão do volume, falha do provedor ou prazo de retenção
  da conta trial. Não há cópia automática independente.

## Riscos

Exclusão de volume após o prazo trial é risco confirmado. O teste de redeploy
abrange um objeto e não demonstra recuperação de inventário completo.

## Evidência necessária

Confirmar montagem em `/data` e comparar conteúdo antes/depois do redeploy.
Evidências: `docs/evidencias/T-06_deploy.txt` e
`docs/evidencias/T-07_persistencia.txt`.

## Condição de revisão

Reabrir se a política de retenção mudar, ocorrer perda de dados, o volume deixar
de montar em `/data`, ou o grupo definir requisito de cópia/recuperação.
