#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: validate_sbom.py <caminho_sbom.json>", file=sys.stderr)
        return 2

    sbom_path = Path(sys.argv[1])
    if not sbom_path.exists():
        print(f"SBOM não encontrada em {sbom_path}.", file=sys.stderr)
        return 1

    try:
        data = json.loads(sbom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"SBOM inválida (JSON malformado): {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []

    if data.get("bomFormat") != "CycloneDX":
        errors.append("bomFormat diferente de CycloneDX.")

    spec_version = data.get("specVersion")
    if not spec_version:
        errors.append("specVersion ausente na SBOM.")

    metadata = data.get("metadata", {})
    if not metadata.get("component"):
        errors.append("metadata.component ausente na SBOM.")

    components = data.get("components", [])
    if not components:
        errors.append("Lista de componentes está vazia.")

    if errors:
        print("Falha na validação da SBOM:", file=sys.stderr)
        for issue in errors:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print(f"SBOM {sbom_path} validada com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
