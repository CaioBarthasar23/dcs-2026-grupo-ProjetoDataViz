# Rastreabilidade

> Matriz atualizada na avaliação ATAM. Uma linha para cada RF e RNF de
> `specs/spec.md`. `Atendido` requer evidência do critério; `parcial` identifica
> a parte demonstrada e a lacuna; sem evidência não há estado atendido.

| Requisito | Decisão / ADR | Componente | Tarefa | Evidência | Estado | Razão |
|---|---|---|---|---|---|---|
| RF-01 | ADR-002, ADR-005, ADR-006 | Domínio Railway porta 9000; serviço MinIO; script `verificar.sh` | T-04, T-06 | `docs/evidencias/verificar_railway.txt`, `docs/evidencias/T-06_deploy.txt` | atendido | Evidência do grupo registra acesso anônimo negado e operação autenticada de gravação/leitura pela API no endpoint HTTPS. |
| RF-02 | ADR-006 | Buckets MinIO e `criar_buckets.sh` | T-03, T-04 | `docs/evidencias/T-03_criar_buckets.txt`, `docs/evidencias/verificar_railway.txt` | parcial | Os quatro buckets existem e a listagem Railway os mostra; não há evidência de duas execuções bem-sucedidas de `criar_buckets.sh railway`. |
| RF-03 | ADR-001, ADR-003 | `docker-compose.yml`, Dockerfile e serviço Railway | T-01, T-02, T-06 | `docs/evidencias/T-01_compose.txt`, `docs/evidencias/T-02_dockerfile.txt`, `docs/evidencias/T-06_deploy.txt` | atendido | A configuração local e o Dockerfile usam a tag fixada; logs do deploy reportam a mesma versão MinIO. |
| RF-04 | ADR-006, ADR-008 | `scripts/verificar.sh`, Cliente mc, evidências | T-04 | `docs/evidencias/T-04_verificar_local.txt`, `docs/evidencias/verificar_local.txt`, `docs/evidencias/verificar_railway.txt`, `docs/evidencias/verificar_railway.txt` | atendido | Saídas registram saúde, 403 anônimo, buckets e ida/volta de objeto nos ambientes local e Railway. |
| RF-05 | ADR-003, ADR-006, ADR-008 | README, Compose e scripts | T-05 | `docs/evidencias/T-05_readme.txt` | parcial | Os comandos documentados passaram no ambiente existente; recriação a partir de ambiente vazio e execução por outro integrante não foram demonstradas. |
| RF-06 | ADR-004 | Volume Railway em `/data` e serviço MinIO | T-06, T-07 | `docs/evidencias/T-06_deploy.txt`, `docs/evidencias/T-07_persistencia.txt` | parcial | A chave e o conteúdo definidos no critério T-07 foram lidos após redeploy; a primeira leitura retornou 502 e a repetição manual após 10 s confirmou o conteúdo. A evidência cobre um objeto, não a persistência de todos os objetos previstos em RF-06. |
| RF-07 | ADR-002, ADR-005 | Endpoint público, autenticação MinIO e armazenamento de credenciais | T-04, T-06 | `docs/evidencias/T-04_verificar_local.txt`, `docs/evidencias/verificar_railway.txt`, `docs/evidencias/T-06_deploy.txt` | parcial | HTTP 403 anônimo foi demonstrado; não há evidência de varredura de segredos em todos os arquivos/referências Git. |
| RNF-01 | ADR-009 | Painel de uso Railway e processo de acompanhamento | T-09 | Nenhuma; T-09 pendente | não atendido | Não foi registrado consumo do crédito nem evidência de que o total permanece menor ou igual a US$ 5. |
| RNF-02 | ADR-001 | Dockerfile e Compose | T-01, T-02, T-06 | `docs/evidencias/T-01_compose.txt`, `docs/evidencias/T-02_dockerfile.txt`, `docs/evidencias/T-06_deploy.txt` | atendido | Evidências e logs mostram a tag fixada; não há referência `latest` nas configurações usadas. |
| RNF-03 | ADR-007 | Lógica de repetição e teste controlado | T-08 | Nenhuma; T-08 pendente | não atendido | A repetição com espera crescente após 502 ainda não foi implementada nem testada. |
| RNF-04 | ADR-008 | Scripts e arquivos em `docs/evidencias/` | T-01 a T-07 | Evidências listadas nesta matriz | atendido | As verificações executadas têm evidências identificadas; os arquivos examinados não incluem valores de credenciais. |

## Decisões sem requisito

Não foram identificadas decisões sem requisito ou restrição relacionado. As
decisões registradas ligam-se aos RF/RNF indicados nos ADRs.

## Requisitos sem cobertura

Nenhum requisito está sem tarefa associada na tabela de cobertura de
`specs/tasks.md`. RNF-01 e RNF-03 têm tarefas, mas permanecem sem evidência de
conclusão; ver estados parciais/não atendidos acima.
