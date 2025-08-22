# AGV Prompt: OrchestratorHelper v3.6 (Granularidade Máxima)

**Tarefa Principal:** Analisar o `@Blueprint_Arquitetural.md`, que é a fonte única da verdade sobre a arquitetura. Suas responsabilidades são: (1) Derivar uma ordem de implementação lógica e (2) Gerar cenários chave para os Testes de Integração.

**Input Principal (Blueprint Arquitetural):**

## --- Conteúdo do Blueprint Arquitetural ---

# **Blueprint Arquitetural: IABANK v1.0.0**

## 1. Visão Geral da Arquitetura

A arquitetura escolhida para o `IABANK` é uma **Arquitetura Monolítica em Camadas (Majestic Monolith)** para o backend, servindo uma aplicação **Single Page Application (SPA)** no frontend.

- **Backend:** Um único serviço Django que encapsula toda a lógica de negócio, acesso a dados e exposição de uma API RESTful. Esta abordagem maximiza a velocidade de desenvolvimento inicial, simplifica o deploy e mantém a coesão do domínio em um único lugar, o que é ideal para a fase atual do projeto. As camadas são:

  1.  **Apresentação (API):** Construída com Django REST Framework (DRF), responsável por expor os endpoints, lidar com autenticação, serialização de dados (DTOs) e validação de requisições.
  2.  **Aplicação (Serviços):** Orquestra a lógica de negócio, coordena a interação entre diferentes modelos de domínio e executa os casos de uso.
  3.  **Domínio (Modelos):** O coração do sistema. Contém os modelos de dados do Django com toda a lógica de negócio intrínseca à entidade (validações, estados, etc.).
  4.  **Infraestrutura:** Camada de acesso a dados (ORM do Django), comunicação com serviços externos (futuras integrações), cache (Redis) e tarefas assíncronas (Celery).

- **Frontend:** Uma aplicação React (SPA) desacoplada que consome a API do backend. Isso permite que a equipe de frontend trabalhe de forma independente e oferece uma experiência de usuário rica e moderna.

- **Organização do Código-Fonte:** Será utilizado um **Monorepo**, gerenciado com ferramentas como `npm workspaces` ou `pnpm` para o frontend. A estrutura conterá duas pastas principais na raiz: `backend/` e `frontend/`.
  - **Justificativa:** Um monorepo facilita a gestão de dependências compartilhadas (ex: tipos de DTOs), simplifica o setup do ambiente de desenvolvimento e permite a execução de testes end-to-end de forma mais integrada. Para uma equipe coesa no início do projeto, os benefícios de coordenação superam a complexidade de múltiplos repositórios.

## 2. Diagramas da Arquitetura (Modelo C4)

### 2.1. Nível 1: Diagrama de Contexto do Sistema (C1)

```mermaid
graph TD
    subgraph "Ecossistema IABANK"
        U1[Gestor / Administrador]
        U2[Consultor / Cobrador]

        System_IABANK[("IABANK Platform")]

        U1 -- "Gerencia empréstimos, finanças e usuários via [Web App]" --> System_IABANK
        U2 -- "Executa gestão de campo via [Web App]" --> System_IABANK

        System_IABANK -- "Consulta dados de crédito (Futuro) via [API REST]" --> SE1[Bureaus de Crédito]
        System_IABANK -- "Processa pagamentos (Futuro) via [API]" --> SE2[Plataformas Bancárias (Pix, Open Finance)]
        System_IABANK -- "Envia notificações (Futuro) via [API]" --> SE3[Sistemas de Comunicação (WhatsApp, Email)]
    end

    style System_IABANK fill:#1E90FF,stroke:#333,stroke-width:2px,color:#fff
```

### 2.2. Nível 2: Diagrama de Containers (C2)

```mermaid
graph TD
    subgraph "Sistema IABANK"
        User[Usuário] -->|HTTPS via Navegador| FE[Frontend SPA\n[React + Vite]\nServe a interface web]

        FE -->|API REST (JSON/HTTPS)| API[Backend API\n[Python / Django]\nContém toda a lógica de negócio]

        API -->|Leitura/Escrita via TCP/IP| DB[Banco de Dados\n[PostgreSQL]\nArmazena dados de empréstimos, clientes, etc.]
        API -->|Comandos| Cache[Cache & Fila\n[Redis]\nArmazena sessões, cache e gerencia tarefas assíncronas]

        Worker[Worker de Tarefas\n[Celery]\nProcessa tarefas em background] --> Cache
        Cache --> Worker
        Worker --> API
        Worker --> DB
    end

    style FE fill:#00D8FF,stroke:#333
    style API fill:#4CAF50,stroke:#333
    style Worker fill:#FFC107,stroke:#333
    style DB fill:#9C27B0,stroke:#333
    style Cache fill:#F44336,stroke:#333
```

### 2.3. Nível 3: Diagrama de Componentes (C3) - Backend API

```mermaid
graph TD
    subgraph "Container: Backend API (Django)"
        direction LR

        Input[Requisições HTTP] --> C1[Apresentação (API Layer)\n[DRF: Views, Serializers, Routers]\nValida e serializa dados]

        C1 --> C2[Aplicação (Service Layer)\n[Python: Services, Use Cases]\nOrquestra a lógica de negócio]

        C2 --> C3[Domínio (Domain Layer)\n[Django: Models, Managers]\nContém as regras e estado do negócio]

        C2 --> C4[Infraestrutura (Infrastructure Layer)\n[Django ORM, Celery Client, etc.]\nAbstrai acesso a DB, Cache, Filas]

        C3 --> C4

        C4 --> DB[(Database)]
        C4 --> Cache[(Cache/Queue)]
    end
```

## 3. Descrição dos Componentes, Interfaces e Modelos de Domínio

### 3.1. Consistência dos Modelos de Dados (SSOT do Domínio)

Esta seção define todos os modelos de dados principais como **Modelos Django**. Eles formam o coração do sistema e são a fonte única da verdade.

```python
# iabank/core/models/tenant.py
from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Outros campos de configuração específicos do tenant

class TenantAwareModel(models.Model):
    """Modelo abstrato para garantir isolamento de dados multi-tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        # Adicionar um índice composto para otimizar queries por tenant
        indexes = [
            models.Index(fields=['tenant']),
        ]

# iabank/users/models.py
from django.contrib.auth.models import AbstractUser
from iabank.core.models.tenant import Tenant

class User(AbstractUser):
    # Campos adicionais se necessário
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    # Perfil de acesso pode ser gerenciado com os Grupos do Django

# iabank/operational/models/customer.py
from iabank.core.models.tenant import TenantAwareModel

class Customer(TenantAwareModel):
    full_name = models.CharField(max_length=255)
    document = models.CharField(max_length=18, unique=True) # CPF/CNPJ
    birth_date = models.DateField(null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    # Endereço
    zip_code = models.CharField(max_length=9, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=20, null=True, blank=True)
    complement = models.CharField(max_length=100, null=True, blank=True)
    neighborhood = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)

    # Informações Profissionais/Financeiras
    profession = models.CharField(max_length=100, null=True, blank=True)
    income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CustomerDocument(TenantAwareModel):
    customer = models.ForeignKey(Customer, related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to='customer_documents/')
    description = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

# iabank/operational/models/consultant.py
class Consultant(TenantAwareModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='consultant_profile')
    full_name = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Configurações do app móvel/web
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name

# iabank/operational/models/loan.py
class Loan(TenantAwareModel):
    class LoanStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'Em Andamento'
        PAID_OFF = 'PAID_OFF', 'Finalizado'
        IN_COLLECTION = 'IN_COLLECTION', 'Em Cobrança'
        DEFAULTED = 'DEFAULTED', 'Inadimplente'

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='loans')
    consultant = models.ForeignKey(Consultant, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')

    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) # % ao mês
    number_of_installments = models.PositiveIntegerField()
    iof_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.IN_PROGRESS)

    contract_date = models.DateField(auto_now_add=True)
    first_installment_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Installment(TenantAwareModel):
    class InstallmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Paga'
        OVERDUE = 'OVERDUE', 'Vencida'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Paga Parcialmente'

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING)

# iabank/operational/models/collection.py
class CollectionLog(TenantAwareModel):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='collection_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    interaction_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField()
    next_action_date = models.DateField(null=True, blank=True)
    next_action_description = models.CharField(max_length=255, null=True, blank=True)

# iabank/financial/models.py
class BankAccount(TenantAwareModel):
    name = models.CharField(max_length=100) # Ex: "Conta Principal Bradesco"
    bank_name = models.CharField(max_length=100)
    agency_number = models.CharField(max_length=10, null=True, blank=True)
    account_number = models.CharField(max_length=20)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

class PaymentCategory(TenantAwareModel):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Payment Categories"

class CostCenter(TenantAwareModel):
    name = models.CharField(max_length=100)

class Supplier(TenantAwareModel):
    name = models.CharField(max_length=255)
    document = models.CharField(max_length=18, null=True, blank=True) # CPF/CNPJ

class FinancialTransaction(TenantAwareModel):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Receita'
        EXPENSE = 'EXPENSE', 'Despesa'
        TRANSFER = 'TRANSFER', 'Transferência'

    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago/Recebido'
        CANCELED = 'CANCELED', 'Cancelado'

    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)

    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)

    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)
    category = models.ForeignKey(PaymentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    # Para vincular pagamentos a parcelas de empréstimos
    installment = models.ForeignKey(Installment, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

# iabank/administration/models.py
class AuditLog(models.Model):
    # Não é TenantAware para que superusuários possam auditar todos os tenants
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255) # Ex: "Criou Empréstimo #123"
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(null=True, blank=True) # Para armazenar payload, etc.

class SystemParameter(TenantAwareModel):
    key = models.CharField(max_length=50, unique=True)
    value = models.JSONField()
    description = models.TextField()

```

### 3.1.1. Detalhamento dos DTOs e Casos de Uso

Definidos com **Pydantic `BaseModel`**, estes DTOs formam o contrato da API.

```python
# iabank/operational/dtos.py
from pydantic import BaseModel, Field, EmailStr
from datetime import date
from decimal import Decimal
from typing import List, Optional

# --- Customer DTOs ---
class CustomerCreateDTO(BaseModel):
    full_name: str = Field(..., max_length=255)
    document: str = Field(..., max_length=18)
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    zip_code: Optional[str] = Field(None, max_length=9)
    # ... outros campos de endereço

class CustomerUpdateDTO(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    # ... outros campos, todos opcionais

class CustomerListDTO(BaseModel):
    id: int
    full_name: str
    document: str
    phone: Optional[str]
    city: Optional[str]

    class Config:
        orm_mode = True

# --- Loan DTOs ---
class LoanCreateDTO(BaseModel):
    customer_id: int
    consultant_id: Optional[int] = None
    principal_amount: Decimal = Field(..., max_digits=12, decimal_places=2, gt=0)
    interest_rate: Decimal = Field(..., max_digits=5, decimal_places=2, ge=0)
    number_of_installments: int = Field(..., gt=0)
    first_installment_date: date

class LoanListDTO(BaseModel):
    id: int
    customer_name: str
    principal_amount: Decimal
    number_of_installments: int
    status: str
    contract_date: date

    class Config:
        orm_mode = True

# ... DTOs para outras entidades (Consultant, FinancialTransaction, etc.) seguiriam o mesmo padrão.
```

### 3.2. Contratos de Dados da View (ViewModel) - Frontend

Para cada tela de listagem, definimos uma estrutura **TypeScript** otimizada para a UI.

**Tela de Empréstimos (4.2): `LoanListViewModel`**

```typescript
// src/features/loans/types/index.ts

export interface LoanListViewModel {
  id: number;
  customerName: string;
  principalAmountFormatted: string; // "R$ 5.000,00"
  installmentsProgress: string; // "3/12"
  status: "IN_PROGRESS" | "PAID_OFF" | "IN_COLLECTION" | "DEFAULTED";
  contractDateFormatted: string; // "25/08/2023"
}

// Mapeamento de Origem:
// Este ViewModel é montado no backend pelo LoanListSerializer do DRF.
// - `customerName` vem de `loan.customer.full_name`.
// - `principalAmountFormatted` é formatado a partir de `loan.principal_amount`.
// - `installmentsProgress` é calculado contando parcelas pagas vs. totais.
// - `status` é o valor do Enum `LoanStatus`.
// - `contractDateFormatted` é formatado a partir de `loan.contract_date`.
```

**Tela de Clientes (4.3): `CustomerListViewModel`**

```typescript
// src/features/customers/types/index.ts

export interface CustomerListViewModel {
  id: number;
  fullName: string;
  documentFormatted: string; // "123.456.789-00"
  phone: string;
  cityState: string; // "São Paulo - SP"
  activeLoansCount: number;
}
```

**Tela de Contas a Pagar (5.1): `PayableListViewModel`**

```typescript
// src/features/financials/types/index.ts

export interface PayableListViewModel {
  id: number;
  description: string;
  supplierName: string | null;
  amountFormatted: string; // "R$ 1.250,50"
  dueDateFormatted: string; // "10/09/2023"
  status: "PENDING" | "PAID" | "CANCELED";
  isOverdue: boolean; // para destacar a linha na UI
}
```

## 4. Descrição Detalhada da Arquitetura Frontend

- **Padrão Arquitetural:** Adotaremos a metodologia **Feature-Sliced Design (FSD)**. O código é organizado em camadas e fatias (features), promovendo baixo acoplamento e alta coesão.

- **Estrutura de Diretórios Proposta (`frontend/src/`):**

  ```
  src/
  ├── app/                # 1. Camada de Aplicação: Configuração global
  │   ├── providers/      # Provedores de contexto, React Query, Router
  │   ├── styles/         # Estilos globais, configuração do Tailwind
  │   └── main.tsx        # Ponto de entrada da aplicação
  │
  ├── pages/              # 2. Camada de Páginas: Compositor de features e widgets
  │   ├── LoginPage.tsx
  │   ├── DashboardPage.tsx
  │   ├── LoansPage.tsx
  │   └── ...
  │
  ├── widgets/            # 3. Camada de Widgets: Componentes complexos
  │   ├── Header/
  │   ├── SidebarMenu/
  │   └── LoansTable/     # Widget que compõe a tabela de empréstimos
  │
  ├── features/           # 4. Camada de Funcionalidades: Lógica de negócio da UI
  │   ├── auth/           # Ex: Login/Logout
  │   ├── create-loan/    # Ex: O wizard de novo empréstimo
  │   └── filter-loans/   # Ex: O componente de filtros avançados
  │
  ├── entities/           # 5. Camada de Entidades: Componentes e lógica de entidades
  │   ├── loan/
  │   │   ├── api/        # Hooks do TanStack Query (useGetLoans, useCreateLoan)
  │   │   ├── model/      # Tipos (ViewModels), helpers
  │   │   └── ui/         # Componentes de UI (ex: LoanStatusBadge)
  │   ├── customer/
  │   └── ...
  │
  └── shared/             # 6. Camada Compartilhada: Código reutilizável e agnóstico
      ├── api/            # Configuração do cliente Axios, interceptors
      ├── config/         # Constantes, variáveis de ambiente
      ├── lib/            # Funções utilitárias (formatação de data, etc.)
      ├── ui/             # Biblioteca de componentes UI Kit (Button, Input, Table)
  ```

- **Estratégia de Gerenciamento de Estado:**

  - **Estado do Servidor:** **TanStack Query (React Query)** será a fonte única da verdade para todos os dados que vêm da API. Ele gerenciará caching, revalidação, mutações (POST/PUT/DELETE) e estados de loading/error de forma declarativa.
  - **Estado Global do Cliente:** Para estado síncrono e global (ex: dados do usuário logado, estado do menu lateral), usaremos **Zustand**. É uma solução leve, sem boilerplate e com uma API simples.
  - **Estado Local do Componente:** O estado efêmero e não compartilhado será gerenciado com os hooks nativos do React (`useState`, `useReducer`).

- **Fluxo de Dados (Exemplo: Listagem de Empréstimos):**
  1.  O usuário navega para a `LoansPage`.
  2.  A `LoansPage` renderiza o widget `LoansTable`.
  3.  O `LoansTable` usa o hook `useGetLoans` da `entities/loan/api`.
  4.  `useGetLoans` (TanStack Query) verifica o cache. Se os dados estiverem obsoletos, ele dispara uma requisição GET para `/api/v1/loans/` usando o cliente Axios configurado em `shared/api`.
  5.  A API responde com um array de `LoanListDTO`.
  6.  O hook `useGetLoans` atualiza seu estado, fazendo com que o `LoansTable` re-renderize com os dados, formatando-os conforme o `LoanListViewModel`.

## 5. Definição das Interfaces Principais

Interfaces (usando `abc.ABC`) definem os contratos para os serviços da camada de aplicação.

```python
# iabank/operational/services/loan_service.py
from abc import ABC, abstractmethod
from .dtos import LoanCreateDTO
from ..models import Loan

class ILoanService(ABC):
    @abstractmethod
    def __init__(self, user, tenant):
        """
        Serviços são instanciados com o contexto da requisição (usuário, tenant).
        """
        pass

    @abstractmethod
    def create_loan(self, data: LoanCreateDTO) -> Loan:
        """
        Cria um novo empréstimo e suas parcelas.
        Retorna a instância do empréstimo criado.
        """
        pass

    @abstractmethod
    def transfer_loans(self, loan_ids: list[int], origin_consultant_id: int, destination_consultant_id: int):
        """
        Transfere uma lista de empréstimos entre consultores.
        """
        pass
```

## 6. Gerenciamento de Dados

- **Persistência:** O **ORM do Django** será usado para todas as interações com o banco de dados PostgreSQL. O padrão **Active Record** do Django é suficiente para a complexidade atual.
- **Gerenciamento de Schema:** As migrações de banco de dados serão gerenciadas pelo sistema de **`makemigrations` e `migrate` do Django**, garantindo a evolução consistente do schema.
- **Seed de Dados:** Para ambientes de desenvolvimento e teste, será utilizada a biblioteca **`factory-boy`** em conjunto com um comando de gerenciamento customizado do Django (`./manage.py seed_db`). Isso permitirá a criação de dados fictícios, mas realistas e consistentes, para popular a aplicação.

## 7. Estrutura de Diretórios Proposta

```
iabank/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── .vscode/
│   └── settings.json
├── backend/
│   ├── src/
│   │   └── iabank/
│   │       ├── __init__.py
│   │       ├── administration/
│   │       ├── core/
│   │       ├── financial/
│   │       ├── operational/
│   │       ├── users/
│   │       ├── settings.py
│   │       ├── urls.py
│   │       └── wsgi.py
│   ├── manage.py
│   └── tests/
│       └── integration/
│           └── test_api_loan_creation.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── pages/
│   │   ├── widgets/
│   │   ├── features/
│   │   ├── entities/
│   │   └── shared/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── CONTRIBUTING.md
├── CHANGELOG.md
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── LICENSE
├── pyproject.toml
└── README.md
```

## 8. Arquivo `.gitignore` Proposto

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
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
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
static_collected/

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# Jupyter Notebook
.ipynb_checkpoints

# Environments
.env
.venv
env/
venv/
ENV/
env.bak
venv.bak

# IDEs
.idea/
.vscode/
*.swp
*.swo

# Docker
.dockerignore
docker-compose.yml

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*
.pnpm-store/
dist/
dist-ssr/
.npm/

# OS-specific
.DS_Store
Thumbs.db
```

## 9. Arquivo `README.md` Proposto

````markdown
# IABANK

[![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow.svg)](https://shields.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.x-green.svg)](https://www.djangoproject.com/)
[![React Version](https://img.shields.io/badge/react-18%2B-blue.svg)](https://reactjs.org/)

Sistema de gestão de empréstimos moderno e eficiente. Plataforma Web SaaS robusta e segura para a gestão completa do ciclo de vida de empréstimos (end-to-end).

## 🚀 Sobre o Projeto

O IABANK é projetado para ser escalável, intuitivo e adaptável às necessidades de instituições financeiras de diversos portes. A visão futura do projeto inclui a integração com um ecossistema de agentes de IA para automatizar todo o ciclo de vida de um empréstimo.

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.10+, Django, Django REST Framework, PostgreSQL, Celery, Redis
- **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS, TanStack Query
- **Infraestrutura:** Docker, Nginx

## 🏁 Como Começar

### Pré-requisitos

- Docker e Docker Compose
- Node.js e pnpm (ou npm/yarn)
- Python 3.10+ e Poetry

### Instalação e Execução

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/iabank.git
    cd iabank
    ```

2.  **Configure as variáveis de ambiente:**
    Copie o arquivo `.env.example` para `.env` na pasta `backend/` e preencha as variáveis necessárias.

    ```bash
    cp backend/.env.example backend/.env
    ```

3.  **Suba os contêineres Docker:**
    Este comando irá construir as imagens e iniciar todos os serviços (backend, frontend, db, redis).

    ```bash
    docker-compose up --build
    ```

4.  **Acesse a aplicação:**
    - Frontend: `http://localhost:5173`
    - Backend API: `http://localhost:8000/api/`

## 🧪 Como Executar os Testes

Para executar os testes do backend, entre no contêiner da aplicação e use o `pytest`.

1.  **Acesse o shell do contêiner do backend:**

    ```bash
    docker-compose exec backend bash
    ```

2.  **Execute os testes:**
    ```bash
    pytest
    ```

## 📂 Estrutura do Projeto

O projeto é um monorepo com a seguinte estrutura principal:

- `backend/`: Contém a aplicação Django (API).
- `frontend/`: Contém a aplicação React (SPA).
- `docker-compose.yml`: Orquestra os serviços do ambiente de desenvolvimento.
- `pyproject.toml`: Gerencia as dependências e ferramentas do projeto Python.
````

## 10. Arquivo `LICENSE` Proposto

Sugere-se a licença **MIT**, que é permissiva e amplamente utilizada.

```
MIT License

Copyright (c) 2023 [Nome do Proprietário do Copyright]

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
```

## 11. Arquivo `CONTRIBUTING.md` Proposto

````markdown
# Como Contribuir para o IABANK

Agradecemos seu interesse em contribuir! Para garantir a qualidade e a consistência do projeto, pedimos que siga estas diretrizes.

## 📜 Filosofia de Desenvolvimento

Este projeto segue o **Método AGV (Architecture-Guided Vision)**. Todas as contribuições devem estar alinhadas com o **Blueprint Arquitetural** definido. Antes de iniciar uma nova feature ou uma refatoração significativa, consulte o blueprint para garantir que sua abordagem está em conformidade com os padrões e decisões arquiteturais estabelecidas.

## ✅ Qualidade de Código

Utilizamos ferramentas para manter um alto padrão de qualidade de código. É obrigatório que todo código submetido passe por essas verificações.

- **Backend (Python):**
  - **Formatador:** `Black`
  - **Linter:** `Ruff`
- **Frontend (TypeScript/React):**
  - **Formatador:** `Prettier`
  - **Linter:** `ESLint`

### Hooks de Pre-commit

Configuramos ganchos de `pre-commit` para automatizar essas verificações antes de cada commit. Para ativá-los, instale o `pre-commit` e rode o seguinte comando na raiz do projeto:

```bash
pip install pre-commit
pre-commit install
```
````

Isso garantirá que seu código seja formatado e validado automaticamente, evitando commits com problemas de estilo.

## 📚 Documentação de Código

- **Python:** Todas as funções, métodos e classes públicas devem ter **docstrings** no formato **Google Style**.
- **TypeScript/React:** Use **JSDoc** para documentar props de componentes, funções complexas e hooks customizados.

## 🔄 Fluxo de Contribuição

1.  Crie um fork do repositório.
2.  Crie um branch para sua feature (`git checkout -b feature/nome-da-feature`).
3.  Implemente sua feature, garantindo a escrita de testes unitários e de integração correspondentes.
4.  Certifique-se de que todos os testes estão passando (`pytest` no backend, `npm test` no frontend).
5.  Faça o commit de suas mudanças (`git commit -m 'feat: Adiciona nova funcionalidade X'`).
6.  Faça o push para o seu branch (`git push origin feature/nome-da-feature`).
7.  Abra um Pull Request para o branch `main` do repositório original.

````

## 12. Estrutura do `CHANGELOG.md`

```markdown
# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-

### Changed
-

### Deprecated
-

### Removed
-

### Fixed
-

### Security
-

## [1.0.0] - YYYY-MM-DD

### Added
- Versão inicial do Blueprint Arquitetural.
- Estrutura base do projeto com Backend (Django) e Frontend (React).
````

## 13. Estratégia de Configuração e Ambientes

- **Ferramenta:** `django-environ`.
- **Mecanismo:** As configurações serão lidas de variáveis de ambiente. Para o desenvolvimento local, um arquivo `.env` na raiz do projeto `backend/` será utilizado para definir essas variáveis.
- **Estrutura:** O arquivo `iabank/settings.py` será configurado para ler chaves como `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, `DEBUG`, etc., a partir do ambiente. Isso garante que nenhum segredo seja comitado no código-fonte.
- **Ambientes:**
  - **Desenvolvimento (local):** `DEBUG=True`, usa o `docker-compose.yml` com o banco de dados e Redis locais.
  - **Homologação/Staging:** `DEBUG=False`, aponta para um banco de dados e Redis de staging.
  - **Produção:** `DEBUG=False`, utiliza configurações otimizadas para performance e segurança, apontando para os serviços de produção.

## 14. Estratégia de Observabilidade Completa

- **Logging Estruturado:**

  - **Backend:** Utilização da biblioteca `structlog` para gerar logs em formato JSON. Em desenvolvimento, os logs serão formatados para leitura humana no console. Em produção, serão enviados como JSON para serem ingeridos por um sistema de agregação de logs (ex: ELK Stack, Datadog).
  - **Níveis:** `INFO` para eventos de negócio (ex: empréstimo criado), `WARNING` para situações anormais que não quebram o sistema, `ERROR` para exceções não tratadas, `CRITICAL` para falhas graves.

- **Métricas de Negócio:**

  - Será exposto um endpoint (ex: `/metrics`, protegido) no padrão Prometheus.
  - **Métricas a coletar:**
    - `loans_created_total`: Contador de novos empréstimos.
    - `payments_received_total`: Soma dos valores de pagamentos recebidos.
    - `active_users_gauge`: Número de usuários ativos na última hora.
    - `api_request_latency_histogram`: Histograma da latência das requisições da API.

- **Distributed Tracing (Preparação):**

  - Embora seja um monolito, as requisições que envolvem tarefas assíncronas (Celery) se beneficiarão do tracing.
  - Bibliotecas como `OpenTelemetry` serão integradas para propagar um `trace_id` entre a requisição HTTP e a tarefa Celery, permitindo rastrear o fluxo completo.

- **Health Checks e SLIs/SLOs:**

  - **Endpoint de Health Check:** `/api/health/`. Ele verificará a conectividade com o Banco de Dados e o Redis. Retornará `200 OK` se tudo estiver funcional.
  - **SLI (Indicador):** Disponibilidade do endpoint de login.
  - **SLO (Objetivo):** 99.9% de disponibilidade mensal para o endpoint de login.

- **Alerting Inteligente:**
  - Configuração de alertas em uma ferramenta como Grafana ou Sentry.
  - **Exemplos:**
    - Alertar se a taxa de erros 5xx da API ultrapassar 1% por mais de 5 minutos.
    - Alertar se a fila do Celery crescer além de 100 tarefas pendentes.
    - Alertar sobre anomalias no volume de criação de empréstimos (usando detecção de desvio padrão).

## 15. Estratégia de Testes Detalhada

- **Estrutura e Convenção de Nomenclatura:**

  - **Testes Unitários:** Residirão dentro de cada app Django, em `backend/src/iabank/<app_name>/tests/`. Foco em testar modelos, serviços e lógica pura em isolamento.
    - Exemplo de arquivo: `backend/src/iabank/operational/tests/test_loans_models.py`
  - **Testes de Integração:** Residirão em um diretório de alto nível, `backend/tests/integration/`. Foco em testar o fluxo completo através da API, envolvendo múltiplos componentes (views, services, models, db).
    - Exemplo de arquivo: `backend/tests/integration/test_api_loan_creation.py`
  - **Convenção:** `test_<nome_do_app_ou_feature>_<nome_do_modulo>.py`.

- **Padrões de Teste de Integração:**
  - **Uso de Factories:** A biblioteca `factory-boy` será utilizada para criar instâncias dos modelos do Django de forma programática e reutilizável.
    - Ex: `LoanFactory` que cria um `Loan` com um `Customer` e `Installments` associados.
  - **Simulação de Autenticação:** Nos testes da API, o método `force_authenticate` do `APIClient` do DRF será usado para simular um usuário logado, evitando a necessidade de testar o endpoint de login em cada teste de endpoint protegido.
  - **Escopo de Teste:** Um teste de integração para a criação de um empréstimo (`POST /api/v1/loans/`) validará:
    1.  A resposta HTTP (status code, payload).
    2.  A criação correta do objeto `Loan` no banco de dados.
    3.  A criação correta das `Installments` associadas.
    4.  A criação do `FinancialTransaction` de saída do valor.
        Ele não re-testará a validação de campo do `Customer`, que já deve ter sido coberta por testes unitários.

## 16. Estratégia de CI/CD

- **Ferramenta:** GitHub Actions.
- **Arquivo de Configuração:** `.github/workflows/ci-cd.yml`.
- **Gatilhos:** Em cada `push` para `main` e em cada abertura/atualização de `Pull Request`.

- **Estágios do Pipeline:**
  1.  **CI - Validação (em Pull Requests e push):**
      - **Setup:** Checkout do código, setup de Python e Node.js.
      - **Lint & Format Check:** Executa `ruff check` e `black --check` (backend), `eslint` e `prettier --check` (frontend).
      - **Tests:** Executa `pytest` com geração de relatório de cobertura (backend) e `npm test` (frontend).
      - **Build:** Executa `npm run build` para o frontend para garantir que o build não quebra.
  2.  **CD - Entrega (apenas em merge para `main`):**
      - **Build & Push Docker Images:** Constrói as imagens Docker para `backend` e `frontend` (com tags da versão/commit) e as envia para um registro de contêineres (ex: Docker Hub, GitHub Container Registry).
  3.  **CD - Implantação (acionado manualmente ou por tag):**
      - **Deploy to Staging:** Um job manual ou automático (em push para um branch `staging`) que se conecta ao ambiente de staging e atualiza os serviços com as novas imagens Docker.
      - **Deploy to Production:** Um job manual que executa o mesmo processo para o ambiente de produção.
  4.  **Rollback:** A estratégia de implantação usará tags de imagem imutáveis. O rollback consistirá em re-implantar a tag da versão estável anterior.

## 17. Estratégia de Versionamento da API

A API será versionada via URL para garantir que futuras mudanças não quebrem os clientes existentes.

- **Formato:** `/api/v1/...`
- **Implementação:** Utilizando os `Namespaces` e `Routers` do Django REST Framework, será criado um `urls.py` principal para a API que inclui os roteadores da `v1`.

  ```python
  # iabank/urls.py
  from django.urls import path, include

  urlpatterns = [
      # ...
      path('api/v1/', include('iabank.api_v1.urls')),
  ]
  ```

## 18. Padrão de Resposta da API e Tratamento de Erros

- **Resposta de Sucesso (2xx):**

  - Para `GET` (lista):
    ```json
    {
      "count": 150,
      "next": "http://.../?page=3",
      "previous": "http://.../?page=1",
      "results": [ ... ]
    }
    ```
  - Para `GET` (detalhe), `POST`, `PUT`:
    ```json
    {
      "data": { ... }
    }
    ```

- **Resposta de Erro (4xx, 5xx):**
  Um `ExceptionHandler` customizado do DRF será implementado para padronizar todas as respostas de erro.
  ```json
  {
    "error": {
      "code": "validation_error", // ou "not_found", "authentication_failed", "server_error"
      "message": "Ocorreu um erro de validação.",
      "details": {
        // opcional, para erros de validação
        "document": ["Este campo não pode ser em branco."],
        "principal_amount": ["Deve ser um número positivo."]
      }
    }
  }
  ```

## 19. Estratégia de Segurança Abrangente

- **Threat Modeling Básico:**

  - **Ameaça 1:** Acesso não autorizado a dados de outro tenant.
    - **Mitigação:** Implementação rigorosa do `TenantAwareModel` com filtragem automática em um `Manager` customizado para garantir que nenhuma query vaze dados. Testes de integração específicos para validar o isolamento.
  - **Ameaça 2:** Injeção de SQL.
    - **Mitigação:** Uso exclusivo do ORM do Django, que parametriza todas as queries, prevenindo esta classe de ataque.
  - **Ameaça 3:** Vazamento de dados sensíveis do cliente (documento, renda).
    - **Mitigação:** Criptografia de dados sensíveis em repouso (usando `django-cryptography` ou `pgcrypto`). Controle de acesso granular (RBAC) para limitar quem pode ver esses dados.

- **Estratégia de Secrets Management:**

  - **Desenvolvimento:** Arquivos `.env` locais, não comitados.
  - **Produção:** Variáveis de ambiente injetadas pelo orquestrador de contêineres (ex: Kubernetes Secrets, AWS Secrets Manager, variaveis de ambiente do serviço de PaaS).

- **Compliance Framework (LGPD):**

  - **Auditoria:** O modelo `AuditLog` registrará todas as operações CRUD em dados pessoais.
  - **RBAC:** O sistema de permissões do Django será usado para implementar o "princípio do menor privilégio".
  - **Retenção de Dados:** Serão implementados scripts (comandos de gerenciamento) para anonimização ou exclusão de dados de clientes mediante solicitação, conforme a LGPD.

- **Security by Design:**
  - **DRF:** Utilização das validações, throttling e permissions built-in do framework.
  - **Django:** Proteções contra CSRF, XSS e Clickjacking ativadas por padrão.
  - **Dependências:** Uso de ferramentas como `pip-audit` ou `Dependabot` do GitHub para monitorar e alertar sobre vulnerabilidades em dependências.

## 20. Justificativas e Trade-offs

- **Monólito vs. Microsserviços:**

  - **Decisão:** Adotar uma arquitetura monolítica (Majestic Monolith).
  - **Justificativa:** Para a fase inicial do projeto, a complexidade operacional de uma arquitetura de microsserviços (deploy, monitoramento, comunicação inter-serviços) superaria os benefícios. O monolito permite um desenvolvimento mais rápido, transações ACID mais simples e um único ponto de implantação. A modularização interna em apps Django (operational, financial, etc.) prepara o terreno para uma futura extração para microsserviços, se necessário.
  - **Trade-off:** Escalabilidade granular é sacrificada. Se um módulo (ex: relatórios) se tornar um gargalo, toda a aplicação precisa ser escalada. Este é um trade-off aceitável no início.

- **Monorepo vs. Multi-repo:**
  - **Decisão:** Monorepo.
  - **Justificativa:** Simplifica o setup do ambiente e a consistência entre frontend e backend. Facilita refatorações que afetam ambas as bases de código.
  - **Trade-off:** O pipeline de CI/CD pode se tornar mais lento com o tempo, pois testa e constrói tudo a cada mudança. Isso pode ser mitigado com pipelines inteligentes que executam jobs apenas para as partes do código que foram alteradas.

## 21. Exemplo de Bootstrapping/Inicialização

A inicialização e injeção de dependência em Django são gerenciadas pelo próprio framework. Um exemplo conceitual de como um serviço seria usado em uma View do DRF demonstra a simplicidade da abordagem:

```python
# iabank/operational/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import LoanService  # Implementação concreta de ILoanService
from .dtos import LoanCreateDTO

class LoanCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # O framework injeta 'request', que contém user e tenant (via middleware)
        loan_service = LoanService(user=request.user, tenant=request.tenant)

        try:
            dto = LoanCreateDTO(**request.data)
            loan = loan_service.create_loan(dto)
            # Serializa a resposta
            return Response({"data": {"id": loan.id}}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Tratamento de erro
            return Response({"error": ...}, status=status.HTTP_400_BAD_REQUEST)

```

A configuração do `LoanService` (`__init__`) recebe suas dependências essenciais (contexto do usuário e tenant) no momento da instanciação, garantindo que ele opere dentro do contexto correto.

## 22. Estratégia de Evolução do Blueprint

- **Versionamento Semântico:** Este blueprint será versionado (ex: `IABANK Blueprint v1.0.0`). Mudanças que adicionam funcionalidades sem quebrar a estrutura são `MINOR` (v1.1.0). Mudanças que alteram fundamentalmente a arquitetura (ex: migrar para microsserviços) são `MAJOR` (v2.0.0).
- **Processo de Evolução:** Mudanças arquiteturais significativas devem ser propostas através de um **Architectural Decision Record (ADR)**. Um ADR é um documento curto em Markdown que descreve a decisão, o contexto, as alternativas consideradas e as consequências. Os ADRs serão armazenados em uma pasta `docs/adr/` no repositório.
- **Compatibilidade:** Para mudanças na API, a estratégia de versionamento (Seção 17) garante a compatibilidade. Componentes internos depreciados devem ser marcados com `warnings.warn` e removidos em uma versão `MAJOR` futura.

## 23. Métricas de Qualidade e Quality Gates

- **Cobertura de Código:**
  - **Meta:** Mínimo de **85%** de cobertura de testes para todo o código do backend.
  - **Exclusões:** Arquivos de migração, `manage.py`, `settings.py`.
  - **Ferramenta:** `pytest-cov`.
- **Complexidade:**
  - **Métrica:** Complexidade Ciclomática.
  - **Limite:** Nenhuma função/método pode ter uma complexidade maior que **12**.
  - **Ferramenta:** `Ruff` (com o plugin `mccabe`).
- **Quality Gates Automatizados (no CI):**
  - O Pull Request será **bloqueado** se qualquer um dos seguintes critérios for atendido:
    1.  A cobertura total de testes cair abaixo de 85%.
    2.  O linter (`Ruff`) reportar qualquer erro.
    3.  Qualquer teste (unitário ou de integração) falhar.
    4.  Uma varredura de segurança (ex: `pip-audit`) encontrar uma vulnerabilidade de alta criticidade.

## 24. Análise de Riscos e Plano de Mitigação

| Categoria       | Risco Identificado                                                                              | Probabilidade (1-5) | Impacto (1-5) | Score (P×I) | Estratégia de Mitigação                                                                                                                                                                                                                                               |
| :-------------- | :---------------------------------------------------------------------------------------------- | :-----------------: | :-----------: | :---------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Segurança**   | **Violação de dados (data breach) devido a falha no isolamento Multi-tenant.**                  |        **3**        |     **5**     |   **15**    | Implementar camada de acesso a dados tenant-aware obrigatória. Testes de integração rigorosos para validar que um usuário do tenant A não consegue acessar dados do tenant B sob nenhuma circunstância. Auditoria de logs de acesso.                                  |
| **Técnico**     | **Débito técnico excessivo devido à velocidade inicial, tornando a manutenção futura custosa.** |        **4**        |     **3**     |   **12**    | Adoção rigorosa de quality gates (linting, testes, cobertura). Processo de code review obrigatório para todos os PRs. Alocação de tempo para refatoração técnica em cada ciclo de desenvolvimento.                                                                    |
| **Performance** | **Consultas lentas em tabelas grandes (empréstimos, transações) impactando a UX.**              |        **3**        |     **4**     |   **12**    | Design de schema com índices apropriados desde o início. Uso do `Django Debug Toolbar` para identificar queries lentas em desenvolvimento. Implementação de paginação em todos os endpoints de listagem. Caching para dados frequentemente acessados e que não mudam. |
| **Negócio**     | **Falha em atender a requisitos regulatórios (LGPD, Bacen), resultando em multas.**             |        **2**        |     **5**     |   **10**    | Consultoria jurídica para mapear requisitos. Construir a plataforma com princípios de Privacy by Design. Implementar trilha de auditoria completa e mecanismos de gestão de consentimento e dados do titular.                                                         |
| **Operacional** | **Perda de dados financeiros por falha de backup ou transação não atômica.**                    |        **2**        |     **5**     |   **10**    | Utilizar transações atômicas (`@transaction.atomic`) do Django para todas as operações financeiras críticas. Configurar backups automáticos e point-in-time recovery (PITR) no PostgreSQL. Realizar testes de restauração de backup periodicamente.                   |

## 25. Conteúdo dos Arquivos de Ambiente e CI/CD

### `pyproject.toml` Proposto

```toml
[tool.poetry]
name = "iabank-backend"
version = "0.1.0"
description = "Backend for IABANK Loan Management System"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{include = "iabank", from = "src"}]

[tool.poetry.dependencies]
python = "^3.10"
django = "^4.2"
djangorestframework = "^3.14"
psycopg2-binary = "^2.9"
django-environ = "^0.11"
celery = {extras = ["redis"], version = "^5.3"}
redis = "^5.0"
pydantic = {extras = ["email"], version = "^2.3"}
structlog = "^23.1"
gunicorn = "^21.2"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-django = "^4.7"
pytest-cov = "^4.1"
factory-boy = "^3.3"
black = "^23.9"
ruff = "^0.0.290"
pre-commit = "^3.4"
pip-audit = "^2.6"

[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "C90", "N", "D"]
ignore = ["D100", "D104", "D105", "D107"]

[tool.ruff.mccabe]
max-complexity = 12

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### `.pre-commit-config.yaml` Proposto

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: "v0.0.290"
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

### `Dockerfile.backend` Proposto

```dockerfile
# Stage 1: Build
FROM python:3.10-slim as builder

WORKDIR /app

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev --no-root

# Stage 2: Final Image
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv ./.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY ./backend/src/ .

# Gunicorn será o entrypoint no docker-compose
EXPOSE 8000
```

### `Dockerfile.frontend` Proposto

```dockerfile
# Stage 1: Build
FROM node:18-alpine as builder

WORKDIR /app

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

COPY frontend/ .

RUN pnpm build

# Stage 2: Serve
FROM nginx:1.25-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Se precisar de um reverse proxy, copie a configuração do Nginx aqui
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

**Diretrizes Essenciais:**

1. **Análise de Dependências com Decomposição Máxima:** A ordem de implementação deve ser determinada pelo princípio de **responsabilidade única por alvo**. Siga estas regras de decomposição:

   a. **Ordem de Módulos Transversais:** Os módulos que fornecem funcionalidades transversais **DEVEM** ser implementados primeiro. A ordem de implementação e validação entre eles deve seguir a lógica de dependência: **Autenticação > Gestão de Usuários e Autorização > Multi-Tenancy**.

   b. **Decomposição Obrigatória por Tipo (Backend):** Para cada módulo de negócio (ex: `iabank.users`, `iabank.loans`), você **DEVE** criar alvos de implementação separados e sequenciais para cada camada lógica, na seguinte ordem:

   1. **Modelos:** Apenas os arquivos `models.py`.
   2. **Repositórios/Infraestrutura:** Apenas a lógica de acesso a dados.
   3. **Serviços de Aplicação:** Apenas a lógica de negócio dos casos de uso.
   4. **Serializers:** Apenas os arquivos `serializers.py` da API.
   5. **Views/URLs:** Apenas os endpoints `views.py` e o roteamento `urls.py`.

   c. **Regra Especial para `users`:** O módulo de usuários **DEVE** ser decomposto em duas fases funcionais distintas, cada uma com sua própria parada de testes:

   1. **Fase 1: Autenticação JWT.** Implemente apenas os modelos, serializers e views necessários para os endpoints de obtenção e refresh de token (ex: `/token/`).
   2. **Fase 2: Gestão de Usuários e Autorização.** Após validar a autenticação, implemente os endpoints de CRUD de usuários (ex: `/users/`, `/users/me/`) e a lógica de permissões/perfis (RBAC).

2. **Criação do "Alvo 0":** Sua primeira tarefa é SEMPRE gerar um item inicial na ordem de implementação chamado **"Alvo 0: Setup do Projeto Profissional"**. Os detalhes do que este alvo implica estão definidos no prompt do Implementador (`F4`).

3. **Geração da Ordem Sequencial e Pontos de Teste:** Crie uma lista numerada de "Alvos de Implementação".

   - **Formato do Alvo:** Cada item da lista deve seguir o formato `**Alvo X:** <Módulo>: <Responsabilidade Única>` (ex: `**Alvo 2:** iabank.users: Modelos e Migrações`).
   - **Identificação de Paradas de Teste:** Insira um ponto de verificação após **um grupo de 2 a 4 alvos** que, juntos, completam uma funcionalidade vertical mínima (ex: após implementar modelos, serializers e views de um CRUD básico).
   - **Formato da Parada de Teste:** O ponto de verificação deve seguir o formato exato:
     `>>> **PARADA DE TESTES DE INTEGRAÇÃO T<Número>** (Nome da Funcionalidade Validada) <<<`
     O `<Número>` deve ser sequencial, começando em 1.

4. **Decomposição Granular Obrigatória da UI:** Ao definir os alvos para a Camada de Apresentação (UI), você **DEVE** criar alvos de implementação separados para cada camada lógica da arquitetura frontend, na seguinte ordem estrita:

   a. **Alvo UI-1:** Camada `shared/ui` (Biblioteca de componentes puros e reutilizáveis).
   b. **Alvo UI-2:** Camada `shared/api` e `shared/lib` (Configuração do cliente HTTP, utilitários e hooks genéricos).
   c. **Alvo UI-3:** Camada `entities` (Componentes, tipos e hooks relacionados a entidades de negócio).
   d. **Alvo UI-4:** Camada `features` (Implementação das lógicas de interação do usuário).
   e. **Alvo UI-5:** Camada `app` e `pages` (Configuração global, roteamento e composição final das telas).

   **Crie paradas de teste intermediárias para validar a UI, por exemplo, uma após a implementação das camadas `shared` e `entities` (para testar os componentes), e outra no final (para testar o fluxo completo).**

5. **Geração de Cenários de Teste de Integração:**

   - Para cada `>>> PARADA ... <<<` criada, você **DEVE** gerar uma seção detalhada logo abaixo dela.
   - Esta seção deve conter:
     - **Módulos no Grupo:** Liste os módulos principais implementados desde a última parada.
     - **Objetivo do Teste:** Descreva em uma frase clara o que se espera validar com a integração deste grupo, baseando-se nas responsabilidades combinadas dos módulos conforme o Blueprint.
     - **Cenários Chave:** Liste de 2 a 4 cenários de teste específicos e acionáveis que verifiquem as interações mais críticas. Para paradas que dependem de etapas anteriores (ex: testar uma funcionalidade que requer autenticação, validar uma regra de negócio que depende de um cliente pré-existente, etc.), os cenários devem mencionar o uso de simulação de pré-condições (ex: "Usando um usuário autenticado simulado...", "Dado um cliente com um empréstimo ativo...", etc.) em vez de repetir o fluxo completo.

6. **Simplicidade do Output:** O resultado final deve ser um documento Markdown contendo apenas a lista numerada da "Ordem de Implementação" com os "Alvos" e as "Paradas de Teste" detalhadas. **Não inclua justificativas ou descrições adicionais; foque apenas no plano de ação.**

**Resultado Esperado:**

Um documento Markdown (`Output_Ordem_e_Testes.md`) contendo a ordem de implementação e, para cada ponto de TI, os detalhes (Módulos, Objetivo, Cenários) para guiar a próxima fase de testes.
