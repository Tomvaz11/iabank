# iabank Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-14

## Active Technologies
- Python 3.11 (backend monolito modular Django/DRF), conforme Art. I da Constituição e instruções do projeto. + Django 4.2 LTS, Django REST Framework 3.15, Celery 5.3 + Redis 7 (para seeds assíncronas e datasets de carga), `factory-boy` como catálogo único de factories, PostgreSQL 15 com `pgcrypto` e RLS multi-tenant, OpenTelemetry SDK + Sentry para observabilidade, ferramentas de carga (k6 ou Gatling equivalente) e Pact/OpenAPI 3.1 para contratos; alinhado a `BLUEPRINT_ARQUITETURAL.md` (§§3.1, 6, 26) e aos ADR-010/ADR-012. (003-seed-data-automation)
- PostgreSQL 15 multi-tenant com banco compartilhado, RLS por tenant e uso de `pgcrypto` para criptografia de dados sensíveis e suporte a anonimização irreversível; nenhum novo datastore é introduzido para esta feature. (003-seed-data-automation)
- Python 3.11; Node.js 20; TypeScript 5.6. + Django 4.2 LTS; Django REST Framework 3.15; Celery 5.3; Redis 7; React 18; Vite 5; TanStack Query 5; Zustand 4; Spectral; Pact; Terraform; Argo CD; OpenTelemetry SDK; Sentry. (002-f-10-fundacao)
- PostgreSQL 15 (pgcrypto); Redis 7; Hashicorp Vault Transit. (002-f-10-fundacao)

## Project Structure

```text
/api/v1/
```

## Commands

cd src && pytest && ruff check .

## Code Style

Python 3.11 (backend monolito modular Django/DRF), conforme Art. I da Constituição e instruções do projeto.: Follow standard conventions

## Recent Changes
- 003-seed-data-automation: Added Python 3.11 (backend monolito modular Django/DRF), conforme Art. I da Constituição e instruções do projeto. + Django 4.2 LTS, Django REST Framework 3.15, Celery 5.3 + Redis 7 (para seeds assíncronas e datasets de carga), `factory-boy` como catálogo único de factories, PostgreSQL 15 com `pgcrypto` e RLS multi-tenant, OpenTelemetry SDK + Sentry para observabilidade, ferramentas de carga (k6 ou Gatling equivalente) e Pact/OpenAPI 3.1 para contratos; alinhado a `BLUEPRINT_ARQUITETURAL.md` (§§3.1, 6, 26) e aos ADR-010/ADR-012.
- 002-f-10-fundacao: Added Python 3.11; Node.js 20; TypeScript 5.6. + Django 4.2 LTS; Django REST Framework 3.15; Celery 5.3; Redis 7; React 18; Vite 5; TanStack Query 5; Zustand 4; Spectral; Pact; Terraform; Argo CD; OpenTelemetry SDK; Sentry.

<!-- MANUAL ADDITIONS START -->
- RESPONDA AO USUARIO SEMPRE EM PT-BR
- COMMITS: use sempre Conventional Commits (`type(scope?): descrição`) conforme validado pelos hooks de commit.
- PRs: sempre use o template `.github/pull_request_template.md`; ao criar com `gh pr create`, prefira `--fill` ou edite mantendo as seções `## Descrição`, `## Checklist`, `## Contexto / Referências` e, quando aplicável, pelo menos uma tag `@SC-00x` no título ou corpo.
<!-- MANUAL ADDITIONS END -->
