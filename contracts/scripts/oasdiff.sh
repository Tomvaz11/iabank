#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DEFAULT_BASELINE="$ROOT_DIR/contracts/api.previous.yaml"
BASELINE_SOURCE="default"
CLI_BASELINE=""

print_usage() {
  cat <<EOF
Uso: $(basename "$0") [--baseline PATH] [BASELINE] [ATUAL]

Ordem de precedência do baseline:
  1) --baseline PATH
  2) variável de ambiente OPENAPI_BASELINE
  3) caminho padrão ($DEFAULT_BASELINE)

Argumentos posicionais (compatibilidade):
  BASELINE  Caminho do contrato baseline (sobreposto por --baseline/env)
  ATUAL     Caminho do contrato atual (default: contracts/api.yaml)
EOF
}

# Parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--baseline)
      if [[ $# -lt 2 ]]; then
        echo "--baseline requer um caminho" >&2
        exit 1
      fi
      CLI_BASELINE="$2"; BASELINE_SOURCE="cli"; shift 2 ;;
    -h|--help)
      print_usage; exit 0 ;;
    --)
      shift; break ;;
    -*)
      echo "Flag desconhecida: $1" >&2; print_usage; exit 1 ;;
    *)
      break ;;
  esac
done

# Posicionais (opcionais)
POS_BASELINE="${1:-}"
POS_CURRENT="${2:-}"

CURR_SPEC="${POS_CURRENT:-$ROOT_DIR/contracts/api.yaml}"

# Resolver baseline conforme precedência
if [[ -n "$CLI_BASELINE" ]]; then
  PREV_SPEC="$CLI_BASELINE"
elif [[ -n "${OPENAPI_BASELINE:-}" ]]; then
  PREV_SPEC="$OPENAPI_BASELINE"; BASELINE_SOURCE="env"
elif [[ -n "$POS_BASELINE" ]]; then
  PREV_SPEC="$POS_BASELINE"; BASELINE_SOURCE="positional"
else
  PREV_SPEC="$DEFAULT_BASELINE"; BASELINE_SOURCE="default"
fi

if [[ ! -f "$PREV_SPEC" ]]; then
  echo "Arquivo de baseline inexistente: $PREV_SPEC" >&2
  exit 2
fi

if [[ ! -f "$CURR_SPEC" ]]; then
  echo "Arquivo de contrato atual inexistente: $CURR_SPEC" >&2
  exit 2
fi

if ! command -v oasdiff >/dev/null 2>&1; then
  echo "oasdiff não encontrado no PATH. Instale via Go: 'go install github.com/oasdiff/oasdiff/cmd/oasdiff@v1.11.7' (ou use o CI)." >&2
  exit 3
fi

echo "Baseline selecionado ($BASELINE_SOURCE): $PREV_SPEC"
echo "Comparando contratos (breaking): $PREV_SPEC -> $CURR_SPEC"
oasdiff breaking "$PREV_SPEC" "$CURR_SPEC"
