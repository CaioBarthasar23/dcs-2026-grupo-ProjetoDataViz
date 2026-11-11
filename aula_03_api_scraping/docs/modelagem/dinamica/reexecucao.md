# Fluxo · Reexecução no mesmo dia

## Diagrama de sequência

```mermaid
sequenceDiagram
    participant Config
    participant ColetorBooks
    participant ColetorPtax
    participant ClienteHttp
    participant Books as books.toscrape.com
    participant PTAX as API PTAX
    participant GravadorS3
    participant Manifesto
    participant Extrator
    participant MinIO as MinIO local ou Railway

    Config->>Manifesto: iniciar nova execução para data D
    Manifesto->>Manifesto: gerar novo id de execução
    ColetorBooks->>ClienteHttp: coletar páginas e detalhes
    ClienteHttp->>Books: GET sequencial
    Books-->>ClienteHttp: respostas da data D
    ClienteHttp-->>ColetorBooks: bytes e metadados de cada resposta
    ColetorBooks->>GravadorS3: gravar raw por fonte, D, recurso e SHA-256
    ColetorPtax->>ClienteHttp: coletar janela GBP até D
    ClienteHttp->>PTAX: GET da janela
    PTAX-->>ClienteHttp: resposta PTAX
    ClienteHttp-->>ColetorPtax: bytes e metadados da resposta
    ColetorPtax->>GravadorS3: gravar raw por fonte, D, janela e SHA-256
    alt Chaves raw já existem com mesmos bytes
        GravadorS3->>MinIO: verificar ou reutilizar a mesma chave determinística
        MinIO-->>GravadorS3: objeto existente preservado
        GravadorS3-->>Manifesto: devolver chave reutilizada
    else Conteúdo mudou para um recurso
        GravadorS3->>MinIO: gravar em chave nova com SHA-256 novo
        MinIO-->>GravadorS3: novo objeto imutável
        GravadorS3-->>Manifesto: devolver chave nova
    end
    Manifesto->>GravadorS3: persistir manifesto novo com id distinto
    GravadorS3->>MinIO: PUT raw/manifestos/data=D/execucao=id.json
    MinIO-->>GravadorS3: manifesto novo preservado
    Extrator->>Manifesto: obter as chaves raw da nova execução
    Manifesto-->>Extrator: chaves e contagens de D
    Extrator->>GravadorS3: ler brutos e preparar JSON Lines
    GravadorS3->>MinIO: GET dos objetos raw
    MinIO-->>GravadorS3: bytes preservados
    GravadorS3-->>Extrator: objetos brutos
    alt Validação da nova execução aprovada
        Extrator->>GravadorS3: substituir livros.jsonl e cotacoes.jsonl de D
        GravadorS3->>MinIO: PUT nos mesmos endereços bronze diários
        MinIO-->>GravadorS3: resultado corrente confirmado
        Extrator->>Manifesto: finalizar nova execução
        Note over Manifesto,MinIO: Manifesto anterior e objetos raw anteriores permanecem preservados
    else Falha HTTP, armazenamento, extração ou divergência
        Extrator->>Manifesto: registrar falha da nova execução
        Note over Manifesto,MinIO: Manifesto anterior e objetos raw permanecem preservados
    end
```

## Requisitos realizados

**RF:** RF-09, RF-10, RF-13, RF-14, RF-15.  
**RNF:** RNF-04, RNF-05, RNF-06, RNF-07, RNF-08, RNF-10.

| RNF | Como o fluxo o realiza |
|---|---|
| RNF-04 | A mesma validação de metadados e o mesmo contrato de armazenamento valem no destino configurado. |
| RNF-05 | Uma falha da nova execução é registrada sem encobrir o estado ou manifesto de execuções anteriores. |
| RNF-06 | Falhas transitórias de coleta ou armazenamento usam retry limitado; erros permanentes são registrados. |
| RNF-07 | Cada reexecução recebe novo manifesto, reutiliza chave raw quando conteúdo e recurso coincidem, mantém brutos imutáveis e substitui apenas os JSONL diários correntes após validação. |
| RNF-08 | Credenciais usadas para acessar MinIO são fornecidas pela configuração local ignorada pelo Git e não aparecem no manifesto. |
| RNF-10 | Trocar MinIO local por Railway requer apenas alterar a configuração do destino, sem mudar os fluxos. |

## Matriz final · Fluxo | RF | RNF

| Fluxo | RF | RNF |
|---|---|---|
| Coleta PTAX | RF-07, RF-08, RF-10, RF-13, RF-16 | RNF-02, RNF-05, RNF-06 |
| Coleta Books | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-09, RF-13, RF-14 | RNF-01, RNF-02, RNF-03, RNF-05, RNF-06 |
| Gravação raw | RF-09, RF-10, RF-13 | RNF-04, RNF-05, RNF-06, RNF-07, RNF-10 |
| Extração | RF-11, RF-12, RF-13, RF-14 | RNF-01, RNF-04, RNF-05, RNF-07, RNF-09, RNF-10 |
| Reexecução | RF-09, RF-10, RF-13, RF-14, RF-15 | RNF-04, RNF-05, RNF-06, RNF-07, RNF-08, RNF-10 |
