# Contexto da pergunta

Pergunta: Por que houve cancelamentos relacionados ao preço?

## Trechos recuperados
- event_id=cancelamento-preco-001; pontuacao=0.2876821; academia=SE-STO-014; motivo=preço do plano ficou alto

## Numeros agregados
- alunos_exatos: 2 (exato; 2026-11)
- alunos_estimados: 2 (estimativa; 2026-11)
- diferenca: 0.0 (exato; 2026-11)

## Consultas
```
{"bool":{"filter":[{"term":{"tipo":"cancelamento"}}],"must":[{"match":{"motivo":"preço"}}]}}
```
```
{"cardinality":{"field":"aluno","precision_threshold":40000}}
```
```
{"terms":{"field":"aluno","size":100000}}
```