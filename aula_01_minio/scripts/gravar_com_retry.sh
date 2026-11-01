#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Uso: %s <chave-do-objeto>\n' "${0##*/}" >&2
}

if [[ "$#" -ne 1 || -z "$1" ]]; then
  usage
  exit 2
fi

object_key="$1"
max_attempts="${MC_WRITE_MAX_ATTEMPTS:-3}"
if [[ ! "$max_attempts" =~ ^[1-9][0-9]*$ ]]; then
  printf 'Erro: MC_WRITE_MAX_ATTEMPTS deve ser um inteiro positivo.\n' >&2
  exit 2
fi

payload_file="$(mktemp)"
trap 'rm -f -- "$payload_file"' EXIT
cat > "$payload_file"

printf 'Limite de tentativas: %s (hipótese: validação pendente).\n' "$max_attempts"

attempt=1
delay_seconds=1
while (( attempt <= max_attempts )); do
  if output="$(mc pipe --quiet "$object_key" < "$payload_file" 2>&1)"; then
    if [[ -n "$output" ]]; then
      printf '%s\n' "$output"
    fi
    exit 0
  else
    command_status=$?
  fi

  if [[ -n "$output" ]]; then
    printf '%s\n' "$output" >&2
  fi

  if [[ "$output" != *502* ]]; then
    printf 'Erro: mc pipe falhou (código %s); resposta sem HTTP 502, não será repetida.\n' \
      "$command_status" >&2
    exit "$command_status"
  fi

  if (( attempt == max_attempts )); then
    printf 'Erro: HTTP 502; limite de %s tentativas esgotado.\n' "$max_attempts" >&2
    exit 1
  fi

  printf 'HTTP 502 na tentativa %s/%s; nova tentativa em %ss.\n' \
    "$attempt" "$max_attempts" "$delay_seconds" >&2
  sleep "$delay_seconds"
  delay_seconds=$((delay_seconds * 2))
  attempt=$((attempt + 1))
done
