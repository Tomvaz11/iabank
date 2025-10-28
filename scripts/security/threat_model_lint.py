#!/usr/bin/env python3
"""
Lint para artefatos de threat modeling.

Valida:
- Existência do arquivo esperado para o release informado.
- Presença da seção \"Mitigation Status\".
- Pelo menos uma ameaça STRIDE e uma LINDDUN documentadas.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida threat model da Fundação Frontend.")
    parser.add_argument(
        "--base-dir",
        default="docs/security/threat-models/frontend-foundation",
        help="Diretório raiz onde os artefatos estão versionados.",
    )
    parser.add_argument(
        "--release",
        default="v1.0",
        help="Release esperado (nome do arquivo Markdown sem extensão).",
    )
    return parser.parse_args()


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"Arquivo de threat model não encontrado: {path}")
        return errors

    content = path.read_text(encoding="utf-8")
    heading = content.splitlines()[0].strip() if content else ""

    if heading and path.stem not in heading:
        errors.append(
            f"O heading inicial '{heading}' não referencia o release '{path.stem}'."
        )

    if "## Mitigation Status" not in content:
        errors.append("Seção obrigatória '## Mitigation Status' ausente.")

    if "| STR-" not in content:
        errors.append("Nenhuma ameaça STRIDE documentada (esperado prefixo 'STR-').")

    if "| LIN-" not in content:
        errors.append("Nenhuma ameaça LINDDUN documentada (esperado prefixo 'LIN-').")

    return errors


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    target = base_dir / f"{args.release}.md"

    errors = validate_file(target)
    if errors:
        for error in errors:
            print(f"[threat-model-lint] {error}", file=sys.stderr)
        return 1

    print(f"[threat-model-lint] Artefato verificado com sucesso: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
