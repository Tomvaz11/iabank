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

### Completed (Phase 0-1)
- [x] Feature specification com 112 requisitos funcionais
- [x] Architecture research baseada na constitution
- [x] Data model com 11 entidades principais
- [x] OpenAPI 3.0 contracts completos
- [x] Quickstart guide com 6 fluxos críticos

### Completed (Phase 3.1 - Setup)
- [x] T001: Estrutura Django backend com Apps modulares
- [x] T002: Projeto Django inicializado com dependências
- [x] T003: Linting configurado (ruff, black, mypy)
- [x] T004: Estrutura React com TypeScript e Feature-Sliced Design
- [x] T005: PostgreSQL com Docker e multi-tenancy
- [x] Multi-tenant architecture com RLS e PITR
- [x] Management commands (backup, RLS enable)
- [x] Code quality tools e scripts de automação

### Next Steps (Phase 3.2 - TDD)
- [ ] T006-T012: Contract tests (RED phase primeiro)
- [ ] T013-T019: Integration tests
- [ ] Create factories com tenant propagation
- [ ] Implement core business logic

## Development Guidelines

### File Organization
```
backend/src/iabank/
├── core/                    # Multi-tenancy, base models
├── customers/               # Django App
│   ├── domain/             # Domain isolation
│   │   ├── entities.py     # Pydantic entities
│   │   └── services.py     # Business logic pura
│   ├── models.py           # Django ORM
│   ├── views.py            # DRF ViewSets
│   └── cli.py              # CLI opcional
├── operations/             # Empréstimos
├── finance/                # Financeiro
└── users/                  # Usuários/permissões
```

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
- 2025-09-13: T001-T005 implementados com sucesso
- 2025-09-13: PostgreSQL configurado com porta 5433 (conflito resolvido)
- 2025-09-13: Multi-tenant architecture com RLS e PITR implementado
- 2025-09-13: Management commands para backup e RLS criados
- 2025-09-13: Code quality tools configurados e funcionais
- 2025-09-13: Remoção de emojis dos arquivos de código fonte
- 2025-09-12: Initial planning phase completed
- 2025-09-12: Constitution v1.0.0 ratified
- 2025-09-12: Data model and API contracts defined

## Useful Commands
```bash
# Setup development environment
python manage.py migrate
python manage.py seed_data --tenant-id <uuid>

# Run tests with tenant isolation
pytest --tenant-isolation
pytest --cov=src --cov-min=85

# Generate API types
pnpm gen:api-types

# Check constitution compliance
ruff check src/
black --check src/
```

---
*Updated: 2025-09-13 | Lines: 159 | Constitution: v1.0.0*