$ docker compose config --quiet
exit status: 0

$ bash scripts/criar_buckets.sh local
Bucket created successfully `local/raw`.
Bucket created successfully `local/bronze`.
Bucket created successfully `local/silver`.
Bucket created successfully `local/gold`.
exit status: 0

$ bash scripts/verificar.sh local
Verificando destino: local
Saúde HTTP: 200
Acesso anônimo HTTP: 403
Buckets listados por mc ls local:
[2026-10-31 23:58:02 UTC]     0B bronze/
[2026-10-31 23:58:02 UTC]     0B gold/
[2026-10-31 23:58:02 UTC]     0B raw/
[2026-10-31 23:58:02 UTC]     0B silver/
23 bytes -> `local/raw/_verificacao/teste.json`
Gravação e leitura: conteúdo confirmado em local/raw/_verificacao/teste.json
Resultado: T-04 aprovado para local.
exit status: 0
