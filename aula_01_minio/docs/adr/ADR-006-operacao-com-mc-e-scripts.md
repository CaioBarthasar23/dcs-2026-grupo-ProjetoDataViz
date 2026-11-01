# ADR-006: operação e verificação com mc e scripts

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

RF-02, RF-04 e RF-05 requerem criação repetível de buckets, testes automatizados
nos dois ambientes e comandos documentados. O plano seleciona `mc` como cliente.

## Requisitos e cenários relacionados

RF-02, RF-04, RF-05, RF-07, CEN-01, CEN-02, CEN-04.

## Alternativas consideradas

1. Operar apenas pelo console: descartada porque não entrega a verificação
   automatizada por comandos e o console não é público.
2. Implementar cliente próprio: descartada por adicionar código de protocolo
   desnecessário para os comandos de operação definidos.
3. Executar comandos sem scripts compartilhados: descartada por aumentar
   diferenças entre integrantes e dificultar evidência repetível.

## Decisão

Usar `mc` para aliases, buckets e objetos, encapsulado em scripts Bash que
carregam `.env` sem imprimir credenciais. Tática de testabilidade: prover
interfaces de operação reproduzíveis e registrar resultados.

## Consequências

- Positivas: mesmas operações podem ser executadas nos destinos local e
  Railway; scripts podem falhar explicitamente e registrar códigos/saídas.
- Negativas (o trade-off): é preciso instalar/manter `mc` no Codespace; aliases
  e configurações locais podem divergir; a saída de `mc mb --ignore-existing`
  não basta para provar idempotência.

## Riscos

Mensagens de sucesso do cliente podem ser interpretadas incorretamente; a
idempotência deve ser inferida do código de saída e do estado/listagem, não só
do texto “Bucket created successfully”.

## Evidência necessária

Execuções e listagens em `docs/evidencias/T-03_criar_buckets.txt`,
`docs/evidencias/T-04_verificar_local.txt` e
`docs/evidencias/verificar_railway.txt`.

## Condição de revisão

Reabrir se `mc` não for compatível com a imagem/serviço, se os scripts não
protegerem segredos ou se outra interface passar a ser requisito.
