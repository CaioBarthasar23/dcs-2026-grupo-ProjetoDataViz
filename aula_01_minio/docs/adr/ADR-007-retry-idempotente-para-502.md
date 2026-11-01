# ADR-007: retry idempotente para respostas 502

- Status: proposto
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

O proxy Railway pode devolver 502 durante uma escrita, sem deixar claro se a
operação foi aplicada. Repetir uma operação com outra chave pode duplicar dados.
RNF-03 pede espera crescente, chave igual e objeto único.

## Requisitos e cenários relacionados

RNF-03, CEN-04.

## Alternativas consideradas

1. Não repetir a operação: descartada como solução completa porque não trata a
   falha transitória.
2. Repetir sem manter chave/conteúdo: descartada por risco de duplicação ou
   conteúdo divergente.
3. Retry ilimitado: descartado por não ter limite operacional e poder prolongar
   carga/custo indefinidamente.

## Decisão

Proposta: repetir a mesma gravação com chave e conteúdo constantes e espera
crescente; definir limite após experimento controlado. Tática de disponibilidade:
retry para falha transitória; tática de integridade: idempotência pela mesma
chave. Não está implementada enquanto T-08 estiver pendente.

## Consequências

- Positivas: permite recuperar falhas transitórias sem criar chaves diferentes
  para a mesma gravação.
- Negativas (o trade-off): tentativas podem aumentar latência e consumo; um
  limite inadequado pode desistir cedo ou insistir demais.

## Riscos

Resultado inicial ambíguo, limites e espera ainda não foram testados. Não se
deve afirmar tolerância a 502 até T-08 passar.

## Evidência necessária

Teste controlado `bash tests/testar_retry_502.sh` conforme T-08, com 502
simulado, mesma chave, conteúdo final e tentativas registradas. Ainda sem
evidência.

## Condição de revisão

Reabrir após o teste T-08, se o proxy mudar comportamento ou se o mecanismo de
armazenamento não garantir resultado idempotente para a mesma chave.
