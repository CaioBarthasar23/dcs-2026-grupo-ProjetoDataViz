# Consultas do painel tatico

Todas usam Flux, bucket `tatico`, measurement `eventos`.

## A - Eventos por minuto por região

```flux
from(bucket: "tatico")
  |> range(start: -60m)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> filter(fn: (r) => r._field == "contagem")
  |> group(columns: ["_time", "regiao"])
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)
```

Exemplo:

```text
_time=2026-11-14T11:02:00Z regiao=eu-estocolmo contagem=18
_time=2026-11-14T11:02:00Z regiao=sa-saopaulo contagem=24
```

## B - Dispositivos vivos por região

Proxy por academias com heartbeat no intervalo recente:

```flux
from(bucket: "tatico")
  |> range(start: -5m)
  |> filter(fn: (r) => r.tipo == "heartbeat")
  |> filter(fn: (r) => r._field == "contagem")
  |> group(columns: ["academia", "regiao"])
  |> sum()
  |> group(columns: ["regiao"])
  |> count(column: "contagem")
```

Exemplo:

```text
regiao=eu-estocolmo academias_vivas=8
regiao=sa-saopaulo academias_vivas=31
```

## C - Check-ins por academia na última hora

```flux
regiao_painel = "eu-estocolmo"

from(bucket: "tatico")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> filter(fn: (r) => r.regiao == regiao_painel)
  |> filter(fn: (r) => r.tipo == "checkin")
  |> filter(fn: (r) => r._field == "contagem")
  |> group(columns: ["academia"])
  |> sum()
```

Exemplo:

```text
academia=SE-STO-014 checkins=42
academia=SE-STO-013 checkins=35
```
