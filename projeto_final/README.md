# Cartas Pokémon como Ativo de Coleção

## Coleção escolhida

**SSP: SV08: Surging Sparks** (groupId **23651**, lançamento 08/11/2024).

Categoria Pokémon no TCGplayer (categoryId 3). Escolha declarada em 31/10/2026.

## Como rodar o coletor

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # preencha; o .env nunca vai para o repositório
```

| Comando | O que faz |
|---|---|
| `python -m src.collector collect` | Coleta TCGCSV (produtos e preços), PTAX e CDI e grava o bruto. Pode rodar mais de uma vez no dia: o que já existe não é regravado. |
| `python -m src.collector upload` | Sobe para o MinIO o bruto gravado em disco local, sem sobrescrever nada. |
| `python -m src.collector check` | Lista as coleções já ocupadas em `raw/tcgplayer/` no MinIO. |
| `python -m pytest` | Testes de unidade. |

`STORAGE=local` (padrão) grava em `data_local/`. `STORAGE=s3` grava direto no data lake da turma (RustFS).
O `S3_ENDPOINT` é `https://s3.afonsolelis.tech` (a API S3), não o link do console. Região `us-east-1`, endereço em estilo path, bucket `tcg`. A chave de acesso fica só no `.env` e nos secrets do GitHub, nunca no repositório.

## Regras que o coletor segue

- **Bruto imutável.** Nenhum objeto em `raw/` é sobrescrito ou apagado. O coletor confere se a chave existe antes de gravar, e o armazenamento local abre o arquivo em modo exclusivo.
- **Horário.** O TCGCSV atualiza por volta de 20h UTC (17h em Brasília). Antes das 18h de Brasília o coletor se recusa a gravar os preços, porque eles ainda seriam os do dia anterior. Agende para 18h30 de Brasília ou depois.
- **PTAX.** Só grava se o boletim de Fechamento já saiu. Depois das 15h, uma resposta vazia é gravada como "sem boletim" (fim de semana ou feriado).
- **CDI.** Grava a janela dos últimos 10 dias, porque a taxa de um dia útil só aparece na manhã seguinte.
- **Falhas isoladas.** Se uma fonte falhar, as outras continuam. O comando termina com código 1 se alguma deu erro.
- **Identificação.** Toda requisição leva `User-Agent` próprio e há pausa de 150 ms entre chamadas (o TCGCSV pede no mínimo 100 ms).

## Agendamento (GitHub Actions)

O workflow `.github/workflows/coleta-diaria.yml` roda todo dia às 18h30 de Brasília (21h30 UTC), com duas tentativas de reserva às 19h30 e 20h30. Como o coletor é idempotente, as repetições não duplicam nada.

Secrets necessários (Settings → Secrets and variables → Actions): `S3_ENDPOINT`, `S3_ACCESS_KEY` e `S3_SECRET_KEY`. Sem eles, o workflow grava só em disco e guarda o bruto como artifact por 90 dias, para nenhum dia da série se perder. Para testar na hora: aba Actions → coleta-diaria → Run workflow.

## Estrutura gravada

```
raw/tcgplayer/group_id=23651/data=AAAA-MM-DD/products.json
raw/tcgplayer/group_id=23651/data=AAAA-MM-DD/prices.json
raw/bcb_ptax/group_id=23651/data=AAAA-MM-DD/cotacao.json
raw/bcb_cdi/group_id=23651/data=AAAA-MM-DD/cdi.json
```

## Lacunas na série

_Registre aqui cada dia sem coleta e o motivo. Dia sem coleta fica como lacuna; nunca é preenchido com dado inventado._

| Data | Motivo |
|---|---|
| (exemplo) 2026-11-03 | job falhou, TCGCSV fora do ar |

## Observações sobre o bruto

Se algum dia for gravado em disco local e enviado ao MinIO depois, o `LastModified` do objeto será posterior à data da coleta. A data correta é a da chave (`data=`).
