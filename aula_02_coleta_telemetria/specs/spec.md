# Especificação do coletor de telemetria

## Contexto

- O equipamento dos caminhões registra tacógrafo, posição GPS e mensagens de rádio; o provedor entrega lotes TXT a cada 15 minutos e não mantém histórico.
- A entrada simulada fica em `pouso/`, configurável por `POUSO_DIR`. O nome esperado é `CAM-XXXX_AAAAMMDDTHHMM.txt`; a data/hora identifica o início da janela de 15 minutos em `America/Sao_Paulo`.
- Os arquivos são UTF-8, usam fim de linha `\n` e contêm 15 linhas de posição (uma por minuto) misturadas com eventos. Há cinco formatos de linha:
  1. `CAM-0412|17/10/26 09:14:03|-23.5481,-46.6390|VEL 087|TAC MOT 03h12`
  2. `#RADIO 09:14 MOTORISTA: parada posto km 214 BR-116`
  3. `CAM-0412 17-10-2026 09:15:03 GPS -23.5502 -46.6411 v=85`, com `TEMP_BAU nn.n` opcional no fim
  4. `ERR SAT SINAL FRACO`
  5. `TAC;CAM-0977;20261017T091500;DIRECAO CONTINUA 05:31;ALERTA`
- O coletor apenas preserva os bytes e conta linhas de alerta `TAC;...;ALERTA`; interpretar os demais conteúdos não faz parte desta especificação.
- O comando `python gerar_lotes.py --inicio 2026-10-17T09:00` cria 80 lotes (20 caminhões × 4 janelas). O arquivo `CAM-0451_20261017T0900.txt` tem 983 bytes e SHA-256 `6789b712602d1985d24df7b48370a1190da3db4e2576a74b07b5520d28601b12`.
- O bucket de destino é `raw`. A chave segue `telemetria/data=AAAA-MM-DD/hora=HH/caminhao=CAM-XXXX/lote_HHMM.txt`, usando data, hora e início da janela convertidos para UTC.
- O provedor pode retransmitir lotes. Um HTTP 502 do proxy do MinIO do Railway não prova que o PUT falhou.

## Requisitos funcionais

### RF-01 — Ler os arquivos disponíveis no pouso
Descrição: o coletor deve considerar os arquivos presentes na pasta configurada por `POUSO_DIR` em cada execução.

- **Dado** arquivos presentes na pasta de pouso,
- **Quando** uma execução iniciar,
- **Então** cada arquivo deve ser avaliado individualmente e ter resultado registrado no manifesto da execução.
- **Verificação:** teste de integração com vários arquivos no pouso; confirmar uma entrada de manifesto para cada arquivo.

### RF-02 — Rejeitar nome fora do padrão sem remover o arquivo
Descrição: um arquivo cujo nome não corresponda a `CAM-XXXX_AAAAMMDDTHHMM.txt` deve terminar como `erro`, sem ser gravado nem removido do pouso.

- **Dado** um arquivo com nome fora do padrão,
- **Quando** o coletor processá-lo,
- **Então** ele não deve ser enviado ao bucket, deve permanecer no pouso e deve constar no manifesto com `status: erro` e `chave: null`; campos que puderem ser obtidos sem interpretar o nome devem ser registrados, e `motivo` pode ser incluído.
- **Verificação:** teste de integração com nome inválido; confirmar ausência de PUT, arquivo ainda presente e linha JSONL com os campos esperados.

### RF-03 — Calcular chave determinística pela janela em UTC
Descrição: o coletor deve converter o início da janela de `America/Sao_Paulo` para UTC e usar a mesma chave para o mesmo lote em qualquer execução.

- **Dado** `pouso/CAM-0451_20261017T0900.txt`, cuja janela começa às 09:00 em Brasília,
- **Quando** o coletor calcular a chave,
- **Então** deve produzir `telemetria/data=2026-10-17/hora=12/caminhao=CAM-0451/lote_1200.txt`, pois 09:00 em UTC−03:00 corresponde a 12:00 UTC; o resultado não deve depender do relógio da execução.
- **E dado** `pouso/CAM-0451_20261017T2200.txt`,
- **Quando** converter 22:00 em Brasília (UTC−03:00),
- **Então** deve produzir `telemetria/data=2026-10-18/hora=01/caminhao=CAM-0451/lote_0100.txt`, pois 22:00 + 3 horas = 01:00 UTC do dia seguinte.
- **Verificação:** teste unitário da função de cálculo de chave, sem relógio; verificar os dois exemplos e que duas chamadas para a mesma entrada retornam a mesma chave.

### RF-04 — Preservar os bytes do lote
Descrição: o conteúdo enviado ao bucket deve ser exatamente a sequência de bytes lida do arquivo, sem decodificação, reserialização ou alteração de fim de linha.

- **Dado** `CAM-0451_20261017T0900.txt`, com 983 bytes e SHA-256 `6789b712602d1985d24df7b48370a1190da3db4e2576a74b07b5520d28601b12`,
- **Quando** o lote for gravado,
- **Então** o objeto deve conter 983 bytes e ter exatamente esse SHA-256.
- **Verificação:** teste de integração comparando bytes de origem e objeto, tamanho e SHA-256.

### RF-05 — Reconhecer retransmissão idêntica como `ja_existia`
Descrição: antes de enviar um lote, o coletor deve consultar a chave com HEAD e, se o SHA-256 existente for igual ao do lote, registrar `ja_existia` sem sobrescrever o objeto.

- **Dado** que a chave já existe e seu SHA-256 é igual ao do arquivo no pouso,
- **Quando** o coletor consultar a chave antes do PUT,
- **Então** deve registrar `status: ja_existia` e não deve sobrescrever o objeto.
- **Verificação:** teste de integração executado duas vezes com os mesmos bytes; confirmar status `ja_existia`, conteúdo original inalterado e ausência de novo PUT.

### RF-06 — Registrar retransmissão com conteúdo diferente como `conflito_hash`
Descrição: se a chave existir com SHA-256 diferente, o coletor deve registrar `conflito_hash`, preservar o objeto existente e manter o arquivo retransmitido no pouso.

- **Dado** que a chave já existe e seu SHA-256 difere do SHA-256 do arquivo no pouso,
- **Quando** o coletor comparar os hashes,
- **Então** deve registrar `status: conflito_hash`, não sobrescrever o objeto e manter o arquivo no pouso.
- **Verificação:** teste de integração com conteúdo diferente para a mesma chave; confirmar status, bytes originais do objeto e permanência do arquivo.

### RF-07 — Remover arquivo somente após confirmação
Descrição: o coletor só deve remover do pouso um arquivo cujo PUT foi confirmado ou cujo status `ja_existia` decorre de SHA-256 igual.

- **Dado** um arquivo no pouso,
- **Quando** o PUT for confirmado ou o HEAD confirmar conteúdo existente com SHA-256 igual,
- **Então** o arquivo pode ser removido; em erro, conflito ou resultado não confirmado, deve permanecer no pouso.
- **Verificação:** teste de integração cobrindo PUT confirmado, `ja_existia`, `erro`, `conflito_hash` e resultado ambíguo.

### RF-08 — Registrar metadados de procedência no objeto
Descrição: cada objeto gravado deve conter os sete metadados ASCII `fonte`, `recebido-em`, `versao-coletor`, `sha256`, `caminhao`, `janela-inicio` e `arquivo-origem`.

- **Dado** um lote com PUT confirmado,
- **Quando** os metadados do objeto forem consultados,
- **Então** devem existir `fonte=provedor-satelite`, `recebido-em` em ISO 8601 UTC, `versao-coletor` de `COLETOR_VERSAO`, SHA-256 dos bytes gravados, identificador do caminhão, início da janela em ISO 8601 UTC e nome original do arquivo.
- **Verificação:** teste de integração consultando os metadados e comparando os sete valores com arquivo, janela e configuração.

### RF-09 — Registrar resultados em manifesto JSON Lines
Descrição: cada execução deve criar o manifesto no caminho UTC previsto e incluir uma linha JSON por lote, inclusive para nomes inválidos e falhas de leitura.

- **Dado** uma execução iniciada em determinado instante UTC e os arquivos encontrados no pouso,
- **Quando** o processamento terminar,
- **Então** deve existir `_manifestos/telemetria/data=AAAA-MM-DD/hora=HH/execucao_<AAAAMMDDTHHMMSSZ>.jsonl`, com data e hora do início da execução em UTC e uma linha por arquivo contendo `arquivo`, `chave`, `status`, `bytes`, `sha256`, `linhas` e `alertas`; `status` deve ser `gravado`, `ja_existia`, `erro` ou `conflito_hash`.
- **E dado** um arquivo que não pôde ser lido,
- **Quando** sua linha for registrada,
- **Então** `bytes`, `sha256`, `linhas` e `alertas` devem ser `null`; `motivo` pode ser incluído. Para arquivo legível, `alertas` deve contar linhas `TAC;...;ALERTA`, sem interpretar os demais formatos.
- **Verificação:** teste de integração com arquivo válido, inválido e ilegível; validar caminho, JSON de cada linha, campos, status, contagens e valores nulos.

### RF-10 — Continuar processamento após falha individual
Descrição: uma falha ao processar um lote não deve impedir a tentativa de processar os demais arquivos da execução.

- **Dado** mais de um arquivo no pouso, sendo um deles causador de erro,
- **Quando** o coletor executar a coleta,
- **Então** deve registrar o erro daquele arquivo e continuar processando os demais.
- **Verificação:** teste de integração com falha simulada em um lote e sucesso em outro; confirmar entradas para ambos no manifesto.

### RF-11 — Sinalizar falha no código de saída
Descrição: a execução deve terminar com código diferente de zero se qualquer lote terminar com status `erro` ou `conflito_hash`.

- **Dado** uma execução em que pelo menos um lote termine como `erro` ou `conflito_hash`,
- **Quando** o processo encerrar,
- **Então** seu código de saída deve ser diferente de zero; sem esses status, deve ser zero.
- **Verificação:** teste de integração do processo para os casos com e sem falha.

## Requisitos não funcionais

### RNF-01 — Repetir falhas transitórias com espera crescente
Descrição: o coletor deve repetir operações afetadas por HTTP 502, 503 ou 504 e timeout do MinIO, usando esperas crescentes.

- **Dado** uma resposta 502, 503 ou 504, ou timeout do MinIO,
- **Quando** a política de repetição for aplicada,
- **Então** as esperas entre tentativas devem crescer; número de tentativas, durações de espera e timeout: hipótese, validação pendente.
- **Verificação:** teste unitário com respostas e relógio simulados; confirmar esperas crescentes sem fixar valores ainda não validados.

### RNF-02 — Não repetir resposta 403
Descrição: uma resposta HTTP 403 não deve causar repetição da operação.

- **Dado** uma operação que recebe HTTP 403,
- **Quando** o coletor tratar a resposta,
- **Então** não deve repetir a operação e deve registrar a falha para o lote.
- **Verificação:** teste unitário com resposta simulada 403; confirmar uma única chamada e status `erro`.

### RNF-03 — Reconciliar PUT ambíguo antes de repetir
Descrição: uma resposta HTTP 502 ou timeout não prova que o PUT falhou e deve ser reconciliada por HEAD antes de qualquer repetição do PUT.

- **Dado** um PUT que termina em HTTP 502 ou timeout,
- **Quando** o coletor decidir o próximo passo,
- **Então** deve consultar a chave com HEAD antes de qualquer repetição do PUT; se o objeto existir com hash igual, deve tratar como `ja_existia`; se existir com hash diferente, como `conflito_hash`; só pode repetir o PUT após HEAD confirmar ausência do objeto.
- **E dado** que o HEAD não consiga confirmar o estado,
- **Quando** não for possível reconciliar,
- **Então** não deve repetir o PUT nem remover o arquivo do pouso, e deve registrar `erro`.
- **Verificação:** teste unitário com PUT simulado como ambíguo e respostas HEAD para igual, diferente, ausente e erro; verificar a ordem das chamadas.
- **Observação:** tentativas, esperas e timeout: hipótese, validação pendente.

### RNF-04 — Configurar execução por variáveis de ambiente
Descrição: a configuração do coletor deve ser lida de `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `BUCKET_RAW`, `S3_REGION`, `COLETOR_VERSAO` e `POUSO_DIR`.

- **Dado** configurações válidas fornecidas por essas variáveis,
- **Quando** a mesma execução for apontada ao MinIO local ou ao MinIO do Railway,
- **Então** o comportamento deve ser o mesmo, mudando apenas os valores de ambiente.
- **Verificação:** teste de integração de configuração com endpoints substituíveis; confirmar que a configuração consumida deriva somente das variáveis listadas.

### RNF-05 — Manter credenciais fora de arquivos versionados
Descrição: credenciais S3 devem ser fornecidas por variáveis de ambiente e não devem aparecer em arquivos versionados.

- **Dado** o repositório do projeto,
- **Quando** `git diff --staged` for revisado antes do commit,
- **Então** nenhum valor de `S3_ACCESS_KEY` ou `S3_SECRET_KEY` deve aparecer.
- **Verificação:** executar `git diff --staged`.

### RNF-06 — Gravar no bucket `raw` do MinIO compatível com S3
Descrição: cada lote confirmado deve existir no bucket `raw` do MinIO com a chave calculada para a janela.

- **Dado** MinIO configurado e um lote com gravação confirmada,
- **Quando** a existência do objeto for consultada,
- **Então** o objeto deve estar no bucket `raw` sob a chave determinística correspondente.
- **Verificação:** executar o teste de integração que consulta o objeto no bucket `raw`.

## Fora de escopo

- Parser semântico ou transformação dos conteúdos dos lotes.
- Conversão ou gravação em Parquet.
- Integração com SFTP real; `pouso/` é a pasta simulada de entrada.
- Agendamento automático em produção.
- Painel de consulta ou visualização.

## Fatos/lacunas/suposições

- **Fatos fornecidos pelo professor:** zona de origem `America/Sao_Paulo`; janela de 15 minutos; formatos, exemplo do gerador, contagem de 80 lotes, tamanho e SHA-256 do lote de referência; bucket, padrão de chave, metadados, manifesto e variáveis listados nesta especificação.
- **Fatos fornecidos pelo professor:** o proxy do MinIO do Railway pode devolver 502 esporádico, que não prova falha do PUT; retransmissões podem ocorrer.
- **Fatos dos documentos de negócio:** P-01 necessita evidência íntegra para consultas posteriores; P-02 acompanha jornada e posição; P-03 precisa saber o resultado da coleta. OBJ-01 prioriza preservação, OBJ-02 completude das janelas e OBJ-03 visibilidade da coleta.
- **Lacunas:** política de retenção, metas de sucesso, limites aceitáveis de falha, tratamento de campos de metadados ausentes no HEAD e comportamento diante de falhas no próprio manifesto.
- **Suposições:** número de tentativas, tempos de espera e timeout serão definidos após validação; até lá, todos são hipótese, validação pendente. O conjunto de políticas e seus valores não foram fornecidos.

## Rastreabilidade

| Requisito | Objetivo ou origem |
|---|---|
| RF-01 | OBJ-02 (completude das janelas), OBJ-03 (visibilidade da coleta) |
| RF-02 | OBJ-03 (visibilidade de erros e arquivos pendentes) |
| RF-03 | OBJ-01 (localização de evidência), OBJ-02 (identificação das janelas) |
| RF-04 | OBJ-01 (preservação íntegra) |
| RF-05 | OBJ-01 (preservar original); métrica de retransmissões (identificar repetição idêntica sem perda ou sobrescrita) |
| RF-06 | OBJ-01 (preservar original); métrica de retransmissões (identificar conteúdo diferente sem perda ou sobrescrita) |
| RF-07 | OBJ-01 (preservação), OBJ-02 (evitar perda de janelas) |
| RF-08 | OBJ-01 (integridade verificável), OBJ-03 (rastreabilidade da origem e recebimento) |
| RF-09 | OBJ-03 (visibilidade da coleta), OBJ-01 (evidência e integridade) |
| RF-10 | OBJ-02 (completude), OBJ-03 (visibilidade de falhas) |
| RF-11 | OBJ-03 (sinalizar falhas da execução) |
| RNF-01 | OBJ-02 (reduzir perda de janelas), OBJ-03 (visibilidade de falhas) |
| RNF-02 | OBJ-01 (preservar confiança na evidência), OBJ-03 (operação previsível); restrição fornecida pelo professor |
| RNF-03 | OBJ-01 (integridade verificável), OBJ-02 (não perder janelas) |
| RNF-04 | OBJ-01, OBJ-02 e OBJ-03 (execução consistente nos ambientes) |
| RNF-05 | OBJ-01 (confiança na evidência), OBJ-03 (operação do coletor); restrição fornecida pelo professor |
| RNF-06 | OBJ-01 (preservação dos lotes no destino); restrição fornecida pelo professor |
