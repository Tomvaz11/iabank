# IABANK - Context for Claude Code

## Project Overview

IABANK é uma plataforma SaaS multi-tenant para empresas de crédito gerenciarem todo o ciclo de vida de empréstimos, desde análise de clientes até cobrança e controle financeiro.

## Architecture

- **Backend**: Django 4.2+ com Django REST Framework, PostgreSQL, Redis, Celery
- **Frontend**: React 18+ com TypeScript, Feature-Sliced Design (FSD), TanStack Query, Zustand
- **Multi-tenancy**: Row-level security obrigatório com tenant_id em todos os modelos
- **API**: REST versionada (/api/v1/) com OpenAPI schema generation

## Constitutional Requirements (NON-NEGOTIABLE)

### Django-Domain-First Architecture

- Cada Django App DEVE ter pasta `domain/` com isolation
- Domain layer: entities.py (Pydantic) + services.py (lógica pura)
- Infrastructure: models.py (Django ORM) + views.py (DRF)
- Domain NÃO pode importar Django

### Testing Strategy (TDD Obrigatório)

- RED-GREEN-Refactor cycle rigoroso
- Cobertura ≥85% obrigatória
- Ordem: Contract→Integration→E2E→Unit
- factory-boy com propagação automática de tenant_id
- Testes de isolamento tenant em cada endpoint

### Multi-Tenancy

- Todos os modelos herdam BaseTenantModel
- Middleware automático filtra por tenant_id
- Índices compostos com tenant_id como primeira coluna
- CLI commands DEVEM receber --tenant-id

### Performance & Observability

- SLA: <500ms p95 para operações CRUD
- structlog com contexto automático (request_id, user_id, tenant_id)
- django-prometheus + /health endpoint
- RPO <5min, RTO <1h para backup/recovery

## Key Entities

### Core Models

- **Tenant**: Empresa cliente da plataforma (isolamento de dados)
- **User**: Usuário do sistema com RBAC
- **Consultant**: Especialização de User para vendedores

### Business Models

- **Customer**: Cliente final com dados pessoais e score de crédito
- **Address**: Endereços dos clientes (múltiplos por cliente)
- **Loan**: Empréstimo com cálculos automáticos (IOF, CET)
- **Installment**: Parcelas individuais com controle de pagamentos

### Financial Models

- **BankAccount**: Contas bancárias da empresa
- **FinancialTransaction**: Receitas/despesas com categorização
- **PaymentCategory**: Categorias para classificação
- **CostCenter**: Centros de custo para controle gerencial

## Regulatory Compliance (Brasil)

### Cálculos Obrigatórios

- **IOF**: Conforme tabela Receita Federal
- **CET**: Fórmula Banco Central (Resolução 4.292/2013)
- **Lei da Usura**: Taxa máxima configurável por tenant
- **Período Arrependimento**: 7 dias corridos (CDC)

### LGPD Compliance

- Campos PII criptografados com django-cryptography
- Anonimização preservando logs de auditoria (10 anos)
- Trilha completa via django-simple-history

## API Standards

### Request/Response Format

```json
// Success (2xx)
{"data": {...}, "meta": {"pagination": {...}}}

// Error (4xx/5xx)
{"errors": [{"status": "422", "code": "...", "detail": "..."}]}
```

### Authentication

- JWT com access_token (15min) + refresh_token (7 dias)
- MFA obrigatório para admins e operações financeiras
- HttpOnly cookies para tokens

## Current Implementation Status

### Completed

- **Setup (T001-T005)**: Base Django + PostgreSQL + Multi-tenancy ✅
- **Enterprise (T071-T078)**: Auditoria + JWT + MFA + PITR + Health ✅
- **CI/CD (T068-T070)**: GitHub Actions + Pre-commit ✅

**Detalhes**: Ver tasks.md para breakdown completo

## Development Guidelines

### File Organization (Implementada)

```
backend/src/iabank/
├── core/                    # Multi-tenancy, auditoria, health, MFA
├── customers/               # Django App + domain/ isolation
├── operations/              # Empréstimos + domain/ isolation
├── finance/                 # Financeiro + domain/ isolation
└── users/                   # Usuários/permissões + domain/ isolation
```

**Status**: ✅ Estrutura Django-Domain-First implementada

### Critical Business Rules

- Empréstimo só editável antes do prazo de arrependimento
- Parcelas não podem ser removidas, apenas ajustadas
- Consultor recebe comissão apenas em empréstimos ACTIVE
- Pagamentos parciais permitidos com múltiplas transações
- Juros de mora aplicados automaticamente após 5 dias

### Security Requirements

- Criptografia em repouso para dados financeiros
- HTTPS obrigatório com HSTS
- Validação de CNPJ/CPF em todos os inputs
- Rate limiting em endpoints sensíveis
- Audit trail para todas as operações críticas

## Recent Changes

- 2025-09-15: T082 Path Filtering CI/CD + Blue-Green implementado (pipeline otimizado + rollback strategy)
- 2025-09-15: T081 Dockerfiles Multi-Stage implementado (Poetry + pnpm + nginx)
- 2025-09-14: T071-T078 CRITICAL implementados (95/100) - Ver tasks.md
- 2025-09-14: CI/CD Pipeline implementado - Ver tasks.md T068-T070
- 2025-09-13: T001-T005 Setup inicial concluído
- 2025-09-13: PostgreSQL multi-tenant + PITR configurado
- 2025-09-13: Code quality tools configurados

## Useful Commands

```bash
# Setup development environment
python manage.py migrate
python manage.py seed_data --tenant-id <uuid>

# Health check and monitoring (T076)
curl http://localhost:8000/health/

# Run tests with tenant isolation
cd backend && python -m pytest tests/contract/test_*.py -v
pytest --tenant-isolation
pytest --cov=src --cov-min=85

# PostgreSQL PITR backup (T074)
python manage.py manage_backups --create
python manage.py manage_backups --list

# MFA setup for admin users (T078)
python manage.py shell -c "from iabank.core.mfa import setup_totp_for_user; setup_totp_for_user('admin')"

# Check structured logs (T073)
tail -f logs/iabank.log | grep -E '"level":"info"'

# Docker & Containerização (T081)
docker-compose up -d                     # Stack completa
docker-compose ps                        # Status containers
curl http://localhost:8000/health/       # Backend health
curl http://localhost:3000               # Frontend
curl http://localhost:3000/api/          # API proxy test

# Generate API types
pnpm gen:api-types

# Check constitution compliance
ruff check src/
black --check src/

# Quality Gates verification (T080)
ruff check --select=C90 src/                # Complexity check
pip-audit -r requirements.txt               # Dependency vulnerabilities
bandit -r src/ -ll -i                       # Code security scan
bandit -r src/ -f sarif -o security-report.sarif --exit-zero  # SARIF report

# CI/CD Path Filtering & Rollback (T082)
# Path filtering testado automaticamente no GitHub Actions
# Rollback de emergência:
git revert <commit-sha> && git push origin main    # Emergency rollback
curl -f https://api.iabank.com/health/             # Verify restoration

# Documentação rollback strategy
cat docs/deployment/rollback-strategy.md           # Rollback procedures

# Fix common test issues
pip uninstall pytest-asyncio -y
```

---

_Updated: 2025-09-15 | Lines: 210 | Constitution: v1.0.0_
