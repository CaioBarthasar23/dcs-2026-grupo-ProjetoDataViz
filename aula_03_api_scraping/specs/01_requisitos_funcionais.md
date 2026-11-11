# Requisitos funcionais · Monitor de preços

## Contexto
- O monitor coleta diariamente preços de livros e cotações GBP/BRL.
- Livros são descobertos no site Books to Scrape e identificados pelo UPC.
- A data de referência da execução segue o calendário de São Paulo.
- Respostas originais são preservadas antes da extração.
- A saída extraída serve de entrada para a Aula 04; conversão para reais não faz parte desta etapa.

## Descoberta

### RF-01 · Descobrir categorias na página inicial
**Origem:** DN-01, OBJ-01, P1.

- **Dado** que a página inicial lista categorias,
- **Quando** uma execução inicia a descoberta,
- **Então** registra o nome e o endereço de cada categoria listada, sem depender de um número fixo de categorias.

### RF-02 · Percorrer as páginas de cada categoria
**Origem:** RN-10, OBJ-01, P1, P2.

- **Dado** que uma página de categoria informa um endereço de próxima página,
- **Quando** a categoria é percorrida,
- **Então** a execução visita a próxima página e continua até não haver próximo endereço, sem assumir uma quantidade fixa de páginas.
- **Dado** que uma página não informa próximo endereço,
- **Quando** seus livros forem processados,
- **Então** a execução encerra a paginação daquela categoria sem repetir livros já encontrados nela.

### RF-03 · Filtrar categorias configuradas
**Origem:** OBJ-01, P1.

- **Dado** que `SCRAPER_CATEGORIAS` contém uma ou mais categorias descobertas,
- **Quando** a execução define seu escopo,
- **Então** coleta somente as categorias nomeadas na configuração.
- **Dado** que `SCRAPER_CATEGORIAS` está ausente ou vazia,
- **Quando** a execução define seu escopo,
- **Então** coleta todas as categorias descobertas.

### RF-04 · Consultar o detalhe de cada livro
**Origem:** RN-01, RN-11, OBJ-03, P3.

- **Dado** que uma página de listagem apresenta um livro e seu endereço de detalhe,
- **Quando** a execução processa esse livro,
- **Então** visita o detalhe e obtém de lá o UPC, a disponibilidade e a categoria; UPC e disponibilidade não são inferidos da listagem.
- **Dado** que a listagem apresenta título e preço em libras e o detalhe apresenta a categoria no breadcrumb,
- **Quando** os dados do livro forem extraídos,
- **Então** o título e o preço correspondem à listagem observada e a categoria corresponde ao detalhe.

## Coleta

### RF-05 · Consultar e registrar as instruções de acesso
**Origem:** RN-04, DN-02, P2.

- **Dado** que uma execução vai iniciar consultas ao site,
- **Quando** a coleta começa,
- **Então** consulta o endereço `robots.txt` e registra seu endereço, horário, código HTTP e conteúdo retornado.
- **Dado** que `robots.txt` responde 404,
- **Quando** a resposta é registrada,
- **Então** a execução registra a ausência do arquivo e não inventa instruções de permissão ou proibição.

### RF-06 · Fazer consultas identificadas e sequenciais
**Origem:** RN-05, RN-06, RN-07 e restrições da disciplina.

- **Dado** que a execução consulta páginas do site,
- **Quando** cada consulta é enviada,
- **Então** o valor de identificação contém `aula_03_api_scraping`, no máximo uma consulta fica ativa por vez e o início da próxima consulta ocorre no mínimo após o intervalo configurado desde o início da anterior.
- **Pendência de produto:** o valor padrão do intervalo mínimo ainda precisa ser definido. Um teste pode fornecer um intervalo explícito no cenário e verificar a diferença entre os instantes de início das consultas.

### RF-07 · Consultar a PTAX para a data de referência
**Origem:** RN-02, RN-03, DN-01, OBJ-01, P1.

- **Dado** que a data de referência D é determinada pelo calendário de São Paulo e há uma janela com datas válidas,
- **Quando** a cotação GBP é consultada,
- **Então** as datas inicial e final são enviadas no formato `MM-DD-AAAA`, e entre os boletins retornados é selecionado o “Fechamento” de data mais recente menor ou igual a D, com a data efetiva da cotação visível.
- **Dado** que a janela contém mais de um boletim “Fechamento” elegível,
- **Quando** a cotação de D é definida,
- **Então** somente o fechamento de data mais recente até D é tratado como cotação de referência.

### RF-08 · Tratar janela sem fechamento
**Origem:** RN-02, DN-02, OBJ-02, P2.

- **Dado** que a consulta à PTAX retorna HTTP 200 com o corpo JSON contendo `"value": []`,
- **Quando** a resposta da janela é processada,
- **Então** a resposta vazia é registrada, a cotação é marcada como indisponível e a execução fica incompleta, sem criar um valor de cotação.
- **Dado** que a consulta retorna boletins, mas nenhum “Fechamento” tem data menor ou igual a D,
- **Quando** a resposta da PTAX é processada,
- **Então** a resposta é preservada, a cotação é marcada como indisponível e a execução fica incompleta, sem criar um valor de cotação.

## Gravação

### RF-09 · Preservar HTML bruto com origem
**Origem:** RN-08, RN-09, OBJ-02, P2.

- **Dado** que uma página de origem respondeu com HTML,
- **Quando** a resposta é recebida,
- **Então** os bytes originais são gravados antes de qualquer interpretação em uma chave determinística composta pela fonte, data de referência, recurso consultado e SHA-256 do corpo; a chave não contém identificador da execução.
- **Dado** que o HTML bruto foi gravado,
- **Quando** ocorre uma extração ou reexecução posterior,
- **Então** o objeto da execução anterior permanece inalterado e seus metadados registram endereço de origem, instante da coleta e SHA-256 dos bytes gravados.
- **Dado** que outra execução da mesma data recebe exatamente os mesmos bytes para a mesma fonte e recurso,
- **Quando** o bruto é gravado,
- **Então** a chave determinística é idêntica e o objeto imutável existente pode ser referenciado pelo novo manifesto.
- **Dado** que o cabeçalho HTTP `Content-Type` não informa charset,
- **Quando** a resposta é preservada,
- **Então** seus bytes são gravados sem alteração nem conversão de texto.

### RF-10 · Preservar a resposta bruta da PTAX
**Origem:** RN-02, RN-08, OBJ-01, OBJ-02, P1, P2.

- **Dado** que a consulta à PTAX retorna uma resposta JSON,
- **Quando** a resposta é recebida,
- **Então** seus bytes originais são gravados antes da interpretação, em chave determinística por fonte, moeda, data de referência, janela consultada e SHA-256, sem identificador da execução, com endereço de origem, instante da coleta e SHA-256.
- **Dado** que a janela não retorna boletins,
- **Quando** a resposta JSON vazia é recebida,
- **Então** ela também é preservada e associada à execução, para que a ausência possa ser auditada.
- **Dado** que outra execução recebe os mesmos bytes para a mesma fonte, moeda, data de referência e janela,
- **Quando** a resposta bruta é gravada,
- **Então** a chave determinística é idêntica e o manifesto da nova execução referencia o objeto imutável existente.

## Extração

### RF-11 · Gerar `livros.jsonl` a partir dos brutos
**Origem:** RN-01, RN-08, RN-11, OBJ-01, OBJ-03, P1, P3.

- **Dado** que os HTML brutos da execução estão disponíveis no MinIO,
- **Quando** os registros de livros são extraídos,
- **Então** a extração lê somente os objetos já gravados no MinIO e gera `livros.jsonl`, sem consultar novamente o site.
- **Dado** que um livro foi extraído,
- **Quando** sua linha é gravada,
- **Então** ela contém exatamente `upc`, `url`, `titulo`, `categoria`, `avaliacao`, `preco_gbp`, `em_estoque`, `qtd_estoque` e `coletado_em`; o UPC vem do detalhe e identifica o livro.
- **Dado** que a página HTML contém charset no próprio documento, mas não no cabeçalho HTTP,
- **Quando** os campos são extraídos,
- **Então** título e demais valores textuais são preservados corretamente e o HTML bruto permanece inalterado.
- **Dado** que a listagem informa uma classificação por estrelas,
- **Quando** `avaliacao` é gravada,
- **Então** ela conserva como string o rótulo original (`One`, `Two`, `Three`, `Four` ou `Five`), sem conversão numérica.
### RF-12 · Gerar `cotacoes.jsonl` a partir do bruto PTAX
**Origem:** RN-02, RN-03, RN-08, OBJ-01, OBJ-03, P1, P3.

- **Dado** que a resposta bruta da PTAX está disponível no MinIO,
- **Quando** a cotação é extraída,
- **Então** a extração lê somente o JSON bruto já gravado, sem consultar novamente a API, e gera `cotacoes.jsonl` contendo exatamente `moeda`, `dataHoraCotacao`, `tipoBoletim`, `cotacaoCompra` e `cotacaoVenda`.
- **Dado** que a resposta não contém fechamento elegível,
- **Quando** `cotacoes.jsonl` é gerado,
- **Então** nenhum valor de cotação é inventado e a ausência é registrada no manifesto.

## Execução

### RF-13 · Registrar manifesto por execução
**Origem:** DN-02, OBJ-02, P2.

- **Dado** que uma execução começa,
- **Quando** ela termina, com sucesso ou incompleta,
- **Então** existe um manifesto próprio com identificador, data de referência, horários de início e fim, estado da execução, quantidades declaradas e extraídas, fontes consultadas e divergências ou ausências observadas; cada item registra seu estado, inclusive `falhou` para erro final.
- **Dado** que uma execução foi reexecutada,
- **Quando** a nova execução termina,
- **Então** seu manifesto é distinto e o manifesto anterior permanece disponível.

### RF-14 · Marcar divergência de quantidade como falha
**Origem:** RN-10, DN-02, OBJ-02, P2.

- **Dado** que a execução coleta todas as categorias,
- **Quando** compara livros extraídos com o total declarado pela página inicial,
- **Então** quantidades diferentes marcam a execução como falha e a diferença numérica fica registrada no manifesto.
- **Dado** que a execução coleta categorias filtradas,
- **Quando** compara livros extraídos com o total esperado,
- **Então** usa a soma dos totais declarados pelas páginas das categorias selecionadas; qualquer divergência marca falha e fica registrada no manifesto.
- **Dado** que as quantidades coincidem,
- **Quando** a comparação termina,
- **Então** o critério de completude de livros é aprovado.

### RF-15 · Reexecutar sem duplicar o resultado diário
**Origem:** RN-09, RN-08, OBJ-02, P2.

- **Dado** que já existe resultado extraído para a data de referência D,
- **Quando** outra execução para D termina,
- **Então** `livros.jsonl` e `cotacoes.jsonl` passam a representar o resultado mais recente de D, sem linhas duplicadas de livro por UPC nem duplicação da cotação de referência.
- **Dado** que uma nova execução para D grava novos brutos,
- **Quando** o resultado diário é substituído,
- **Então** os brutos e o manifesto da execução anterior permanecem preservados e associados aos seus identificadores de execução.

### RF-16 · Enviar datas PTAX no formato aceito
**Origem:** RN-02, RN-03, DN-02, OBJ-02, P2.

- **Dado** que a data inicial e a data final da janela são datas válidas,
- **Quando** a consulta à PTAX é preparada,
- **Então** ambas são enviadas no formato `MM-DD-AAAA`; por exemplo, 24/10/2026 é enviado como `10-24-2026`, nunca como `2026-10-24` ou `24-10-2026`.
- **Dado** que a API PTAX responde com HTTP 500 após receber uma data no formato inválido,
- **Quando** a resposta é processada,
- **Então** o manifesto registra falha de consulta e a execução não classifica o erro como janela sem fechamento nem como resposta vazia HTTP 200.

## Matriz RN → RF

| RN | RF |
|---|---|
| RN-01 | RF-04, RF-11 |
| RN-02 | RF-07, RF-08, RF-10, RF-12, RF-16 |
| RN-03 | RF-07, RF-12, RF-16 |
| RN-04 | RF-05 |
| RN-05 | RF-06 |
| RN-06 | RF-06 |
| RN-07 | RF-06 |
| RN-08 | RF-09, RF-10, RF-11, RF-12, RF-15 |
| RN-09 | RF-09, RF-15 |
| RN-10 | RF-02, RF-14 |
| RN-11 | RF-04, RF-11 |
