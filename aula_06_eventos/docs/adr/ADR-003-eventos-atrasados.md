# ADR-003 - Eventos atrasados no CEP

- **Data:** 2026-11-22
- **Status:** hipóteses de negócio pendentes de validação

Eventos com `ocorrido_em` anterior ao watermark são avaliados e o complexo
resultante recebe `atrasado=true`. Isso preserva a evidência de atraso e permite
que a ocorrência seja auditada sem descartar a janela.

Alternativas descartadas:

1. **Descartar o evento atrasado:** perde evidência e pode impedir a regra de
   detectar uma recorrência real.
2. **Reprocessar como evento atual:** marca a ocorrência no tempo errado e
   altera a janela por tempo de chegada.
3. **Bloquear até atraso zero:** reduz disponibilidade e não é verificável com
   atraso ilimitado.

O estado é persistido localmente em JSON e recarregado na partida. Em produção,
o estado deve ficar em um motor de fluxo com checkpoints, como Flink ou Kafka
Streams. O offset só é confirmado depois de persistir o estado e publicar os
complexos.

Os limites de quantidade e janela são hipótese, validação pendente:
2 falhas em P7D, 5 minutos sem heartbeat, 3 cancelamentos em P1D e
7 dias sem matrícula. A folga do watermark é configurável.
