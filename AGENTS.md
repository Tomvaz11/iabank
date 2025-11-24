# iabank Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-24

## Active Technologies
- Python 3.11 para backend/CLI; Node.js 20 para lint/diff/contratos (Art. I) + Django 4.2 LTS, DRF 3.15, Celery 5.3, Redis 7, factory-boy, OpenAPI tooling (Spectral/Prism/Pact), k6, Vault Transit client, OpenTelemetry SDK, Sentry (Blueprint §§3.1/6/26; ADR-008/010/011/012) (003-seed-data-automation)
- PostgreSQL 15 com pgcrypto/RLS obrigatorios; WORM storage para relatorios assinados; Redis como broker/estado de fila curta; Vault Transit para FPE deterministica (003-seed-data-automation)
- Python 3.11; Node.js 20; TypeScript 5.6. + Django 4.2 LTS; Django REST Framework 3.15; Celery 5.3; Redis 7; React 18; Vite 5; TanStack Query 5; Zustand 4; Spectral; Pact; Terraform; Argo CD; OpenTelemetry SDK; Sentry. (002-f-10-fundacao)
- PostgreSQL 15 (pgcrypto); Redis 7; Hashicorp Vault Transit. (002-f-10-fundacao)

## Project Structure

```text
web/
```

## Commands

cd src && pytest && ruff check .

## Code Style

Python 3.11 para backend/CLI; Node.js 20 para lint/diff/contratos (Art. I): Follow standard conventions

## Recent Changes
- 003-seed-data-automation: Added Python 3.11 para backend/CLI; Node.js 20 para lint/diff/contratos (Art. I) + Django 4.2 LTS, DRF 3.15, Celery 5.3, Redis 7, factory-boy, OpenAPI tooling (Spectral/Prism/Pact), k6, Vault Transit client, OpenTelemetry SDK, Sentry (Blueprint §§3.1/6/26; ADR-008/010/011/012)
- 002-f-10-fundacao: Added Python 3.11; Node.js 20; TypeScript 5.6. + Django 4.2 LTS; Django REST Framework 3.15; Celery 5.3; Redis 7; React 18; Vite 5; TanStack Query 5; Zustand 4; Spectral; Pact; Terraform; Argo CD; OpenTelemetry SDK; Sentry.

<!-- MANUAL ADDITIONS START -->
- RESPONDA AO USUARIO SEMPRE EM PT-BR

- Commits: `scripts/git/verify-commit-msg.sh`
- PR – template: `.github/pull_request_template.md`
- PR – tag @SC-00x: `scripts/ci/validate-sc-tag.sh`
- Pre-commit: `.pre-commit-config.yaml`
- Sincronizar branch antes do PR: `CONTRIBUTING.md`
- Docs gate: `scripts/ci/check-docs-needed.js`
<!-- MANUAL ADDITIONS END -->
