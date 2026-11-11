# Fluxo · Gravação de objeto raw com falha do proxy

## Diagrama de sequência

```mermaid
sequenceDiagram
    participant ColetorBooks
    participant GravadorS3
    participant Railway as MinIO no Railway
    participant Manifesto

    ColetorBooks->>GravadorS3: gravar_raw chave, bytes e metadados
    GravadorS3->>GravadorS3: calcular SHA-256 e montar chave determinística
    GravadorS3->>Railway: PUT do corpo na chave K
    alt Proxy retorna 502 transitório
        Railway-->>GravadorS3: HTTP 502
        GravadorS3->>Manifesto: registrar tentativa de gravação e erro transitório
        GravadorS3->>GravadorS3: aguardar backoff dentro do limite
        GravadorS3->>Railway: repetir PUT dos mesmos bytes na mesma chave K
        alt Retry retorna 2xx
            Railway-->>GravadorS3: objeto K gravado
            GravadorS3-->>ColetorBooks: confirmar chave K e SHA-256
            ColetorBooks->>Manifesto: registrar item gravado
        else Proxy continua falhando ou limite excedido
            Railway-->>GravadorS3: erro final
            GravadorS3-->>ColetorBooks: retornar erro de gravação
            ColetorBooks->>Manifesto: marcar item falho sem apontar para objeto inexistente
        end
    else PUT retorna 2xx
        Railway-->>GravadorS3: objeto K gravado
        GravadorS3-->>ColetorBooks: confirmar chave K e SHA-256
        ColetorBooks->>Manifesto: registrar item gravado
    else Erro permanente
        Railway-->>GravadorS3: falha não repetível
        GravadorS3-->>ColetorBooks: retornar erro permanente
        ColetorBooks->>Manifesto: registrar item falho
    end
```

## Requisitos realizados

**RF:** RF-09, RF-10, RF-13.  
**RNF:** RNF-04, RNF-05, RNF-06, RNF-07, RNF-10.

| RNF | Como o fluxo o realiza |
|---|---|
| RNF-04 | Metadados ASCII são validados antes do PUT; o mesmo formato é usado no destino local e Railway. |
| RNF-05 | Cada tentativa e o erro final são registrados no manifesto, sem marcar como gravado um objeto que falhou. |
| RNF-06 | O 502 transitório recebe retry limitado e espera com backoff. Cada retry usa os mesmos bytes e a mesma chave K. |
| RNF-07 | A chave derivada da fonte, data, recurso e hash não incorpora ID de execução; retry não cria outra chave nem altera conteúdo. |
| RNF-10 | O adaptador mantém o mesmo contrato para MinIO local e Railway; apenas o endpoint configurado muda. |
