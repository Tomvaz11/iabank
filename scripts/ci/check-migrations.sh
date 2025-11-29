#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_PATH="$ROOT_DIR"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      TARGET_PATH="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

if [ ! -d "$TARGET_PATH" ]; then
  echo "[migrations] Caminho invalido: $TARGET_PATH" >&2
  exit 1
fi

python3 - "$TARGET_PATH" <<'PY'
import re
import sys
from pathlib import Path

base_path = Path(sys.argv[1]).resolve()
migration_files = sorted(base_path.glob("**/migrations/*.py"))

failures: list[str] = []
concurrent_re = re.compile(r"CONCURRENTLY", flags=re.IGNORECASE)
destructive_re = re.compile(r"DROP TABLE|DROP COLUMN", flags=re.IGNORECASE)

for path in migration_files:
    if path.name == "__init__.py":
        continue
    text = path.read_text()

    if concurrent_re.search(text) and "atomic = False" not in text:
        failures.append(f"{path}: uso de CONCURRENTLY sem atomic = False (necessario para expand/contract)")

    if destructive_re.search(text):
        failures.append(
            f"{path}: operacao destrutiva detectada (use expand/contract ou migre com reversao segura)",
        )

if failures:
    print("[migrations] Falhas encontradas:")
    for item in failures:
        print(f"- {item}")
    sys.exit(1)

print(f"[migrations] OK: {len(migration_files)} arquivos verificados em {base_path}")
PY
