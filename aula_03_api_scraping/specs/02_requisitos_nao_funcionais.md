# Requisitos não funcionais · Monitor de preços

## Premissas

- As medidas de 16/10/2026 são linha de base informada, não metas: 1.081 requisições (1 inicial + 80 páginas + 1.000 detalhes), mediana 0,15 s, p95 0,33 s, máxima 9,9 s, cerca de 18 min de espera com intervalo de 1 s, 1.083 objetos e 21,5 MiB de bruto por execução; `livros.jsonl` com 268 KiB.
- Metas sem fonte estabelecida estão marcadas como **hipótese — validação pendente**.
- Componentes citados são prováveis pontos de implementação, não escolha de biblioteca.

## Adequação funcional

### RNF-01 · Correção e completude dos registros extraídos
- **Critério de aceite:** em 100% dos casos de teste com brutos conhecidos, cada linha extraída corresponde aos campos de origem definidos nos RFs; o total de livros coincide com o total declarado para o escopo, ou a execução fica marcada como falha, conforme RF-14.
- **Medida:** executar a extração sobre fixtures de HTML e JSON com resultados esperados versionados; comparar campos e contagens linha a linha. Meta de 100% — hipótese — validação pendente.
- **RFs ligados:** RF-04, RF-07, RF-11, RF-12, RF-14.
- **Personas:** P1, P2, P3.
- **Componente provável:** validadores e transformação de registros.

## Eficiência de desempenho

### RNF-02 · Timeout explícito por requisição
- **Critério de aceite:** toda requisição HTTP externa tem timeout finito explícito para conexão e leitura; em teste com servidor que não responde, a tentativa termina em até 15 s — hipótese — validação pendente.
- **Medida:** teste com servidor simulado que não envia resposta; medir o tempo até timeout e verificar que os limites de conexão e leitura estão configurados.
- **RFs ligados:** RF-05, RF-06, RF-07, RF-16.
- **Personas:** P2.
- **Componente provável:** configuração e cliente de comunicação HTTP.

### RNF-03 · Intervalo, ausência de paralelismo e duração da coleta
- **Critério de aceite:** em uma coleta completa, há no máximo uma requisição ativa ao site; o início de cada requisição ocorre pelo menos após o intervalo mínimo configurado desde o início da anterior. O valor padrão de 1 s é apenas linha de base informada para 16/10/2026; o intervalo mínimo de aceite ainda é **hipótese — validação pendente**. A duração total não excede 30 min — **hipótese — validação pendente**.
- **Medida:** servidor simulado registra início/fim de cada requisição e concorrência máxima; um teste compara cada diferença entre inícios com o intervalo mínimo explicitamente configurado no cenário. Execução de referência mede tempo monotônico entre início e término, incluindo espera e retries, e compara com o limite de 30 min, ainda sujeito a validação.
- **RFs ligados:** RF-01, RF-02, RF-04, RF-05, RF-06.
- **Personas:** P1, P2.
- **Componente provável:** coordenador da coleta e limitador de frequência.

## Compatibilidade

### RNF-04 · Metadados compatíveis com os dois destinos
- **Critério de aceite:** 100% das chaves e valores de metadados de origem contêm somente caracteres ASCII e podem ser gravados e lidos sem alteração nos dois destinos MinIO — hipótese — validação pendente.
- **Medida:** validar chaves e valores com codificação ASCII estrita e comparar metadados antes e depois de gravar e ler nos ambientes local e Railway.
- **RFs ligados:** RF-09, RF-10.
- **Personas:** P2, P3.
- **Componente provável:** criação de metadados e adaptador de armazenamento.

## Usabilidade

### RNF-05 · Diagnóstico de execução incompleta
- **Critério de aceite:** em 100% dos cenários de falha induzida, o manifesto identifica o estado incompleto e a ausência ou divergência observada, conforme RF-08, RF-13 e RF-14.
- **Medida:** provocar janela PTAX vazia e divergência de contagem; verificar automaticamente os campos correspondentes no manifesto. Meta de 100% — hipótese — validação pendente.
- **RFs ligados:** RF-08, RF-13, RF-14.
- **Personas:** P2, P3.
- **Componente provável:** geração do manifesto e relatório da execução.

## Confiabilidade

### RNF-06 · Repetição limitada a falhas transitórias
- **Critério de aceite:** timeout, erro de conexão e respostas HTTP 408, 429 e 5xx podem ser repetidos; outros 4xx não são repetidos. O total é limitado a 4 tentativas — hipótese — validação pendente. Entre tentativas, a espera usa full jitter uniforme entre 0 e `min(8 s, 0,5 s × 2^k)`, com k iniciando em 0; um `Retry-After` válido prevalece sobre o cálculo. Valores de base, teto e tentativas são hipóteses — validação pendente.
- **Medida:** servidor simulado alterna erros transitórios, permanentes e sucesso; injetar relógio e gerador aleatório para verificar classificação, quantidade de tentativas, limites de espera e precedência de `Retry-After`.
- **RFs ligados:** RF-05, RF-06, RF-07, RF-16.
- **Personas:** P2.
- **Componente provável:** política de repetição do cliente de comunicação.

### RNF-07 · Reexecução sem duplicação e com bruto preservado
- **Critério de aceite:** após duas execuções para a mesma data, há zero UPC duplicado e uma cotação de referência no resultado diário; brutos endereçados por fonte, data, recurso e SHA-256 não são sobrescritos, e manifestos anteriores permanecem inalterados.
- **Medida:** executar duas vezes sobre o mesmo conjunto de respostas; contar UPCs repetidos e cotações no resultado corrente, verificar que bytes iguais resultam na mesma chave content-addressed e comparar hashes dos brutos e manifestos anteriores. Meta de zero duplicação — hipótese — validação pendente.
- **RFs ligados:** RF-09, RF-10, RF-13, RF-15.
- **Personas:** P2, P3.
- **Componente provável:** publicação dos resultados diários e organização por execução.

## Segurança

### RNF-08 · Segredos ausentes do controle de versão
- **Critério de aceite:** zero arquivos de credenciais ou valores de segredo são adicionados ao Git; configurações locais com segredos permanecem ignoradas.
- **Medida:** confirmar que `.env` não aparece em `git ls-files` e que `git check-ignore .env` retorna sucesso; um teste lê os valores de variáveis secretas do `.env` ignorado e procura correspondências nos conteúdos dos arquivos rastreados pelo Git, reportando somente nomes de arquivos e quantidade de ocorrências, nunca os valores. Critério: zero correspondências.
- **RFs ligados:** RF-06, RF-09, RF-10, RF-13.
- **Personas:** P2.
- **Componente provável:** configuração local e regras de versionamento.

## Manutenibilidade

### RNF-09 · Extração verificável sem rede externa
- **Critério de aceite:** 100% dos testes de extração de livros e cotações executam com rede externa bloqueada, lendo respostas brutas previamente gravadas e produzindo saídas comparáveis a resultados esperados.
- **Medida:** executar a suíte de extração com conexões externas proibidas; verificar que não há tentativas de conexão e comparar linhas produzidas com fixtures esperadas. Meta de 100% — hipótese — validação pendente.
- **RFs ligados:** RF-09, RF-10, RF-11, RF-12.
- **Personas:** P2, P3.
- **Componente provável:** extratores e testes com dados de amostra.

## Portabilidade

### RNF-10 · Mesmo código para MinIO local e Railway
- **Critério de aceite:** a mesma revisão do código passa pelos mesmos testes de armazenamento nos ambientes MinIO local e Railway; a única diferença de configuração entre execuções é o arquivo `.env`, sem alteração de código.
- **Medida:** executar a mesma suíte de integração em ambos os endpoints e comparar os resultados funcionais; registrar hash da revisão e diferenças de configuração, excluindo valores secretos. Meta de aprovação nos dois destinos — hipótese — validação pendente.
- **RFs ligados:** RF-09, RF-10, RF-11, RF-12, RF-13, RF-15.
- **Personas:** P2, P3.
- **Componente provável:** configuração do destino e adaptador de armazenamento.

## Matriz RF → RNF

| RF | RNF |
|---|---|
| RF-01 | RNF-03 |
| RF-02 | RNF-03 |
| RF-03 | RNF-01 |
| RF-04 | RNF-01, RNF-03 |
| RF-05 | RNF-02, RNF-03, RNF-06 |
| RF-06 | RNF-02, RNF-03, RNF-06, RNF-08 |
| RF-07 | RNF-02, RNF-06 |
| RF-08 | RNF-05 |
| RF-09 | RNF-04, RNF-07, RNF-08, RNF-09, RNF-10 |
| RF-10 | RNF-04, RNF-07, RNF-08, RNF-09, RNF-10 |
| RF-11 | RNF-01, RNF-09, RNF-10 |
| RF-12 | RNF-01, RNF-09, RNF-10 |
| RF-13 | RNF-05, RNF-07, RNF-08, RNF-10 |
| RF-14 | RNF-01, RNF-05 |
| RF-15 | RNF-07, RNF-10 |
| RF-16 | RNF-02, RNF-06 |
