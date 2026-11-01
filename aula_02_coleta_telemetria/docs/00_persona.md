# Personas dos dados de telemetria

## P-01 Analista jurídica da transportadora
- Quem é: profissional do jurídico trabalhista que consulta registros relacionados à jornada; familiaridade técnica com arquivos é desconhecida.
- Decisão que toma: avaliar a resposta da transportadora em uma fiscalização ou processo trabalhista sobre a jornada de um motorista.
- Dor atual: o provedor não guarda histórico; meses depois, pode não haver o lote original ou prova de que permaneceu íntegro.
- Frequência de uso: por fiscalização ou processo (hipótese, validação pendente).
- O que precisa do dado: lotes do caminhão e da janela relevante, com horário de recepção e evidência de integridade. O conteúdo deve continuar bruto nesta etapa.
- Fatos: precisa consultar registros do tacógrafo posteriormente e demonstrar que o arquivo não foi alterado. Contexto do professor: pode ser necessário provar um alerta de direção contínua acima de 5h30, relacionado à Lei 13.103/2015.
- Suposições: pode consultar os lotes diretamente ou solicitar apoio para localizá-los (hipótese, validação pendente).

## P-02 Coordenação de frota
- Quem é: pessoa responsável por acompanhar a jornada e a posição dos caminhões.
- Decisão que toma: acompanhar a jornada e a posição dos caminhões.
- Dor atual: não informada; o provedor entrega lotes a cada 15 minutos e não mantém histórico.
- Frequência de uso: não informada (hipótese, validação pendente).
- O que precisa do dado: informações de posição e jornada disponíveis nos lotes, preservadas para consulta; necessidades de acesso e apresentação não estão definidas.
- Fatos: acompanha jornada e posição.
- Suposições: nenhuma decisão além desse acompanhamento foi informada.

## P-03 Mantenedora do coletor
- Quem é: pessoa de engenharia de dados que mantém a coleta e o armazenamento bruto.
- Decisão que toma: decidir se um lote com falha precisa ser recoletado (hipótese, validação pendente).
- Dor atual: lotes TXT sem formato fixo chegam por caminhão; falhas e critérios de recuperação não foram informados.
- Frequência de uso: não informada (hipótese, validação pendente).
- O que precisa do dado: saber se o coletor rodou, o que ficou no pouso e o que falhou; os arquivos recebidos devem permanecer sem alteração e permitir verificar recebimento e integridade.
- Fatos: nesta etapa há coleta e armazenamento bruto, sem parser nem painel.
- Suposições: será responsável por investigar falhas de coleta e atender solicitações de recuperação (hipótese, validação pendente).

## Fatos, lacunas e suposições
- Fatos (contexto do professor): caminhões operam em rodovias brasileiras; o equipamento registra tacógrafo, GPS e mensagens de rádio; os lotes TXT são entregues por caminhão a cada 15 minutos; o provedor não guarda histórico.
- Fatos (contexto do professor): a coordenação acompanha jornada e posição; o jurídico precisa consultar registros meses depois e verificar a integridade; pode precisar provar alerta de direção contínua acima de 5h30, relacionado à Lei 13.103/2015.
- Lacunas: formatos e conteúdo dos lotes; como identificar caminhões e janelas; quem acessa os arquivos; retenção necessária; responsáveis por operação e recuperação.
- Suposições: frequência de consulta, familiaridade técnica, responsabilidades da mantenedora e necessidades de uso além das explicitadas devem ser validadas. Não foram definidos prazos de guarda.

## Perguntas para o cliente
- Como o jurídico identifica o caminhão e a janela de interesse e que evidência de integridade precisa apresentar?
- Com que frequência a coordenação consulta os dados?
- Quem mantém a coleta, acompanha falhas e atende pedidos de recuperação?
- Por quanto tempo os lotes precisam estar disponíveis? (hipótese, validação pendente)
- Quem pode acessar tacógrafo, GPS e mensagens de rádio?
- Como tratar arquivos duplicados, vazios ou com nome repetido?
