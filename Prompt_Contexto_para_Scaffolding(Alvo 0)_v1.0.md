# AGV Prompt: Contexto para Scaffolding (Alvo 0)

## Tarefa Principal

Você é um assistente especializado do Método AGV. Sua tarefa é analisar o `@Blueprint_Mestre` e identificar **os números de todas as seções** que são relevantes para a execução do **"Alvo 0: Setup do Projeto Profissional"** pelo agente `F4-Scaffolder`.

## Fonte da Verdade

- **Blueprint Mestre:**

# **Blueprint Arquitetural: IABANK v1.0**

**Versão do Documento:** 1.0.0
**Data:** 2025-08-23
**Autores:** AGV Method

---

## 1. Visão Geral da Arquitetura

A arquitetura do `IABANK` será baseada em uma abordagem de **Monólito Modular em Camadas**. Esta escolha visa equilibrar a velocidade de desenvolvimento inicial com a manutenibilidade e escalabilidade futuras.

- **Backend:** Um único serviço Django que expõe uma API RESTful. Internamente, o código será organizado em "apps" Django que representam os domínios de negócio (ex: `loans`, `customers`, `finance`), promovendo alta coesão e baixo acoplamento entre os módulos. A arquitetura interna seguirá o padrão de Camadas (Apresentação, Aplicação, Domínio, Infraestrutura) para uma clara separação de responsabilidades.
- **Frontend:** Uma Single Page Application (SPA) desenvolvida em React/TypeScript, que consome a API do backend. Ela será responsável por toda a renderização e experiência do usuário.
- **Comunicação:** A comunicação entre Frontend e Backend será síncrona, via API RESTful (JSON sobre HTTPS). Tarefas assíncronas (como envio de e-mails) serão delegadas ao Celery com um broker Redis.
- **Multi-tenancy:** A arquitetura será multi-tenant desde o início, utilizando uma estratégia de **isolamento de dados por chave estrangeira (`tenant_id`)**. Todos os dados de negócio serão particionados por Tenant no nível do banco de dados, e a camada de acesso a dados garantirá que nenhuma query possa vazar dados entre tenants.

**Organização do Código-Fonte:** Será utilizado um **monorepo**, gerenciado com ferramentas de workspace se necessário. Esta abordagem simplifica o desenvolvimento e o CI/CD, garantindo que o contrato entre a API do backend e o consumidor do frontend permaneça sempre sincronizado no mesmo commit. O repositório conterá duas pastas principais na raiz: `backend/` e `frontend/`.

## 2. Diagramas da Arquitetura (Modelo C4)

### 2.1. Nível 1: Diagrama de Contexto do Sistema (C1)

Este diagrama mostra o sistema `IABANK` e suas interações com usuários e sistemas externos.

```mermaid
graph TD
    subgraph "Ecossistema IABANK"
        style IABANK fill:#f9f,stroke:#333,stroke-width:4px
        IABANK[("IABANK SaaS Platform")]
    end

    Admin[Gestor / Administrador] -- "Gerencia a plataforma via" --> WebApp
    Consultant[Consultor / Cobrador] -- "Executa operações via" --> WebApp

    subgraph "Navegador Web"
        WebApp[Painel Web (React SPA)]
    end

    WebApp -- "Usa (HTTPS/REST API)" --> IABANK

    IABANK -- "Envia e-mails via" --> SMTP[Sistema de E-mail (SMTP)]
    IABANK -.->|Futuro: Consulta dados de crédito| CreditBureau[Bureaus de Crédito]
    IABANK -.->|Futuro: Inicia transações| OpenFinance[Plataformas Bancárias (Open Finance, Pix)]

    style CreditBureau fill:#ccc,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style OpenFinance fill:#ccc,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
```

### 2.2. Nível 2: Diagrama de Containers (C2)

Este diagrama detalha os principais blocos tecnológicos que compõem a plataforma `IABANK`.

```mermaid
graph TD
    User[Usuário (Gestor, Consultor)] -- "Acessa via HTTPS" --> WebApp[Frontend SPA (React + TypeScript)]

    subgraph "Infraestrutura Cloud (Containerizada com Docker)"
        WebApp -- "Consome API REST (HTTPS)" --> Nginx[Nginx Reverse Proxy]
        Nginx -- "/api/*" --> BackendAPI[Backend API (Python/Django)]
        Nginx -- "/*" --> WebApp

        BackendAPI -- "Lê/Escreve dados (TCP/IP)" --> Database[(PostgreSQL DB)]
        BackendAPI -- "Enfileira tarefas" --> Queue[Fila de Tarefas (Redis)]
        Worker[Worker (Celery)] -- "Processa tarefas" --> Queue
        Worker -- "Lê/Escreve dados" --> Database
    end
```

### 2.3. Nível 3: Diagrama de Componentes (C3) - Container Backend API

Este diagrama detalha a organização interna do container `Backend API (Django)`.

```mermaid
graph TD
    subgraph "Container: Backend API (Django)"
        direction LR
        API[Camada de Apresentação (DRF Views/Serializers)]
        Services[Camada de Aplicação (Services)]
        Domain[Camada de Domínio (Django Models)]
        Infra[Camada de Infraestrutura (ORM, Caching)]

        API -- "Utiliza" --> Services
        Services -- "Orquestra" --> Domain
        Services -- "Acessa via" --> Infra
        Infra -- "Persiste" --> Domain
    end

    Nginx -- "Encaminha requisições HTTP" --> API
    Infra -- "Conecta-se a" --> Database[(PostgreSQL)]
    Infra -- "Conecta-se a" --> Cache[(Redis)]
```

## 3. Descrição dos Componentes, Interfaces e Modelos de Domínio

### 3.1. Consistência dos Modelos de Dados (SSOT do Domínio - Backend)

Esta seção é a Fonte Única da Verdade para todas as estruturas de dados do projeto. Todos os modelos são definidos como `models.Model` do Django.

**Tecnologia Chave:** Modelos Django.

#### **3.1.1. Core / Multi-Tenancy (`iabank.core`)**

```python
# iabank/core/models.py
from django.db import models
from django.conf import settings
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, verbose_name="Nome da Empresa")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TenantAwareModel(models.Model):
    """Modelo abstrato para garantir isolamento de dados por tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class AuditableModel(models.Model):
    """Modelo abstrato para auditoria de criação/modificação."""
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_updated', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True
```

#### **3.1.2. Módulo de Usuários e Administração (`iabank.users`, `iabank.administration`)**

```python
# iabank/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from iabank.core.models import Tenant

class User(AbstractUser):
    # Adicionar campos customizados se necessário no futuro
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    # Role/Profile pode ser um campo aqui ou gerenciado por Grupos do Django

# iabank/administration/models.py
from iabank.core.models import TenantAwareModel, AuditableModel

class BankAccount(TenantAwareModel, AuditableModel):
    name = models.CharField(max_length=100, verbose_name="Nome da Conta")
    bank_name = models.CharField(max_length=100, verbose_name="Nome do Banco")
    agency = models.CharField(max_length=20, verbose_name="Agência")
    account_number = models.CharField(max_length=30, verbose_name="Número da Conta")
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Saldo Inicial")

class IOFParameter(TenantAwareModel, AuditableModel):
    daily_rate = models.DecimalField(max_digits=10, decimal_places=5, verbose_name="Alíquota Diária (%)")
    additional_rate = models.DecimalField(max_digits=10, decimal_places=5, verbose_name="Alíquota Adicional (%)")
    is_active = models.BooleanField(default=True)

class Holiday(TenantAwareModel):
    date = models.DateField(unique=True, verbose_name="Data")
    description = models.CharField(max_length=255, verbose_name="Descrição")

class AuditLog(models.Model):
    # Note: Pode não precisar ser TenantAware se logs forem centralizados
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255, verbose_name="Ação")
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(verbose_name="Detalhes")
```

#### **3.1.3. Módulo Operacional (`iabank.loans`, `iabank.customers`)**

```python
# iabank/customers/models.py
from django.db import models
from iabank.core.models import TenantAwareModel, AuditableModel

class Customer(TenantAwareModel, AuditableModel):
    full_name = models.CharField(max_length=255, verbose_name="Nome Completo")
    document_number = models.CharField(max_length=18, unique=True, verbose_name="CPF/CNPJ")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    # Endereço
    zip_code = models.CharField(max_length=9, verbose_name="CEP")
    street = models.CharField(max_length=255, verbose_name="Rua")
    number = models.CharField(max_length=20, verbose_name="Número")
    complement = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="UF")
    # Contato
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    # Info Financeira
    income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Renda")
    profession = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profissão")

# iabank/loans/models.py
from django.db import models
from iabank.core.models import TenantAwareModel, AuditableModel
from iabank.customers.models import Customer
from iabank.users.models import User # Supondo que consultores são Users ou um modelo relacionado

class Consultant(TenantAwareModel, AuditableModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="consultant_profile")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Saldo")
    # Outras configurações de app viriam aqui

class PromissoryCreditor(TenantAwareModel, AuditableModel):
    name = models.CharField(max_length=255, verbose_name="Nome")
    document_number = models.CharField(max_length=18, verbose_name="CPF/CNPJ")
    address = models.CharField(max_length=255, verbose_name="Endereço")

class Loan(TenantAwareModel, AuditableModel):
    class LoanStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'Em Andamento'
        PAID_OFF = 'PAID_OFF', 'Finalizado'
        IN_COLLECTION = 'IN_COLLECTION', 'Em Cobrança'
        CANCELED = 'CANCELED', 'Cancelado'

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="loans", verbose_name="Cliente")
    consultant = models.ForeignKey(Consultant, on_delete=models.PROTECT, related_name="loans", verbose_name="Consultor")
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Principal")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taxa de Juros (% a.m.)")
    num_installments = models.PositiveIntegerField(verbose_name="Nº de Parcelas")
    first_installment_date = models.DateField(verbose_name="Data da 1ª Parcela")
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.IN_PROGRESS, verbose_name="Status")
    contract_date = models.DateField(auto_now_add=True, verbose_name="Data do Contrato")

class Installment(TenantAwareModel):
    class InstallmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Vencida'

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="installments", verbose_name="Empréstimo")
    installment_number = models.PositiveIntegerField(verbose_name="Nº da Parcela")
    due_date = models.DateField(verbose_name="Data de Vencimento")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    paid_date = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Valor Pago")
    status = models.CharField(max_length=20, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING)

class CollectionHistory(TenantAwareModel, AuditableModel):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="collection_history")
    interaction_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(verbose_name="Notas da Interação")
    next_action_date = models.DateField(null=True, blank=True, verbose_name="Data da Próxima Ação")
```

#### **3.1.4. Módulo Financeiro e Cadastros Gerais (`iabank.finance`, `iabank.registrations`)**

```python
# iabank/registrations/models.py
from iabank.core.models import TenantAwareModel, AuditableModel

class Supplier(TenantAwareModel, AuditableModel):
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=18, blank=True, null=True)

class PaymentCategory(TenantAwareModel, AuditableModel):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=[('INCOME', 'Receita'), ('EXPENSE', 'Despesa')])

class CostCenter(TenantAwareModel, AuditableModel):
    name = models.CharField(max_length=100)

class PaymentMethod(TenantAwareModel, AuditableModel):
    name = models.CharField(max_length=100)

# iabank/finance/models.py
from django.db import models
from iabank.core.models import TenantAwareModel, AuditableModel
from iabank.registrations.models import Supplier, PaymentCategory, CostCenter
from iabank.administration.models import BankAccount

class FinancialTransaction(TenantAwareModel, AuditableModel):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'A Receber'
        EXPENSE = 'EXPENSE', 'A Pagar'

    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Vencido'

    description = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)

    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)
    category = models.ForeignKey(PaymentCategory, on_delete=models.PROTECT)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    # Relação polimórfica para vincular à origem (ex: Parcela de Empréstimo)
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    # object_id = models.PositiveIntegerField(null=True)
    # source_object = GenericForeignKey('content_type', 'object_id')
```

### 3.1.5. Detalhamento dos DTOs e Casos de Uso

**Tecnologia Chave:** `pydantic.BaseModel`

Estes DTOs definem os contratos de dados para a comunicação entre a camada de serviço e a API.

```python
# iabank/customers/dtos.py
import pydantic
from datetime import date

class CustomerCreateDTO(pydantic.BaseModel):
    full_name: str
    document_number: str
    zip_code: str
    street: str
    number: str
    neighborhood: str
    city: str
    state: str
    phone: str | None = None
    email: pydantic.EmailStr | None = None

# iabank/loans/dtos.py
import pydantic
from datetime import date
from decimal import Decimal

class LoanCreateDTO(pydantic.BaseModel):
    customer_id: int
    consultant_id: int
    principal_amount: Decimal
    interest_rate: Decimal
    num_installments: int
    first_installment_date: date

class LoanListDTO(pydantic.BaseModel):
    id: int
    customer_name: str
    principal_amount: Decimal
    status: str
    contract_date: date
    num_installments: int

    class Config:
        orm_mode = True # Permite mapeamento direto de modelos Django

# iabank/finance/dtos.py
class FinancialTransactionCreateDTO(pydantic.BaseModel):
    description: str
    type: str  # 'INCOME' or 'EXPENSE'
    amount: Decimal
    due_date: date
    bank_account_id: int
    category_id: int
    cost_center_id: int | None = None
    supplier_id: int | None = None
```

### 3.2. Camada de Apresentação (UI) - Contratos de Dados (ViewModels)

**Tecnologia Chave:** TypeScript

Estes são os contratos de dados que o Frontend espera receber da API para renderizar as telas.

#### 3.2.1. ViewModel: `LoanListItemViewModel` (Tela de Empréstimos)

Derivado do `LoanListDTO` do backend, formatado para exibição.

```typescript
// src/features/loans/types.ts
export interface StatusBadge {
  label: string; // 'Em Andamento', 'Finalizado', 'Em Cobrança'
  color: "yellow" | "green" | "red" | "gray";
}

export interface LoanListItemViewModel {
  id: number;
  customerName: string;
  principalAmountFormatted: string; // Ex: "R$ 5.000,00"
  status: StatusBadge;
  contractDateFormatted: string; // Ex: "15/08/2023"
  installmentsSummary: string; // Ex: "12 Parcelas"
}
```

#### 3.2.2. ViewModel: `CustomerListItemViewModel` (Tela de Clientes)

```typescript
// src/features/customers/types.ts
export interface CustomerListItemViewModel {
  id: number;
  fullName: string;
  documentNumberFormatted: string; // Ex: "123.456.789-00"
  cityState: string; // Ex: "São Paulo - SP"
  phone: string;
  activeLoansCount: number;
}
```

#### 3.2.3. ViewModel: `FinancialTransactionListItemViewModel` (Telas de Contas a Pagar/Receber)

```typescript
// src/features/finance/types.ts
export interface StatusBadge {
  // Reutilizável
  label: string;
  color: "yellow" | "green" | "red" | "gray";
}

export interface FinancialTransactionListItemViewModel {
  id: number;
  description: string;
  categoryName: string;
  amountFormatted: string; // Ex: "R$ 250,00"
  dueDateFormatted: string; // Ex: "30/10/2023"
  status: StatusBadge;
}
```

## 4. Descrição Detalhada da Arquitetura Frontend

- **Padrão Arquitetural:** Será adotada uma arquitetura **Feature-Sliced Design**. O código é organizado por funcionalidades de negócio, promovendo alta coesão e baixo acoplamento. Cada _feature_ é autocontida, com seus próprios componentes de UI, lógica de estado e chamadas de API.

- **Estrutura de Diretórios Proposta (`src/`):**

  ```
  src/
  |-- app/                # Configuração global: providers, router, store, styles
  |-- pages/              # Componentes de página, que compõem layouts a partir das features
  |-- features/           # Módulos de negócio (ex: loan-creation-wizard, loan-list)
  |   |-- loan-list/
  |   |   |-- api/        # Hooks e funções para chamadas à API (usando TanStack Query)
  |   |   |-- components/ # Componentes de UI específicos da feature
  |   |   |-- model/      # Lógica, estado e tipos da feature
  |   |   |-- index.ts    # Ponto de entrada público do módulo
  |-- entities/           # Entidades de negócio (ex: CustomerCard, LoanStatusBadge)
  |-- shared/             # Código reutilizável e agnóstico de negócio
  |   |-- api/            # Configuração do cliente Axios/Fetch, interceptors
  |   |-- lib/            # Funções utilitárias (formatters, validators)
  |   |-- ui/             # Biblioteca de componentes de UI (Button, Input, Table)
  |   |-- assets/         # Imagens, fontes, etc.
  ```

- **Estratégia de Gerenciamento de Estado:**

  - **Estado do Servidor:** Gerenciado exclusivamente pelo `TanStack Query (React Query)`. Ele será a fonte da verdade para todos os dados assíncronos vindos da API, tratando de caching, revalidação, e estados de loading/error.
  - **Estado Global do Cliente:** Gerenciado pelo `Zustand`. Usado para estado síncrono e global, como informações do usuário autenticado, tema da UI, ou estado de um menu lateral. Sua simplicidade e API baseada em hooks são ideais.
  - **Estado Local do Componente:** Utilizará os hooks nativos do React (`useState`, `useReducer`) para estado que não precisa ser compartilhado, como o controle de inputs em um formulário.

- **Fluxo de Dados:**
  1.  O usuário interage com um componente em uma `pages/`.
  2.  A página invoca uma ação de um módulo em `features/`.
  3.  A feature utiliza um hook do `TanStack Query` (de `features/.../api/`) para buscar ou modificar dados.
  4.  O hook faz a chamada HTTP através do cliente configurado em `shared/api/`.
  5.  O `TanStack Query` gerencia o cache e o estado da requisição.
  6.  Componentes (`features/`, `entities/`, `shared/ui/`) que usam o hook reagem às mudanças de estado e re-renderizam para exibir os novos dados, feedback de loading ou erros.

## 5. Definição das Interfaces Principais

Os contratos de dados (DTOs e ViewModels) já foram definidos. As interfaces de serviço no backend seguirão um padrão claro.

**Exemplo: Interface para o Serviço de Criação de Empréstimos**

- **Componente:** `iabank.loans.services.LoanCreationService`
- **Dependências Diretas:**
  - `iabank.loans.models.Loan`
  - `iabank.loans.models.Installment`
  - `iabank.customers.models.Customer`
  - `iabank.loans.dtos.LoanCreateDTO`
- **Interface (Contrato Funcional):**

```python
# iabank/loans/services.py

class LoanCreationService:
    def __init__(self, tenant: Tenant, user: User):
        """
        Inicializa o serviço com o contexto de tenant e usuário necessários.
        """
        self.tenant = tenant
        self.user = user

    def create_loan(self, dto: LoanCreateDTO) -> Loan:
        """
        Orquestra a criação de um novo empréstimo.
        - Valida os dados do DTO.
        - Busca o cliente e o consultor.
        - Cria o objeto Loan.
        - Gera o plano de parcelas (Installments).
        - Retorna a instância do Empréstimo criado.
        """
        # ... lógica de negócio ...
```

## 6. Gerenciamento de Dados

- **Persistência:** Os dados serão persistidos no PostgreSQL através do ORM do Django. A lógica de acesso a dados será encapsulada dentro dos `managers` dos modelos Django ou, para lógica mais complexa, em uma camada de Repositório (se necessário).
- **Gerenciamento de Schema:** As migrações de banco de dados serão gerenciadas pelo sistema nativo do Django (`makemigrations`, `migrate`). Cada mudança no schema será um novo arquivo de migração versionado no controle de código.
- **Seed de Dados:** Para o ambiente de desenvolvimento, serão criados `management commands` do Django para popular o banco com dados fictícios (tenants, usuários, clientes, empréstimos). A biblioteca `factory-boy` será utilizada para gerar esses dados de forma consistente e realista.

## 7. Estrutura de Diretórios Proposta

```
iabank-monorepo/
├── .github/
│   └── workflows/
│       └── main.yml        # Pipeline de CI/CD
├── backend/
│   ├── src/
│   │   ├── iabank/
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   ├── wsgi.py
│   │   │   ├── asgi.py
│   │   │   ├── core/         # App para Tenant, modelos base, etc.
│   │   │   ├── users/        # App para Usuários, autenticação
│   │   │   ├── customers/    # App para Clientes
│   │   │   │   ├── models.py
│   │   │   │   ├── services.py
│   │   │   │   ├── views.py
│   │   │   │   ├── serializers.py
│   │   │   │   └── tests/
│   │   │   │       └── test_customers_models.py
│   │   │   │       └── test_customers_api.py
│   │   │   ├── loans/        # App para Empréstimos
│   │   │   └── finance/      # App para Financeiro
│   │   └── manage.py
│   ├── tests/
│   │   └── integration/
│   │       └── test_api_full_loan_lifecycle.py
│   └── pyproject.toml
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── features/
│   │   ├── entities/
│   │   └── shared/
│   ├── package.json
│   └── tsconfig.json
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

## 8. Arquivo `.gitignore` Proposto

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
*.pot
*.pyo
*.log
local_settings.py
db.sqlite3
.env
.venv/
venv/
ENV/
env/
env.bak/
venv.bak/

# Node.js
node_modules/
dist/
.npm
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.env.local
.env.development.local
.env.test.local
.env.production.local
.DS_Store

# IDEs
.idea/
.vscode/
*.swp
*~

# Docker
docker-compose.override.yml
```

## 9. Arquivo `README.md` Proposto

(Conteúdo completo gerado abaixo)

## 10. Arquivo `LICENSE` Proposto

(Texto completo da licença MIT gerado abaixo)

## 11. Arquivo `CONTRIBUTING.md` Proposto

(Template de conteúdo gerado abaixo)

## 12. Estrutura do `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project structure based on AGV Blueprint.

## [0.1.0] - YYYY-MM-DD

### Added

- First release features.
```

## 13. Estratégia de Configuração e Ambientes

- **Tecnologia:** `django-environ`.
- **Desenvolvimento:** As configurações serão lidas de um arquivo `.env` na raiz do projeto `backend/`, que **não** será versionado.
- **Homologação/Produção:** As configurações serão injetadas exclusivamente via **variáveis de ambiente** no container Docker. Isso segue a prática recomendada do "The Twelve-Factor App".
- **Segredos:** Chaves de API, senhas e outros segredos nunca serão codificados. Eles serão gerenciados via variáveis de ambiente.

## 14. Estratégia de Observabilidade Completa

- **Logging Estruturado:** Todos os logs da aplicação Django serão emitidos em formato JSON. A biblioteca `python-json-logger` será configurada para enriquecer os logs com contexto da requisição (ID do usuário, ID do tenant, trace ID). Níveis de log serão `INFO` para produção e `DEBUG` para desenvolvimento.
- **Métricas de Negócio:** Serão expostas métricas via um endpoint `/metrics` (usando `django-prometheus`). Métricas chave:
  - `iabank_loans_created_total`: Contador de novos empréstimos.
  - `iabank_loan_principal_amount_total`: Soma do valor principal de novos empréstimos.
  - `iabank_active_users`: Gauge de usuários ativos.
  - `iabank_api_request_duration_seconds`: Histograma da latência da API, com labels por endpoint.
- **Distributed Tracing:** Embora seja um monólito, a base para tracing será estabelecida com `OpenTelemetry`. Cada requisição receberá um `trace_id` único, que será incluído nos logs. Isso facilitará a depuração e a futura migração para microsserviços.
- **Health Checks e SLIs/SLOs:**
  - Um endpoint `/health/` será criado, verificando a conectividade com o banco de dados e o Redis.
  - **SLI:** Disponibilidade da API (taxa de sucesso de respostas não-5xx). Latência do endpoint de criação de empréstimo.
  - **SLO:** 99.9% de disponibilidade mensal. 95% das criações de empréstimo em < 300ms.
- **Alerting Inteligente:** Alertas serão configurados em uma ferramenta externa (ex: Grafana, Sentry, Datadog) com base em anomalias (ex: aumento súbito na taxa de erros 5xx) e violações de SLO, não apenas em thresholds fixos.

## 15. Estratégia de Testes Detalhada

- **Ferramentas:** `pytest`, `pytest-django`, `factory-boy`, `DRF APIClient`.
- **Estrutura e Nomenclatura:**
  - **Testes Unitários:** Residem em `<app_name>/tests/` (ex: `backend/src/iabank/loans/tests/`). Eles testam a lógica de um único módulo isoladamente (ex: um método em um `service`). A nomenclatura será `test_<nome_do_app>_<nome_do_modulo>.py` (ex: `test_loans_services.py`, `test_customers_models.py`).
  - **Testes de Integração:** Residem em `backend/tests/integration/`. Eles testam a colaboração entre múltiplos componentes, como o fluxo completo de uma requisição API até o banco de dados. A nomenclatura será `test_api_<nome_da_funcionalidade>.py` (ex: `test_api_loan_creation.py`).
- **Padrões de Teste de Integração:**
  - **Uso de Factories:** `factory-boy` será usado obrigatoriamente para criar dados de teste (Tenants, Users, Customers), garantindo consistência.
  - **Simulação de Autenticação:** O `APIClient` do DRF será usado com `force_authenticate(user=self.user)` para simular um usuário autenticado, evitando testar o fluxo de login em cada endpoint protegido.
  - **Escopo de Teste:** Um teste de integração para a API de empréstimos assume que a criação de clientes e a autenticação funcionam (já cobertos por seus próprios testes). O foco é validar o endpoint de empréstimo (validação, criação, resposta correta). O isolamento de tenant será testado em uma suíte de testes de integração dedicada à segurança de acesso.

## 16. Estratégia de CI/CD

- **Ferramenta:** GitHub Actions.
- **Gatilhos:** A pipeline será executada em cada `push` para a branch `main` e em cada abertura/atualização de `Pull Request`.
- **Estágios do Pipeline (`.github/workflows/main.yml`):**
  1.  **Setup:** Checkout do código e configuração do ambiente (Python, Node.js).
  2.  **Lint & Format:** Executa `ruff` e `black` no backend, e `eslint` e `prettier` no frontend para garantir a qualidade do código.
  3.  **Backend Tests:** Instala dependências Python, sobe serviços (DB, Redis) e executa a suíte de testes com `pytest`, gerando um relatório de cobertura.
  4.  **Frontend Tests:** Instala dependências Node, executa testes unitários/componentes.
  5.  **Build:** Se os testes passarem, constrói as imagens Docker para o backend e o frontend usando `multi-stage builds`.
  6.  **Push:** Envia as imagens para um registro de contêineres (ex: Docker Hub, GitHub Container Registry).
  7.  **Deploy (manual/automático):** Em um `push` para `main`, um job (que pode ser de acionamento manual) se conectará ao ambiente de produção e atualizará os serviços com as novas imagens.

## 17. Estratégia de Versionamento da API

A API será versionada via URL para garantir clareza e evitar quebras de contrato com clientes futuros.

- **Formato:** `https://api.iabank.com/api/v1/...`
- **Implementação:** Em Django, isso será feito usando `namespaces` no `urls.py`. Cada versão da API terá seu próprio conjunto de URLs e, se necessário, Serializers.

## 18. Padrão de Resposta da API e Tratamento de Erros

Um formato de resposta JSON consistente será usado para todos os endpoints.

- **Sucesso (2xx):**
  ```json
  {
    "status": "success",
    "data": { ... } // Objeto ou array de objetos
  }
  ```
- **Erro de Cliente (4xx):**
  ```json
  {
    "status": "fail",
    "data": {
      "field_name": ["Error message 1.", "Error message 2."]
    }
  }
  ```
- **Erro de Servidor (5xx) ou Erro Genérico:**
  ```json
  {
    "status": "error",
    "message": "An unexpected error occurred."
  }
  ```
- **Implementação:** Um `exception handler` customizado do DRF será implementado para capturar todas as exceções e formatá-las nesta estrutura padrão.

## 19. Estratégia de Segurança Abrangente

- **Threat Modeling Básico:**
  - **Ameaça:** Acesso não autorizado a dados de um tenant por outro.
    - **Mitigação:** Validação rigorosa do `tenant_id` em toda query na camada de acesso a dados (manager customizado). Testes de integração específicos para garantir o isolamento.
  - **Ameaça:** Injeção de SQL.
    - **Mitigação:** Uso exclusivo do ORM do Django, que parametriza todas as queries.
  - **Ameaça:** Cross-Site Scripting (XSS).
    - **Mitigação:** Uso de React, que escapa dados por padrão. Configuração de cabeçalhos de segurança HTTP (CSP, X-Content-Type-Options).
- **Estratégia de Secrets Management:** Em produção, os segredos serão gerenciados por um serviço de nuvem (ex: AWS Secrets Manager, GCP Secret Manager) ou injetados como variáveis de ambiente em um ambiente seguro. Nunca serão armazenados em arquivos `.env` em produção.
- **Compliance Framework (LGPD):**
  - **Auditoria:** O `AuditLog` registrará todas as ações críticas.
  - **RBAC:** O sistema de Grupos e Permissões do Django será usado para implementar controle de acesso granular.
  - **Criptografia:** HTTPS obrigatório (trânsito). Dados sensíveis em repouso (se houver, como documentos) serão criptografados.
- **Security by Design:**
  - **Validação de Entrada:** DRF Serializers e Pydantic DTOs no backend; `Zod` no frontend.
  - **Menor Privilégio:** Usuários terão o mínimo de permissões necessárias para suas funções.
  - **Dependências:** Scans de vulnerabilidade de dependências (ex: `pip-audit`, `npm audit`) serão parte do pipeline de CI.

## 20. Justificativas e Trade-offs

- **Monólito vs. Microsserviços:** A escolha do monólito modular é intencional para a fase inicial do projeto.
  - **Justificativa:** Reduz a complexidade operacional, acelera o desenvolvimento e facilita transações ACID. A modularização interna prepara o terreno para uma futura extração de microsserviços quando a complexidade do domínio justificar.
  - **Trade-off:** Menor escalabilidade granular e maior acoplamento de implantação em comparação com microsserviços.
- **Monorepo vs. Multi-repo:**
  - **Justificativa:** Simplifica a gestão de dependências e garante a consistência atômica entre as mudanças de API e do frontend.
  - **Trade-off:** A pipeline de CI pode se tornar mais lenta com o tempo, pois precisa verificar ambas as partes do projeto.

## 21. Exemplo de Bootstrapping/Inicialização

```python
# iabank/loans/views.py (Conceitual)
from rest_framework.views import APIView
from rest_framework.response import Response
from .services import LoanCreationService
from .dtos import LoanCreateDTO

class LoanCreateAPIView(APIView):
    # permission_classes = [IsAuthenticated, HasLoanCreationPermission]

    def post(self, request, *args, **kwargs):
        # O tenant e o usuário vêm do contexto da requisição (middleware)
        current_tenant = request.tenant
        current_user = request.user

        # 1. Validação do payload da requisição
        dto = LoanCreateDTO(**request.data)

        # 2. Instanciação do serviço com suas dependências (configuração via __init__)
        service = LoanCreationService(tenant=current_tenant, user=current_user)

        # 3. Execução da lógica de negócio
        try:
            new_loan = service.create_loan(dto)
            # ... serializar a resposta ...
            return Response({"status": "success", "data": {"id": new_loan.id}})
        except Exception as e:
            # ... tratar exceção ...
            return Response({"status": "error", "message": str(e)}, status=400)
```

## 22. Estratégia de Evolução do Blueprint

- **Versionamento Semântico:** Este documento seguirá o SemVer (v1.0.0). Mudanças que não quebram a arquitetura (ex: adicionar um novo módulo) incrementam a versão menor (v1.1.0). Mudanças que quebram a arquitetura (ex: mudar de monólito para microsserviços) incrementam a versão maior (v2.0.0).
- **Processo de Evolução:** Mudanças significativas serão propostas através de um "Architecture Decision Record" (ADR). Um ADR é um documento curto que descreve o contexto, a decisão e as consequências de uma mudança arquitetural. Os ADRs serão armazenados em uma pasta `docs/adr/` no repositório.
- **Compatibilidade e Deprecação:** Quando uma interface de API (ex: v1) for substituída, ela será mantida por um período definido e marcada como `deprecated` na documentação.

## 23. Métricas de Qualidade e Quality Gates

- **Cobertura de Código:** Meta mínima de **85%** de cobertura de testes para o código do backend, medida com `pytest-cov`.
- **Complexidade Ciclomática:** Nenhuma função/método deve exceder uma complexidade de **10**, medida com `ruff`.
- **Quality Gates Automatizados (no Pull Request):**
  1.  Pipeline de CI deve passar (lint, testes).
  2.  Cobertura de testes não pode diminuir.
  3.  Scan de vulnerabilidades (`pip-audit`) não pode encontrar vulnerabilidades de severidade `HIGH` ou `CRITICAL`.
  4.  Análise de código estático (`ruff`) não pode reportar erros.

## 24. Análise de Riscos e Plano de Mitigação

| Categoria       | Risco Identificado                                                                                            | Probabilidade (1-5) | Impacto (1-5) | Score (P×I) | Estratégia de Mitigação                                                                                                                                                                        |
| :-------------- | :------------------------------------------------------------------------------------------------------------ | :-----------------: | :-----------: | :---------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Segurança**   | **Violação de dados (Data Breach)** resultando em vazamento de informações financeiras sensíveis.             |          3          |       5       |   **15**    | Implementar defesa em profundidade: RBAC granular, criptografia, logs de auditoria, scans de vulnerabilidade no CI/CD, política de senhas fortes, 2FA.                                         |
| **Técnico**     | **Vazamento de dados entre Tenants (Cross-Tenant Data Leakage)** devido a uma falha na lógica de isolamento.  |          2          |       5       |   **10**    | Implementar um `Manager` padrão do Django que aplica o filtro `tenant_id` automaticamente. Criar testes de integração específicos que tentam acessar dados de outro tenant e garantem a falha. |
| **Negócio**     | **Baixa Adoção do Produto** devido a uma interface de usuário complexa ou a um fluxo de trabalho ineficiente. |          3          |       4       |   **12**    | Seguir rigorosamente os princípios de design da UI definidos no mapeamento. Realizar sessões de feedback com usuários-piloto (beta testers) antes do lançamento oficial.                       |
| **Performance** | **Degradação de Performance** com o aumento do volume de dados, tornando as listagens e relatórios lentos.    |          4          |       3       |   **12**    | Indexação estratégica do banco de dados desde o início. Otimização de queries (uso de `select_related`, `prefetch_related`). Implementação de paginação em todas as APIs de listagem.          |

---

## 25. Conteúdo dos Arquivos de Ambiente e CI/CD

### `pyproject.toml` Proposto

```toml
[tool.poetry]
name = "iabank-backend"
version = "0.1.0"
description = "Backend for IABANK Loan Management System"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
django = "^4.2"
djangorestframework = "^3.15"
psycopg2-binary = "^2.9.9"
django-environ = "^0.11.2"
celery = "^5.3.6"
redis = "^5.0.1"
pydantic = "^2.4.2"
gunicorn = "^21.2.0"
python-json-logger = "^2.0.7"
django-prometheus = "^2.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-django = "^4.7.0"
factory-boy = "^3.3.0"
ruff = "^0.1.5"
black = "^23.10.1"
pip-audit = "^2.6.1"
pytest-cov = "^4.1.0"

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "C90"]

[tool.black]
line-length = 88
```

### `.pre-commit-config.yaml` Proposto

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: "v0.1.5"
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

### `Dockerfile.backend` Proposto

```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install poetry
COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Stage 2: Final
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/src /app/

# Add a non-root user for security
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["gunicorn", "iabank.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### `Dockerfile.frontend` Proposto

```dockerfile
# Stage 1: Build
FROM node:18-alpine as builder
WORKDIR /app
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install
COPY frontend/ .
RUN yarn build

# Stage 2: Serve
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# COPY nginx.conf /etc/nginx/conf.d/default.conf # Optional: for custom nginx config
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Anexos

### `README.md`

````markdown
# IABANK - Sistema de Gestão de Empréstimos

[![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellowgreen.svg)](https://shields.io/)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-4.2-blue.svg)](https://www.djangoproject.com/)
[![React Version](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Plataforma Web SaaS robusta e segura, desenvolvida em Python e React, projetada para a gestão completa de empréstimos (end-to-end).

## Sobre o Projeto

O `IABANK` é concebido para ser uma solução escalável, intuitiva e adaptável às necessidades de instituições financeiras de diversos portes. O objetivo é automatizar o ciclo de vida de um empréstimo, desde a originação até a cobrança, otimizando a eficiência operacional.

A arquitetura do projeto está documentada no **Blueprint Arquitetural**, que serve como a fonte única da verdade para decisões técnicas e de produto.

## Stack Tecnológica

- **Backend:** Python 3.11+, Django, Django REST Framework
- **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS
- **Banco de Dados:** PostgreSQL
- **Cache & Filas:** Redis, Celery
- **Infraestrutura:** Docker, Nginx

## Como Começar

### Pré-requisitos

- Docker e Docker Compose
- Git

### Instalação e Execução

1.  Clone o repositório:

    ```bash
    git clone https://github.com/your-org/iabank.git
    cd iabank
    ```

2.  Crie os arquivos de ambiente. No diretório `backend/`, copie `.env.example` para `.env` e ajuste as variáveis.

3.  Suba os contêineres:

    ```bash
    docker-compose up --build
    ```

4.  Acesse a aplicação:
    - Frontend: `http://localhost:3000`
    - Backend API: `http://localhost:8000/api/v1/`

## Como Executar os Testes

Para executar os testes do backend, entre no contêiner da aplicação e rode o `pytest`:

```bash
docker-compose exec backend pytest
```
````

## Estrutura do Projeto

O projeto utiliza um monorepo com a seguinte estrutura principal:

- `backend/`: Contém a aplicação Django API.
- `frontend/`: Contém a aplicação React SPA.
- `docker-compose.yml`: Orquestra os serviços para o ambiente de desenvolvimento.

Consulte o Blueprint Arquitetural para mais detalhes sobre a organização interna de cada parte.

```

### `LICENSE`
```

MIT License

Copyright (c) 2023 [Nome do Proprietário do Projeto]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

````

### `CONTRIBUTING.md`
```markdown
# Como Contribuir para o IABANK

Agradecemos o seu interesse em contribuir! Para manter o projeto organizado e de alta qualidade, pedimos que siga estas diretrizes.

## Processo de Desenvolvimento

1.  **Siga o Blueprint Arquitetural:** Todas as contribuições devem estar alinhadas com as definições, padrões e contratos estabelecidos no Blueprint. Ele é a nossa fonte única da verdade.
2.  **Crie uma Issue:** Antes de começar a trabalhar em uma nova funcionalidade ou correção, crie uma issue para discutir a proposta.
3.  **Crie um Pull Request (PR):** Faça o fork do repositório, crie um branch para a sua feature (`feature/nome-da-feature`) e envie um PR para a branch `main`.

## Qualidade de Código

A qualidade do código é fundamental. Automatizamos a verificação de qualidade para garantir consistência.

-   **Formatação e Linting:** Utilizamos `Black` e `Ruff` para o backend (Python) e `Prettier` e `ESLint` para o frontend (TypeScript/React).
-   **Ganchos de Pre-commit:** É altamente recomendado configurar os ganchos de pre-commit para formatar seu código automaticamente antes de cada commit. O arquivo `.pre-commit-config.yaml` já está configurado.
    ```bash
    pip install pre-commit
    pre-commit install
    ```
-   **Testes:** Toda nova lógica de negócio deve ser acompanhada de testes unitários e/ou de integração. O PR deve manter ou aumentar a cobertura de testes do projeto.

## Documentação de Código

-   **Docstrings:** Funções, classes e métodos públicos no backend devem ter docstrings claras explicando seu propósito, argumentos e o que retornam.
-   **Comentários:** Use comentários para explicar partes complexas ou não óbvias do código, mas prefira um código claro e autoexplicativo.

Obrigado por ajudar a construir o IABANK!
````

---

## Diretrizes Essenciais

1.  **Foco no Setup:** Sua análise deve se concentrar em tudo que é necessário para criar a estrutura de diretórios, arquivos de configuração, ambiente de desenvolvimento e documentação inicial do projeto.

2.  **Segurança ("Errar para Mais"):** Em caso de dúvida, é preferível incluir uma seção que forneça contexto geral (como "Visão Geral da Arquitetura") do que omitir algo que possa ser útil. O objetivo é garantir que o `F4-Scaffolder` tenha todas as informações necessárias.

3.  **Output Específico:** Seu resultado deve ser **APENAS** uma lista de números e os títulos das seções correspondentes. Não forneça o conteúdo das seções, apenas a identificação delas.

## Formato do Resultado Esperado

```markdown
### Seções Relevantes para o Scaffolding (Alvo 0)

Com base na análise do Blueprint Mestre, as seguintes seções são essenciais ou fornecem contexto útil para a criação do andaime do projeto:

- **1.** Visão Geral da Arquitetura
- **7.** Estrutura de Diretórios Proposta
- **8.** Arquivo `.gitignore` Proposto
- **9.** Arquivo `README.md` Proposto
- **10.** Arquivo `LICENSE` Proposto
- **11.** Arquivo `CONTRIBUTING.md` Proposto
- **12.** Estrutura do `CHANGELOG.md`
- **13.** Estratégia de Configuração e Ambientes
- **15.** Estratégia de Testes Detalhada (para criação da estrutura de pastas de teste)
- **16.** Estratégia de CI/CD (para criação de arquivos de pipeline)
- _(Incluir aqui quaisquer outras seções que contenham conteúdo de arquivos de configuração, como pyproject.toml, Dockerfiles, etc.)_
```
