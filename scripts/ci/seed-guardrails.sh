#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EXIT_CODE=0

echo "[seed-data] Guardrail anti-snapshot/dump de produção."

# 1) Bloqueia manifestos apontando para ambiente de produção.
if [ -d "$ROOT_DIR/configs/seed_profiles" ]; then
  if rg --files-with-matches --glob '*.yml' --glob '*.yaml' 'environment:\s*prod' "$ROOT_DIR/configs/seed_profiles" >/tmp/seed_guardrails_prod_env 2>/dev/null; then
    echo "✗ Encontrado manifesto com environment=prod (proibido para seeds):"
    cat /tmp/seed_guardrails_prod_env
    EXIT_CODE=1
  fi
fi

# 2) Detecta comandos de dump/snapshot em scripts/código (fail-close).
if rg --files-with-matches --glob '!scripts/ci/seed-guardrails.sh' '(pg_dump|mysqldump|mongodump|mongoexport)' "$ROOT_DIR/scripts" "$ROOT_DIR/backend" >/tmp/seed_guardrails_dump_refs 2>/dev/null; then
  echo "✗ Referências a ferramentas de dump encontradas (remova ou isole em mocks):"
  cat /tmp/seed_guardrails_dump_refs
  EXIT_CODE=1
fi

# 3) Impede que dumps SQL/binários sejam cometidos em artifacts/ ou specs.
if find "$ROOT_DIR/artifacts" "$ROOT_DIR/specs" -type f \( -name '*.sql' -o -name '*.dump' -o -name '*.bak' \) 2>/dev/null | grep -E '.' >/tmp/seed_guardrails_dump_files; then
  echo "✗ Arquivos potencialmente sensíveis (.sql/.dump/.bak) detectados em artifacts/specs:"
  cat /tmp/seed_guardrails_dump_files
  EXIT_CODE=1
fi

if [ "$EXIT_CODE" -ne 0 ]; then
  echo "Guardrail reprovado: snapshots/dumps de produção são proibidos para seeds/factories."
  exit "$EXIT_CODE"
fi

echo "[seed-data] Guardrail aprovado (nenhum snapshot/dump suspeito encontrado)."
