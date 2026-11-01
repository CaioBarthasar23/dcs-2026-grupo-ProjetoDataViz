# ADR-008: evidências de verificação rastreáveis

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

RNF-04 pede evidências de verificações com ambiente e resultado identificados,
sem segredos, para sustentar revisão e rastreabilidade do projeto.

## Requisitos e cenários relacionados

RNF-04, RF-04, RF-05.

## Alternativas consideradas

1. Manter resultados somente no terminal: descartada porque não deixa registro
   durável para revisão.
2. Registrar saídas sem sanitização: descartada porque pode publicar
   credenciais ou valores sensíveis.
3. Registrar somente uma declaração de sucesso: descartada por não permitir
   auditoria do comando e do resultado observado.

## Decisão

Guardar saídas relevantes em `docs/evidencias/`, identificadas por tarefa e
ambiente; revisar antes de salvar para não incluir credenciais. Tática de
testabilidade: tornar os resultados observáveis e rastreáveis.

## Consequências

- Positivas: revisão pode comparar saída, ambiente, requisito e tarefa.
- Negativas (o trade-off): evidências podem ficar desatualizadas e exigem
  sanitização; uma evidência prova apenas o escopo do teste executado.

## Riscos

Uma saída pode conter dado sensível ou não corresponder ao critério formal;
o caso T-07 evidencia que chave e conteúdo precisam ser conferidos contra a
tarefa, não apenas contra um teste bem-sucedido.

## Evidência necessária

Arquivos T-01 a T-07 existentes em `docs/evidencias/`; comparar cada arquivo
com o critério correspondente e revisar para ausência de segredos.

## Condição de revisão

Reabrir se a política de evidências mudar, ocorrer exposição de dados, ou o
grupo exigir retenção/armazenamento diferente.
