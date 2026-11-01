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

if [[ ! -f .env ]]; then
  printf 'Erro: arquivo .env não encontrado na raiz do projeto.\n' >&2
  exit 1
fi

set -a
. ./.env
set +a

if ! command -v mc >/dev/null 2>&1; then
  printf 'Erro: o cliente mc não está instalado ou não está no PATH.\n' >&2
  exit 1
fi

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
    endpoint="$MINIO_RAILWAY_ENDPOINT"
    username="$MINIO_RAILWAY_USER"
    password="$MINIO_RAILWAY_PASSWORD"
    ;;
esac

mc alias set "$target" "$endpoint" "$username" "$password" >/dev/null

for bucket in raw bronze silver gold; do
  mc mb --ignore-existing "${target}/${bucket}"
done