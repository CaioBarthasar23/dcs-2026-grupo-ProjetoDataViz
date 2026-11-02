# ADR-002 — Idempotência: primeira gravação prevalece

- **Status:** Aceito.
- **Data:** 2026-11-02.

## Contexto

O provedor pode retransmitir arquivos e não mantém histórico. A chave é
determinística por janela (ADR-001). Uma retransmissão com o mesmo nome pode
ser idêntica ou conter bytes diferentes; sobrescrever silenciosamente apagaria
a evidência anterior.

## Alternativas consideradas

1. Sobrescrever sempre a chave com o último PUT.
2. Tratar toda chave existente como duplicata, sem comparar conteúdo.
3. Consultar HEAD e comparar o metadado SHA-256; aceitar hash igual como
   `ja_existia` e classificar hash diferente como `conflito_hash`, sem PUT.
4. Armazenar cada retransmissão em uma chave nova com número de revisão.

## Decisão

Antes do PUT do lote, consultar HEAD. Se não existir, gravar os bytes e o
metadado SHA-256. Se existir com SHA-256 igual, registrar `ja_existia`; se
existir com hash diferente, registrar `conflito_hash`. Nunca sobrescrever
automaticamente um objeto conflitante. Remover do pouso somente depois de
confirmação de PUT ou de `ja_existia` com hash igual.

A primeira gravação confirmada daquela chave prevalece. Metadado SHA-256
ausente ou inválido é erro, não autorização para sobrescrever.

## Consequências positivas

- Retransmissão idêntica não gera novo PUT serial e pode ser removida após
  confirmação do hash.
- Divergência fica visível no manifesto e mantém o arquivo retransmitido no
  pouso para investigação.
- A evidência original não é substituída por um conteúdo diferente sem decisão
  explícita.

## Consequências negativas

- HEAD seguido de PUT não é atômico: dois coletores simultâneos podem observar
  ausência e competir; conteúdo divergente ainda pode ser sobrescrito por
  corrida. Escritor único, lock ou PUT condicional não estão implementados.
- Metadado ausente impede decisão automática, exigindo intervenção.
- Não há fluxo aprovado para aceitar uma correção legítima nem para registrar
  nova revisão mantendo cadeia de custódia.
- A remoção do pouso após PUT ocorre antes do PUT final do manifesto; falha do
  manifesto pode deixar o arquivo removido sem registro durável da execução.

## Requisitos relacionados

RF-04, RF-05, RF-06, RF-07; RNF-03; OBJ-01, OBJ-02, OBJ-03.

## Evidência

- `src/gravacao.py::gravar_lote` e `src/limpeza.py::remover_confirmado`.
- `tests/test_idempotencia.py::test_duas_execucoes_identicas_fazem_um_put_e_status_ja_existia`.
- `tests/test_conflito_hash.py::test_mesma_chave_conteudo_diferente_registra_conflito_sem_put_e_mantem_pouso`.
- `tests/test_retry.py` cobre reconciliação de PUT ambíguo com HEAD igual,
  diferente, ausente e inconclusivo.
- O teste de integração local informado executa duas coletas, verifica o
  conjunto de 80 chaves e exige `ja_existia` na segunda. Não há evidência
  suficiente para afirmar que versionamento está habilitado no bucket.

## Condição de revisão

Revisar antes de permitir múltiplos escritores concorrentes, quando o provedor
definir mecanismo de revisão/correção, se o SHA-256 deixar de estar disponível
no HEAD, ou quando for definida a ordem transacional entre lote, remoção e
manifesto.
