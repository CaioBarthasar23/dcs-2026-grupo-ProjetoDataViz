from __future__ import annotations

import argparse
import os
import urllib.parse
import urllib.request


FLUX_CARDINALIDADE = '''
from(bucket: "tatico")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "eventos")
  |> keep(columns: ["regiao", "academia", "tipo", "_value", "_time"])
  |> group(columns: ["regiao", "academia", "tipo"])
  |> count()
'''


def principal() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=os.environ.get("INFLUXDB_BUCKET", "tatico"))
    parser.add_argument("--url", dest="url", default=os.environ.get("INFLUXDB_URL", "http://127.0.0.1:8086"))
    parser.add_argument("--org", dest="org", default=os.environ.get("INFLUXDB_ORG", "tatame"))
    parser.add_argument("--token", dest="token", default=os.environ.get("INFLUXDB_TOKEN"))
    args = parser.parse_args()
    if not args.token:
        raise RuntimeError("INFLUXDB_TOKEN ausente")
    query = FLUX_CARDINALIDADE.replace('"tatico"', f'"{args.bucket}"')
    parametros = urllib.parse.urlencode({"org": args.org})
    request = urllib.request.Request(
        f"{args.url.rstrip('/')}/api/v2/query?{parametros}",
        data=query.encode("utf-8"),
        headers={
            "Authorization": f"Token {args.token}",
            "Content-Type": "application/vnd.flux",
            "Accept": "application/csv",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        csv = response.read().decode("utf-8")
    data_rows = [
        line for line in csv.splitlines()
        if line and not line.startswith("#") and not line.startswith("result,table")
    ]
    print(f"cardinalidade_series_aproximada={len(data_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
