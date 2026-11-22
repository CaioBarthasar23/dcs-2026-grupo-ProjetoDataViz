// A: eventos por minuto por região, últimos 60 minutos.
from(bucket: "tatico")
  |> range(start: -60m)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> filter(fn: (r) => r._field == "contagem")
  |> group(columns: ["_time", "regiao"])
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)

// B: dispositivos vivos por região, proxy por academias com heartbeat recente.
from(bucket: "tatico")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> filter(fn: (r) => r.tipo == "heartbeat")
  |> filter(fn: (r) => r._field == "contagem")
  |> group(columns: ["academia", "regiao"])
  |> sum()
  |> group(columns: ["regiao"])
  |> count(column: "contagem")

// C: check-ins por academia na última hora, região parametrizável.
regiao_painel = "eu-estocolmo"

from(bucket: "tatico")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> filter(fn: (r) => r.regiao == regiao_painel)
  |> filter(fn: (r) => r.tipo == "checkin")
  |> filter(fn: (r) => r._field == "contagem")
  |> group(columns: ["academia"])
  |> sum()

// Cardinalidade aproximada pelas combinações distintas de tags.
from(bucket: "tatico")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> keep(columns: ["regiao", "academia", "tipo"])
  |> group(columns: ["regiao", "academia", "tipo"])
  |> distinct(column: "regiao")
  |> count()
