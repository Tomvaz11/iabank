# Runbook — Renovate Config Validation

Objetivo: validar a configuração do Renovate (`renovate.json`) no CI usando o validador oficial com regras estritas.

## Workflow
- Arquivo: `.github/workflows/renovate-validation.yml`.
- Disparo: `workflow_dispatch`, `push` (branch `main`) e `pull_request` quando `renovate.json` muda.
- Ambiente: Node `22.13.0` (necessário porque `renovate@latest` requer Node ≥ 22.13).

## Passos principais
1. Checkout do repositório.
2. Setup Node 22.13.0 (`actions/setup-node@v4`).
3. Validação: `npx --yes -p renovate@latest renovate-config-validator --strict renovate.json`.
4. Verificação adicional: garante que `assignees` estejam configurados e válidos.

## Sintomas comuns e correções
- EBADENGINE (Unsupported engine): usar Node 22.13.x no job (já configurado no workflow).
- "Config migration necessary" com `--strict`: migrar chaves depreciadas no `renovate.json`.
  - `matchPaths` → `matchFileNames`.
  - `stabilityDays` → `minimumReleaseAge` (ex.: `"3 days"`).
  - `schedule` composto ("after X and before Y") → entradas separadas (ex.: `"after 10pm on Sunday"`, `"before 6am on Sunday"`).

## Execução manual
- GitHub → Actions → "Renovate Config Validation" → Run workflow (branch `main`).
- Resultado esperado: `INFO: Config validated successfully`.

## Referências
- Renovate Docs: https://docs.renovatebot.com/
- Config Schema: `https://docs.renovatebot.com/renovate-schema.json`
