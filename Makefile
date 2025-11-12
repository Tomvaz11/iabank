##
## IABank — Atalhos de DX (delegam para scripts existentes)
##

.PHONY: help up down ps logs lint test test\:frontend test\:backend openapi contracts\:verify perf\:smoke sbom

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

perf\:smoke: ## Teste de performance (k6) em modo local
	pnpm perf:smoke:local

sbom: ## Gera SBOM do frontend
	pnpm sbom:frontend
