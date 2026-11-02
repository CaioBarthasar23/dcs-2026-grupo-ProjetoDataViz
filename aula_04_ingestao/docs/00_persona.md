# Personas

## P1 · Time dono de uma fonte

Responsável por produzir dados de uma fonte que ainda não envia dados à plataforma. Precisa entregar novos dados sem pedir a criação de uma tabela dedicada. Nesta aula, as fontes abrangem `telemetria`, `livros` e `ptax`.

**Decisão que toma:** quando a fonte está pronta para começar a enviar dados pelo contrato de ingestão e qual domínio (`data_tag`) identifica seus dados.

## P2 · Analista no ClickHouse

Consulta no ClickHouse os dados recebidos para responder perguntas analíticas sobre as fontes disponíveis. O conteúdo de cada domínio pode exigir tratamento posterior.

**Decisão que toma:** se os dados disponíveis são adequados para responder à pergunta analítica e podem embasar sua análise.

## P3 · Engenheiro de dados da ingestão

Opera o servidor de ingestão e é acionado quando algo para. Acompanha o caminho da mensagem da API e da fila até o lake, o ClickHouse e o manifesto do lote.

**Decisão que toma:** em que ponto a ingestão parou, qual ação de recuperação é apropriada e quando é seguro retomar o processamento.
