# Issue #86 — Validação prática (canário)

## Artefatos e referências
- PR canário: https://github.com/Tomvaz11/iabank/pull/126 (branch `chore/issue-86-validate-canary`)
- Frontend Foundation CI (run): https://github.com/Tomvaz11/iabank/actions/runs/19249672893 — status: success
- Renovate Config Validation (run): https://github.com/Tomvaz11/iabank/actions/runs/19249680849 — status: success
- CI Outage Selftest (run): https://github.com/Tomvaz11/iabank/actions/runs/19249745327 — status: success
- Artefatos Lighthouse: `artifacts_download/issue-86/observabilidade/data/lighthouse-latest.json`, `.../artifacts/lighthouse/home.summary.json`

## Resultados por item do checklist

1) Renovate validator (pin de versão major)
- Resultado: NÃO ATENDIDO (executa com `renovate@latest`).
- Evidência (log): `npx --yes -p renovate@latest renovate-config-validator --strict renovate.json` (run 19249680849).

2) Poetry no CI (`--no-interaction --no-ansi --sync`)
- Resultado: PARCIAL (sem `--sync`).
- Evidência (log): etapa "Install Python dependencies" usa `poetry install --with dev --no-ansi --no-interaction` (run 19249672893 > job Security Checks).

3) Cache pnpm sensível a `scripts/**`
- Resultado: NÃO ATENDIDO (cache hit apesar de alteração em `scripts/ci/*`).
- Evidência (log): "Cache restored from key: node-cache-...-pnpm-<hash de pnpm-lock.yaml>" (run 19249672893 > job Vitest). Mudança em `scripts/` não alterou a chave.

4) Serviços DB via hostname do serviço (`postgres`) e sem mapear porta do host
- Resultado: NÃO ATENDIDO (usa localhost/127.0.0.1 + mapeamento de porta).
- Evidência (log): `FOUNDATION_DB_HOST: 127.0.0.1` e verificação `/dev/tcp/127.0.0.1/5432`; services: `ports: 5432:5432` (run 19249672893 > job Security Checks).

5) DRY + Step summaries (incl. Lighthouse/ZAP)
- Resultado: PARCIAL/OK (summaries presentes; DRY não avaliado nesta validação).
- Evidência: etapa "Resumo dos budgets Lighthouse" executada; artefatos Lighthouse presentes em `performance-lighthouse-budgets`. Etapa "Resumo ZAP" escreve no `GITHUB_STEP_SUMMARY` (run 19249672893 > jobs Performance/Security).

6) Outage policy (retry/backoff; fail-open/closed)
- Resultado: OK (selftest cobre cenários fail-open e fail-closed).
- Evidência: workflow "CI Outage Selftest" (run 19249745327) concluiu ambos os jobs, com simulação de outage e comportamento esperado.

7) Pre-commit no CI (opcional)
- Resultado: NÃO IMPLEMENTADO (nenhum job `pre-commit` encontrado nos workflows).
- Evidência: busca por `pre-commit` vazia em `.github/workflows/`.

## Conclusão de validação
- A issue #86 permanece apenas parcialmente atendida. Itens confirmados: step summaries e outage selftest. Pendente/fora do esperado: pin do Renovate validator, uso de `--sync` no Poetry, cache pnpm sensível a `scripts/**`, conexão ao DB por hostname `postgres` sem mapear porta, e job opcional de pre-commit.

## Ações recomendadas (follow-up)
- Renovate validator: trocar `npx -p renovate@latest` por `npx -p renovate@^39 renovate-config-validator` (exemplo) e fixar major.
- Poetry: alterar comandos para `poetry install --no-interaction --no-ansi --sync` nas etapas de instalação.
- pnpm cache: incluir `cache-dependency-path` com múltiplos paths (ex.: `pnpm-lock.yaml\nfrontend/scripts/**\nscripts/**`) nas etapas com cache pnpm.
- DB no CI: remover `ports:` do serviço Postgres e usar `FOUNDATION_DB_HOST=postgres` nos jobs que precisam de banco.
- Pre-commit: adicionar job leve com `pre-commit run --all-files` e resumo no `GITHUB_STEP_SUMMARY`.

