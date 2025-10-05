#!/usr/bin/env python3
"""Validate structlog JSON entries for sensitive data redaction.

Usage:
    python scripts/observability/check_structlog.py <logfile> [<logfile> ...]

The script reads line-delimited JSON logs and raises an error if any of the
sensitive keys (default: CPF, CNPJ, email, document, token, password) appear
without being redacted. Values are considered redacted when they match one of
MASK_PATTERNS.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List

SENSITIVE_KEYS: List[str] = [
    "cpf",
    "cnpj",
    "email",
    "document",
    "token",
    "password",
    "access_token",
    "refresh_token",
]

MASK_PATTERNS = (
    re.compile(r"^\*{3,}$"),
    re.compile(r"^\[REDACTED\]$", re.IGNORECASE),
    re.compile(r"^redacted:?", re.IGNORECASE),
)


class RedactionError(ValueError):
    """Raised when a sensitive field is not properly redacted."""


def _is_masked(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    return any(pattern.match(value) for pattern in MASK_PATTERNS)


def validate_entry(entry: dict, sensitive_keys: Iterable[str] = SENSITIVE_KEYS) -> None:
    """Validate a single log entry.

    Args:
        entry: Parsed JSON object representing a structlog entry.
        sensitive_keys: Keys that must be redacted.

    Raises:
        RedactionError: When a sensitive key appears without masking.
    """

    for key in sensitive_keys:
        if key not in entry:
            continue
        value = entry[key]
        if not _is_masked(value):
            raise RedactionError(f"Key '{key}' is not redacted (value={value!r})")


def scan_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RedactionError(
                    f"Invalid JSON on line {line_number} of {path}: {exc}"
                ) from exc
            validate_entry(entry)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate structlog redaction")
    parser.add_argument("paths", nargs="+", help="Log files to validate")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    errors: List[str] = []
    for item in args.paths:
        path = Path(item)
        if not path.exists():
            errors.append(f"Path not found: {path}")
            continue
        try:
            scan_file(path)
        except RedactionError as exc:
            errors.append(str(exc))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("✓ Structlog redaction validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
