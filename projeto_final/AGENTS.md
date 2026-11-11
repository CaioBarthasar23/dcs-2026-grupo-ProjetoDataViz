AGENTS.md — projeto_final (Cartas Pokémon como Ativo de Coleção)
Leia este arquivo antes de qualquer tarefa. Se um pedido contradisser este arquivo, pare e pergunte.
Escopo
Trabalhe somente dentro de `projeto\_final/`. Não altere as pastas de aula nem a raiz do repositório, exceto `.github/workflows/coleta-diaria.yml` e `.gitignore`, e só quando a tarefa pedir.
Projeto individual. Coleção: SSP (SV08: Surging Sparks), groupId 23651. Responsável: CaioBarthasar23 (pendente de confirmação do professor).
O agente analisa, propõe e executa o que foi autorizado. Não cria requisito, não aceita risco e não encerra divergência: essas decisões são do aluno e ficam em ADR com nome e motivo.
Comandos
Permitidos (dentro de `projeto\_final/`):
`pip install -r requirements.txt`, `python -m pytest`
`python -m src.collector check` (somente leitura)
`python -m src.silver rebuild --fonte local --destino local` (ensaio sem rede)
`git status`, `git diff`, `git log`
Somente com autorização expressa do aluno na mesma mensagem:
`python -m src.collector collect | upload | backfill-ptax`, `python -m src.silver rebuild --destino s3` (gravam no bucket compartilhado, só no prefixo `group\_id=23651`)
Proibidos: `git commit`, `git push`, apagar ou sobrescrever objetos do bucket, ler ou imprimir `.env`.
O agente propõe a mensagem de commit; quem comita é o aluno.
Segredos
A chave do RustFS da turma e qualquer credencial ficam só no `.env` (fora do Git) e nos secrets do GitHub: `S3\_ENDPOINT`, `S3\_ACCESS\_KEY`, `S3\_SECRET\_KEY`.
Nunca escreva valor de credencial em código, docs, evidências, prompts, logs, commits ou mensagens ao agente. `.env.example` só tem nomes.
Evidências em `docs/evidencias/` são conferidas antes do commit: sem segredo.
Se uma credencial aparecer em qualquer commit, avisar o professor: apagar o arquivo não basta, o histórico é público.
Invariantes de dados (valem em toda etapa)
`raw/` é imutável: nunca sobrescrever nem apagar; conferir se a chave existe antes de gravar.
Silver e gold são derivadas e reconstruíveis a partir do bruto com um comando.
Nulo não é zero. Dia sem coleta é lacuna declarada no README, nunca preenchida com dado inventado.
Silver segue o contrato comum da turma (nomes e tipos exatos; colunas extras permitidas).
Câmbio: última PTAX de fechamento conhecida, nunca posterior ao dia do preço (ASOF JOIN).
Carteira: a escolha das cartas usa só dados do primeiro dia; taxa de venda é parâmetro (15% é hipótese declarada em ADR).
Filtros de preço mínimo em dólar. Code Card fica fora das perguntas 1, 3 e 4.
Nunca escrever no prefixo de outra coleção.
Fluxo SDD e gates
Ordem: AGENTS.md, persona, objetivos, especificação, plano, tarefas, implementação, validação ATAM. Um prompt CREATE por etapa; ao fim de cada uma, pare e aguarde revisão.
Etapa	Artefato	Gate
Persona	docs/00_persona.md	decisão, frequência e dor presentes; número sem origem marcado como hipótese
Objetivos	docs/01_objetivos_negocio.md	cada objetivo com métrica verificável e origem
Especificação	specs/spec.md	RF/RNF com Dado/Quando/Então, cada um ligado a um objetivo
Plano	specs/plan.md	C4 contexto e contêineres em Mermaid; cada escolha aponta para RF, RNF ou restrição
Tarefas	specs/tasks.md	cada tarefa com requisito e verificação executável
Implementação	src/, tests/, dashboard/	uma tarefa por vez, teste junto, saída real em docs/evidencias/
ATAM	docs/atam.md, docs/adr/, docs/rastreabilidade.md	cenários de seis partes; uma linha por RF e RNF
Mostre o plano e espere confirmação antes de editar arquivos.
Não invente números. Sem origem: "hipótese, validação pendente". A marca de hipótese sobrevive de uma etapa para a outra.
Nenhum arquivo em `src/` sem requisito que o justifique; nenhuma tarefa sem verificação.
`docs/prompts.md` guarda só os prompts realmente enviados, como foram enviados, com data, agente e modelo. Não reescrever.
Não declare sucesso sem mostrar a saída real do comando.
Commits
Formato: `tipo(T-xx): descrição \[RF-yy]`, por exemplo `feat(T-05): gravador do raw recusa sobrescrita \[RF-02]`. Etapas de documento: `docs(T-00): persona do colecionador`.
Um assunto por commit. O ADR da carteira `propria` precisa de commit anterior ao primeiro cálculo da carteira.
Nunca commitar `.env`, `data\_local/`, `artifacts/`, `.venv/`.
Estado atual (honesto)
`src/collector.py` e `src/silver.py` foram escritos antes da persona e da especificação, porque o histórico de preços só começa com a coleta. Registrar em ADR-001, com a origem do código. A especificação descreve o comportamento esperado; a rastreabilidade marca o estado real (atendido, parcial, não atendido). Não reescrever a cronologia.
Ainda não existem: gold, dashboard, carteiras e a maior parte da documentação.