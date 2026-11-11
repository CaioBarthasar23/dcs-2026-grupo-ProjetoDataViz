# ADR-004 · Coleta sequencial com intervalo mínimo

**Status:** Proposta

## Contexto

A restrição da disciplina e RN-06 exigem consultas sequenciais; RN-07 e RF-06 exigem intervalo entre inícios de requisições. RNF-03 torna concorrência máxima de uma chamada ao site e o intervalo configurado verificáveis. A coleta completa pode exigir muitas páginas e detalhes, então paralelismo reduziria duração, mas aumentaria pressão sobre a fonte.

## Decisão

Executar uma requisição ao site por vez. Antes de iniciar a próxima, garantir que transcorreu o intervalo mínimo configurado desde o início da requisição anterior. O valor padrão de aceite ainda está pendente de validação; não fixar uma meta a partir da linha de base de 1 segundo. Aplicar a política no `ClienteHttp` para evitar que um coletor contorne o limite.

## Alternativas

- Paralelizar categorias ou detalhes para reduzir duração.
- Aplicar intervalo apenas entre lotes ou categorias.
- Fazer rate limiting independente em cada coletor.

## Consequências

- O comportamento é simples de auditar e controla a taxa de consulta ao site.
- A duração pode ser maior, especialmente em execução completa; retries também contam para a duração.
- Centralizar o intervalo evita divergência entre coletores, mas exige uma única instância/coordenador por execução.
- O valor configurado e o relógio usado para medir os intervalos precisam ser cobertos por testes.

**Origem:** DN-02; RF-05, RF-06; RN-04, RN-05, RN-06, RN-07; RNF-03.

**Diagramas da Etapa 08:** [coleta Books](../modelagem/dinamica/coleta_books.md), [coleta PTAX](../modelagem/dinamica/coleta_ptax.md).

**Referências:** [regras de negócio](../02_regras_de_negocio.md), [requisitos funcionais](../../specs/01_requisitos_funcionais.md).
