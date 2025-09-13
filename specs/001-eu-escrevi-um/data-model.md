# Data Model: Sistema IABANK - Plataforma SaaS de Gestão de Empréstimos

**Feature**: Sistema IABANK  
**Date**: 2025-09-12  
**Status**: COMPLETE

## Entity Definitions

### Core Multi-Tenancy

#### Tenant
Representa uma empresa cliente da plataforma, contém configurações específicas e serve como contexto de isolamento para todos os dados.

**Fields**:
- `id`: UUID (Primary Key)
- `name`: String(255) - Nome da empresa
- `document`: String(20) - CNPJ da empresa (único)
- `domain`: String(100) - Domínio customizado (opcional)
- `settings`: JSONField - Configurações específicas do tenant
- `is_active`: Boolean - Status do tenant
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- document deve ser CNPJ válido
- domain deve ser único se preenchido
- settings deve conter configurações válidas (taxa_juros_max, periodo_cobranca, etc.)

**Business Rules**:
- Todos os outros modelos DEVEM herdar de BaseTenantModel
- Isolamento automático por tenant via middleware

---

### User Management

#### User
Usuário do sistema, vinculado a um tenant específico, com papéis e permissões definidas.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant) - Tenant ao qual pertence
- `email`: EmailField - Email único por tenant
- `first_name`: String(50)
- `last_name`: String(50)
- `password`: String(128) - Hash da senha
- `role`: ChoiceField - [ADMIN, MANAGER, CONSULTANT, COLLECTOR]
- `is_active`: Boolean
- `last_login`: DateTime
- `mfa_enabled`: Boolean - Multifactor authentication
- `mfa_secret`: String(32) - TOTP secret
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- email único dentro do mesmo tenant
- role deve ser um dos valores válidos
- password deve atender critérios de segurança

**State Transitions**:
- ACTIVE ↔ INACTIVE (admins podem ativar/desativar)
- MFA: DISABLED → ENABLED (irreversível por segurança)

#### Consultant
Especialização de usuário que representa consultores/vendedores, com controle de comissões.

**Fields**:
- `user`: OneToOneField(User) - Relacionamento 1:1 com User
- `commission_rate`: DecimalField(5,4) - Taxa de comissão (ex: 0.0250 = 2.5%)
- `commission_balance`: DecimalField(15,2) - Saldo atual de comissões
- `bank_account`: String(50) - Conta para recebimento
- `is_active_for_loans`: Boolean - Pode criar novos empréstimos

**Validations**:
- commission_rate entre 0 e 1
- commission_balance pode ser negativo (débitos)
- user.role deve ser CONSULTANT

---

### Customer Management

#### Customer
Cliente final que solicita empréstimos, com dados pessoais, documentos e histórico.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `document_type`: ChoiceField - [CPF, CNPJ]
- `document`: String(20) - CPF ou CNPJ (único por tenant)
- `name`: String(255) - Nome completo ou razão social
- `email`: EmailField
- `phone`: String(20)
- `birth_date`: DateField - Data de nascimento (pessoa física)
- `gender`: ChoiceField - [M, F, OTHER] (opcional)
- `profession`: String(100)
- `monthly_income`: DecimalField(15,2)
- `credit_score`: IntegerField - Score de crédito (0-1000)
- `score_last_updated`: DateTime
- `is_active`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- document único por tenant
- document deve ser CPF ou CNPJ válido conforme document_type
- credit_score entre 0 e 1000
- monthly_income deve ser positivo

**Business Rules**:
- Score atualizado automaticamente via integrações com bureaus
- Histórico completo de alterações via django-simple-history

#### Address
Endereços dos clientes, podendo ter múltiplos endereços por cliente.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `customer`: ForeignKey(Customer)
- `type`: ChoiceField - [RESIDENTIAL, COMMERCIAL, CORRESPONDENCE]
- `street`: String(255)
- `number`: String(20)
- `complement`: String(100) (opcional)
- `neighborhood`: String(100)
- `city`: String(100)
- `state`: String(2) - Código UF
- `zipcode`: String(10) - CEP
- `is_primary`: Boolean - Endereço principal
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- zipcode deve ser CEP válido (formato XXXXX-XXX)
- state deve ser UF válida
- Apenas um endereço primary=True por customer

---

### Loan Management

#### Loan
Empréstimo concedido, com valor principal, taxa de juros, parcelas e informações regulatórias.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `customer`: ForeignKey(Customer)
- `consultant`: ForeignKey(Consultant) - Consultor responsável
- `principal_amount`: DecimalField(15,2) - Valor principal
- `interest_rate`: DecimalField(5,4) - Taxa de juros mensal
- `installments_count`: IntegerField - Número de parcelas
- `iof_amount`: DecimalField(15,2) - Valor do IOF
- `cet_monthly`: DecimalField(7,4) - CET mensal
- `cet_yearly`: DecimalField(7,4) - CET anual
- `total_amount`: DecimalField(15,2) - Valor total com juros
- `contract_date`: DateField - Data do contrato
- `first_due_date`: DateField - Vencimento primeira parcela
- `status`: ChoiceField - [ANALYSIS, APPROVED, ACTIVE, FINISHED, COLLECTION, CANCELLED]
- `regret_deadline`: DateField - Prazo para arrependimento (7 dias)
- `notes`: TextField (opcional)
- `version`: IntegerField - Controle de concorrência otimista
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- principal_amount > 0
- interest_rate conforme Lei da Usura (configurável por tenant)
- installments_count entre 1 e 120
- regret_deadline = contract_date + 7 dias
- total_amount = principal_amount + juros + iof_amount

**State Transitions**:
- ANALYSIS → APPROVED → ACTIVE → FINISHED
- ANALYSIS → CANCELLED
- ACTIVE → COLLECTION (parcelas vencidas >5 dias)
- ACTIVE → CANCELLED (dentro do prazo de arrependimento)

**Business Rules**:
- Cálculos de IOF e CET automáticos conforme legislação
- Histórico completo via django-simple-history
- Controle de concorrência para edições simultâneas

#### Installment
Parcela individual do empréstimo, com valor, data de vencimento e status de pagamento.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `loan`: ForeignKey(Loan)
- `sequence`: IntegerField - Número sequencial da parcela
- `due_date`: DateField - Data de vencimento
- `principal_amount`: DecimalField(15,2) - Valor principal da parcela
- `interest_amount`: DecimalField(15,2) - Valor de juros
- `total_amount`: DecimalField(15,2) - Valor total da parcela
- `amount_paid`: DecimalField(15,2) - Valor já pago (default: 0)
- `payment_date`: DateField (opcional) - Data do último pagamento
- `late_fee`: DecimalField(15,2) - Multa por atraso (default: 0)
- `interest_penalty`: DecimalField(15,2) - Juros de mora (default: 0)
- `status`: ChoiceField - [PENDING, PAID, OVERDUE, PARTIALLY_PAID]
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- sequence único por loan
- total_amount = principal_amount + interest_amount
- amount_paid <= total_amount + late_fee + interest_penalty
- payment_date obrigatório se status = PAID

**State Transitions**:
- PENDING → PAID (pagamento total)
- PENDING → OVERDUE (vencimento sem pagamento)
- PENDING → PARTIALLY_PAID (pagamento parcial)
- PARTIALLY_PAID → PAID (complemento do pagamento)
- OVERDUE → PAID/PARTIALLY_PAID (pagamento em atraso)

**Business Rules**:
- late_fee e interest_penalty calculados automaticamente
- Status OVERDUE aplicado via job assíncrono diário
- Permite múltiplos pagamentos parciais

---

### Financial Management

#### BankAccount
Contas bancárias da empresa para controle de fluxo de caixa.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `bank_code`: String(10) - Código do banco
- `bank_name`: String(100) - Nome do banco
- `agency`: String(20) - Agência
- `account_number`: String(30) - Número da conta
- `account_type`: ChoiceField - [CHECKING, SAVINGS, INVESTMENT]
- `balance`: DecimalField(15,2) - Saldo atual
- `is_active`: Boolean
- `is_main`: Boolean - Conta principal
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- bank_code deve existir na tabela de bancos do Bacen
- Apenas uma conta com is_main=True por tenant
- account_number único por bank_code + agency

#### FinancialTransaction
Transações financeiras (receitas/despesas) com categorização e rastreamento.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `bank_account`: ForeignKey(BankAccount)
- `installment`: ForeignKey(Installment) (opcional) - Se relacionada a pagamento
- `type`: ChoiceField - [INCOME, EXPENSE]
- `category`: ForeignKey(PaymentCategory)
- `cost_center`: ForeignKey(CostCenter) (opcional)
- `supplier`: ForeignKey(Supplier) (opcional) - Para despesas
- `amount`: DecimalField(15,2)
- `description`: String(255)
- `reference_date`: DateField - Data de referência
- `due_date`: DateField (opcional) - Para despesas futuras
- `payment_date`: DateField (opcional) - Data de efetivação
- `status`: ChoiceField - [PENDING, PAID, CANCELLED]
- `document_number`: String(50) (opcional) - NF, recibo, etc.
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- amount > 0
- payment_date obrigatório se status = PAID
- supplier obrigatório se type = EXPENSE
- installment permitido apenas se type = INCOME

**Business Rules**:
- Atualiza balance da BankAccount automaticamente
- Histórico completo via django-simple-history

#### PaymentCategory
Categorias para classificação de pagamentos e despesas.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `name`: String(100)
- `type`: ChoiceField - [INCOME, EXPENSE, BOTH]
- `is_active`: Boolean
- `created_at`: DateTime

**Validations**:
- name único por tenant
- type determina onde a categoria pode ser usada

#### CostCenter
Centros de custo para controle gerencial.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `code`: String(20) - Código interno
- `name`: String(100)
- `description`: TextField (opcional)
- `is_active`: Boolean
- `created_at`: DateTime

**Validations**:
- code único por tenant

#### Supplier
Fornecedores para registro de despesas operacionais.

**Fields**:
- `id`: UUID (Primary Key)
- `tenant`: ForeignKey(Tenant)
- `document_type`: ChoiceField - [CPF, CNPJ]
- `document`: String(20) - CPF ou CNPJ
- `name`: String(255) - Nome/Razão social
- `email`: EmailField (opcional)
- `phone`: String(20) (opcional)
- `is_active`: Boolean
- `created_at`: DateTime
- `updated_at`: DateTime

**Validations**:
- document único por tenant
- document válido conforme document_type

---

## Relationships

### Primary Relationships
```
Tenant (1) ←→ (N) User
Tenant (1) ←→ (N) Customer
Tenant (1) ←→ (N) Loan
Customer (1) ←→ (N) Address
Customer (1) ←→ (N) Loan
User (1) ←→ (1) Consultant [opcional]
Consultant (1) ←→ (N) Loan
Loan (1) ←→ (N) Installment
BankAccount (1) ←→ (N) FinancialTransaction
Installment (1) ←→ (0..N) FinancialTransaction
```

### Secondary Relationships
```
PaymentCategory (1) ←→ (N) FinancialTransaction
CostCenter (1) ←→ (N) FinancialTransaction
Supplier (1) ←→ (N) FinancialTransaction
```

## Indexes

### Performance Indexes (tenant-first obrigatório)
```sql
-- Multi-tenancy indexes
CREATE INDEX idx_user_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_customer_tenant_document ON customers(tenant_id, document);
CREATE INDEX idx_loan_tenant_status ON loans(tenant_id, status);
CREATE INDEX idx_installment_tenant_due_date ON installments(tenant_id, due_date);
CREATE INDEX idx_financial_transaction_tenant_date ON financial_transactions(tenant_id, reference_date);

-- Business logic indexes
CREATE INDEX idx_loan_consultant_status ON loans(consultant_id, status);
CREATE INDEX idx_installment_loan_sequence ON installments(loan_id, sequence);
CREATE INDEX idx_address_customer_primary ON addresses(customer_id, is_primary);
```

## Data Validation Rules

### Financial Calculations
- IOF: Calculado conforme tabela Receita Federal
- CET: Fórmula Banco Central (Resolução 4.292/2013)
- Juros de mora: Taxa Selic + 1% ao mês (configurável)
- Multa atraso: 2% sobre valor da parcela (configurável)

### Business Constraints
- Empréstimo só pode ser editado antes do prazo de arrependimento
- Parcelas não podem ser removidas, apenas ajustadas
- Cliente pode ter múltiplos empréstimos simultâneos
- Consultor recebe comissão apenas em empréstimos ACTIVE

### Regulatory Compliance
- Lei da Usura: Taxa máxima configurável por tenant
- LGPD: Campos PII criptografados, auditoria preservada
- Período arrependimento: 7 dias corridos conforme CDC
- Retenção dados: 10 anos para auditoria fiscal

---

## Version Control & Auditing

Entidades com histórico obrigatório (django-simple-history):
- `User` - Alterações de permissões e dados
- `Customer` - Mudanças em dados pessoais
- `Loan` - Modificações em contratos
- `Installment` - Ajustes em parcelas
- `FinancialTransaction` - Todas as movimentações

**Metadados de auditoria**:
- `history_date`: Timestamp da alteração
- `history_user`: Usuário responsável
- `history_type`: CREATE, UPDATE, DELETE
- `history_change_reason`: Motivo da alteração

---

**Next Step**: Gerar contratos de API baseados neste modelo de dados