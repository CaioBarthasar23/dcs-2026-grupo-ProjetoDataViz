# ADR-007 · Consulta PTAX por janela de dias

**Status:** Aceita

## Contexto

DN-01 precisa de uma referência GBP/BRL válida para a data local da coleta. RN-02 define o último boletim `Fechamento` com data menor ou igual à data de referência; RN-03 define `America/Sao_Paulo`. RF-07/RF-16 especificam consulta por período e formato `MM-DD-AAAA`; RF-08/RF-10 exigem tratar e preservar janela sem fechamento. RNF-01 exige que a cotação corresponda à regra temporal.

## Decisão

Consultar a API PTAX para GBP em uma janela de 30 dias corridos anteriores à data de referência D, incluindo D no final do período. Preservar os bytes da resposta. Selecionar o `Fechamento` elegível de data mais recente menor ou igual a D, mantendo `dataHoraCotacao` visível no contrato bronze. Se a resposta estiver vazia ou não contiver fechamento elegível, registrar ausência e marcar a execução incompleta, sem inventar cotação. O limite de 30 dias é uma escolha operacional aprovada para a primeira implementação; não representa garantia para qualquer feriado ou indisponibilidade histórica.

## Alternativas

- Consultar somente a data D.
- Consultar uma data anterior calculada por regra fixa de dia útil.
- Usar o boletim mais recente sem limitar pela data de referência.
- Fabricar ou reaproveitar silenciosamente cotação quando a janela não retorna fechamento.

## Consequências

- Fins de semana e feriados podem ser tratados usando um fechamento anterior e explícito.
- Uma janela maior pode aumentar tamanho da resposta e custo de parsing; uma janela curta pode não conter o fechamento elegível.
- A seleção deve comparar datas de boletim e data local de referência sem confundir horário de recebimento com data efetiva.
- Uma janela vazia ou malformada é diagnosticada como ausência ou erro de consulta, não como cotação válida.

**Origem:** DN-01, DN-02; RF-07, RF-08, RF-10, RF-12, RF-16; RN-02, RN-03; RNF-01, RNF-05.

**Diagramas da Etapa 08:** [coleta PTAX](../modelagem/dinamica/coleta_ptax.md), [extração](../modelagem/dinamica/extracao.md), [reexecução](../modelagem/dinamica/reexecucao.md).

**Referências:** [regras de negócio](../02_regras_de_negocio.md), [modelo de dados](../../specs/03_modelo_de_dados.md), [requisitos funcionais](../../specs/01_requisitos_funcionais.md).
