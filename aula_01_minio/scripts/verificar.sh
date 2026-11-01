#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Uso: %s {local|railway}\n' "${0##*/}" >&2
}

if [[ "$#" -ne 1 ]]; then
  usage
  exit 2
fi

target="$1"
case "$target" in
  local|railway)
    ;;
  *)
    usage
    exit 2
    ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
cd "$project_root"

evidence_file="docs/evidencias/verificar_${target}.txt"
if [[ "${_VERIFICAR_SCRIPT_INTERNO:-}" != "1" ]]; then
  set +e
  _VERIFICAR_SCRIPT_INTERNO=1 bash "$0" "$target" 2>&1 | tee "$evidence_file"
  pipeline_status=("${PIPESTATUS[@]}")
  if [[ "${pipeline_status[1]}" -ne 0 ]]; then
    printf 'Erro: não foi possível gravar a evidência em %s.\n' "$evidence_file" >&2
    exit 1
  fi
  exit "${pipeline_status[0]}"
fi

if [[ ! -f .env ]]; then
  printf 'Erro: arquivo .env não encontrado na raiz do projeto.\n' >&2
  exit 1
fi

set -a
. ./.env
set +a

for command_name in curl mc; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Erro: o comando %s não está instalado ou não está no PATH.\n' "$command_name" >&2
    exit 1
  fi
done

case "$target" in
  local)
    : "${MINIO_ROOT_USER:?MINIO_ROOT_USER não definido no .env}"
    : "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD não definido no .env}"
    endpoint="http://127.0.0.1:9000"
    username="$MINIO_ROOT_USER"
    password="$MINIO_ROOT_PASSWORD"
    ;;
  railway)
    : "${MINIO_RAILWAY_ENDPOINT:?MINIO_RAILWAY_ENDPOINT não definido no .env}"
    : "${MINIO_RAILWAY_USER:?MINIO_RAILWAY_USER não definido no .env}"
    : "${MINIO_RAILWAY_PASSWORD:?MINIO_RAILWAY_PASSWORD não definido no .env}"
    endpoint="${MINIO_RAILWAY_ENDPOINT%/}"
    username="$MINIO_RAILWAY_USER"
    password="$MINIO_RAILWAY_PASSWORD"
    ;;
esac

printf 'Verificando destino: %s\n' "$target"

health_status="$(
  curl --location --silent --show-error --max-time 10 \
    --output /dev/null --write-out '%{http_code}' \
    "${endpoint}/minio/health/live"
)"
printf 'Saúde HTTP: %s\n' "$health_status"
if [[ "$health_status" != "200" ]]; then
  printf 'Erro: endpoint de saúde retornou HTTP %s; esperado 200.\n' "$health_status" >&2
  exit 1
fi

anonymous_status="$(
  curl --location --silent --show-error --max-time 10 \
    --output /dev/null --write-out '%{http_code}' \
    "$endpoint/"
)"
printf 'Acesso anônimo HTTP: %s\n' "$anonymous_status"
if [[ "$anonymous_status" != "403" ]]; then
  printf 'Erro: acesso anônimo retornou HTTP %s; esperado 403.\n' "$anonymous_status" >&2
  exit 1
fi

mc alias set "$target" "$endpoint" "$username" "$password" >/dev/null

bucket_listing="$(mc ls "$target")"
printf 'Buckets listados por mc ls %s:\n%s\n' "$target" "$bucket_listing"
actual_buckets="$(
  printf '%s\n' "$bucket_listing" |
    awk 'NF { sub(/\/$/, "", $NF); print $NF }' |
    sort
)"
expected_buckets="$(printf '%s\n' bronze gold raw silver | sort)"
if [[ "$actual_buckets" != "$expected_buckets" ]]; then
  printf 'Erro: listagem de buckets diferente do esperado.\n' >&2
  exit 1
fi

object_key="${target}/raw/_verificacao/teste.json"
expected_content='{"verificacao":"T-04"}'
printf '%s\n' "$expected_content" | mc pipe --quiet "$object_key"
actual_content="$(mc cat "$object_key")"
if [[ "$actual_content" != "$expected_content" ]]; then
  printf 'Erro: o conteúdo lido não corresponde ao conteúdo gravado.\n' >&2
  exit 1
fi
printf 'Gravação e leitura: conteúdo confirmado em %s\n' "$object_key"
printf 'Resultado: T-04 aprovado para %s.\n' "$target"
