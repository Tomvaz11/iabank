# Quickstart Guide: Sistema IABANK

**Feature**: Sistema IABANK - Plataforma SaaS de Gestão de Empréstimos  
**Date**: 2025-09-12  
**Purpose**: Validação rápida do sistema através de cenários críticos

## Prerequisites

### Environment Setup
```bash
# Clone repository
git clone https://github.com/empresa/iabank.git
cd iabank

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py seed_data --tenant-count 2 --users-per-tenant 5

# Setup frontend
cd ../frontend
npm install
npm run gen:api-types  # Generate TypeScript types from OpenAPI

# Start services
docker-compose up -d  # PostgreSQL + Redis
python backend/manage.py runserver &
npm run dev  # Frontend dev server
```

### Test Data
```bash
# Create test tenant and users
python manage.py seed_data --tenant empresa-teste --admin-email admin@empresateste.com.br
```

**Test Credentials**:
- **Admin**: admin@empresateste.com.br / SecurePass123!
- **Consultant**: consultor@empresateste.com.br / SecurePass123!
- **Manager**: gestor@empresateste.com.br / SecurePass123!

## Critical User Flows

### Flow 1: Autenticação e Setup Inicial (5 minutos)

#### 1.1 Login de Usuário
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@empresateste.com.br",
  "password": "SecurePass123!",
  "tenant_domain": "empresa-teste"
}
```

**Expected Response**:
```json
{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 900,
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "admin@empresateste.com.br",
      "role": "ADMIN",
      "first_name": "Admin",
      "last_name": "Sistema"
    }
  }
}
```

#### 1.2 Verificar Informações do Tenant
```http
GET /api/v1/tenants/current
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": {
    "id": "tenant-uuid",
    "name": "Empresa Teste",
    "document": "12.345.678/0001-90",
    "domain": "empresa-teste",
    "is_active": true
  }
}
```

#### 1.3 Setup Conta Bancária Principal
```http
POST /api/v1/bank-accounts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "bank_code": "001",
  "bank_name": "Banco do Brasil",
  "agency": "1234-5",
  "account_number": "67890-1",
  "account_type": "CHECKING",
  "is_main": true
}
```

**Success Criteria**:
- ✅ Login realizado com sucesso
- ✅ Token JWT válido recebido
- ✅ Dados do tenant carregados
- ✅ Conta bancária principal criada

---

### Flow 2: Gestão de Clientes (8 minutos)

#### 2.1 Cadastro de Cliente Pessoa Física
```http
POST /api/v1/customers
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "document_type": "CPF",
  "document": "123.456.789-00",
  "name": "João Silva Santos",
  "email": "joao.silva@email.com",
  "phone": "(11) 99999-9999",
  "birth_date": "1985-05-15",
  "monthly_income": 5000.00,
  "addresses": [
    {
      "type": "RESIDENTIAL",
      "street": "Rua das Flores",
      "number": "123",
      "complement": "Apto 45",
      "neighborhood": "Centro",
      "city": "São Paulo",
      "state": "SP",
      "zipcode": "01234-567",
      "is_primary": true
    }
  ]
}
```

**Expected Response**:
```json
{
  "data": {
    "id": "customer-uuid",
    "document_type": "CPF",
    "document": "123.456.789-00",
    "name": "João Silva Santos",
    "email": "joao.silva@email.com",
    "credit_score": 0,
    "is_active": true,
    "addresses": [
      {
        "id": "address-uuid",
        "type": "RESIDENTIAL",
        "street": "Rua das Flores",
        "is_primary": true
      }
    ]
  }
}
```

#### 2.2 Análise de Crédito do Cliente
```http
POST /api/v1/customers/{customer_id}/credit-analysis
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": {
    "credit_score": 750,
    "risk_level": "LOW",
    "recommendation": "APPROVE",
    "max_loan_amount": 50000.00
  }
}
```

#### 2.3 Buscar Clientes por Documento
```http
GET /api/v1/customers?search=123.456.789-00
Authorization: Bearer <access_token>
```

**Success Criteria**:
- ✅ Cliente criado com dados completos
- ✅ Endereço principal associado
- ✅ CPF validado corretamente
- ✅ Análise de crédito executada
- ✅ Score atualizado no perfil
- ✅ Busca por documento funcional

---

### Flow 3: Criação e Gestão de Empréstimos (12 minutos)

#### 3.1 Criar Empréstimo
```http
POST /api/v1/loans
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "customer_id": "customer-uuid",
  "principal_amount": 10000.00,
  "interest_rate": 0.0299,
  "installments_count": 12,
  "first_due_date": "2025-10-15",
  "notes": "Empréstimo para capital de giro"
}
```

**Expected Response**:
```json
{
  "data": {
    "id": "loan-uuid",
    "customer": {
      "id": "customer-uuid",
      "name": "João Silva Santos"
    },
    "consultant": {
      "id": "consultant-uuid",
      "first_name": "Consultor"
    },
    "principal_amount": 10000.00,
    "interest_rate": 0.0299,
    "installments_count": 12,
    "iof_amount": 41.10,
    "cet_monthly": 0.0315,
    "cet_yearly": 0.4512,
    "total_amount": 11245.67,
    "contract_date": "2025-09-12",
    "first_due_date": "2025-10-15",
    "status": "ANALYSIS",
    "regret_deadline": "2025-09-19",
    "installments": [
      {
        "sequence": 1,
        "due_date": "2025-10-15",
        "principal_amount": 833.33,
        "interest_amount": 103.72,
        "total_amount": 937.05,
        "status": "PENDING"
      }
    ]
  }
}
```

#### 3.2 Aprovar Empréstimo
```http
POST /api/v1/loans/{loan_id}/approve
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": {
    "id": "loan-uuid",
    "status": "APPROVED"
  }
}
```

#### 3.3 Ativar Empréstimo (Simulação de Assinatura)
```http
PUT /api/v1/loans/{loan_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "ACTIVE"
}
```

#### 3.4 Listar Parcelas do Empréstimo
```http
GET /api/v1/loans/{loan_id}/installments
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": [
    {
      "id": "installment-1-uuid",
      "sequence": 1,
      "due_date": "2025-10-15",
      "total_amount": 937.05,
      "amount_paid": 0.00,
      "status": "PENDING"
    },
    {
      "id": "installment-2-uuid",
      "sequence": 2,
      "due_date": "2025-11-15",
      "total_amount": 937.05,
      "amount_paid": 0.00,
      "status": "PENDING"
    }
  ]
}
```

**Success Criteria**:
- ✅ Empréstimo criado em status ANALYSIS
- ✅ Cálculos de IOF e CET automáticos
- ✅ 12 parcelas geradas automaticamente
- ✅ Período de arrependimento definido (7 dias)
- ✅ Aprovação alterou status para APPROVED
- ✅ Ativação alterou status para ACTIVE
- ✅ Todas as parcelas listadas corretamente

---

### Flow 4: Processamento de Pagamentos (10 minutos)

#### 4.1 Pagamento Total de Parcela
```http
POST /api/v1/installments/{installment_id}/payments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount": 937.05,
  "payment_date": "2025-10-15",
  "payment_method": "PIX",
  "bank_account_id": "bank-account-uuid"
}
```

**Expected Response**:
```json
{
  "data": {
    "installment": {
      "id": "installment-1-uuid",
      "amount_paid": 937.05,
      "status": "PAID",
      "payment_date": "2025-10-15"
    },
    "transaction": {
      "id": "transaction-uuid",
      "type": "INCOME",
      "amount": 937.05,
      "description": "Pagamento parcela 1/12 - Empréstimo #loan-uuid",
      "status": "PAID"
    }
  }
}
```

#### 4.2 Pagamento Parcial de Parcela
```http
POST /api/v1/installments/{installment_2_id}/payments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount": 500.00,
  "payment_date": "2025-11-15",
  "payment_method": "BOLETO",
  "bank_account_id": "bank-account-uuid"
}
```

**Expected Response**:
```json
{
  "data": {
    "installment": {
      "id": "installment-2-uuid",
      "total_amount": 937.05,
      "amount_paid": 500.00,
      "status": "PARTIALLY_PAID",
      "payment_date": "2025-11-15"
    },
    "transaction": {
      "id": "transaction-uuid",
      "type": "INCOME",
      "amount": 500.00,
      "description": "Pagamento parcial 2/12 - Empréstimo #loan-uuid"
    }
  }
}
```

#### 4.3 Complemento do Pagamento Parcial
```http
POST /api/v1/installments/{installment_2_id}/payments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "amount": 437.05,
  "payment_date": "2025-11-20",
  "payment_method": "TRANSFER"
}
```

**Expected Response**:
```json
{
  "data": {
    "installment": {
      "id": "installment-2-uuid",
      "amount_paid": 937.05,
      "status": "PAID",
      "payment_date": "2025-11-20"
    }
  }
}
```

**Success Criteria**:
- ✅ Pagamento total alterou status para PAID
- ✅ Transação financeira criada automaticamente
- ✅ Saldo da conta bancária atualizado
- ✅ Pagamento parcial criou status PARTIALLY_PAID
- ✅ Múltiplos pagamentos na mesma parcela
- ✅ Complemento finalizou a parcela

---

### Flow 5: Relatórios e Dashboard (6 minutos)

#### 5.1 Dashboard Principal
```http
GET /api/v1/reports/dashboard?period=30d
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": {
    "total_active_loans": 1,
    "total_loan_amount": 10000.00,
    "default_rate": 0.00,
    "monthly_revenue": 1874.10,
    "loans_by_status": {
      "ACTIVE": 1,
      "ANALYSIS": 0,
      "COLLECTION": 0
    },
    "payments_trend": [
      {
        "date": "2025-10-15",
        "amount": 937.05,
        "count": 1
      }
    ]
  }
}
```

#### 5.2 Relatório de Fluxo de Caixa
```http
GET /api/v1/reports/cash-flow?start_date=2025-09-01&end_date=2025-09-30
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": {
    "period": {
      "start_date": "2025-09-01",
      "end_date": "2025-09-30"
    },
    "income": 1874.10,
    "expenses": 0.00,
    "net_flow": 1874.10,
    "daily_flow": [
      {
        "date": "2025-10-15",
        "income": 937.05,
        "expenses": 0.00,
        "net": 937.05
      }
    ]
  }
}
```

#### 5.3 Listar Transações Financeiras
```http
GET /api/v1/financial-transactions?type=INCOME&start_date=2025-09-01
Authorization: Bearer <access_token>
```

**Success Criteria**:
- ✅ Dashboard carrega métricas principais
- ✅ Totais de empréstimos corretos
- ✅ Fluxo de caixa calculado corretamente
- ✅ Receitas registradas adequadamente
- ✅ Filtros de data funcionais

---

### Flow 6: Conformidade e Auditoria (8 minutos)

#### 6.1 Cancelamento por Arrependimento
```http
POST /api/v1/loans/{loan_id}/cancel
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Cancelamento por arrependimento do cliente dentro do prazo legal"
}
```

**Expected Response** (dentro de 7 dias):
```json
{
  "data": {
    "id": "loan-uuid",
    "status": "CANCELLED",
    "regret_deadline": "2025-09-19"
  }
}
```

#### 6.2 Verificar Histórico de Alterações
```http
GET /api/v1/loans/{loan_id}/history
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": [
    {
      "history_date": "2025-09-12T10:00:00Z",
      "history_type": "CREATE",
      "history_user": "admin@empresateste.com.br",
      "changes": {
        "status": "ANALYSIS",
        "principal_amount": 10000.00
      }
    },
    {
      "history_date": "2025-09-12T10:05:00Z",
      "history_type": "UPDATE",
      "history_user": "admin@empresateste.com.br",
      "changes": {
        "status": "APPROVED"
      }
    }
  ]
}
```

#### 6.3 Validar Cálculos Regulatórios
```http
GET /api/v1/loans/{loan_id}/regulatory-validation
Authorization: Bearer <access_token>
```

**Expected Response**:
```json
{
  "data": {
    "cet_compliance": true,
    "iof_compliance": true,
    "usury_law_compliance": true,
    "regret_period_valid": true,
    "calculations": {
      "iof_rate": 0.0041,
      "iof_amount": 41.10,
      "cet_monthly": 0.0315,
      "cet_yearly": 0.4512,
      "max_interest_rate": 0.12
    }
  }
}
```

**Success Criteria**:
- ✅ Cancelamento por arrependimento aceito
- ✅ Histórico de alterações registrado
- ✅ Auditoria completa das operações
- ✅ Cálculos regulatórios validados
- ✅ Conformidade com Lei da Usura
- ✅ IOF e CET calculados corretamente

---

## Multi-Tenancy Validation

### Test Tenant Isolation
```bash
# Create second tenant
python manage.py seed_data --tenant empresa-dois --admin-email admin@empresadois.com.br

# Login with first tenant
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresateste.com.br","password":"SecurePass123!"}'

# Try to access second tenant data (should fail)
curl -X GET http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer <tenant1_token>"

# Verify only tenant1 customers returned
```

**Success Criteria**:
- ✅ Tenant 1 vê apenas seus próprios dados
- ✅ Tenant 2 isolado completamente
- ✅ Tentativa de acesso cross-tenant falha
- ✅ Middleware de isolamento funcional

---

## Performance Validation

### Load Test Critical Endpoints
```bash
# Install load testing tool
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

**Performance Targets**:
- Login: < 200ms p95
- Customer creation: < 300ms p95
- Loan creation: < 500ms p95
- Payment processing: < 400ms p95
- Dashboard: < 800ms p95

**Success Criteria**:
- ✅ Todos os endpoints < SLA definido
- ✅ Sistema mantém estabilidade sob carga
- ✅ Queries otimizadas com tenant_id

---

## Final Validation Checklist

### Functional Requirements
- ✅ FR-001: Cadastro completo de clientes
- ✅ FR-004: Criação de empréstimos com cálculos
- ✅ FR-005: Cálculo automático de IOF
- ✅ FR-006: Cálculo de CET conforme Banco Central
- ✅ FR-009: Período de arrependimento
- ✅ FR-019: Isolamento completo entre tenants
- ✅ FR-041: Métricas específicas expostas
- ✅ FR-088: Pagamentos parciais de parcelas

### Technical Requirements
- ✅ Multi-tenancy com isolamento automático
- ✅ API REST versionada (/api/v1/)
- ✅ Autenticação JWT funcional
- ✅ Criptografia de dados sensíveis
- ✅ Auditoria completa de operações
- ✅ Performance dentro dos SLAs

### Regulatory Compliance
- ✅ Cálculos financeiros precisos
- ✅ Lei da Usura respeitada
- ✅ Período de arrependimento (7 dias)
- ✅ Trilha de auditoria completa
- ✅ LGPD compliance preparado

---

## Next Steps

Após validação completa do quickstart:

1. **Execute /tasks command** para gerar lista detalhada de tarefas
2. **Implement TDD approach** seguindo constitution
3. **Setup CI/CD pipeline** com quality gates
4. **Configure production environment** com Docker
5. **Execute integration tests** completos

**Estimated Total Time**: 45-60 minutos para validação completa

---

*This quickstart validates the core business flows and technical architecture of IABANK system*