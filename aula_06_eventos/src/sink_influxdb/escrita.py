from __future__ import annotations

import os
import urllib.parse
import urllib.request


class EscritorInfluxDB:
    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        org: str | None = None,
        bucket: str | None = None,
    ) -> None:
        self.url = (url or os.environ.get("INFLUXDB_URL", "http://127.0.0.1:8086")).rstrip("/")
        self.token = token or os.environ.get("INFLUXDB_TOKEN")
        self.org = org or os.environ.get("INFLUXDB_ORG", "tatame")
        self.bucket = bucket or os.environ.get("INFLUXDB_BUCKET", "tatico")
        if not self.token:
            raise RuntimeError("INFLUXDB_TOKEN ausente")

    def escrever(self, linhas: list[str]) -> None:
        if not linhas:
            return
        parametros = urllib.parse.urlencode({
            "org": self.org,
            "bucket": self.bucket,
            "precision": "ns",
        })
        requisicao = urllib.request.Request(
            f"{self.url}/api/v2/write?{parametros}",
            data="\n".join(linhas).encode("utf-8"),
            headers={
                "Authorization": f"Token {self.token}",
                "Content-Type": "text/plain",
            },
            method="POST",
        )
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            if resposta.status not in (200, 204):
                raise RuntimeError(f"InfluxDB retornou HTTP {resposta.status}")
