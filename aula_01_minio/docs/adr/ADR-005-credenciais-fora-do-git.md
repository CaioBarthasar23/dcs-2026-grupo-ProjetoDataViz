# ADR-005: credenciais fora do Git

- Status: aceito
- Data: 2026-11-01
- Responsáveis: Grupo do projeto

## Contexto e forças

O repositório é público (RES-05). RF-07 exige acesso autenticado e ausência de
segredos nos arquivos versionados. O serviço e os scripts dependem de
credenciais externas à configuração versionada.

## Requisitos e cenários relacionados

RF-07, CEN-02.

## Alternativas consideradas

1. Versionar `.env` ou valores em arquivos de configuração: descartada por
   expor credenciais no repositório público.
2. Codificar valores nos scripts: descartada pela mesma exposição e por
   dificultar rotação.
3. Permitir acesso anônimo: descartada por contrariar RF-07.

## Decisão

Manter `.env` apenas localmente e variáveis no serviço Railway; scripts carregam
o arquivo sem imprimir valores. Táticas de segurança: autenticação e
confidencialidade das credenciais em repouso no repositório.

## Consequências

- Positivas: arquivos versionados não precisam conter credenciais; acesso
  anônimo pode ser testado independentemente.
- Negativas (o trade-off): cada ambiente exige configuração manual coerente;
  divergência de valores pode impedir autenticação; rotação requer atualização
  em mais de um local.

## Riscos

Não existe evidência de varredura do histórico Git nem de ensaio de rotação. Um
startup inicial Railway apresentou alerta de credenciais padrão; logs
posteriores, após ação do grupo, não mostraram o alerta. A ocorrência reforça a
necessidade de verificar a aplicação das variáveis em serviço e ambiente
corretos.

## Evidência necessária

HTTP 403 sem autenticação em `docs/evidencias/verificar_railway.txt`;
varredura de arquivos e histórico Git ainda pendente.

## Condição de revisão

Reabrir se uma credencial for encontrada em referência pública, se houver
alteração do mecanismo de configuração, ou se o teste anônimo deixar de negar
acesso.
