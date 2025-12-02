#!/usr/bin/env bash
set -euo pipefail

# Uso: verify-commit-msg.sh <path-to-commit-msg-file>
# Valida o título (primeira linha) segundo Conventional Commits.

msg_file=${1:-}
if [[ -z "${msg_file}" || ! -f "${msg_file}" ]]; then
  echo "[commit-msg] Arquivo de mensagem inválido: ${msg_file:-<vazio>}" >&2
  exit 1
fi

title=$(head -n1 "$msg_file" | tr -d '\r')

# Permitir commits de merge padrão do Git
if [[ "$title" =~ ^Merge\  ]]; then
  exit 0
fi

# Padrão: type[optional scope][!]: subject
# Types: build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test
regex='^((build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([A-Za-z0-9._/\-]+\))?!?: .+)$'

if [[ ! "$title" =~ $regex ]]; then
  cat >&2 <<'EOF'
[commit-msg] Mensagem fora do padrão Conventional Commits.
Esperado: type(scope?): descrição
Exemplos válidos:
  - feat: listar contas por tenant
  - fix(api): corrige validação de CPF
  - chore(release): 0.2.0
Tipos suportados: build, chore, ci, docs, feat, fix, perf, refactor, revert, style, test
EOF
  echo "Título lido: '$title'" >&2
  exit 1
fi

exit 0
