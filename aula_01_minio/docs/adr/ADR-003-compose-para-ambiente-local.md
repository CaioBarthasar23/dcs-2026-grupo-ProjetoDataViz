# ADR-003: Docker Compose para o ambiente local

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

RF-03 e RF-04 pedem ambiente local reprodutível e verificável. O plano fixa
imagem/tag, portas 9000/9001, volume nomeado e healthcheck `mc ready local`.

## Requisitos e cenários relacionados

RF-03, RF-04, RF-05, RNF-02.

## Alternativas consideradas

1. Executar MinIO manualmente no host: descartada por exigir configuração
   individual não expressa como configuração versionada.
2. Usar imagem/tag diferente localmente: descartada por divergir do ambiente
   publicado.
3. Não oferecer ambiente local: descartada por impedir verificação local e
   reduzir reprodutibilidade.

## Decisão

Usar `docker-compose.yml` com a imagem/tag fixada, portas locais 9000/9001,
volume nomeado `minio_data` e healthcheck existente. Tática de modificabilidade:
encapsular a configuração do serviço em um manifesto reproduzível.

## Consequências

- Positivas: inicialização e configuração local podem ser repetidas pelos
  integrantes; configuração pode ser validada sem imprimir valores com
  `docker compose config --quiet`.
- Negativas (o trade-off): ambiente local não reproduz domínio, proxy ou ciclo
  de vida de volume do Railway; diferenças ainda precisam ser avaliadas em
  verificações no serviço publicado.

## Riscos

O healthcheck depende do alias `local` existir dentro do contexto do contêiner;
isso é uma pergunta técnica registrada em `specs/plan.md`.

## Evidência necessária

Validar configuração, estado `healthy`, portas e imagem. Evidência:
`docs/evidencias/T-01_compose.txt`; equivalência de tag também em
`docs/evidencias/T-02_dockerfile.txt`.

## Condição de revisão

Reabrir se a configuração local deixar de iniciar de forma reprodutível ou se
Compose não estiver disponível nos ambientes usados pelo grupo.
