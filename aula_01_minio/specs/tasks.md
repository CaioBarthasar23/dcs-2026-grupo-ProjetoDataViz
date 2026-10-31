# Tarefas

> Etapa 5 do SDD. Preenchido pelo prompt 5 a partir de `specs/plan.md`.
> Tarefa pequena: cabe em um prompt de implementação e termina com uma verificação
> executável. Marque [x] só depois de ver a saída da verificação.

| ID | Tarefa | Requisito | Verificação (teste ou comando) | Evidência esperada | Status |
|---|---|---|---|---|---|
| T-01 | Criar `docker-compose.yml` do MinIO local com imagem/tag fixadas, portas 9000 e 9001, volume nomeado e healthcheck `mc ready local`. | RF-03, RF-04, RNF-02 | `docker compose config --quiet`; após autorização para iniciar o ambiente, `docker compose up -d` e `docker compose ps` | Configuração válida e serviço local com estado `healthy`; sem segredos na saída registrada. | [x] |
| T-02 | Criar `minio_railway/Dockerfile` com a imagem fixada e o comando de inicialização definidos em `specs/plan.md`. | RF-01, RF-03, RNF-02 | `docker build -f minio_railway/Dockerfile -t minio-grupo:RELEASE.2025-10-15T17-29-55Z minio_railway` | Build concluído com sucesso e uso da tag fixada, sem `latest`. | [x] |
| T-03 | Criar `scripts/criar_buckets.sh` para criar `raw`, `bronze`, `silver` e `gold` de forma idempotente nos destinos `local` e `railway`; ler as variáveis do `.env` conforme `.env.example` sem imprimir valores. Acesso ao Railway pode consumir crédito. | RF-02, RF-07 | Executar duas vezes `bash scripts/criar_buckets.sh local` e duas vezes `bash scripts/criar_buckets.sh railway`; conferir `mc ls local` e `mc ls railway`. | Todas as execuções terminam com código 0 e cada listagem contém exatamente os quatro buckets; saídas sem segredos. | [ ] |
| T-04 | Criar `scripts/verificar.sh` para `local` e `railway`: saúde, HTTP 403 para acesso anônimo, buckets, gravação e leitura do mesmo objeto de teste; salvar saída em `docs/evidencias/`. Ler as variáveis do `.env` sem imprimi-las. Sem lógica de nova tentativa. Acesso ao Railway pode consumir crédito. | RF-01, RF-02, RF-04, RF-07, RNF-04 | `bash scripts/verificar.sh local` e `bash scripts/verificar.sh railway` | Ambas as execuções passam nas verificações definidas e deixam evidências identificadas por ambiente em `docs/evidencias/`, sem segredos. | [ ] |
| T-05 | Documentar no README da pasta os passos de recriação do zero para os ambientes local e publicado, incluindo dependências, comandos e verificações. | RF-05 | Seguir os passos documentados em um ambiente local vazio; executar `docker compose config --quiet`, `bash scripts/criar_buckets.sh local` e `bash scripts/verificar.sh local`. | Um integrante consegue recriar e verificar o ambiente seguindo o README; saída da verificação fica em `docs/evidencias/`. | [ ] |
| T-06 | Fazer deploy no Railway conforme o Prompt 8, configurar o serviço, volume em `/data` e domínio HTTPS somente para a porta 9000. Cria recursos no Railway e consome crédito. | RF-01, RF-03, RF-07 | `railway status`; em Bash, `set -a; . ./.env; set +a; curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' "$MINIO_RAILWAY_ENDPOINT"` | Serviço ativo e domínio HTTPS retorna uma resposta; console não publicado. A verificação completa fica em T-04. | [ ] |
| T-07 | Testar persistência de um objeto após redeploy manual do serviço no painel do Railway; o grupo autoriza e executa o redeploy, que pode consumir crédito. | RF-06 | Antes do redeploy: `mc pipe railway/raw/t07-persistencia.txt <<'EOF'` seguido do conteúdo `persistencia-t07` e `EOF`. Depois do redeploy manual: `mc cat railway/raw/t07-persistencia.txt` e comparar o conteúdo retornado com `persistencia-t07`. | O objeto retorna o conteúdo `persistencia-t07` após o redeploy; evidência registrada sem segredos. | [ ] |
| T-08 | Implementar a repetição de gravação com espera crescente e mesma chave, e teste controlado que simula uma falha 502 seguida de repetição; não depender de resposta real do Railway. | RNF-03 | `bash tests/testar_retry_502.sh` | O teste demonstra a falha simulada, a repetição da gravação na mesma chave e um único objeto final com o conteúdo esperado. O máximo de tentativas continua hipótese: validação pendente. | [ ] |

## Ordem de execução e dependências
- T-01 e T-02 podem ser iniciadas em paralelo.
- T-06 depende de T-02 e das tarefas manuais de login e credenciais; a cópia do domínio para o `.env` ocorre depois que o domínio estiver disponível.
- T-03 depende de T-01 para `local` e de T-06 para `railway`.
- T-04 depende de T-01, T-03 e T-06; assim, a sequência publicada é T-06 → T-04 → T-07, sem ciclo.
- T-07 depende de T-04; o redeploy é feito manualmente pelo grupo no painel do Railway.
- T-08 cria a pasta nova `tests/` e implementa a simulação local/controlada do 502; não depende do Railway.
- T-05 consolida os passos após T-01 a T-08 estarem definidos e verificados.
- T-09 começa após T-06 e acompanha o consumo durante o trial; é uma tarefa manual do grupo.

## Cobertura dos requisitos
- RF-01: T-02, T-04, T-06.
- RF-02: T-03, T-04.
- RF-03: T-01, T-02, T-06.
- RF-04: T-01, T-04.
- RF-05: T-05.
- RF-06: T-07.
- RF-07: T-03, T-04, T-06 e tarefas manuais de credenciais.
- RNF-01: T-09.
- RNF-02: T-01, T-02.
- RNF-03: T-08.
- RNF-04: T-04.

## Tarefas manuais (feitas pelo grupo, não pelo agente)

- [ ] Fazer login no Railway.
- [ ] Gerar a senha e cadastrá-la como variável do serviço Railway e no `.env` local; não compartilhar nem versionar o valor.
- [ ] Copiar o domínio público do Railway para `MINIO_RAILWAY_ENDPOINT` no `.env` local.

| ID | Tarefa | Requisito | Verificação (teste ou comando) | Evidência esperada | Status |
|---|---|---|---|---|---|
| T-09 | Acompanhar manualmente o consumo do crédito do trial no painel do Railway e registrar a evidência em `docs/evidencias/`, sem credenciais. | RNF-01 | Consultar o consumo acumulado no painel do Railway e conferir se permanece dentro do limite de US$ 5 do trial. | Registro do consumo observado em `docs/evidencias/`, suficiente para verificar o limite sem expor segredos. | [ ] |
