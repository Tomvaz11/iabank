# iabank Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-19

## Active Technologies
- Python 3.11; Node.js 20; TypeScript 5.6. + Django 4.2 LTS; Django REST Framework 3.15; Celery 5.3; Redis 7; React 18; Vite 5; TanStack Query 5; Zustand 4; Spectral; Pact; Terraform; Argo CD; OpenTelemetry SDK; Sentry. (002-f-10-fundacao)
- PostgreSQL 15 (pgcrypto); Redis 7; Hashicorp Vault Transit. (002-f-10-fundacao)

## Project Structure
```
backend/
frontend/
infra/
contracts/
docs/
observabilidade/
```

## Commands
cd src && pytest && ruff check .

## Code Style
Python 3.11; Node.js 20; TypeScript 5.6.: Follow standard conventions

## Recent Changes
- 002-f-10-fundacao: Added Python 3.11; Node.js 20; TypeScript 5.6. + Django 4.2 LTS; Django REST Framework 3.15; Celery 5.3; Redis 7; React 18; Vite 5; TanStack Query 5; Zustand 4; Spectral; Pact; Terraform; Argo CD; OpenTelemetry SDK; Sentry.

<!-- MANUAL ADDITIONS START -->
- RESPONDA AO USUARIO SEMPRE EM PT-BR

## PR/Commits (Spec‑Kit)
- Use `.github/pull_request_template.md`; título em Conventional Commits; inclua ao menos uma tag `@SC-00x` (SC‑001..SC‑005).
- Validadores: `scripts/git/verify-commit-msg.sh`, `scripts/ci/check-pr-template.sh`, `scripts/ci/validate-sc-tag.sh` (CI: `.github/workflows/frontend-foundation.yml`).
<!-- MANUAL ADDITIONS END -->
