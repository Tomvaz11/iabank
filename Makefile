##
## IABank — Atalhos de DX (delegam para scripts existentes)
##

.PHONY: help up down ps logs lint test test\:frontend test\:backend openapi contracts\:verify perf\:smoke sbom baseline seed-data\:lint seed-data\:dry-run seed-data\:contracts seed-data\:finops seed-data\:deps

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z0-9_.:\\-]+:.*?## ' $(MAKEFILE_LIST) \
	| sed -E 's/:.*?## /\t- /' \
	| sed -E 's/^/make /' \
	| sed -E 's/\\\:/:/g'

# Orquestração local (fonte de verdade: scripts/dev/foundation-stack.sh)
up: ## Sobe a stack local (docker ou nativa)
	./scripts/dev/foundation-stack.sh up

down: ## Derruba a stack local
	./scripts/dev/foundation-stack.sh down

ps: ## Lista status dos serviços
	./scripts/dev/foundation-stack.sh ps

logs: ## Segue logs (SERVICE=backend para um serviço específico)
	./scripts/dev/foundation-stack.sh logs $(SERVICE)

# Qualidade e testes (delegam para comandos existentes)
lint: ## Lint do frontend (ESLint + regras FSD/Zustand)
	pnpm lint

test: ## Testes (suite existente)
	pnpm test

test\:frontend: ## Testes do frontend com cobertura
	pnpm test:coverage

test\:backend: ## Testes do backend (pytest)
	poetry run pytest -q

openapi: ## Lint + diff + codegen dos contratos OpenAPI
	pnpm openapi

contracts\:verify: ## Verifica contratos (OpenAPI + Pact)
	pnpm contracts:verify

seed-data\:lint: ## Lint/diff de contratos seed_data + validação de manifestos/caps Q11
	./scripts/ci/seed-data-lint.sh

seed-data\:contracts: ## Gate de contratos seed_data (Spectral/oasdiff + stub Pact)
	./scripts/ci/validate-seed-contracts.sh

seed-data\:dry-run: ## Dry-run do comando seed_data com stub seguro e fail-close de telemetria
	./scripts/ci/seed-data-dry-run.sh

seed-data\:finops: ## Valida cost-model FinOps (schema + tetos por ambiente)
	./scripts/ci/validate-finops.sh

seed-data\:deps: ## Auditoria de dependências seeds/factories/Vault/perf (pip-audit + pnpm audit)
	./scripts/ci/deps-seed.sh

perf\:smoke: ## Teste de performance (k6) em modo local
	pnpm perf:smoke:local

sbom: ## Gera SBOM do frontend
	pnpm sbom:frontend

# -----------------------------------------------------------------------------
# Baseline pós-fase (automatiza checklist da issue #173)
# Uso:
#   make baseline TAG=v0.2.0-f11 [BRANCH=baseline/f11] [PHASE=f11] [ARTIFACTS_DIR=artifacts] [CLOBBER=0] [NOTES_FILE=artifacts/release-notes.md]
# Notas:
#   - Requer gh CLI autenticado (gh auth status) e permissão de push no origin.
#   - Idempotente: não recria tag/branch/arquivos se já existirem.
#   - CLOBBER=1 permite sobrescrever assets já existentes no Release do GitHub.
#   - NOTES_FILE (opcional) preenche as notas do Release via --notes-file (create/edit).
# -----------------------------------------------------------------------------
DATE := $(shell date +%F)
ARTIFACTS_DIR ?= artifacts
# Artefatos críticos da F-10 (padrão); pode ser sobrescrito via ARTIFACTS_PATHS="a b c"
ARTIFACTS_PATHS ?= specs/002-f-10-fundacao AGENTS.md .specify/memory/constitution.md
TAG ?=
BRANCH ?=
# PHASE (ex.: f11). Se não informado, tenta derivar de BRANCH dentro da receita.
PHASE ?=
# CLOBBER=1 para substituir assets no release
CLOBBER ?= 0

baseline: ## Cria tag (+branch opcional), bundle, tar, checksums e publica Release (TAG obrigatória)
	@bash -euo pipefail <<'BASH'
	TAG='$(TAG)'
	BRANCH='$(BRANCH)'
	PHASE='$(PHASE)'
	ARTIFACTS_DIR='$(ARTIFACTS_DIR)'
	DATE='$(DATE)'
	CLOBBER='$(CLOBBER)'
	NOTES_FILE='$(NOTES_FILE)'

	if [ -z "$TAG" ]; then
	  echo "[ERRO] Informe TAG. Ex.: make baseline TAG=v0.2.0-f11 [BRANCH=baseline/f11]" >&2
	  exit 1
	fi

	# 1) Verificações básicas
	if ! command -v gh >/dev/null 2>&1; then
	  echo "[ERRO] gh CLI não encontrado" >&2
	  exit 1
	fi
	mkdir -p "$ARTIFACTS_DIR"

	# 2) Tag anotada + push (idempotente)
	if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
	  echo "[OK] Tag já existe: $TAG"
	else
	  git tag -a "$TAG" -m "Baseline após $TAG"
	  git push origin "$TAG"
	  echo "[OK] Tag criada e publicada: $TAG"
	fi

	# 3) Branch baseline + push (opcional e idempotente)
	if [ -n "$BRANCH" ]; then
	  if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
	    echo "[OK] Branch remota já existe: $BRANCH"
	    if ! git show-ref --verify --quiet "refs/heads/$BRANCH"; then
	      git branch --track "$BRANCH" "origin/$BRANCH" 2>/dev/null || true
	    fi
	  else
	    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
	      echo "[OK] Branch local já existe: $BRANCH"
	    else
	      git branch "$BRANCH"
	      echo "[OK] Branch local criada: $BRANCH"
	    fi
	    git push -u origin "$BRANCH"
	    echo "[OK] Branch publicada: $BRANCH"
	  fi
	else
	  echo "[INFO] BRANCH não informada — pulando criação/publicação de branch."
	fi

	# 4) Descobrir PHASE (ex.: f11) se não definido
	PHASE_VAL="$PHASE"
	if [ -z "$PHASE_VAL" ] && [ -n "$BRANCH" ]; then
	  PHASE_VAL=$(printf '%s\n' "$BRANCH" | sed -n 's#.*/\(f[0-9][0-9]*\).*#\1#p')
	fi
	if [ -z "$PHASE_VAL" ]; then
	  PHASE_VAL=$(printf '%s\n' "$TAG" | sed -n 's#.*-\(f[0-9][0-9]*\).*#\1#p')
	fi
	if [ -z "$PHASE_VAL" ]; then
	  echo "[ERRO] Não foi possível derivar PHASE; informe PHASE=fXX" >&2
	  exit 1
	fi
	echo "[INFO] PHASE=$PHASE_VAL"

	BUNDLE_PATH="$ARTIFACTS_DIR/backup-$PHASE_VAL-$DATE.bundle"
	TAR_PATH="$ARTIFACTS_DIR/$PHASE_VAL-artifacts-$DATE.tar.gz"
	CHECKSUMS_PATH="$ARTIFACTS_DIR/$PHASE_VAL-checksums-$DATE.txt"

	if [ -z "$BUNDLE_PATH" ] || [ -z "$TAR_PATH" ] || [ -z "$CHECKSUMS_PATH" ]; then
	  echo "[ERRO] Caminhos de artefatos não devem ser vazios" >&2
	  exit 1
	fi

	# 5) Gerar bundle do repositório (idempotente)
	if [ -f "$BUNDLE_PATH" ]; then
	  echo "[OK] Bundle já existe: $BUNDLE_PATH"
	else
	  git bundle create "$BUNDLE_PATH" --all
	  echo "[OK] Bundle criado: $BUNDLE_PATH"
	fi

	# 6) Empacotar artefatos críticos (idempotente)
	if [ -f "$TAR_PATH" ]; then
	  echo "[OK] Tar já existe: $TAR_PATH"
	else
	  tar -czf "$TAR_PATH" $(ARTIFACTS_PATHS)
	  echo "[OK] Tar criado: $TAR_PATH"
	fi

	# 7) Checksums e tamanhos
	SHA_BUNDLE=$(sha256sum "$BUNDLE_PATH" | awk '{print $1}')
	SHA_TAR=$(sha256sum "$TAR_PATH" | awk '{print $1}')
	SIZE_BUNDLE=$(du -h "$BUNDLE_PATH" | awk '{print $1}')
	SIZE_TAR=$(du -h "$TAR_PATH" | awk '{print $1}')
	printf '%s  %s\n' "$SHA_BUNDLE" "$BUNDLE_PATH" > "$CHECKSUMS_PATH"
	printf '%s  %s\n' "$SHA_TAR" "$TAR_PATH" >> "$CHECKSUMS_PATH"
	echo "[OK] Checksums em: $CHECKSUMS_PATH"

	# 8) Release no GitHub (idempotente)
	if gh release view "$TAG" >/dev/null 2>&1; then
	  echo "[OK] Release já existe: $TAG"
	else
	  if [ -n "$NOTES_FILE" ] && [ -f "$NOTES_FILE" ]; then
	    gh release create "$TAG" --title "Baseline após $TAG" --notes-file "$NOTES_FILE"
	  else
	    gh release create "$TAG" --title "Baseline após $TAG" \
	      --notes "Marco de backup $TAG — artefatos: bundle e pacote de fase ($PHASE_VAL)."
	  fi
	  echo "[OK] Release criado: $TAG"
	fi

	# 9) Upload dos artefatos (com opção de clobber)
	CLOBBER_FLAG=""; [ "$CLOBBER" = "1" ] && CLOBBER_FLAG="--clobber"
	if ! gh release upload "$TAG" $CLOBBER_FLAG "$BUNDLE_PATH" "$TAR_PATH" "$CHECKSUMS_PATH"; then
	  echo "[AVISO] Upload pode ter falhado por arquivos já existirem. Use CLOBBER=1 para substituir."
	fi

	# 10) Atualizar notas (se arquivo fornecido) e gerar resumo final
	if [ -n "$NOTES_FILE" ] && [ -f "$NOTES_FILE" ]; then
	  gh release edit "$TAG" --notes-file "$NOTES_FILE" || true
	fi
	echo
	echo "Resumo:"
	echo "- Tag: $TAG"
	[ -n "$BRANCH" ] && echo "- Branch: $BRANCH" || true
	echo "- Bundle: $BUNDLE_PATH ($SIZE_BUNDLE) — SHA-256: $SHA_BUNDLE"
	echo "- Tar: $TAR_PATH ($SIZE_TAR) — SHA-256: $SHA_TAR"
	REL_URL=$(gh release view "$TAG" --json url --jq .url 2>/dev/null || true)
	[ -n "$REL_URL" ] && echo "- Release: $REL_URL" || true
	BASH
