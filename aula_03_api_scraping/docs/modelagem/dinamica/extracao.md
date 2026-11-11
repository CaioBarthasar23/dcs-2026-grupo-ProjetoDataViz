# Fluxo · Extração dos objetos MinIO para JSON Lines

## Diagrama de sequência

```mermaid
sequenceDiagram
    participant Config
    participant Extrator
    participant Manifesto
    participant GravadorS3
    participant MinIO as MinIO local ou Railway

    Config->>Extrator: fornecer configuração de armazenamento
    Extrator->>Manifesto: obter chaves raw da execução concluída
    Manifesto-->>Extrator: lista de chaves de livros e PTAX
    loop Cada objeto raw referenciado
        Extrator->>GravadorS3: ler_raw chave
        GravadorS3->>MinIO: GET do objeto
        alt Leitura retorna bytes
            MinIO-->>GravadorS3: corpo bruto e metadados
            GravadorS3-->>Extrator: bytes imutáveis
            Extrator->>Extrator: interpretar HTML ou JSON e validar campos
        else Objeto ausente ou erro de leitura
            MinIO-->>GravadorS3: erro de armazenamento
            GravadorS3-->>Extrator: erro de leitura
            Extrator->>Manifesto: registrar falha de extração
        end
    end
    alt Validação e contagens aprovadas
        Extrator->>Extrator: serializar nove campos de Livro e cinco de Cotacao
        Extrator->>GravadorS3: gravar_bronze livros.jsonl e cotacoes.jsonl
        GravadorS3->>MinIO: PUT dos JSON Lines diários
        alt Gravação bronze retorna 2xx
            MinIO-->>GravadorS3: objetos bronze confirmados
            GravadorS3-->>Extrator: publicação concluída
            Extrator->>Manifesto: registrar contagens e estado final
        else Erro de gravação bronze
            MinIO-->>GravadorS3: erro de armazenamento
            GravadorS3-->>Extrator: erro de publicação
            Extrator->>Manifesto: registrar execução incompleta ou falha
        end
    else JSON inválido, campos inválidos ou contagem divergente
        Extrator->>Manifesto: registrar divergência e marcar falha
        Note over Extrator,Manifesto: Nenhuma cotação fictícia é criada
    end
```

Não há participante nem chamada de rede externa neste fluxo. O Extrator lê somente os objetos brutos pelo `GravadorS3`, valida e então publica os JSONL diários.

## Requisitos realizados

**RF:** RF-11, RF-12, RF-13, RF-14.  
**RNF:** RNF-01, RNF-04, RNF-05, RNF-07, RNF-09, RNF-10.

| RNF | Como o fluxo o realiza |
|---|---|
| RNF-01 | A extração valida os campos contratuais e compara o total extraído ao declarado antes de publicar. |
| RNF-04 | Metadados dos brutos são consumidos sem alteração e os objetos gerados seguem o mesmo contrato de armazenamento. |
| RNF-05 | Erros de leitura, dados inválidos e divergências são associados à execução no manifesto. |
| RNF-07 | Resultados bronze são publicados nos endereços diários correntes sem duplicar linhas por reexecução. |
| RNF-09 | A extração usa apenas chaves e bytes já persistidos no MinIO, sem requests ou qualquer rede de origem. |
| RNF-10 | `GravadorS3` aplica a mesma interface de leitura e gravação aos destinos local e Railway. |
