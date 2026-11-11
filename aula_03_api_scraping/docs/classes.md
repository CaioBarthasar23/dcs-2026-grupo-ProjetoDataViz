# Arquitetura de classes · Monitor de preços

Os nomes das classes correspondem aos módulos previstos em `src/`. Assinaturas descrevem interfaces de projeto; não há implementação nesta etapa. `data_ref` fica no manifesto e nas chaves, não é campo extra dos JSONL.

```mermaid
classDiagram
    class Config {
        +endpoint_minio: str
        +access_key: str
        +secret_key: str
        +bucket_raw: str
        +bucket_bronze: str
        +categorias: list[str]
        +timeout: tuple[float, float]
        +max_tentativas: int
        +intervalo_minimo: float
        +user_agent: str
        +de_ambiente() Config
    }

    class ClienteHttp {
        +timeout: tuple[float, float]
        +max_tentativas: int
        +intervalo_minimo: float
        +user_agent: str
        +get(url: str, headers: dict[str, str] | None) Resposta
        -espera(tentativa: int, retry_after: float | None) float
    }

    class Resposta {
        +url: str
        +status_http: int
        +headers: dict[str, str]
        +corpo: bytes
        +tentativas: int
        +recebido_em: datetime
        +sucesso() bool
    }

    class ColetorBooks {
        +coletar(data_ref: date) None
        -descobrir_categorias(html: bytes) list[str]
        -extrair_proxima_pagina(html: bytes) str | None
        -extrair_livros(html: bytes) list[dict]
    }

    class ColetorPtax {
        +coletar(data_ref: date) None
        -montar_url(data_ref: date) str
        -selecionar_fechamento(corpo: bytes, data_ref: date) Cotacao | None
    }

    class GravadorS3 {
        +gravar_raw(chave: str, corpo: bytes, metadados: dict[str, str]) None
        +ler_raw(chave: str) bytes
        +gravar_bronze(chave: str, linhas: list[str]) None
    }

    class Manifesto {
        +id: str
        +data_ref: date
        +inicio: datetime
        +fim: datetime | None
        +estado: str
        +total_declarado: int | None
        +itens: list[ItemManifesto]
        +iniciar(data_ref: date) None
        +registrar_robots(item: ItemManifesto) None
        +registrar_item(item: ItemManifesto) None
        +finalizar(estado: str) str
        +chaves_raw() list[str]
    }

    class ItemManifesto {
        +url: str
        +chave: str | None
        +status_http: int | None
        +tentativas: int
        +bytes: int
        +sha256: str | None
        +erro: str | None
    }

    class Extrator {
        +extrair(manifesto: Manifesto) tuple[int, int]
        -extrair_livros(chaves: list[str]) list[Livro]
        -extrair_cotacoes(chaves: list[str]) list[Cotacao]
    }

    class Livro {
        +upc: str
        +url: str
        +titulo: str
        +categoria: str
        +avaliacao: str
        +preco_gbp: Decimal
        +em_estoque: bool
        +qtd_estoque: int | None
        +coletado_em: datetime
        +para_json() str
    }

    class Cotacao {
        +moeda: str
        +dataHoraCotacao: datetime
        +tipoBoletim: str
        +cotacaoCompra: Decimal
        +cotacaoVenda: Decimal
        +para_json() str
    }

    Config ..> ClienteHttp : configura
    Config ..> GravadorS3 : configura destino
    ClienteHttp ..> Resposta : retorna
    ColetorBooks --> ClienteHttp : consulta
    ColetorBooks --> GravadorS3 : recebe e grava bruto
    ColetorBooks --> Manifesto : registra respostas
    ColetorPtax --> ClienteHttp : consulta
    ColetorPtax --> GravadorS3 : recebe e grava bruto
    ColetorPtax --> Manifesto : registra resposta
    ColetorPtax ..> Cotacao : seleciona
    Manifesto *-- ItemManifesto : contém
    Manifesto --> GravadorS3 : persiste manifesto
    Extrator --> Manifesto : obtém chaves raw
    Extrator --> GravadorS3 : lê raw e grava bronze
    Extrator ..> Livro : produz
    Extrator ..> Cotacao : produz
```

## Dependências e limites

- `ColetorBooks` e `ColetorPtax` recebem `ClienteHttp`, `GravadorS3` e `Manifesto` por injeção; não inicializam nem importam o cliente MinIO.
- `Extrator` depende de `Manifesto` para localizar os brutos e de `GravadorS3` para lê-los e publicar JSONL. Não importa `requests`, `ClienteHttp` ou qualquer cliente de rede externa.
- `GravadorS3` recebe endpoint e credenciais via `Config`; os mesmos métodos servem MinIO local e Railway, com troca apenas da configuração.
- `ItemManifesto` registra cada tentativa final por recurso. `Manifesto` mantém totais e estado da execução e referencia chaves raw sem incorporar o ID da execução nessas chaves.
- `Livro.para_json()` emite exatamente os nove campos do contrato de livros. `Cotacao.para_json()` emite exatamente os cinco campos do contrato PTAX.
