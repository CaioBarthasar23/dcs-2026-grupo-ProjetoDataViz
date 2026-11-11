# Fluxo · Coleta da PTAX

## Diagrama de sequência

```mermaid
sequenceDiagram
    participant Config
    participant ColetorPtax
    participant ClienteHttp
    participant PTAX as API PTAX
    participant GravadorS3
    participant Manifesto

    Config->>ColetorPtax: fornecer configuração e data_ref D
    ColetorPtax->>ColetorPtax: montar janela em MM-DD-AAAA
    ColetorPtax->>ClienteHttp: get(url GBP com dataInicial e dataFinalCotacao)
    loop até sucesso ou limite configurado
        ClienteHttp->>PTAX: GET da janela com timeout explícito
        alt HTTP 200 com JSON
            PTAX-->>ClienteHttp: corpo JSON e status 200
            ClienteHttp-->>ColetorPtax: Resposta com corpo e tentativas
        else Timeout ou erro transitório e tentativas restantes
            PTAX--x ClienteHttp: timeout, erro de conexão, 408, 429 ou 5xx
            ClienteHttp->>ClienteHttp: aguardar Retry-After ou full jitter exponencial
        else Erro permanente ou retries esgotados
            PTAX-->>ClienteHttp: erro HTTP final ou timeout final
            ClienteHttp-->>ColetorPtax: erro de consulta
        end
    end
    alt Resposta HTTP 200 recebida
        ColetorPtax->>GravadorS3: gravar_raw com chave por fonte, janela e SHA-256
        GravadorS3-->>ColetorPtax: bruto gravado ou chave idêntica existente
        ColetorPtax->>ColetorPtax: selecionar Fechamento mais recente até D
        alt Existe fechamento elegível
            ColetorPtax->>Manifesto: registrar item, chave raw e cotação efetiva
        else value vazio ou sem Fechamento elegível
            ColetorPtax->>Manifesto: registrar ausência e estado incompleto
        end
    else Consulta falhou, incluindo data inválida
        ColetorPtax->>Manifesto: registrar falha sem classificar como janela vazia
    end
```

## Requisitos realizados

**RF:** RF-07, RF-08, RF-10, RF-13, RF-16.  
**RNF:** RNF-02, RNF-05, RNF-06.

| RNF | Como o fluxo o realiza |
|---|---|
| RNF-02 | `ClienteHttp` aplica timeout explícito de conexão e leitura à chamada PTAX. |
| RNF-05 | Janela vazia, falta de Fechamento e falha HTTP são registradas no manifesto como ausência ou falha, sem gerar cotação fictícia. |
| RNF-06 | Só falhas transitórias são repetidas, com limite configurado, backoff exponencial com full jitter e precedência de `Retry-After`. Erro permanente de formato não é tratado como janela vazia. |
