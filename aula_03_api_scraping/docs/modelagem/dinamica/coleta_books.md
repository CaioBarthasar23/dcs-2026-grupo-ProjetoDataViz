# Fluxo · Coleta de categoria, paginação e detalhes

## Diagrama de sequência

```mermaid
sequenceDiagram
    participant Config
    participant ColetorBooks
    participant ClienteHttp
    participant Books as books.toscrape.com
    participant GravadorS3
    participant Manifesto

    Config->>ColetorBooks: fornecer categorias, User-Agent e data_ref
    ColetorBooks->>ClienteHttp: get robots.txt
    ClienteHttp->>Books: GET robots.txt com User-Agent
    alt robots.txt responde 200 ou 404
        Books-->>ClienteHttp: resposta com bytes e status
        ClienteHttp-->>ColetorBooks: Resposta robots
        ColetorBooks->>GravadorS3: gravar bytes de robots com chave determinística
        ColetorBooks->>Manifesto: registrar URL, status e chave de robots
    else Erro permanente ou retries esgotados
        Books-->>ClienteHttp: erro HTTP ou timeout final
        ClienteHttp-->>ColetorBooks: erro de robots
        ColetorBooks->>Manifesto: registrar erro e encerrar coleta do site
    end
    loop Cada categoria selecionada e suas páginas até não haver next
        ColetorBooks->>ClienteHttp: get(url da categoria ou próxima página)
        ClienteHttp->>Books: GET sequencial com intervalo e User-Agent
        alt Página responde HTTP 200
            Books-->>ClienteHttp: HTML da listagem
            ClienteHttp-->>ColetorBooks: Resposta da listagem
            ColetorBooks->>GravadorS3: gravar HTML antes de interpretar
            ColetorBooks->>ColetorBooks: localizar livros e link next
            loop Cada livro listado
                ColetorBooks->>ClienteHttp: get(url do detalhe)
                ClienteHttp->>Books: GET detalhe
                alt Resposta 429 com Retry-After 2
                    Books-->>ClienteHttp: 429 Retry-After 2
                    ClienteHttp->>ClienteHttp: aguardar 2 segundos
                    ClienteHttp->>Books: repetir GET do mesmo detalhe
                    alt Retry retorna 200
                        Books-->>ClienteHttp: HTML do detalhe
                        ClienteHttp-->>ColetorBooks: Resposta recuperada
                        ColetorBooks->>GravadorS3: gravar HTML do detalhe
                        ColetorBooks->>Manifesto: registrar status, tentativas, bytes e hash
                    else Retry retorna falha final
                        Books-->>ClienteHttp: erro HTTP ou timeout
                        ClienteHttp-->>ColetorBooks: erro final
                        ColetorBooks->>Manifesto: registrar item falho
                    end
                else Read timeout
                    Books--x ClienteHttp: timeout de leitura
                    ClienteHttp->>ClienteHttp: aguardar backoff com full jitter
                    ClienteHttp->>Books: repetir GET do mesmo detalhe
                    alt Retry após timeout retorna 200
                        Books-->>ClienteHttp: HTML do detalhe
                        ClienteHttp-->>ColetorBooks: Resposta recuperada
                        ColetorBooks->>GravadorS3: gravar HTML do detalhe
                        ColetorBooks->>Manifesto: registrar status, tentativas, bytes e hash
                    else Timeout repetido até esgotar tentativas
                        Books--x ClienteHttp: timeout de leitura final
                        ClienteHttp-->>ColetorBooks: erro final
                        ColetorBooks->>Manifesto: registrar item falho e causa
                    end
                else Resposta HTTP 200 sem retry
                    Books-->>ClienteHttp: HTML do detalhe
                    ClienteHttp-->>ColetorBooks: Resposta do detalhe
                    ColetorBooks->>GravadorS3: gravar HTML antes de interpretar
                    ColetorBooks->>Manifesto: registrar item gravado
                else Erro permanente ou limite excedido
                    Books-->>ClienteHttp: erro final
                    ClienteHttp-->>ColetorBooks: erro não recuperável
                    ColetorBooks->>Manifesto: registrar item falho
                end
            end
        else Erro de listagem ou retries esgotados
            Books-->>ClienteHttp: erro HTTP ou timeout final
            ClienteHttp-->>ColetorBooks: erro da página
            ColetorBooks->>Manifesto: registrar página falha e execução incompleta
        end
    end
```

## Requisitos realizados

**RF:** RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-09, RF-13, RF-14.  
**RNF:** RNF-01, RNF-02, RNF-03, RNF-05, RNF-06.

| RNF | Como o fluxo o realiza |
|---|---|
| RNF-01 | Campos são extraídos da listagem e do detalhe da mesma observação; a contagem final é comparada ao total declarado e divergência fica visível. |
| RNF-02 | Cada GET usa timeout explícito de conexão e leitura. |
| RNF-03 | Uma requisição ao site fica ativa por vez e o intervalo configurado separa o início de cada chamada. |
| RNF-05 | Erro em robots, listagem ou detalhe é registrado no manifesto com estado e causa. |
| RNF-06 | 429 respeita `Retry-After`; read timeout é transitório e repetido com full jitter, até o limite configurado. Erros permanentes não são repetidos. |
