# MinIO do grupo

Este diretório contém o ambiente local e os scripts de operação do storage do
grupo. A imagem usada é
`ghcr.io/coollabsio/minio:RELEASE.2025-10-15T17-29-55Z`, com a mesma tag fixada
para os ambientes local e publicado.

## Dependências

- Docker com Docker Compose
- Bash
- `curl`
- Cliente `mc`

### Instalar `mc` no Codespace

O download oficial do cliente retornou HTTP 410 neste ambiente. Com o contêiner
local MinIO em execução, copie o cliente que já vem na imagem:

```bash
mkdir -p "$HOME/.local/bin"
docker cp minio_local-minio-1:/usr/bin/mc "$HOME/.local/bin/mc"
chmod +x "$HOME/.local/bin/mc"
export PATH="$HOME/.local/bin:$PATH"
mc --version
```

Para manter o diretório no `PATH` em novos terminais, adicione
`export PATH="$HOME/.local/bin:$PATH"` ao arquivo de inicialização do seu shell.

## Recriar e verificar o ambiente local

1. Crie o `.env` local a partir do exemplo e preencha as credenciais localmente.
   Nunca versione nem compartilhe o `.env`; não coloque valores de credenciais
   neste README ou em evidências.

   ```bash
   cp -n .env.example .env
   ```

2. Valide a configuração sem imprimir valores e inicie o serviço:

   ```bash
   docker compose config --quiet
   docker compose up -d
   docker compose ps
   ```

   Aguarde o serviço `minio` ficar `healthy`.

3. Se necessário, instale `mc` seguindo a seção acima. Crie os buckets:

   ```bash
   bash scripts/criar_buckets.sh local
   ```

   A criação é repetível. `mc mb --ignore-existing` pode imprimir
   `Bucket created successfully` mesmo quando o bucket já existe; essa mensagem
   não prova que um novo bucket foi criado. A prova de idempotência é cada
   execução terminar com código 0 e os timestamps dos quatro buckets
   permanecerem iguais em listagens sucessivas de `mc ls local`.

   ```bash
   mc ls local
   bash scripts/criar_buckets.sh local
   mc ls local
   ```

4. Execute a verificação local:

   ```bash
   bash scripts/verificar.sh local
   ```

   Ela verifica saúde HTTP, acesso anônimo negado, os quatro buckets e a
   gravação/leitura do objeto fixo `raw/_verificacao/teste.json`. A saída fica
   em `docs/evidencias/verificar_local.txt`; não contém credenciais.

## Ambiente publicado

Os passos do Railway dependem do deploy e da configuração manual previstos em
T-06 no Prompt 8. Não faça deploy como parte da recriação local. Depois que o
grupo concluir essa etapa e configurar as variáveis do serviço e do `.env`
local sem compartilhar credenciais, os comandos de criação e verificação são:

```bash
bash scripts/criar_buckets.sh railway
mc ls railway
bash scripts/verificar.sh railway
```

Não execute esses comandos antes da conclusão de T-06. O console não deve ser
publicado; somente a API S3 deve ficar disponível pelo domínio HTTPS configurado
no Railway.

## Tarefas ainda pendentes

- T-06: deploy e configuração do serviço no Railway, conforme o Prompt 8.
- T-07: verificar persistência após redeploy manual do serviço publicado.
- T-08: implementar e testar a repetição controlada após resposta 502.
