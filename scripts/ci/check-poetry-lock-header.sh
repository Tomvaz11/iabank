#!/usr/bin/env bash
set -euo pipefail

if [ ! -f "poetry.lock" ]; then
  echo "poetry.lock não encontrado; nada a verificar."
  exit 0
fi

header=$(head -n1 poetry.lock || true)
if echo "$header" | grep -Eq 'Poetry 2\.'; then
  echo "poetry.lock gerado por Poetry 2.x — padronize para Poetry 1.8.3 (execute: poetry lock --no-update com Poetry 1.8.3)." >&2
  exit 1
fi

echo "Header do poetry.lock OK: ${header}"
exit 0

