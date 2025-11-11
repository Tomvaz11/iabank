#!/usr/bin/env bash
set -euo pipefail

# Validação prática do Lote 3 (issues #137 e #133)
# - Cria branches de teste e PRs para exercitar gates por paths
# - Observa execuções do workflow "Frontend Foundation CI"

WF_FILE=".github/workflows/frontend-foundation.yml"
WF_NAME="Frontend Foundation CI"
BASE_BRANCH="${1:-main}"

echo "[info] Branch base: ${BASE_BRANCH}"

if ! command -v gh >/dev/null 2>&1; then
  echo "[erro] gh CLI não encontrado. Instale o GitHub CLI (gh)." >&2
  exit 1
fi

echo "[info] Verificando autenticação do gh..."
if ! gh auth status -t >/dev/null 2>&1; then
  echo "[erro] gh sem autenticação. Execute: gh auth login" >&2
  exit 1
fi

echo "[info] Verificando acesso ao repositório remoto..."
gh repo view >/dev/null

current_branch="$(git rev-parse --abbrev-ref HEAD)"
echo "[info] Branch atual: ${current_branch}"

# Garante que o workflow com as alterações do Lote 3 está commitado e no remoto
if ! git diff --quiet -- "$WF_FILE"; then
  echo "[info] Alterações locais no workflow detectadas; criando branch para publicar..."
  ci_branch="feature/lote-3-ci"
  if git show-ref --verify --quiet "refs/heads/${ci_branch}"; then
    git switch "${ci_branch}"
  else
    git switch -c "${ci_branch}"
  fi
  git add "$WF_FILE"
  git commit -m "ci(workflow): Lote 3 — separar testes FE/BE e Pact/contracts gates (#137 #133)" || true
  git push -u origin "${ci_branch}" || true
  base_for_tests="${ci_branch}"
else
  base_for_tests="${current_branch}"
fi

echo "[info] Base para branches de validação: ${base_for_tests}"

function create_validation_branch() {
  local branch="$1"; shift
  local touch_path="$1"; shift
  local title="$1"; shift
  local commit_msg="$1"; shift

  echo "[info] Criando branch ${branch} a partir de ${base_for_tests}"
  git switch "${base_for_tests}"
  if git show-ref --verify --quiet "refs/heads/${branch}"; then
    git branch -D "${branch}" || true
  fi
  git switch -c "${branch}"

  mkdir -p "$(dirname "${touch_path}")"
  date -Iseconds > "${touch_path}"
  git add "${touch_path}"
  git commit -m "${commit_msg}"
  git push -u origin "${branch}" || true

  echo "[info] Abrindo PR draft: ${title}"
  gh pr create --base "${BASE_BRANCH}" --head "${branch}" --title "${title}" --body "${title}" --draft || true

  echo "[info] Aguardando execução do workflow (${WF_NAME}) para ${branch}"
  gh run watch --branch "${branch}" --workflow "${WF_NAME}" --interval 5 || true
  gh run list --branch "${branch}" --workflow "${WF_NAME}" --limit 1
}

# 1) FE-only (espera rodar test-frontend e Pact; sem Spectral/OpenAPI diff; backend não roda)
create_validation_branch "feature/l3-validate-fe" "frontend/.ci-validate.txt" "Lote 3: validação FE-only" "test(frontend): Lote 3 validação FE-only"

# 2) BE-only (espera rodar test-backend; frontend não roda; contracts não roda passos Node/Pact)
create_validation_branch "feature/l3-validate-be" "backend/.ci-validate.txt" "Lote 3: validação BE-only" "test(backend): Lote 3 validação BE-only"

# 3) Contracts-only (espera rodar Spectral/OpenAPI diff e Pact; FE/BE não rodam)
create_validation_branch "feature/l3-validate-contracts" "contracts/.ci-validate.txt" "Lote 3: validação Contracts-only" "test(contracts): Lote 3 validação Contracts-only"

echo "[info] Resumo final das últimas execuções por branch:"
for b in feature/l3-validate-fe feature/l3-validate-be feature/l3-validate-contracts; do
  run_id="$(gh run list --branch "$b" --workflow "$WF_NAME" --json databaseId -q '.[0].databaseId' || true)"
  echo "- Branch $b (run_id=$run_id)"
  if [ -n "$run_id" ]; then
    gh run view "$run_id" --json jobs -q '.jobs[] | {name: .name, conclusion: .conclusion}' || true
  fi
done

echo "[ok] Validação Lote 3 finalizada. Verifique conclusões dos jobs conforme esperado."
