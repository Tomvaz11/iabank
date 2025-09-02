# Blueprint Arquitetural: IABANK (Tocrisna v7.4)

Este documento define a arquitetura de alto nível, técnica e de produto, para o sistema de gestão de empréstimos IABANK. Ele serve como a fonte única da verdade para a estrutura, componentes e contratos da plataforma.

## 1. Visão Geral da Arquitetura

A arquitetura escolhida é uma **Arquitetura em Camadas (Layered Architecture)** aplicada a uma aplicação **Monolítica Modular**. O backend Django será estruturado seguindo princípios da Arquitetura Limpa (Clean Architecture) para garantir uma forte separação de responsabilidades, testabilidade e manutenibilidade.

- **Monolito Modular:** Em vez de microserviços, optamos por um único codebase (monolito) dividido em módulos de negócio bem definidos (apps Django como `loans`, `finance`, `customers`). Esta abordagem reduz a complexidade operacional inicial, acelera o desenvolvimento e é ideal para a fase atual do projeto, enquanto a modularidade interna facilita uma futura extração para microserviços, se necessário.
- **Arquitetura em Camadas (Backend):** O backend será dividido em quatro camadas distintas:
  1.  **Apresentação (Presentation):** Responsável por lidar com requisições HTTP e serialização de dados. (Django REST Framework: Views, Serializers, Routers).
  2.  **Aplicação (Application):** Orquestra os casos de uso do sistema. Contém a lógica de aplicação, chama serviços de domínio e de infraestrutura. (Camada de Serviços).
  3.  **Domínio (Domain):** O coração do sistema. Contém a lógica de negócio pura, modelos de dados e regras de negócio. (Django Models, Lógica de Domínio).
  4.  **Infraestrutura (Infrastructure):** Lida com detalhes técnicos como acesso ao banco de dados, comunicação com serviços externos, caches, etc. (Django ORM, Celery, Clientes de API).
- **Frontend (SPA):** O frontend será uma Single Page Application (SPA) desacoplada, comunicando-se com o backend exclusivamente via API RESTful.
- **Organização do Código-Fonte:** Adotaremos um **monorepo**, contendo tanto o código do backend (`backend/`) quanto do frontend (`frontend/`) no mesmo repositório Git.
  - **Justificativa:** Esta abordagem simplifica o gerenciamento de dependências, facilita a consistência entre a API e o cliente, e agiliza o pipeline de CI/CD, já que uma única alteração de contrato na API pode ser implementada e validada no frontend na mesma Pull Request.

---

## 2. Diagramas da Arquitetura (Modelo C4)

### 2.1. Nível 1: Diagrama de Contexto do Sistema (C1)

Este diagrama mostra o sistema IABANK no seu ambiente, interagindo com usuários e sistemas externos.

```mermaid
graph TD
    subgraph "Ecossistema IABANK"
        A[IABANK SaaS Platform]
    end

    U1[Gestor / Administrador] -->|Gerencia e supervisiona via Web App| A
    U2[Consultor / Cobrador] -->|Executa operações via Web App| A

    A -.->|Integração Futura| SE1[Bureaus de Crédito]
    A -.->|Integração Futura| SE2[Plataformas Bancárias (Pix, Open Finance)]
    A -.->|Integração Futura| SE3[Plataformas de Comunicação (WhatsApp)]

    style A fill:#1E90FF,stroke:#333,stroke-width:2px,color:#fff
```

### 2.2. Nível 2: Diagrama de Containers (C2)

Este diagrama detalha as principais unidades executáveis que compõem a plataforma IABANK.

```mermaid
graph TD
    U[Usuário] -->|HTTPS via Navegador| F[Frontend SPA <br><strong>[React, TypeScript, Vite]</strong>]

    subgraph "Infraestrutura na Cloud"
        F -->|API REST (JSON/HTTPS)| B[Backend API <br><strong>[Python, Django, DRF]</strong>]
        B -->|Leitura/Escrita (TCP/IP)| DB[(PostgreSQL Database <br><strong>[Armazena dados de tenants, empréstimos, transações]</strong>)]
        B -->|Tarefas Assíncronas| Q[Fila de Tarefas <br><strong>[Redis]</strong>]
        W[Worker <br><strong>[Celery]</strong>] -->|Consome de| Q
        W -->|Executa lógica| B
        W -->|Leitura/Escrita| DB
    end

    style F fill:#61DAFB,stroke:#333,stroke-width:2px
    style B fill:#092E20,stroke:#333,stroke-width:2px,color:#fff
    style DB fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    style Q fill:#DC382D,stroke:#333,stroke-width:2px,color:#fff
    style W fill:#3776AB,stroke:#333,stroke-width:2px,color:#fff
```

### 2.3. Nível 3: Diagrama de Componentes (C3) - Backend API

Este diagrama detalha os principais componentes internos do container "Backend API".

```mermaid
graph TD
    subgraph "Container: Backend API (Django)"
        direction TB

        C1[Camada de Apresentação <br><strong>[DRF: ViewSets, Serializers]</strong><br><em>Recebe requisições HTTP, valida e serializa dados.</em>]
        C2[Camada de Aplicação <br><strong>[Serviços: LoanService, CustomerService]</strong><br><em>Orquestra casos de uso e transações.</em>]
        C3[Camada de Domínio <br><strong>[Django: Models, Managers, Lógica de Negócio Pura]</strong><br><em>Contém as regras e entidades de negócio.</em>]
        C4[Camada de Infraestrutura <br><strong>[ORM, Celery Clients, Gateways]</strong><br><em>Interage com DB, filas e sistemas externos.</em>]

        C1 --> C2
        C2 --> C3
        C2 --> C4
    end

    F[Frontend SPA] -->|Chama| C1
    C4 --> DB[(Database)]
```

---

## 3. Descrição dos Componentes, Interfaces e Modelos de Domínio

### 3.1. Consistência dos Modelos de Dados (SSOT do Domínio - `models.py`)

Esta é a Fonte Única da Verdade para todas as entidades de dados do IABANK. Todos os modelos incluem um campo `tenant` para garantir isolamento de dados (multi-tenancy) desde o início.

**Tecnologia Chave:** `Django ORM`

```python
# iabank/core/models.py (Modelos base)
from django.db import models
from django.contrib.auth.models import AbstractUser

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    # ... outros detalhes do tenant

class User(AbstractUser):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")
    # ... outros campos de usuário

class BaseTenantModel(models.Model):
    """Modelo abstrato para garantir que todos os dados sejam vinculados a um tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# -------------------------------------------------------------

# iabank/customers/models.py
class Customer(BaseTenantModel):
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=20, unique=True) # CPF/CNPJ
    birth_date = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    # Endereço
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=20, null=True, blank=True)
    complement = models.CharField(max_length=100, null=True, blank=True)
    neighborhood = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    # ... outros campos de cliente

# iabank/operations/models.py
class Consultant(BaseTenantModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # ... outros campos do consultor

class Loan(BaseTenantModel):
    class LoanStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'Em Andamento'
        PAID_OFF = 'PAID_OFF', 'Finalizado'
        IN_COLLECTION = 'IN_COLLECTION', 'Em Cobrança'
        CANCELED = 'CANCELED', 'Cancelado'

    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='loans')
    consultant = models.ForeignKey(Consultant, on_delete=models.PROTECT, related_name='loans')
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) # Taxa %
    number_of_installments = models.PositiveSmallIntegerField()
    contract_date = models.DateField()
    first_installment_date = models.DateField()
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.IN_PROGRESS)
    # ... outros campos do empréstimo

class Installment(BaseTenantModel):
    class InstallmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Vencida'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Parcialmente Pago'

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveSmallIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING)

# iabank/finance/models.py
class BankAccount(BaseTenantModel):
    name = models.CharField(max_length=100)
    agency = models.CharField(max_length=10, blank=True)
    account_number = models.CharField(max_length=20)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

class PaymentCategory(BaseTenantModel):
    name = models.CharField(max_length=100)

class CostCenter(BaseTenantModel):
    name = models.CharField(max_length=100)

class Supplier(BaseTenantModel):
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=20, null=True, blank=True)

class FinancialTransaction(BaseTenantModel):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Receita'
        EXPENSE = 'EXPENSE', 'Despesa'

    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=TransactionType.choices)

    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)
    category = models.ForeignKey(PaymentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    installment = models.OneToOneField('operations.Installment', on_delete=models.SET_NULL, null=True, blank=True) # Link para parcela de empréstimo
```

### 3.1.1. Detalhamento dos DTOs e Casos de Uso

**Tecnologia Chave:** `Pydantic`

```python
# iabank/operations/dtos.py
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

class LoanCreateDTO(BaseModel):
    customer_id: int
    consultant_id: int
    principal_amount: Decimal = Field(..., gt=0)
    interest_rate: Decimal = Field(..., ge=0)
    number_of_installments: int = Field(..., gt=0)
    contract_date: date
    first_installment_date: date

class LoanListDTO(BaseModel):
    id: int
    customer_name: str
    principal_amount: Decimal
    status: str
    contract_date: date

    class Config:
        orm_mode = True

class CustomerCreateDTO(BaseModel):
    name: str
    document_number: str
    email: str | None = None
    phone: str | None = None
    # ... outros campos para criação
```

### 3.2. Camada de Apresentação (UI)

#### Decomposição em Telas/Componentes

- **Telas (Views):** `Dashboard`, `LoanList`, `LoanDetails`, `NewLoanWizard`, `CustomerList`, `CustomerForm`, `AccountsPayable`, `Login`.
- **Componentes Reutilizáveis:** `SmartTable` (com filtros, paginação, seleção de colunas), `KPI_Card`, `WizardStepper`, `StatusBadge`, `FormInput`, `DatePicker`.

#### Contrato de Dados da View (ViewModel)

**Tecnologia Chave:** `TypeScript Interfaces`

```typescript
// frontend/src/features/loans/types/index.ts

// ViewModel para a tela de listagem de empréstimos
export interface LoanListViewModel {
  id: number;
  customerName: string;
  principalAmountFormatted: string; // "R$ 10.000,00"
  status: "IN_PROGRESS" | "PAID_OFF" | "IN_COLLECTION" | "CANCELED";
  statusLabel: string; // "Em Andamento"
  statusColor: "yellow" | "green" | "red" | "gray"; // Para o StatusBadge
  contractDateFormatted: string; // "dd/mm/yyyy"
  installmentsProgress: string; // "3/12"
}

// Mapeamento: Derivado do LoanListDTO do backend.
// O Serializer no DRF irá pré-calcular campos como `customer_name`.
// O frontend irá formatar valores monetários e datas e mapear o status para label/cor.

// frontend/src/features/customers/types/index.ts

// ViewModel para a tela de listagem de clientes
export interface CustomerListViewModel {
  id: number;
  name: string;
  documentNumberFormatted: string; // "123.456.789-00"
  phone: string;
  city: string;
  activeLoansCount: number;
}
```

---

## 4. Descrição Detalhada da Arquitetura Frontend

A arquitetura do frontend seguirá um padrão **Feature-based** (baseado em funcionalidades), que promove alta coesão e baixo acoplamento.

- **Padrão Arquitetural:** O código é organizado por fatias verticais de negócio (`features`), em vez de fatias horizontais por tipo de arquivo (`components`, `hooks`). Isso mantém toda a lógica de uma funcionalidade (ex: gestão de empréstimos) em um único lugar.

- **Estrutura de Diretórios Proposta (`frontend/src/`):**

  ```
  src/
  ├── app/                # Configuração global da aplicação (providers, store, router, styles)
  ├── pages/              # Componentes de página, que compõem layouts a partir das features
  ├── features/           # Funcionalidades de negócio (ex: loan-list, customer-form)
  │   ├── loan-list/
  │   │   ├── api/        # Hooks de API (TanStack Query) e definições de requisição
  │   │   ├── components/ # Componentes específicos desta feature (ex: LoanFilterPanel)
  │   │   ├── model/      # Types, schemas de validação (Zod)
  │   │   └── ui/         # O componente principal da feature (ex: LoanListTable.tsx)
  │   └── ...
  ├── entities/           # Componentes e lógica de entidades de negócio (ex: LoanCard, CustomerAvatar)
  └── shared/             # Código reutilizável e agnóstico de negócio
      ├── api/            # Configuração do cliente Axios/Fetch global
      ├── config/         # Constantes, configurações de ambiente
      ├── lib/            # Funções utilitárias, helpers, hooks genéricos
      └── ui/             # Biblioteca de componentes de UI puros (Button, Input, Table)
  ```

- **Estratégia de Gerenciamento de Estado:**

  - **Estado do Servidor:** **TanStack Query (React Query)** será a fonte da verdade para todos os dados assíncronos vindos da API. Ele gerenciará caching, revalidação, mutações e estados de loading/error de forma declarativa.
  - **Estado Global do Cliente:** **Zustand** será usado para estados globais síncronos e de baixa frequência de atualização, como informações do usuário autenticado, tema da UI ou estado de um menu lateral.
  - **Estado Local do Componente:** Os hooks nativos do React (`useState`, `useReducer`) serão usados para estado efêmero e contido dentro de um único componente (ex: estado de um input de formulário).

- **Fluxo de Dados:**
  1.  O usuário interage com um componente na camada `pages` ou `features`.
  2.  O componente dispara um hook da camada `features/api` (ex: `useLoans()`).
  3.  TanStack Query faz a chamada à API backend através do cliente configurado em `shared/api`.
  4.  A resposta da API é armazenada no cache do TanStack Query.
  5.  O hook `useLoans()` retorna os dados, que são passados para os componentes `entities` ou `shared/ui` para renderização.
  6.  Mutações (Create, Update, Delete) usam o hook `useMutation` do TanStack Query, que automaticamente revalida os dados relevantes após o sucesso da operação.

---

## 5. Definição das Interfaces Principais

Exemplo de interface para um serviço de aplicação no backend.

**Tecnologia Chave:** Python (Lógica Pura), Pydantic

```python
# iabank/operations/services.py
from .dtos import LoanCreateDTO
from .models import Loan
from ..customers.models import Customer
from .repositories import LoanRepository # Abstração do acesso a dados

class LoanService:
    def __init__(self, loan_repo: LoanRepository):
        """
        O serviço é inicializado com suas dependências (Injeção de Dependência).
        A configuração (ex: taxas padrão) pode ser passada aqui ou obtida
        de um serviço de configuração.
        """
        self.loan_repo = loan_repo

    def create_loan(self, tenant_id: int, loan_data: LoanCreateDTO) -> Loan:
        """
        Cria um novo empréstimo e suas parcelas.
        Responsabilidade: Orquestrar a lógica de negócio, validações e persistência
        dentro de uma transação atômica.
        """
        # 1. Validações de negócio (ex: cliente existe, consultor ativo)
        # 2. Lógica de cálculo de parcelas
        # 3. Persistência usando o repositório
        # 4. Criação de transações financeiras associadas
        # ...
        pass
```

---

## 6. Gerenciamento de Dados

- **Persistência e Acesso:** O **ORM do Django** será a principal ferramenta de acesso a dados. O padrão Repository pode ser usado em módulos complexos para abstrair as queries do ORM, facilitando os testes.
- **Gerenciamento de Schema:** As migrações de banco de dados serão gerenciadas pelo sistema nativo do Django (`makemigrations`, `migrate`), garantindo a evolução consistente do schema.
- **Seed de Dados:** Para ambientes de desenvolvimento e teste, serão criados **comandos de gerenciamento customizados** do Django (ex: `python manage.py seed_data`). Estes comandos utilizarão a biblioteca **`factory-boy`** para gerar dados fictícios, porém realistas e consistentes (respeitando as relações de tenant).

---

## 7. Estrutura de Diretórios Proposta (Monorepo)

```
iabank/
├── .github/
│   └── workflows/
│       └── main.yml           # Pipeline de CI/CD
├── backend/
│   ├── src/
│   │   └── iabank/
│   │       ├── __init__.py
│   │       ├── asgi.py
│   │       ├── settings.py
│   │       ├── urls.py
│   │       ├── wsgi.py
│   │       ├── core/            # App com modelos base, middlewares, etc.
│   │       ├── customers/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── admin.py
│   │       │   ├── apps.py
│   │       │   ├── serializers.py
│   │       │   ├── views.py
│   │       │   └── tests/
│   │       │       ├── __init__.py
│   │       │       ├── test_models.py
│   │       │       └── test_views.py
│   │       ├── finance/         # App Financeiro
│   │       ├── operations/      # App Operacional (Empréstimos, Consultores)
│   │       └── users/           # App de Usuários e Permissões
│   ├── manage.py
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── public/
│   ├── src/                 # Estrutura detalhada na seção 4
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── tests/
│   └── integration/
│       ├── __init__.py
│       └── test_full_loan_workflow.py
├── docker-compose.yml
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

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
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE files
.idea/
.vscode/
*.swp
*.swo

# node.js
node_modules/
dist/
dist-ssr/
*.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Docker
docker-compose.override.yml

# OS files
.DS_Store
Thumbs.db
```

---

## 9. Arquivo `README.md` Proposto

````markdown
# IABANK

[![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)](https://github.com/your-org/iabank)
[![CI/CD](https://github.com/your-org/iabank/actions/workflows/main.yml/badge.svg)](https://github.com/your-org/iabank/actions)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Sistema de gestão de empréstimos moderno e eficiente.

## Sobre o Projeto

O IABANK é uma plataforma Web SaaS robusta e segura, desenvolvida em Python e React, projetada para a gestão completa de empréstimos (end-to-end). A arquitetura é multi-tenant e foi concebida para ser escalável, intuitiva e adaptável.

## Stack Tecnológica

- **Backend:** Python 3.10+, Django, Django REST Framework
- **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS
- **Banco de Dados:** PostgreSQL
- **Cache & Fila de Tarefas:** Redis, Celery
- **Containerização:** Docker, Docker Compose

## Como Começar

### Pré-requisitos

- Docker e Docker Compose
- Node.js e pnpm (para o frontend)
- Python e Poetry (para o backend)

### Instalação e Execução

1.  Clone o repositório:

    ```bash
    git clone https://github.com/your-org/iabank.git
    cd iabank
    ```

2.  Crie um arquivo `.env` na raiz do projeto a partir do `.env.example`.

3.  Suba os contêineres Docker:

    ```bash
    docker-compose up -d --build
    ```

4.  A aplicação estará disponível em:
    - Frontend: `http://localhost:5173`
    - Backend API: `http://localhost:8000/api/`

## Como Executar os Testes

Para executar os testes do backend, entre no contêiner do Django e use o `pytest`:

```bash
docker-compose exec backend bash
pytest
```
````

## Estrutura do Projeto

O projeto é um monorepo com duas pastas principais:

- `/backend`: Contém a aplicação Django (API).
- `/frontend`: Contém a Single Page Application (SPA) em React.

Consulte o [Blueprint Arquitetural](docs/architecture.md) para mais detalhes.

```

---

## 10. Arquivo `LICENSE` Proposto

```

MIT License

Copyright (c) [Ano] [Nome do Proprietário do Copyright]

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

---

## 11. Arquivo `CONTRIBUTING.md` Proposto

```markdown
# Como Contribuir para o IABANK

Agradecemos o seu interesse em contribuir! Para garantir a qualidade e a consistência do projeto, pedimos que siga estas diretrizes.

## Processo de Desenvolvimento

1.  **Siga o Blueprint:** Todas as contribuições devem estar alinhadas com o [Blueprint Arquitetural](docs/architecture.md). Mudanças na arquitetura devem ser discutidas e aprovadas antes da implementação.
2.  **Crie uma Issue:** Antes de começar a trabalhar, abra uma issue descrevendo o bug ou a feature.
3.  **Crie um Branch:** Crie um branch a partir do `main` com um nome descritivo (ex: `feature/add-loan-export` ou `fix/login-bug`).
4.  **Desenvolva com Testes:** Todo novo código de negócio deve ser acompanhado de testes unitários e/ou de integração.
5.  **Abra um Pull Request:** Ao concluir, abra um Pull Request para o branch `main`. Descreva as suas alterações e vincule a issue correspondente.

## Qualidade de Código

Utilizamos ferramentas para garantir um padrão de código consistente.

*   **Backend (Python):**
    *   **Formatador:** [Black](https://github.com/psf/black)
    *   **Linter:** [Ruff](https://github.com/astral-sh/ruff)
*   **Frontend (TypeScript):**
    *   **Formatador:** [Prettier](https://prettier.io/)
    *   **Linter:** [ESLint](https://eslint.org/)

### Ganchos de Pre-commit

Configuramos ganchos de pre-commit usando a ferramenta `pre-commit` para executar essas checagens automaticamente antes de cada commit. Para instalar, execute:

```bash
pip install pre-commit
pre-commit install
````

Qualquer código que não passe nas verificações do linter/formatador será bloqueado.

## Padrão de Documentação

- **Python:** Todas as funções públicas, classes e métodos devem ter docstrings no estilo [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- **React:** Componentes complexos devem ter comentários explicando seu propósito, props e estado.

````

---

## 12. Estrutura do `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and architecture blueprint.

## [0.1.0] - YYYY-MM-DD

### Added
- ...
````

---

## 13. Estratégia de Configuração e Ambientes

A configuração será gerenciada usando a biblioteca **`django-environ`**.

- Um arquivo `.env` na raiz do `backend/` conterá as variáveis de ambiente para desenvolvimento local (ex: `DATABASE_URL`, `SECRET_KEY`, `DEBUG=True`). Este arquivo não deve ser versionado.
- Um arquivo `.env.example` será versionado para servir como template.
- Em ambientes de homologação e produção, as configurações serão injetadas diretamente como **variáveis de ambiente** no provedor de nuvem ou no orquestrador de contêineres. Isso garante que segredos nunca sejam armazenados em código.
- O arquivo `settings.py` do Django será o único ponto de leitura dessas variáveis, usando `env('VARIABLE_NAME', default='value')`.

---

## 14. Estratégia de Observabilidade Completa

- **Logging Estruturado:** Utilizaremos a biblioteca **`structlog`** para gerar logs em formato **JSON**. Em desenvolvimento, os logs serão formatados para leitura humana no console. Em produção, o output JSON será facilmente ingerido por serviços como Datadog, Sentry ou um stack ELK. Os logs incluirão contexto automático, como `request_id`, `user_id` e `tenant_id`.
- **Métricas de Negócio:** Serão expostas via um endpoint `/metrics` (usando `django-prometheus`). Métricas chave incluem: `loans_created_total`, `installments_paid_total`, `overdue_amount_total`, `api_request_latency_seconds`. Dashboards no Grafana ou similar visualizarão essas métricas.
- **Distributed Tracing:** Embora seja um monolito, o uso de `OpenTelemetry` será considerado desde o início para rastrear requisições. Isso será crucial quando futuras integrações (agentes de IA, sistemas externos) forem adicionadas.
- **Health Checks e SLIs/SLOs:**
  - Um endpoint `/health` será criado, retornando `200 OK` se os serviços essenciais (conexão com DB e Redis) estiverem funcionando.
  - **SLI:** Latência da API do endpoint `GET /api/v1/loans/` < 500ms.
  - **SLO:** 99.9% de disponibilidade mensal do sistema.
- **Alerting Inteligente:** **Sentry** será integrado para captura automática de exceções no backend e frontend. Alertas serão configurados para picos de erros (`5xx`), aumento de latência e anomalias nas métricas de negócio, com integração ao Slack/PagerDuty.

---

## 15. Estratégia de Testes Detalhada

- **Estrutura e Nomenclatura:**

  - **Testes Unitários:** Residem dentro de cada app Django, em `<app_name>/tests/`. Validam a lógica de um único componente isoladamente (ex: um método de modelo, uma função de serviço com dependências mockadas).
  - **Testes de Integração:** Residem no diretório de alto nível `tests/integration/`. Validam a interação entre múltiplos componentes (ex: um fluxo completo de API, desde a view até o banco de dados).
  - **Convenção de Nomenclatura:** Todos os arquivos de teste seguirão o padrão `test_<nome_do_modulo>.py` (ex: `test_models.py`, `test_serializers.py`).

- **Ferramentas:**

  - **Executor:** `pytest`
  - **Cliente de API:** Cliente de teste do Django REST Framework (`APIClient`).
  - **Dados Fictícios:** `factory-boy`.
  - **Mocks:** `unittest.mock`.

- **Padrões de Teste de Integração:**

  - **Uso de Factories:** `factory-boy` será mandatório para criar o estado inicial do banco de dados para os testes, garantindo consistência e legibilidade.
  - **Simulação de Autenticação:** Usaremos `api_client.force_authenticate(user=self.user)` para simular um usuário logado em testes de API, evitando o fluxo completo de login.

- **Padrões Obrigatórios para Test Data Factories (`factory-boy`):**

  - **Princípio da Herança Explícita de Contexto (Multi-tenancy):**

    - **Regra:** Factories que criam objetos aninhados **DEVEM** propagar o `tenant` da factory pai para todas as sub-factories.
    - **Exemplo Mandatório:**

      ```python
      # iabank/operations/tests/factories.py
      import factory
      from iabank.core.tests.factories import TenantFactory
      from iabank.customers.tests.factories import CustomerFactory
      from ..models import Loan

      class LoanFactory(factory.django.DjangoModelFactory):
          class Meta:
              model = Loan

          tenant = factory.SubFactory(TenantFactory)
          # CRÍTICO: Propagar o tenant para o cliente relacionado
          customer = factory.SubFactory(CustomerFactory, tenant=factory.SelfAttribute('..tenant'))
          # ... outros campos
      ```

  - **Testes Obrigatórios para Factories (Meta-testes):**

    - **Regra:** Para cada `factories.py`, um arquivo `test_factories.py` deve existir para validar a consistência dos dados gerados.
    - **Exemplo de teste crítico:**

      ```python
      # iabank/operations/tests/test_factories.py
      from django.test import TestCase
      from .factories import LoanFactory, TenantFactory

      class OperationFactoriesTestCase(TestCase):
          def test_loan_factory_tenant_consistency(self):
              """Garante que LoanFactory propaga o tenant para o cliente."""
              tenant = TenantFactory()
              loan = LoanFactory(tenant=tenant)

              self.assertEqual(loan.tenant, tenant)
              self.assertEqual(loan.customer.tenant, tenant, "O tenant do cliente deve ser o mesmo do empréstimo.")
      ```

---

## 16. Estratégia de CI/CD (Integração e Implantação Contínuas)

- **Ferramenta:** GitHub Actions (arquivo de workflow em `.github/workflows/main.yml`).
- **Gatilhos:** Em cada `push` para o branch `main` e em cada abertura/atualização de `Pull Request`.
- **Estágios do Pipeline:**
  1.  **CI (Validação em PR):**
      - **Setup:** Checkout do código, setup do Python e Node.js, instalação de dependências (com cache).
      - **Lint & Format:** Executa `ruff`, `black`, `eslint`, `prettier` para garantir a qualidade do código.
      - **Test:** Executa a suíte completa de testes unitários e de integração do backend e do frontend.
      - **Build:** Executa o build de produção do frontend (`pnpm build`) para garantir que não há erros.
  2.  **CD (Deploy em `main`):**
      - (Após sucesso da etapa de CI)
      - **Build & Push Images:** Constrói as imagens Docker do backend e frontend e as envia para um registro (ex: Docker Hub, AWS ECR). As imagens são tagueadas com o hash do commit.
      - **Deploy:** Um job separado (usando environments do GitHub Actions) se conecta ao ambiente de produção (ex: AWS, Heroku) e atualiza os serviços para usar as novas imagens.
  - **Rollback:** A estratégia de rollback será baseada em reverter o commit em `main` e deixar o pipeline de CD rodar novamente, ou implantar manualmente a tag da imagem Docker anterior que era estável.

---

## 17. Estratégia de Versionamento da API

A API será versionada via **URL**. Todas as rotas serão prefixadas com a versão, ex: `/api/v1/loans/`. Isso permite introduzir uma `v2` no futuro sem quebrar o cliente `v1` existente. A versão será gerenciada pelo `URLconf` do Django e pelo `DefaultRouter` do DRF.

---

## 18. Padrão de Resposta da API e Tratamento de Erros

- **Resposta de Sucesso (`2xx`):**
  ```json
  {
    "data": {
      /* objeto ou lista de objetos */
    },
    "meta": {
      "pagination": {
        "count": 100,
        "page": 1,
        "pages": 10,
        "per_page": 10
      }
    }
  }
  ```
- **Resposta de Erro (`4xx`, `5xx`):**
  ```json
  {
    "errors": [
      {
        "status": "422",
        "code": "validation_error",
        "source": { "pointer": "/data/attributes/principal_amount" },
        "detail": "Este campo não pode ser menor ou igual a zero."
      }
    ]
  }
  ```
  Um `ExceptionHandler` customizado no DRF será implementado para capturar todas as exceções e formatá-las neste padrão consistente.

---

## 19. Estratégia de Segurança Abrangente

- **Threat Modeling Básico:**
  - **Ameaça:** Acesso não autorizado a dados de outro tenant.
    - **Mitigação:** Middleware de Tenant obrigatório que injeta `tenant_id` em todas as queries. Testes de integração que verificam falha ao tentar acessar recursos de outro tenant.
  - **Ameaça:** Injeção de SQL.
    - **Mitigação:** Uso exclusivo do ORM do Django, que parametriza todas as queries.
  - **Ameaça:** Vazamento de segredos no código.
    - **Mitigação:** Uso de `pre-commit` hooks para detectar segredos e política rigorosa de uso de variáveis de ambiente.
- **Secrets Management:** Em produção, utilizaremos um serviço dedicado como **AWS Secrets Manager** ou **HashiCorp Vault**. As aplicações receberão permissões IAM para acessar apenas os segredos de que necessitam em tempo de execução.
- **Compliance (LGPD):** A arquitetura suporta os princípios da LGPD:
  - **RBAC:** O módulo "Usuários e Permissões" implementa o controle de acesso granular.
  - **Isolamento:** A arquitetura multi-tenant garante o isolamento dos dados dos titulares.
  - **Auditoria:** O módulo "Logs de Atividade" registra todas as operações críticas.
- **Security by Design:**
  - **Autenticação:** JWT (JSON Web Tokens) com tokens de acesso de curta duração e refresh tokens.
  - **Autorização:** Verificação de permissões em nível de API View, usando as classes de permissão do DRF.
  - **Defesa em Profundidade:** HTTPS obrigatório, headers de segurança (HSTS, CSP), proteção contra CSRF e XSS (nativa no Django/React).

---

## 20. Justificativas e Trade-offs

- **Monolito vs. Microserviços:**
  - **Decisão:** Monolito Modular.
  - **Justificativa:** Para a fase inicial e o tamanho da equipe, a complexidade operacional de microserviços (deploy, monitoramento, comunicação inter-serviços) superaria os benefícios. O monolito permite um desenvolvimento mais rápido e transações ACID mais simples. A estrutura modular interna mantém o código organizado e preparado para uma futura extração, se o sistema crescer em complexidade e escala.
  - **Trade-off:** Menor flexibilidade para escalar componentes individualmente e risco de acoplamento acidental se a disciplina de modularidade não for mantida.

---

## 21. Exemplo de Bootstrapping/Inicialização

A inicialização e injeção de dependências serão gerenciadas implicitamente pelo Django. Para os serviços da camada de aplicação, a instanciação ocorrerá dentro das Views do DRF, onde as dependências (como repositórios) serão passadas:

```python
# iabank/operations/views.py
from rest_framework.viewsets import ModelViewSet
from .services import LoanService
from .repositories import DjangoLoanRepository

class LoanViewSet(ModelViewSet):
    # ... queryset, serializer_class, etc.

    def get_loan_service(self):
        # A injeção de dependência acontece aqui
        loan_repo = DjangoLoanRepository()
        return LoanService(loan_repo=loan_repo)

    def perform_create(self, serializer):
        loan_service = self.get_loan_service()
        tenant_id = self.request.user.tenant_id
        # O DTO é construído a partir dos dados validados pelo serializer
        loan_dto = LoanCreateDTO(**serializer.validated_data)
        loan_service.create_loan(tenant_id=tenant_id, loan_data=loan_dto)

```

---

## 22. Estratégia de Evolução do Blueprint

- **Versionamento:** O próprio Blueprint será versionado usando **Semantic Versioning**. Mudanças que não quebram a estrutura (adição de um novo módulo) são `MINOR`. Mudanças que alteram a arquitetura fundamental (ex: mudança de monolito para microserviços) são `MAJOR`.
- **Processo de Evolução:** Mudanças arquiteturais significativas devem ser propostas através de um **Architectural Decision Record (ADR)**. Um ADR é um documento curto em markdown que descreve o contexto, a decisão tomada e as consequências.
- **Documentação (ADRs):** Será criada uma pasta `docs/adr/` no repositório para armazenar os ADRs, criando um registro histórico das decisões de arquitetura.

---

## 23. Métricas de Qualidade e Quality Gates

- **Cobertura de Código:** Mínimo de **85%** de cobertura de testes para todo o código de negócio. A cobertura será medida com `pytest-cov` e verificada no pipeline de CI.
- **Complexidade Ciclomática:** Nenhuma função/método deve exceder uma complexidade de **10**. Verificado estaticamente pelo `ruff`.
- **Quality Gates Automatizados (no CI):** Um Pull Request só poderá ser mesclado se:
  1.  Todos os testes passarem.
  2.  A cobertura de código não diminuir.
  3.  Nenhum erro de linter (`ruff`, `eslint`) for encontrado.
  4.  Nenhuma vulnerabilidade de segurança de criticidade alta for detectada por ferramentas de SAST (ex: Snyk, CodeQL).

---

## 24. Análise de Riscos e Plano de Mitigação

| Categoria       | Risco Identificado                                                                    | Probabilidade (1-5) | Impacto (1-5) | Score (P×I) | Estratégia de Mitigação                                                                                                                                                           |
| :-------------- | :------------------------------------------------------------------------------------ | :-----------------: | :-----------: | :---------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Segurança**   | Vazamento de dados entre tenants devido a falha na lógica de isolamento.              |          2          |       5       |     10      | Middleware mandatório para escopo de tenant, testes de integração para verificar o isolamento em cada endpoint crítico, code reviews focados em segurança.                        |
| **Negócio**     | Inconsistência nos cálculos financeiros (juros, parcelas, saldo devedor).             |          3          |       5       |     15      | Lógica de cálculo centralizada em módulos de domínio puros e bem definidos. Cobertura de testes unitários de 100% para toda a lógica de cálculo, com múltiplos cenários.          |
| **Técnico**     | Acoplamento excessivo entre os módulos do monolito, dificultando a manutenção futura. |          3          |       3       |      9      | Adoção rigorosa da arquitetura em camadas. Uso de interfaces (ABCs) para comunicação entre serviços de diferentes módulos. Revisões de arquitetura periódicas.                    |
| **Performance** | Lentidão em relatórios e listagens com grande volume de dados.                        |          4          |       3       |     12      | Otimização de queries (uso de `select_related`, `prefetch_related`), indexação estratégica de colunas no banco de dados, implementação de paginação em todas as APIs de listagem. |

---

## 25. Conteúdo dos Arquivos de Ambiente e CI/CD

### `pyproject.toml` Proposto

```toml
[tool.poetry]
name = "iabank"
version = "0.1.0"
description = "IABANK Backend API"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "iabank", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
django = "^4.2"
djangorestframework = "^3.14"
psycopg2-binary = "^2.9.9"
django-environ = "^0.11.2"
celery = "^5.3.6"
redis = "^5.0.1"
gunicorn = "^21.2.0"
pydantic = {extras = ["email"], version = "^1.10.13"}
structlog = "^23.2.0"
django-filter = "^23.3"
djangorestframework-simplejwt = "^5.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-django = "^4.7.0"
factory-boy = "^3.3.0"
pytest-cov = "^4.1.0"
black = "^23.11.0"
ruff = "^0.1.6"
pre-commit = "^3.5.0"

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I", "C90"]

[tool.black]
line-length = 88

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
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
    rev: 23.11.0
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
```

### `Dockerfile` Proposto (Backend)

```dockerfile
# --- Build Stage ---
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install poetry

COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# --- Final Stage ---
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/src/ .

USER app

EXPOSE 8000

CMD ["gunicorn", "iabank.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### `Dockerfile` Proposto (Frontend)

```dockerfile
# --- Build Stage ---
FROM node:18-alpine as builder

WORKDIR /app

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install

COPY frontend/ .
RUN pnpm build

# --- Final Stage ---
FROM nginx:1.25-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config if you have one
# COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```
