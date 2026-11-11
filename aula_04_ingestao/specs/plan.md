# Plano de construção e testes

## Objetivo e limites da etapa

Esta etapa especifica o trabalho em tarefas verificáveis e cria testes antes da implementação. `src/` permanece sem alterações. A suíte deve ficar vermelha agora por ausência da implementação importada, e não por erro de sintaxe ou de descoberta dos testes.

## Ordem e dependências

| Ordem | Tarefa | Depende de | Resultado |
|---:|---|---|---|
| 1 | T-01 testes de contrato | — | Um caso parametrizado por cada arquivo de `specs/exemplos/`, status codificado no nome e motivo para recusas. |
| 2 | T-02 testes HTTP | T-01 | Testes 202, 422, 400 e 413 com dublê da publicação. |
| 3 | T-03 integração de recepção e gravação | T-01, T-02 | Teste marcado `integracao` publica 20 envelopes pela API e verifica 20 linhas no ClickHouse e no lake. |
| 4 | T-04 implementar e fechar contrato | T-01 | `src/contrato.py` passa os casos de `tests/test_contrato.py`. |
| 5 | T-05 implementar e fechar API | T-02 | `src/api.py` passa `tests/test_api.py`. |
| 6 | T-06 a T-09 consumidor e persistência | T-03 | Consumidor, raw, bronze e ClickHouse passam o teste integrado; cada tarefa é limitada a um comportamento/arquivo principal. |
| 7 | T-10 a T-13 manifesto, ack e recuperação | T-06 a T-09 | Adicionar testes específicos antes de implementar esses comportamentos, pois o teste integrado pedido não os verifica. |

## Convenções de verificação

| Verificação | Comando | Evidência esperada nesta etapa |
|---|---|---|
| Suíte local | `pytest -q` | Falhas de importação de `src.contrato`, `src.api` e `src.consumidor` porque a implementação ainda não existe. Não aceitar erros de sintaxe ou erros nos próprios testes. |
| Integração, quando os três serviços estiverem disponíveis | `pytest -q -m integracao` | 20 envelopes publicados e 20 linhas verificadas no ClickHouse e no lake, usando a fila `ingestao_teste` e o bucket `teste`. |

O teste de integração pode ser ignorado quando os serviços locais não estiverem disponíveis. Sua execução requer que os serviços do compose estejam iniciados e que as variáveis necessárias estejam configuradas no ambiente de teste. As credenciais não são copiadas para testes ou documentação.

## Interface de teste esperada

Os testes usam `src.contrato.validar(corpo, DOMINIOS)` e `EnvelopeInvalido` com código e motivo, `src.api.app` e a função substituível `src.api.publicar_na_fila`, além da aplicação iniciada com consumidor ativo para o percurso integrado. Essa interface orienta a implementação futura; não afirma que ela já exista.

## Itens não verificados nesta etapa

Os testes solicitados cobrem contrato, respostas HTTP e contagem ponta a ponta. Ack após manifesto, manifesto de erro, persistência após `kill -9`, reprocessamento e demais detalhes de recuperação dos RF/RNF continuam cobertos pelas especificações, mas exigem testes adicionais antes das respectivas implementações.
