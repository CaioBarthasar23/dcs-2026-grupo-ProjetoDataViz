# ADR-009: acompanhamento manual do crédito do trial

- Status: proposto
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

RNF-01 e OBJ-01 limitam o consumo no trial a US$ 5. T-09 prevê consulta manual
ao painel; não há evidência do consumo atual nem requisito aprovado para uma
integração automatizada de cobrança.

## Requisitos e cenários relacionados

RNF-01, CEN-03.

## Alternativas consideradas

1. Não acompanhar uso: descartada porque não permite verificar o teto do trial.
2. Criar integração automatizada de cobrança/alertas: não selecionada por não
   haver requisito ou autorização para serviço adicional.
3. Consultar manualmente o painel Railway: alternativa proposta, alinhada a
   T-09, mas ainda sem execução evidenciada.

## Decisão

Proposta: usar o painel Railway para registrar manualmente o consumo e manter
evidência sem credenciais. Tática de disponibilidade/custo: limitar demanda de
recursos e observar consumo. A frequência de consulta e limiar de alerta
continuam por decidir.

## Consequências

- Positivas: não adiciona serviço nem integração de cobrança.
- Negativas (o trade-off): depende de disciplina humana e pode não detectar
  aumento de uso entre consultas; não há alerta preventivo.

## Riscos

Sem T-09 executada, custo atual e margem restante são desconhecidos. O teto do
trial é fato; permanecer abaixo dele não está demonstrado.

## Evidência necessária

Consulta ao painel de uso, valor/data e registro em `docs/evidencias/` conforme
T-09. Ainda sem evidência.

## Condição de revisão

Reabrir se o consumo se aproximar do crédito, se o painel não oferecer dados
adequados ou se o grupo definir limite/frequência que exija automação.
