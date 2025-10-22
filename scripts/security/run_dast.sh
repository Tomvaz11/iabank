#!/usr/bin/env bash
set -euo pipefail

# Placeholder DAST hook: em ambientes completos, integrar OWASP ZAP.
# Por enquanto, executa testes de segurança que validam mascaramento de PII.
source .venv/bin/activate 2>/dev/null || true
pytest tests/security/test_log_redaction.py
