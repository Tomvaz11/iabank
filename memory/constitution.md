# IABANK Constitution

## Core Principles

### I. Django-Domain-First (NÃO-NEGOCIÁVEL)
Toda funcionalidade **DEVE** começar como Django App modular com domain isolation obrigatório:
- **Estrutura mandatória**: `domain/` dentro de cada Django App
- **Domain puro**: entities.py (Pydantic) + services.py (lógica pura)
- **Infrastructure**: models.py (Django ORM como implementação) + views.py (DRF)
- **Application**: coordination.py (orquestra domain + infrastructure quando necessário)
- **Separation**: Domain NÃO pode importar Django, mas pode ser usado POR models.py

### II. CLI Interface Multi-Tenant Aware (Opcional)
Apps Django **PODEM** expor funcionalidade via CLI para automação:
- Interface em cli.py quando necessário para operações batch
- **OBRIGATÓRIO**: CLI commands DEVEM receber --tenant-id como parâmetro
- **OBRIGATÓRIO**: CLI DEVE validar tenant_id antes de qualquer operação
- Entrada via stdin/argumentos, saída via stdout
- Suporte JSON para integração com scripts/pipelines

### III. Arquitetura em Camadas (NÃO-NEGOCIÁVEL)
A arquitetura **DEVE** seguir rigorosamente o padrão de Arquitetura em Camadas aplicada a um Monolíto Modular. A estrutura **OBRIGATÓRIA** é:
1. **Apresentação (Presentation)**: Django REST Framework (Views, Serializers, Routers)
2. **Aplicação (Application)**: Camada de Serviços que orquestra casos de uso
3. **Domínio (Domain)**: Lógica de negócio pura (Models/Managers para lógica simples, Serviços para lógica complexa)
4. **Infraestrutura (Infrastructure)**: Django ORM, Celery, clientes de APIs externas, caches

### IV. Multi-Tenancy Obrigatório
**TODOS** os modelos de dados **DEVEM** herdar de `BaseTenantModel` e incluir campo `tenant`. **TODAS** as queries **DEVEM** filtrar por tenant através de middleware obrigatório. Isolamento de dados por tenant é **NÃO-NEGOCIÁVEL**.

### V. Stack Tecnológica Mandatória
**Backend**: Python 3.11+, Django 4.2+, Django REST Framework, PostgreSQL, Redis, Celery, Gunicorn
**Frontend**: React 18+, TypeScript, Vite, Feature-Sliced Design (FSD), TanStack Query, Zustand, Tailwind CSS
**Containerização**: Docker, Docker Compose obrigatórios
**Monorepo**: Backend e frontend **DEVEM** residir no mesmo repositório

### VI. Requisitos Regulatórios Brasileiros (CRÍTICOS)
**OBRIGATÓRIO** implementar desde o início:
- Cálculo do CET (Custo Efetivo Total) mensal e anual
- Cálculo do IOF (Imposto sobre Operações Financeiras)
- Conformidade com Lei da Usura (taxas configuráveis)
- Suporte ao período de arrependimento (7 dias)
- Conformidade LGPD: IABANK como Operador, clientes como Controladores

### VII. Contract-First TDD (NÃO-NEGOCIÁVEL)
**NENHUM código de implementação pode ser escrito antes de:**
1. **Contratos de API escritos primeiro** (OpenAPI manual ou via spec)
2. **Testes de contrato escritos** validando schema
3. **Testes unitários serem escritos** e definidos completamente
4. **Testes serem validados e aprovados** pelo usuário/stakeholder
5. **Testes serem confirmados como FALHANDO** (Red phase do TDD)
6. **Só então implementar** código mínimo para fazer testes passarem (Green phase)

**Cobertura mínima 85%** obrigatória. **Factories devem** propagar tenant para sub-factories. **Meta-testes obrigatórios** para validar factories. **Ferramentas**: pytest, factory-boy, APIClient do DRF.

### VIII. Feature-Sliced Design (FSD) Obrigatório
**Frontend DEVE** seguir rigorosamente Feature-Sliced Design (FSD):
- **Estrutura mandatória**: app/ → pages/ → features/ → entities/ → shared/
- **Organização por fatias verticais** de negócio, não por tipo de arquivo
- **Cada feature contém**: api/, components/, model/, ui/
- **Estado**: TanStack Query (servidor), Zustand (global cliente), useState (local)
- **Colocação**: Toda lógica de uma funcionalidade em um único diretório

### IX. Schema-First Development (NÃO-NEGOCIÁVEL)
**Sincronização automática** Backend-Frontend obrigatória:
- Django REST Framework **DEVE** gerar schema OpenAPI 3 atualizado
- **openapi-typescript-codegen OBRIGATÓRIO** para interfaces TypeScript
- Pipeline CI **DEVE** verificar tipos atualizados (script `pnpm gen:api-types`)
- **Falha na sincronização BLOQUEIA merge** - zero tolerância a dessincronização
- Schema **DEVE** ser versionado no repositório

### X. Observabilidade com Performance Balance (CRÍTICA)
**Logging estruturado JSON obrigatório** com structlog:
- **Contexto automático**: request_id, user_id, tenant_id via Middleware customizado
- **Middleware otimizado**: Context injection em <10ms via thread-local storage
- **Logging assíncrono**: structlog com handler assíncrono para não bloquear requests
- **Formato**: JSON em produção, human-readable em desenvolvimento
- **SLI mandatório**: Latência API < 500ms INCLUINDO overhead de logging
- **SLO mandatório**: 99.9% disponibilidade mensal do sistema
- **Endpoints obrigatórios**: /metrics (django-prometheus) + /health
- **Alerting**: Sentry integrado com Slack/PagerDuty para anomalias

### XI. API Design Standards (NÃO-NEGOCIÁVEL)
**Versionamento via URL obrigatório**: Prefixo `/api/v1/` para **TODAS** as rotas
**Formato resposta padronizado mandatório**:
- **Sucesso (2xx)**: `{"data": {...}, "meta": {"pagination": {...}}}`
- **Erro (4xx/5xx)**: `{"errors": [{"status": "422", "code": "...", "source": {...}, "detail": "..."}]}`
- **ExceptionHandler customizado DRF OBRIGATÓRIO** para formatação consistente
- **Pydantic obrigatório** para DTOs e entidades de domínio puras

## Stack Tecnológica Detalhada

### Backend Mandatório
- **Python**: 3.11+ (obrigatório)
- **Framework**: Django 4.2+, Django REST Framework 3.14+
- **Banco**: PostgreSQL com indexação tenant-first obrigatória
- **Cache/Fila**: Redis 5.0+, Celery 5.3+ com acks_late=True
- **Servidor**: Gunicorn para produção
- **Validação**: Pydantic 1.10+ para DTOs
- **Logs**: structlog para logging estruturado JSON

### Frontend Mandatório
- **Framework**: React 18+ com TypeScript
- **Build**: Vite obrigatório
- **Arquitetura**: Feature-Sliced Design (FSD) - estrutura de pastas não-negociável
- **Estado**: TanStack Query (dados servidor), Zustand (estado global cliente)
- **Styling**: Tailwind CSS obrigatório
- **Tipos**: openapi-typescript-codegen para sincronização automática de tipos

### Ferramentas de Qualidade Obrigatórias
- **Python**: Black (formatação), Ruff (linting), pytest (testes)
- **TypeScript**: Prettier (formatação), ESLint (linting)
- **Pre-commit**: Hooks obrigatórios para validação automática
- **CI/CD**: GitHub Actions com quality gates

## Regras de Arquitetura e Desenvolvimento

### Organização de Código
**Monorepo obrigatório** com estrutura Django-Domain-First:
```
iabank/
├── backend/src/iabank/
│   ├── core/           # Modelos base, middleware
│   ├── customers/      # Django App
│   │   ├── domain/     # ← Domain isolation
│   │   │   ├── entities.py  # Pydantic entities
│   │   │   └── services.py  # Business logic pura
│   │   ├── models.py   # Django ORM
│   │   ├── views.py    # DRF ViewSets
│   │   └── cli.py      # CLI opcional
│   ├── operations/     # Django App (empréstimos)
│   │   ├── domain/     # ← Domain isolation
│   │   ├── models.py   # Django persistence
│   │   └── views.py    # Web interface
│   ├── finance/        # Django App (financeiro)
│   └── users/          # Django App (usuários)
└── frontend/src/       # React + FSD (inalterado)
    ├── app/           # Configuração global
    ├── features/      # Funcionalidades (FSD)
    └── shared/        # Código reutilizável
```

### Lógica de Domínio
**Domain Isolation obrigatório** dentro de cada Django App:
- **Domain puro** (`domain/entities.py`): Pydantic entities para lógica de negócio
- **Domain services** (`domain/services.py`): Business logic sem dependências Django
- **Infrastructure** (`models.py`): Django ORM como detalhe de implementação
- **Presentation** (`views.py`): DRF ViewSets que orquestram domain + infrastructure
- **Regra crítica**: Domain NÃO pode importar nada do Django (zero coupling)

### Segurança Obrigatória
- **Autenticação**: JWT com access_token (15min) + refresh_token (7 dias) em HttpOnly cookie
- **Autorização**: Permissões granulares por tenant via DRF
- **Criptografia**: Dados em repouso, campos PII com django-cryptography
- **MFA**: Obrigatório para perfis administrativos e operações financeiras críticas
- **MFA Performance SLA**: Operações MFA latência <2000ms, fallback de emergência com audit trail
- **Headers**: HTTPS, HSTS, CSP, proteção CSRF/XSS obrigatórias

### Performance e Observabilidade
**Indexação**: tenant_id como primeira coluna em todos os índices compostos
**Backup**: PITR com PostgreSQL, WAL contínuo, RPO < 5 minutos, RTO < 1 hora
**Auditoria**: django-simple-history obrigatório para Loan, Installment, Customer, FinancialTransaction, User
**Métricas**: django-prometheus com endpoint /metrics
**Logging**: structlog com contexto automático (request_id, user_id, tenant_id)
**Health Check**: Endpoint /health obrigatório
**SLI/SLO**: Latência API < 500ms, 99.9% disponibilidade mensal

**Disaster Recovery Pilot Light obrigatório**:
- **Replicação assíncrona** PostgreSQL para região secundária (standby)
- **RPO mandatório**: < 5 minutos (máxima perda de dados aceitável)
- **RTO mandatório**: < 4 horas (tempo máximo incluindo DNS propagation)
- **DNS failover**: Route53 health checks reduzem RTO para ~15 minutos
- **IaC com Terraform** para recriação rápida da stack completa
- **Processo semi-automatizado**: Promover réplica → IaC → Atualizar DNS
- **Testes DR trimestrais obrigatórios** para validar eficácia do plano

### Processamento Assíncrono
**Celery obrigatório** com:
- **Idempotência**: ID único para tarefas críticas
- **Retentativas**: Backoff exponencial automático (autoretry_for, retry_kwargs, retry_backoff=True)
- **Confirmação tardia**: acks_late=True para tarefas críticas
- **Dead-Letter Queue**: Para tarefas falhas após max_retries
- **Decorator obrigatório**: @shared_task para todas as tarefas assíncronas

### Versionamento e API
**API versionada via URL obrigatório**: Todas as rotas **DEVEM** usar prefixo "/api/v1/"
**Padrão de resposta obrigatório**:
- **Sucesso (2xx)**: `{"data": {...}, "meta": {"pagination": {...}}}`
- **Erro (4xx/5xx)**: `{"errors": [{"status": "422", "code": "...", "source": {...}, "detail": "..."}]}`
**ExceptionHandler customizado** do DRF obrigatório para formatação consistente

### Configuração e Ambientes
**django-environ obrigatório**: Configuração via variáveis de ambiente
**Arquivo .env** obrigatório para desenvolvimento (não versionado)
**Arquivo .env.example** obrigatório (versionado como template)
**settings.py** como único ponto de leitura das variáveis
**Produção**: Variáveis injetadas diretamente no provedor de nuvem

## Quality Gates

### Pipeline CI/CD Obrigatório
**GitHub Actions** com estágios mandatórios:
1. **Lint/Format**: ruff, black, eslint, prettier (falha bloqueia merge)
2. **Testes**: Cobertura ≥85% (falha bloqueia merge)
3. **Build**: Frontend pnpm build deve passar
4. **Security**: SAST sem vulnerabilidades críticas
5. **Path Filtering**: Jobs seletivos por diretório modificado

### Desenvolvimento
**Seed Data Strategy obrigatória**:
- **Comandos Django customizados**: `python manage.py seed_data` obrigatório
- **factory-boy OBRIGATÓRIO** com propagação tenant para todas as factories
- **Cenários multi-tenant realistas** para desenvolvimento e teste
- **Dados fictícios consistentes** respeitando relações e constraints
- **Ambientes**: seed separado para dev/test/staging com volumes adequados

- **TDD Rigoroso OBRIGATÓRIO**: 
  1. **Red** (Escrever teste que falha)
  2. **Green** (Implementação mínima para passar)  
  3. **Refactor** (Melhorar código mantendo testes passando)
  4. **Aprovação usuário** antes de prosseguir para próxima funcionalidade
- **Pirâmide de Testes Obrigatória**:
  - **70% Testes Unitários**: Lógica isolada, mocks para dependências
  - **20% Testes Integração**: APIs completas, banco de dados real
  - **10% Testes E2E**: Fluxos críticos fim-a-fim
- **Multi-Tenant Testing (CRÍTICO)**:
  - **Factories**: Propagação tenant obrigatória + validação isolamento automática
  - **Tenant Isolation Tests**: Todo endpoint DEVE ter teste anti-vazamento
  - **Meta-testes**: Validação factories + teste tenant leakage em cada PR
- **Testes Regulatórios Obrigatórios**:
  - **CET/IOF**: Property-based testing para cálculos financeiros
  - **LGPD**: Testes anonimização, exportação e exclusão por tenant
  - **Lei da Usura**: Validação limites configuráveis automatizada
  - **Período Arrependimento**: Testes temporais para cancelamentos
- **E2E Testing Detalhado**: Cypress/Playwright para fluxos críticos obrigatórios:
  - Criação empréstimo completo (login → simulação → aprovação → contrato)
  - Pagamento parcela (registro → atualização saldo → notificação)
  - Relatório financeiro (filtros → exportação → dados corretos)
- **Performance Testing**: Load tests para SLI/SLO < 500ms integrados ao pipeline
- **Auditoria Testing**: Validação trilha completa django-simple-history
- **Code Review**: Verificação compliance + validação tenant isolation
- **Migrações**: Retrocompatíveis obrigatórias + testes rollback
- **Complexidade Ciclomática**: Máximo 10 por função/método (ruff)
- **ADRs obrigatórios**: docs/adr/ para decisões arquiteturais
- **Seed Data**: Comandos Django + factory-boy com cenários multi-tenant

### Deployment
- **Containers**: Dockerfile multi-stage obrigatório
- **Configuração**: django-environ, variáveis de ambiente (nunca hardcode)
- **Secrets**: AWS Secrets Manager/HashiCorp Vault em produção
- **Rollback**: Estratégia através de revert + CD pipeline
- **DR**: Pilot Light com réplica PostgreSQL assíncrona
- **Backup Strategy**: 
  - **PITR**: Point-in-Time Recovery com WAL contínuo
  - **Retenção**: WAL 14 dias, backups diários 30 dias, mensais 1 ano
  - **Teste de Restore**: Trimestral obrigatório
- **IaC**: Terraform obrigatório para infraestrutura
- **Ambientes**: Desenvolvimento, Staging, Produção com CI/CD específico

## Governance

Esta constitution **SUPERSEDE** todas as outras práticas e documentações. Toda Pull Request **DEVE** ser verificada quanto à compliance. Complexidade **DEVE** ser justificada através de ADRs (Architectural Decision Records).

**Amendments**: Mudanças na constitution requerem documentação via ADR, aprovação da equipe e plano de migração. Blueprint arquitetural é a fonte única da verdade (SSOT) para estrutura e contratos.

**Quality Gates**: Nenhum código pode ser mergeado sem passar em:
- [x] Todos os testes unitários e integração (pirâmide 70/20/10)
- [x] Cobertura de código ≥85% sem regressão
- [x] Testes tenant isolation com validação anti-vazamento
- [x] Testes regulatórios (CET/IOF/LGPD/Lei da Usura)
- [x] Performance tests ≤500ms para endpoints críticos
- [x] Zero erros de linting (ruff, eslint, prettier)
- [x] Complexidade ciclomática ≤10 por função/método
- [x] SAST sem vulnerabilidades críticas/altas
- [x] E2E tests passando para 3 fluxos críticos
- [x] Auditoria testing (django-simple-history)
- [x] Schema OpenAPI atualizado + tipos sincronizados

**Version**: 1.0.0 | **Ratified**: 2025-09-12 | **Last Amended**: 2025-09-12