# Plano de implementação · Aula 03

Este plano antecede a implementação e distribui o trabalho em tarefas de até 30 minutos, conforme a decomposição em [tasks.md](./tasks.md). Os tempos são estimativas de execução focada, não metas de desempenho do pipeline.

## Bibliotecas previstas

| Biblioteca | Uso previsto | RNF que justifica |
|---|---|---|
| `requests` | GET HTTP, timeout explícito, cabeçalhos, bytes de resposta e `Retry-After`; o retry e o intervalo são controlados pelo projeto. | RNF-02, RNF-03, RNF-06 |
| `beautifulsoup4` | Parsing de HTML já preservado no MinIO, sem rede no extrator. | RNF-01, RNF-09 |
| `boto3` | Acesso S3 compatível para ler e gravar objetos MinIO em ambos os destinos. | RNF-04, RNF-07, RNF-10 |
| `python-dotenv` | Carregar configuração local sem codificar credenciais; `.env` fica ignorado pelo Git. | RNF-08, RNF-10 |
| `pytest` | Testes unitários e de integração para contratos, falhas e destinos MinIO. | RNF-01, RNF-05, RNF-06, RNF-09, RNF-10 |

O restante usa a biblioteca padrão do Python, inclusive serialização JSON, hash SHA-256, datas/fusos, CLI, servidor HTTP simulado e mocks. Não adicionar outras dependências sem requisito RNF explícito.

## Estrutura prevista

```text
src/
  __init__.py
  cli.py                 # comandos executar, coletar e extrair
  config.py              # validação de ambiente e configuração
  http.py                # ClienteHttp, timeout, retry e intervalo
  storage.py             # GravadorS3 e chaves/metadados
  manifest.py            # Manifesto e ItemManifesto
  pipeline.py            # coordena coleta, validação e extração
  models.py              # Resposta, Livro e Cotacao/serialização
  collectors/
    __init__.py
    books.py              # robots.txt, categorias, paginação e detalhes
    ptax.py               # janela PTAX e seleção de Fechamento
  extractor.py            # leitura raw, parsing offline e bronze
tests/
  conftest.py
  fixtures/
    books/
    ptax/
  test_config.py
  test_http.py
  test_storage.py
  test_manifest.py
  test_books.py
  test_ptax.py
  test_models.py
  test_extractor.py
  test_cli.py
  integration/
    test_storage_minio.py
    test_pipeline.py
```

Fixtures contêm respostas sintéticas ou exemplos autorizados e versionados. Testes unitários, HTTP simulado e parsing não usam rede externa. Testes de armazenamento usam o MinIO local e o bucket de teste `teste`; limpeza deve apagar somente os objetos criados pelo teste nesse bucket.

## Comandos de execução

### Desenvolvimento e MinIO local

```bash
cd aula_03_api_scraping
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Preencha .env localmente, sem imprimir ou versionar credenciais.
docker compose up -d --wait
# Inicialize o bucket de teste `teste` no MinIO local conforme o setup do laboratório.
pytest -q
python -m src.cli executar
```

Para executar uma etapa isolada:

```bash
python -m src.cli coletar
python -m src.cli extrair --data-ref AAAA-MM-DD
```

O subcomando `executar` coleta, valida e extrai conforme os fluxos definidos. A implementação deve validar argumentos e configuração e encerrar com código não zero em falha.

### MinIO no Railway

Configure no ambiente Railway as mesmas variáveis S3 do `.env.example`, apontando o endpoint para o serviço MinIO remoto e usando credenciais do ambiente, não do Git. O projeto Railway deve ter buckets `raw`, `bronze` e `teste` provisionados; o último é usado somente pela integração.

```bash
cd aula_03_api_scraping
railway link
railway run python -m src.cli executar
```

Executar uma etapa isolada remotamente:

```bash
railway run python -m src.cli coletar
railway run python -m src.cli extrair --data-ref AAAA-MM-DD
```

`railway run` injeta a configuração do projeto no processo local; não transportar valores secretos para a linha de comando. Os comandos assumem Railway CLI instalado e projeto/serviço vinculados. Agendamento em produção continua fora de escopo.

### Validação direcionada

```bash
pytest tests/test_http.py -q
pytest tests/test_books.py tests/test_ptax.py tests/test_extractor.py -q
TEST_MINIO=1 pytest tests/integration/test_storage_minio.py -q
TEST_MINIO=1 pytest tests/integration/test_pipeline.py -q
```

Para executar a mesma integração no MinIO do Railway, use `railway run env TEST_MINIO=railway pytest tests/integration/test_storage_minio.py -q`. Os testes MinIO devem falhar explicitamente se o serviço ou bucket `teste` não estiver disponível; não substituir integração ausente por sucesso simulado.
