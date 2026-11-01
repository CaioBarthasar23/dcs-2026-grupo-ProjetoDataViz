# ADR-002: publicar somente a API na porta 9000

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

RF-01 requer API S3 por HTTPS no Railway. RES-04 identifica 9000 como API e
9001 como console; o console público está fora do escopo.

## Requisitos e cenários relacionados

RF-01, RF-07, CEN-02.

## Alternativas consideradas

1. Publicar 9000 e 9001: descartada porque exporia o console à Internet.
2. Não publicar domínio: descartada porque impediria o acesso HTTPS exigido por
   RF-01.
3. Publicar somente 9001: descartada porque essa porta é o console, não a API
   S3.

## Decisão

Criar domínio Railway somente para a porta 9000 e manter a porta 9001 sem domínio
público. Tática de segurança: reduzir a superfície de ataque exposta; a
autenticação continua sendo exigida pela API.

## Consequências

- Positivas: endpoint público limitado à API necessária; console fica fora da
  exposição pública observada.
- Negativas (o trade-off): administração pelo console não fica disponível
  remotamente; operações precisam usar acesso local ou ferramentas autenticadas.

## Riscos

Uma mudança de configuração pode adicionar acidentalmente domínio à porta 9001.
A restrição de porta não substitui autenticação ou gestão de credenciais.

## Evidência necessária

Listar domínios do serviço e confirmar que o único destino é a porta 9000;
validar API HTTPS e negar acesso anônimo. Evidências: saída de
`railway domain list --service minio` observada na revisão (não persistida em
`docs/evidencias/`), `docs/evidencias/T-06_deploy.txt` e
`docs/evidencias/verificar_railway.txt`.

## Condição de revisão

Reabrir se o serviço precisar de administração remota ou se a API/console mudar
de porta; qualquer publicação da porta 9001 requer nova avaliação de segurança.
