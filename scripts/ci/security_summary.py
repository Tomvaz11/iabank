#!/usr/bin/env python
from __future__ import annotations

import os
import sys


def _icon(status: str) -> str:
    status_lower = status.lower()
    if status_lower == "success":
        return "✅"
    if status_lower == "skipped":
        return "⚪"
    if status_lower == "cancelled":
        return "⏹️"
    return "❌"


def main() -> int:
    summary_rows = [
        ("Semgrep (SAST)", os.environ.get("SAST", "skipped")),
        ("OWASP ZAP (DAST)", os.environ.get("DAST", "skipped")),
        ("pgcrypto validation", os.environ.get("PGCRYPTO", "skipped")),
        ("pip-audit", os.environ.get("PIP_AUDIT", "skipped")),
        ("Safety", os.environ.get("SAFETY", "skipped")),
        ("pnpm audit", os.environ.get("PNPM_AUDIT", "skipped")),
        ("SBOM generate", os.environ.get("SBOM_GENERATE", "skipped")),
        ("SBOM validate", os.environ.get("SBOM_VALIDATE", "skipped")),
    ]

    lines = ["| Check | Status |", "|-------|--------|"]
    failures: list[str] = []

    for name, status in summary_rows:
        icon = _icon(status)
        lines.append(f"| {name} | {icon} {status} |")
        if status.lower() not in {"success", "skipped"}:
            failures.append(name)

    summary_output = ["### Resumo dos checks de segurança", *lines]
    if failures:
        summary_output.append("")
        summary_output.append("Checks com falha: " + ", ".join(failures))

    summary_text = "\n".join(summary_output) + "\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handler:
            handler.write(summary_text)
    else:
        print(summary_text)

    require_fail_closed = os.environ.get("CI_ENFORCE_FULL_SECURITY", "").lower() == "true"

    if failures:
        if require_fail_closed:
            print("Falhas de segurança detectadas em modo fail-closed:", ", ".join(failures))
            return 1
        print("Falhas de segurança detectadas (modo fail-open). Consulte o resumo para detalhes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

