#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: check_pgcrypto.sh [OPTIONS] <path>

Scans migrations or SQL assets for pgcrypto usage and field-level encryption helpers.

Options:
  --patterns <comma-separated>  Extra patterns to search for (default: pgcrypto,pgp_sym_encrypt,EncryptedField)
  --require-extension           Fail when CREATE EXTENSION pgcrypto is not found
  -h, --help                    Show this help message

Examples:
  check_pgcrypto.sh backend/
  check_pgcrypto.sh --require-extension infrastructure/sql
USAGE
}

extra_patterns=""
require_extension=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --patterns)
      extra_patterns="$2"
      shift 2
      ;;
    --require-extension)
      require_extension=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -* )
      echo "Unknown option $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      target="$1"
      shift
      break
      ;;
  esac
done

if [[ -z "${target:-}" ]]; then
  echo "ERROR: target path not provided" >&2
  usage >&2
  exit 1
fi

if [[ ! -d "$target" ]]; then
  echo "ERROR: '$target' is not a directory" >&2
  exit 1
fi

patterns=("pgcrypto" "pgp_sym_encrypt" "pgp_pub_encrypt" "EncryptedField")
IFS=',' read -r -a extras <<<"$extra_patterns"
for item in "${extras[@]}"; do
  [[ -n "$item" ]] && patterns+=("$item")
done

found_any=false

search_tool="grep"
if command -v rg >/dev/null 2>&1; then
  search_tool="rg"
fi

for pattern in "${patterns[@]}"; do
  if [[ "$search_tool" == "rg" ]]; then
    matches=$(rg --color=never -n "$pattern" "$target" || true)
  else
    matches=$(grep -RIn "$pattern" "$target" || true)
  fi
  if [[ -n "$matches" ]]; then
    found_any=true
    echo "✓ Pattern '$pattern' found in:"
    printf '%s\n' "$matches"
  else
    echo "⚠ Pattern '$pattern' not found"
  fi
done

if ! $found_any; then
  echo "ERROR: No pgcrypto-related patterns detected under '$target'" >&2
  exit 1
fi

if $require_extension; then
  if [[ "$search_tool" == "rg" ]]; then
    ext_matches=$(rg --color=never -n "CREATE\s+EXTENSION\s+IF\s+NOT\s+EXISTS\s+pgcrypto" "$target" || true)
  else
    ext_matches=$(grep -RIn "CREATE\s\+EXTENSION\s\+IF\s\+NOT\s\+EXISTS\s\+pgcrypto" "$target" || true)
  fi
  if [[ -z "$ext_matches" ]]; then
    echo "ERROR: pgcrypto extension declaration not found" >&2
    exit 1
  fi
  echo "✓ pgcrypto extension declaration present"
fi

exit 0
