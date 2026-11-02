# Registro de prompts

## Etapa 01 · Personas e objetivos

- **Data:** 2026-11-02.
- **Quem enviou:** usuário.
- **Agente e modelo:** Codex, GPT-6.
- **Arquivos alterados:** `docs/00_persona.md`, `docs/01_objetivos.md`, `docs/prompts.md`.
- **Confirmação do plano:**

```text
Ok, pode executar, com estas restrições. (1) Altere somente docs/00_persona.md, docs/01_objetivos.md e docs/prompts.md; não leia o .env, não acesse o Railway. (2) Personas: P1 time dono de fonte, P2 analista no ClickHouse, P3 engenheiro que opera a ingestão e é acionado quando algo para; cada uma com a decisão que toma. (3) Objetivos OBJ-01... com persona, métrica, como medir (comando ou consulta) e meta; cubra P1 (fonte nova sem mudar o banco), P2 (dado consultável logo após o 202 do POST) e P3 (saber o que parou e recuperar sem perder dado). (4) Meta sem origem fica “hipótese, validação pendente”; “poucos segundos” não é meta, não invente números. (5) Domínios: telemetria, livros e ptax. Fora de escopo: schema por domínio, DLX, prefetch, ReplacingMergeTree, modelo dimensional e painel. (6) No prompts.md, registre data, quem enviou, agente e modelo, arquivos alterados e o prompt literal. Nada de código.
```

- **Prompt literal recebido:**

```text
[C] Personagem
Você é gerente de produto de dados. Descreve quem empurra dado para a
plataforma, quem consome e que decisão cada um toma. Não escreve código.

[R] Pedido
Crie dois arquivos:
1. docs/00_persona.md com três personas: P1 time dono de uma fonte que
   precisa entregar dado novo sem pedir tabela nova; P2 analista que
   consulta o dado no ClickHouse; P3 engenheiro de dados que opera o
   servidor de ingestão e é acionado quando algo para.
2. docs/01_objetivos.md com objetivos OBJ-01... ligados às personas,
   cada um com métrica, como medir (comando ou consulta) e meta.

[E] Exemplos
## OBJ-01 · Fonte nova sem mudar o banco
- Persona: P1.
- Métrica: passos para uma fonte nova começar a gravar.
- Como medir: incluir a tag em DOMINIOS no .env e reiniciar o servidor;
  nenhum CREATE TABLE.
- Meta: hipótese, validação pendente.
## OBJ-02 · Dado consultável em poucos segundos
- Persona: P2.
- Métrica: tempo entre o 202 do POST e a linha no ClickHouse.
- Como medir: script de medição da Etapa 09.

[A] Ajustes
- Domínios desta aula: telemetria (Aula 02), livros e ptax (Aula 03).
- Fora de escopo: schema de cada domínio (Aula 07), DLX, prefetch e
  ReplacingMergeTree (Aula 06), modelo dimensional (Aula 05), painel.
- Valor sem origem: "hipótese, validação pendente".
- Nada de código.

[T] Tipo de saída
Markdown. 00_persona.md com até 60 linhas; 01_objetivos.md com até 70
linhas e as seções Objetivos, Restrições, Fora de escopo e Hipóteses.

[E] Extras
Leia AGENTS.md. Mostre o plano, espere meu ok, escreva, registre o
prompt em docs/prompts.md e pare.
```
