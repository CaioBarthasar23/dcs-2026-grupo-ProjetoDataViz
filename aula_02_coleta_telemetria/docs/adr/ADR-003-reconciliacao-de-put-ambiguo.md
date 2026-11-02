# ADR-003 — Reconciliação de PUT ambíguo antes de repetir

- **Status:** Aceito; configuração operacional de retry pendente.
- **Data:** 2026-11-02.

## Contexto

Um 502/503/504 ou timeout pode ocorrer após o storage ter persistido o objeto.
Repetir o PUT sem consultar o estado pode sobrescrever conteúdo ou gerar
versões. RNF-01 a RNF-03 exigem waits crescentes para falhas transitórias,
proibição de retry para 403 e HEAD antes de qualquer novo PUT.

## Alternativas consideradas

1. Deixar o retry automático do SDK repetir PUT sem reconciliação.
2. Não repetir nem consultar o estado depois de falha ambígua.
3. Desativar retry automático, fazer HEAD após resultado ambíguo e repetir
   somente após HEAD confirmar ausência, sob política explícita.

## Decisão

Usar cliente boto3 com retries automáticos desativados para a operação. O
gravador trata falhas ambíguas de PUT com HEAD: hash igual resulta em
`ja_existia`, hash diferente em `conflito_hash`, ausência confirmada permite
novo PUT somente se uma política de atrasos tiver sido injetada; HEAD
inconclusivo resulta em `erro` e preserva o arquivo. HTTP 403 não gera nova
tentativa nem reconciliação adicional.

Nenhum número de tentativas, timeout ou duração é assumido como padrão. A
política é recebida por parâmetros. O CLI atual não injeta atrasos/sleeper:
assim, no caminho de produção atual ocorre no máximo o PUT inicial e uma
reconciliação HEAD; retry operacional permanece pendente de validação e
configuração.

## Consequências positivas

- Um resultado ambíguo não é interpretado como falha confirmada.
- Um novo PUT só ocorre após evidência HEAD de ausência.
- 403 não é repetido; atrasos podem ser testados sem sleep real.
- O limite de tentativas e as esperas não são inventados.

## Consequências negativas

- Sem política injetada, o CLI não recupera um PUT transitório após HEAD 404;
  devolve `erro` e mantém o arquivo no pouso.
- A sequência de chamadas aumenta latência e depende de disponibilidade do
  próprio HEAD.
- Não há teste de integração contra resposta 502 real do Railway.

## Requisitos relacionados

RNF-01, RNF-02, RNF-03; RF-05, RF-06, RF-07.

## Evidência

- `src/gravacao.py::gravar_lote` e `src/coletor.py::main`.
- `tests/test_retry.py::test_502_head_ausente_reenvia_put_apos_espera_crescente`.
- `tests/test_retry.py::test_403_nao_faz_nova_tentativa_nem_reconciliacao`.
- `tests/test_retry.py::test_502_head_igual_registra_ja_existia_sem_repetir`.
- `tests/test_retry.py::test_502_head_diferente_registra_conflito_sem_repetir`.
- `tests/test_retry.py::test_502_head_inconclusivo_retorna_erro_sem_repetir`.

## Condição de revisão

Revisar quando forem acordados e validados número de tentativas, timeout e
backoff, antes de configurar retry no CLI, ou após integração de um mecanismo
de escrita condicional/coordenação entre instâncias.
