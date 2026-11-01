#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
retry_script="${project_root}/scripts/gravar_com_retry.sh"
temp_dir="$(mktemp -d)"
trap 'rm -rf -- "$temp_dir"' EXIT

fake_bin="${temp_dir}/bin"
mkdir -p "$fake_bin"

cat > "${fake_bin}/mc" <<'FAKE_MC'
#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 3 || "$1" != "pipe" || "$2" != "--quiet" ]]; then
  printf 'mc simulado recebeu argumentos inesperados.\n' >&2
  exit 2
fi

object_key="$3"
count_file="${FAKE_STATE_DIR}/attempts"
attempt=0
if [[ -f "$count_file" ]]; then
  read -r attempt < "$count_file"
fi
attempt=$((attempt + 1))
printf '%s\n' "$attempt" > "$count_file"
printf '%s\n' "$object_key" >> "${FAKE_STATE_DIR}/keys"

object_path="${FAKE_STATE_DIR}/objects/${object_key#*/}"
mkdir -p "$(dirname -- "$object_path")"
cat > "$object_path"

if [[ "$FAKE_MODE" == "retry_then_success" && "$attempt" -le 2 ]] ||
  [[ "$FAKE_MODE" == "always_502" ]]; then
  printf 'mc simulado: HTTP 502 após aceitar a gravação.\n' >&2
  exit 1
fi

byte_count="$(wc -c < "$object_path" | tr -d '[:space:]')"
printf '%s bytes -> %s\n' "$byte_count" "$object_key"
FAKE_MC

cat > "${fake_bin}/sleep" <<'FAKE_SLEEP'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$1" >> "${FAKE_STATE_DIR}/delays"
printf 'Espera simulada: %ss\n' "$1"
FAKE_SLEEP

chmod +x "${fake_bin}/mc" "${fake_bin}/sleep"

expected_key='local/raw/_verificacao/teste.json'
expected_content='conteudo-esperado-t08'

assert_equals() {
  local expected="$1"
  local actual="$2"
  local description="$3"
  if [[ "$actual" != "$expected" ]]; then
    printf 'Falha: %s (esperado: %s; obtido: %s)\n' \
      "$description" "$expected" "$actual" >&2
    exit 1
  fi
}

printf 'Caso 1: falhas HTTP 502 e retry idempotente até sucesso\n'
success_state="${temp_dir}/success"
mkdir -p "$success_state"
success_output="$(
  printf '%s' "$expected_content" |
    PATH="${fake_bin}:${PATH}" \
      FAKE_STATE_DIR="$success_state" \
      FAKE_MODE=retry_then_success \
      MC_WRITE_MAX_ATTEMPTS=3 \
      bash "$retry_script" "$expected_key" 2>&1
)"
printf '%s\n' "$success_output"

assert_equals '3' "$(cat "${success_state}/attempts")" 'número de tentativas'
printf '%s\n' "$expected_key" "$expected_key" "$expected_key" > "${temp_dir}/expected-keys"
cmp -s "${temp_dir}/expected-keys" "${success_state}/keys" ||
  { printf 'Falha: as tentativas não reutilizaram a mesma chave.\n' >&2; exit 1; }
printf '1\n2\n' > "${temp_dir}/expected-delays"
cmp -s "${temp_dir}/expected-delays" "${success_state}/delays" ||
  { printf 'Falha: as esperas não cresceram de 1s para 2s.\n' >&2; exit 1; }
object_path="${success_state}/objects/raw/_verificacao/teste.json"
assert_equals "$expected_content" "$(cat "$object_path")" 'conteúdo do objeto'
assert_equals '1' "$(find "${success_state}/objects" -type f | wc -l | tr -d '[:space:]')" \
  'quantidade de objetos finais'
printf 'Confirmado: 3 tentativas na mesma chave, esperas 1s e 2s, 1 objeto final com conteúdo esperado.\n'

printf '\nCaso 2: esgotamento do limite\n'
exhausted_state="${temp_dir}/exhausted"
mkdir -p "$exhausted_state"
if exhausted_output="$(
  printf '%s' "$expected_content" |
    PATH="${fake_bin}:${PATH}" \
      FAKE_STATE_DIR="$exhausted_state" \
      FAKE_MODE=always_502 \
      MC_WRITE_MAX_ATTEMPTS=2 \
      bash "$retry_script" "$expected_key" 2>&1
)"; then
  exhausted_status=0
else
  exhausted_status=$?
fi
printf '%s\n' "$exhausted_output"
assert_equals '1' "$exhausted_status" 'código ao esgotar tentativas'
assert_equals '2' "$(cat "${exhausted_state}/attempts")" \
  'tentativas antes de encerrar'
printf 'Confirmado: saída não zero após 2 tentativas, sem ultrapassar o limite.\n'

printf '\nResultado: T-08 aprovado.\n'
