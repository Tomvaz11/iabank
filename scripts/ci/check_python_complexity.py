#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

THRESHOLD = 10
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_FILE = PROJECT_ROOT / 'scripts' / 'ci' / 'complexity_allowlist.json'


def main() -> int:
    if shutil.which('radon') is None:
        print("radon não encontrado. Instale com 'poetry install --with dev'.", file=sys.stderr)
        return 1

    cmd = ['radon', 'cc', 'backend', '-s', '-j', '--exclude', '*/tests/*']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode not in (0, 1):
        print(result.stderr, file=sys.stderr)
        return result.returncode or 1

    try:
        payload = json.loads(result.stdout or '{}')
    except json.JSONDecodeError as exc:
        print(f'Falha ao interpretar saída do radon: {exc}', file=sys.stderr)
        return 1

    allowlist = _load_allowlist()
    violations: list[tuple[Path, int, str | None, str, int]] = []
    for filename, entries in payload.items():
        for entry in entries:
            complexity = int(entry.get('complexity', 0))
            if complexity <= THRESHOLD:
                continue
            rel_path = _normalize_path(filename)
            name = entry.get('name', '<desconhecido>')
            classname = entry.get('classname')
            key = (rel_path, classname, name)
            allowed_max = allowlist.get(key)
            if allowed_max is not None and complexity <= allowed_max:
                continue
            lineno = int(entry.get('lineno', 0))
            violations.append((rel_path, lineno, classname, name, complexity))

    if violations:
        print('Complexidade ciclomática acima do limite (10) detectada:')
        for rel_path, lineno, classname, name, complexity in sorted(violations):
            target = f'{classname}.{name}' if classname else name
            print(f'- {rel_path}:{lineno} {target} (cc={complexity})')
        return 1

    print('Complexidade ciclomática dentro do limite (<=10).')
    return 0


def _normalize_path(filename: str) -> Path:
    path = Path(filename)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path.relative_to(PROJECT_ROOT)


def _load_allowlist() -> dict[tuple[Path, str | None, str], int]:
    if not ALLOWLIST_FILE.exists():
        return {}
    try:
        raw = json.loads(ALLOWLIST_FILE.read_text())
    except json.JSONDecodeError as exc:
        print(f'Falha ao ler allowlist de complexidade: {exc}', file=sys.stderr)
        return {}

    entries: dict[tuple[Path, str | None, str], int] = {}
    for item in raw:
        try:
            path = _normalize_path(item['path'])
            name = item['name']
            classname = item.get('classname')
            max_complexity = int(item.get('max_complexity', THRESHOLD))
        except (KeyError, TypeError, ValueError):
            continue
        entries[(path, classname, name)] = max_complexity
    return entries


if __name__ == '__main__':
    sys.exit(main())

