#!/usr/bin/env bash
set -euo pipefail

if ! command -v bandit >/dev/null 2>&1; then
  echo "bandit não encontrado. Instale com 'pip install bandit'." >&2
  exit 1
fi

bandit -q -r backend
