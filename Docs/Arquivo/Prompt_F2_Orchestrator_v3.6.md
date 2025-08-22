# AGV Prompt: OrchestratorHelper v3.6 (Granularidade Máxima)

**Tarefa Principal:** Analisar o `@Blueprint_Arquitetural.md`, que é a fonte única da verdade sobre a arquitetura. Suas responsabilidades são: (1) Derivar uma ordem de implementação lógica e (2) Gerar cenários chave para os Testes de Integração.

**Input Principal (Blueprint Arquitetural):**

## --- Conteúdo do Blueprint Arquitetural ---

# Blueprint Arquitetural: IABANK v1.0.0

Este documento define a arquitetura de alto nível, componentes, interfaces e padrões para o desenvolvimento da plataforma SaaS IABANK. Ele serve como a fonte única da verdade (SSOT) para a equipe de engenharia e produto.

## 1. Visão Geral da Arquitetura

A arquitetura escolhida para o IABANK é uma **Arquitetura em Camadas (Layered Architecture)** para o backend, servindo uma aplicação **Single-Page Application (SPA)** no frontend. Esta abordagem promove uma forte separação de responsabilidades, testabilidade e manutenibilidade.

- **Backend (Monólito Modular):** Um único serviço Django, mas estruturado internamente em "aplicações" que correspondem aos domínios de negócio (empréstimos, finanças, usuários). Isso oferece os benefícios de um monólito (simplicidade de deploy e transações atômicas) com a organização de microsserviços, facilitando uma futura transição, se necessário.
- **Frontend (SPA):** Uma aplicação React desacoplada que consome a API RESTful do backend. Toda a lógica de apresentação e estado da UI reside no cliente.

### Estratégia de Organização do Código-fonte

Adotaremos um **monorepo**, contendo tanto o código do backend (`backend/`) quanto do frontend (`frontend/`) no mesmo repositório Git.

**Justificativa:**
1.  **Desenvolvimento Simplificado:** Facilita a execução do ambiente de desenvolvimento completo com um único comando (`docker-compose up`).
2.  **Consistência de Contratos:** Manter a API e seu consumidor principal no mesmo repositório facilita a manutenção da consistência entre os DTOs do backend e os tipos do frontend.
3.  **CI/CD Unificado:** Um único pipeline pode construir, testar e implantar ambas as partes da aplicação de forma coordenada.

---

## 2. Diagramas da Arquitetura (Modelo C4)

### 2.1. Nível 1: Diagrama de Contexto do Sistema (C1)

Este diagrama mostra o IABANK no seu ambiente, interagindo com usuários e sistemas externos planejados.

```mermaid
graph TD
    subgraph "Ambiente IABANK"
        A[IABANK SaaS Platform]
    end

    U1[Gestor / Administrador] -->|Gerencia o sistema via [Web Browser]| A
    U2[Consultor / Cobrador] -->|Executa operações via [Web Browser]| A

    A -.->|Integração Futura| SE1[Bureaus de Crédito]
    A -.->|Integração Futura| SE2[Sistemas Bancários (Pix, Open Finance)]
    A -.->|Integração Futura| SE3[Plataformas de Comunicação (WhatsApp)]

    style A fill:#1f77b4,stroke:#fff,stroke-width:2px,color:#fff
    style U1 fill:#ff7f0e,stroke:#fff,stroke-width:2px,color:#fff
    style U2 fill:#2ca02c,stroke:#fff,stroke-width:2px,color:#fff
```

### 2.2. Nível 2: Diagrama de Containers (C2)

Este diagrama detalha as principais unidades executáveis/implantáveis que compõem a plataforma IABANK.

```mermaid
graph TD
    U[Usuário] -->|HTTPS| F[Frontend SPA <br> [React / Vite]]

    subgraph "Nuvem / Servidor"
        N[Nginx <br> [Reverse Proxy]]
        B[Backend API <br> [Python / Django]]
        DB[(PostgreSQL DB <br> [Dados Primários])]
        C[(Redis Cache <br> [Cache / Fila])]
        W[Celery Worker <br> [Tarefas Assíncronas]]
    end

    F -->|API REST (JSON)| N
    N -->|/api/*| B
    N -->|/*| F
    B -->|Leitura/Escrita [SQL]| DB
    B -->|Leitura/Escrita| C
    W -->|Leitura de Tarefas| C
    W -->|Leitura/Escrita [SQL]| DB

    style F fill:#17a2b8,stroke:#fff,stroke-width:2px,color:#fff
    style N fill:#6c757d,stroke:#fff,stroke-width:2px,color:#fff
    style B fill:#007bff,stroke:#fff,stroke-width:2px,color:#fff
    style DB fill:#333,stroke:#fff,stroke-width:2px,color:#fff
    style C fill:#dc3545,stroke:#fff,stroke-width:2px,color:#fff
    style W fill:#ffc107,stroke:#fff,stroke-width:2px,color:#000
```

### 2.3. Nível 3: Diagrama de Componentes (C3) - Backend API

Este diagrama detalha a arquitetura interna do container `Backend API`, seguindo o padrão de Arquitetura em Camadas.

```mermaid
graph TD
    subgraph "Container: Backend API (Django)"
        direction TB
        A[Apresentação (API Endpoints) <br> [Django REST Framework Views]]
        B[Aplicação (Serviços) <br> [Lógica de Caso de Uso / Orquestração]]
        D[Domínio (Core) <br> [Modelos, Regras de Negócio, Validações]]
        I[Infraestrutura <br> [Repositórios, Clientes Externos, Celery Tasks]]
    end

    A -->|Chama| B
    B -->|Usa| D
    B -->|Usa| I

    style A fill:#007bff,stroke:#fff,stroke-width:2px,color:#fff
    style B fill:#17a2b8,stroke:#fff,stroke-width:2px,color:#fff
    style D fill:#28a745,stroke:#fff,stroke-width:2px,color:#fff
    style I fill:#6c757d,stroke:#fff,stroke-width:2px,color:#fff
```

---

## 3. Descrição dos Componentes, Interfaces e Modelos de Domínio

### 3.1. Consistência dos Modelos de Dados (SSOT do Domínio)

Esta seção define a estrutura de dados central do IABANK. Todos os modelos são definidos aqui usando `django.db.models` e pertencem à Camada de **Domínio**. Eles são a fonte única da verdade para a persistência de dados.

#### **Core & Multi-tenancy Models**

```python
# iabank/core/models.py
from django.db import models
from django.conf import settings

class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class TenantAwareModel(models.Model):
    """Abstract base model for all models that belong to a tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True

# Custom QuerySet/Manager para garantir isolamento de dados
class TenantAwareManager(models.Manager):
    def get_queryset(self):
        # Esta lógica seria implementada com um middleware
        # que injeta o tenant atual na thread/request.
        # Ex: tenant = get_current_tenant()
        # return super().get_queryset().filter(tenant=tenant)
        return super().get_queryset()
```

#### **Administration & Users Models**

```python
# iabank/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from iabank.core.models import Tenant

class User(AbstractUser):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    # Adicionar campos adicionais se necessário

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Criação'
        UPDATE = 'UPDATE', 'Atualização'
        DELETE = 'DELETE', 'Exclusão'
        LOGIN = 'LOGIN', 'Login'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=Action.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField() # Detalhes da ação, como dados antigos e novos
```

#### **Operational Models (Empréstimos, Clientes, etc.)**

```python
# iabank/loans/models.py
from django.db import models
from iabank.core.models import TenantAwareModel, TenantAwareManager

class Customer(TenantAwareModel):
    # Aba 1: Dados Pessoais
    full_name = models.CharField(max_length=255)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    # Aba 2: Endereço e Contato
    zip_code = models.CharField(max_length=9)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    # Aba 3: Informações Financeiras
    income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    
    objects = TenantAwareManager()
    
class Consultant(TenantAwareModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consultant_profile')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    objects = TenantAwareManager()
    
class Lender(TenantAwareModel):
    """Credor Promissória"""
    name = models.CharField(max_length=255)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    address = models.CharField(max_length=255)
    
    objects = TenantAwareManager()

class Loan(TenantAwareModel):
    class LoanStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'Em Andamento'
        PAID_OFF = 'PAID_OFF', 'Finalizado'
        IN_COLLECTION = 'IN_COLLECTION', 'Em Cobrança'
        DEFAULTED = 'DEFAULTED', 'Inadimplente'
        
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='loans')
    consultant = models.ForeignKey(Consultant, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')
    lender = models.ForeignKey(Lender, on_delete=models.PROTECT, related_name='loans')
    
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) # Taxa mensal
    iof_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    number_of_installments = models.PositiveIntegerField()
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.IN_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantAwareManager()

class Installment(TenantAwareModel):
    class InstallmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Vencido'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Parcialmente Pago'

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=InstallmentStatus.choices, default=InstallmentStatus.PENDING)
    
    objects = TenantAwareManager()
    
    class Meta:
        unique_together = ('loan', 'installment_number')
```

#### **Financial Models**

```python
# iabank/financials/models.py
from django.db import models
from iabank.core.models import TenantAwareModel, TenantAwareManager

# Cadastros Gerais que suportam o financeiro
class Supplier(TenantAwareModel):
    name = models.CharField(max_length=255)
    
class PaymentCategory(TenantAwareModel):
    name = models.CharField(max_length=100)
    
class CostCenter(TenantAwareModel):
    name = models.CharField(max_length=100)

class PaymentMethod(TenantAwareModel):
    name = models.CharField(max_length=100)

class BankAccount(TenantAwareModel):
    name = models.CharField(max_length=100)
    agency = models.CharField(max_length=10, blank=True)
    account_number = models.CharField(max_length=20)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

class FinancialTransaction(TenantAwareModel):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Receita'
        EXPENSE = 'EXPENSE', 'Despesa'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Vencido'
    
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TransactionType.choices)
    status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    
    category = models.ForeignKey(PaymentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)

    # Vínculo com a origem da transação
    installment = models.OneToOneField('loans.Installment', on_delete=models.SET_NULL, null=True, blank=True)
    
    objects = TenantAwareManager()
```

### 3.1.1. Detalhamento dos DTOs e Casos de Uso

DTOs (Data Transfer Objects) definem os contratos da API. Serão implementados com `pydantic.BaseModel` e usados pela camada de **Aplicação (Serviços)**.

**Exemplo para o Caso de Uso "Novo Empréstimo":**

```python
# iabank/loans/dtos.py
import pydantic
from datetime import date

class CustomerCreateDTO(pydantic.BaseModel):
    full_name: str
    cpf_cnpj: str
    zip_code: str
    phone: str
    # ... outros campos essenciais para o cadastro rápido

class LoanCreateDTO(pydantic.BaseModel):
    customer_id: int | None = None
    new_customer: CustomerCreateDTO | None = None
    consultant_id: int
    lender_id: int
    principal_amount: pydantic.condecimal(max_digits=10, decimal_places=2)
    interest_rate: pydantic.condecimal(max_digits=5, decimal_places=2)
    number_of_installments: pydantic.PositiveInt
    start_date: date
```

### 3.2. Detalhamento da Camada de Apresentação (UI)

A UI será decomposta em Telas (Páginas), Funcionalidades (Features) e Componentes Reutilizáveis (UI Kit).

#### **Exemplo de Tela: `Empréstimos (Painel de Gestão)`**

-   **Propósito:** Listar, filtrar e gerenciar todos os empréstimos.
-   **Interação com Serviços Backend:**
    -   `GET /api/v1/loans/`: Para buscar a lista paginada de empréstimos.
    -   `GET /api/v1/loans/?status=IN_PROGRESS&...`: Para aplicar filtros.
    -   `DELETE /api/v1/loans/{id}/`: Para excluir um empréstimo.
    -   `PATCH /api/v1/loans/batch-update/`: Para ações em lote.

-   **Contrato de Dados da View (ViewModel):**
    -   **Estrutura (TypeScript):**
        ```typescript
        // frontend/src/features/loans/types.ts
        export interface LoanListItemViewModel {
          id: number;
          customerName: string;
          consultantName: string | null;
          principalAmountFormatted: string; // "R$ 5.000,00"
          installmentsProgress: string; // "3/12"
          status: 'IN_PROGRESS' | 'PAID_OFF' | 'IN_COLLECTION' | 'DEFAULTED';
          startDateFormatted: string; // "15/08/2023"
        }
        ```
    -   **Mapeamento de Origem:** Este ViewModel é montado no backend pelo `LoanListSerializer` do DRF. Ele combina dados dos modelos `Loan`, `Customer` e `Consultant`, aplicando formatação para os campos monetários e de data, e calculando o progresso das parcelas (`installmentsProgress`). A API retorna essa estrutura JSON diretamente, otimizada para exibição.

---

## 4. Descrição Detalhada da Arquitetura Frontend

A arquitetura do frontend seguirá uma variação do padrão **Feature-Sliced Design**, que promove escalabilidade e baixo acoplamento.

-   **Padrão Arquitetural:** O código será organizado por funcionalidades de negócio. Cada *slice* de funcionalidade (ex: `loans`, `customers`) contém seus próprios componentes, hooks, tipos e lógica de API, tornando-os independentes e fáceis de manter.

-   **Estrutura de Diretórios Proposta (`frontend/src/`):**

    ```
    src/
    ├── app/                # Configuração global da aplicação (provedores, roteador, store global)
    ├── pages/              # Componentes de página, que compõem layouts a partir de features e widgets
    ├── features/           # Funcionalidades de negócio (ex: criar-empréstimo, filtrar-clientes)
    ├── entities/           # Entidades de negócio (ex: card de Empréstimo, modelo de Cliente)
    └── shared/             # Código reutilizável e agnóstico de negócio
        ├── api/            # Configuração do Axios, hooks de API gerados, tipos de DTOs
        ├── lib/            # Funções utilitárias (formatação de data, validação)
        ├── ui/             # UI Kit: Componentes puros e burros (Button, Input, Table, Badge)
        └── assets/         # Imagens, fontes, etc.
    ```

-   **Estratégia de Gerenciamento de Estado:**

    -   **Estado do Servidor:** **TanStack Query (React Query)** será a fonte da verdade para todos os dados assíncronos vindos da API. Ele gerenciará fetching, caching, revalidação e mutações.
    -   **Estado Global do Cliente:** **Zustand** será usado para estados globais síncronos e de baixa frequência de atualização, como informações do usuário autenticado e estado do menu lateral (aberto/fechado).
    -   **Estado Local do Componente:** O estado nativo do React (`useState`, `useReducer`, `React Hook Form`) será usado para controlar o estado de formulários, modais e outros elementos de UI que não precisam ser compartilhados.

-   **Fluxo de Dados (Exemplo: Filtrando Empréstimos):**
    1.  O usuário interage com os componentes de filtro na `pages/LoansPage`.
    2.  O estado do filtro é gerenciado localmente (ex: `useState`).
    3.  A alteração no filtro dispara a re-execução do hook `useQuery` (de TanStack Query).
    4.  O hook `useQuery` chama a função de API (ex: `api.loans.getList({ status: 'PAID_OFF' })`).
    5.  TanStack Query gerencia o estado da requisição (`isLoading`, `isSuccess`, `data`, `error`).
    6.  A `pages/LoansPage` re-renderiza com a nova lista de dados (ou o estado de loading), passando os dados para os componentes da camada `entities/` (ex: `LoanRow`).

---

## 5. Definição das Interfaces Principais (Backend)

Interfaces definem contratos entre as camadas.

-   **Interface do Serviço de Empréstimos:**
    ```python
    # iabank/loans/services.py
    from .dtos import LoanCreateDTO
    from .models import Loan
    from .repositories import LoanRepository

    class LoanService:
        def __init__(self, loan_repo: LoanRepository):
            self.loan_repo = loan_repo

        def create_loan(self, dto: LoanCreateDTO) -> Loan:
            """
            Cria um novo empréstimo e suas parcelas.
            Valida regras de negócio.
            Operação atômica.
            """
            # ... lógica de negócio ...
            return self.loan_repo.create(...)
    ```
    -   **Construção e Configuração:** A instância do `LoanRepository` é injetada via construtor (`__init__`), promovendo desacoplamento e facilitando testes (podemos injetar um repositório mockado).

---

## 6. Gerenciamento de Dados

-   **Persistência e Acesso:** O **ORM do Django** será a principal ferramenta de acesso a dados. O **Padrão Repository** será aplicado para encapsular consultas complexas e isolar a camada de aplicação dos detalhes de implementação do ORM.
-   **Gerenciamento de Schema:** As migrações de banco de dados serão gerenciadas pelo sistema de **`migrations` nativo do Django** (`manage.py makemigrations` e `manage.py migrate`).
-   **Seed de Dados:** Para o ambiente de desenvolvimento, serão criados **comandos de gerenciamento customizados do Django** (ex: `manage.py seed_data`) que usarão a biblioteca `factory-boy` para popular o banco de dados com dados fictícios consistentes.

---

## 7. Estrutura de Diretórios Proposta (Backend)

Adotaremos o layout `src` para o backend, promovendo um empacotamento mais limpo.

```
iabank-monorepo/
├── backend/
│   ├── src/
│   │   └── iabank/
│   │       ├── __init__.py
│   │       ├── asgi.py
│   │       ├── wsgi.py
│   │       ├── settings.py
│   │       ├── urls.py
│   │       ├── core/          # Lógica compartilhada, Tenant model, base models
│   │       ├── users/         # App de usuários e autenticação
│   │       ├── loans/         # App para Empréstimos, Clientes, Consultores
│   │       │   ├── models.py
│   │       │   ├── dtos.py
│   │       │   ├── services.py
│   │       │   ├── repositories.py
│   │       │   ├── api/
│   │       │   │   ├── urls.py
│   │       │   │   ├── views.py
│   │       │   │   └── serializers.py
│   │       │   └── tests/
│   │       │       ├── test_models.py
│   │       │       └── test_services.py
│   │       ├── financials/    # App para o módulo financeiro
│   │       └── ...            # Outros apps de negócio
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── ... (estrutura já detalhada)
│   ├── index.html
│   ├── package.json
│   └── Dockerfile
├── .gitignore
├── docker-compose.yml
├── README.md
└── ...
```

---

## 8. Arquivo `.gitignore` Proposto

```gitignore
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
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak
venv.bak

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/

# node.js
node_modules/
.npm
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*
report.[0-9]*.[0-9]*.[0-9]*.[0-9]*.json
.pnp.*

# build output
dist
dist-ssr
.output
.vite-inspect/

# IDEs
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
```

---

## 9. Arquivo `README.md` Proposto

```markdown
# IABANK - Sistema de Gestão de Empréstimos

![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Django](https://img.shields.io/badge/Django-4.x-green)
![React](https://img.shields.io/badge/React-18%2B-blue)

## Sobre o Projeto

**IABANK** é uma plataforma Web SaaS robusta e segura, desenvolvida em Python e React, projetada para a gestão completa de empréstimos (end-to-end). Foi concebida para ser escalável, intuitiva e adaptável às necessidades de instituições financeiras de diversos portes.

A visão futura é integrar um ecossistema de agentes de IA para automatizar todo o ciclo de vida de um empréstimo, minimizando a intervenção humana e otimizando a eficiência operacional.

## Stack Tecnológica

-   **Backend:** Python, Django, Django REST Framework
-   **Frontend:** TypeScript, React, Vite, Tailwind CSS
-   **Banco de Dados:** PostgreSQL
-   **Cache & Fila de Tarefas:** Redis, Celery
-   **Infraestrutura:** Docker, Nginx

## Como Começar

### Pré-requisitos

-   Docker
-   Docker Compose

### Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu-usuario/iabank.git
    cd iabank
    ```

2.  **Crie o arquivo de ambiente:**
    Copie o arquivo de exemplo `backend/.env.example` para `backend/.env` e preencha as variáveis necessárias.

3.  **Suba os containers com Docker Compose:**
    ```bash
    docker-compose up --build
    ```

4.  **Acesse as aplicações:**
    -   Frontend: `http://localhost:5173`
    -   Backend API: `http://localhost:8000/api/v1/`

### Como Executar os Testes

Para executar os testes do backend, entre no container do backend e use o pytest:

```bash
# Encontre o ID do container do backend
docker ps

# Acesse o shell do container
docker exec -it <container_id_backend> /bin/bash

# Execute os testes
pytest
```

## Estrutura do Projeto

O projeto é um monorepo com a seguinte estrutura principal:

-   `backend/`: Contém a aplicação Django (API).
-   `frontend/`: Contém a aplicação React (SPA).
-   `docker-compose.yml`: Orquestra os serviços necessários para o ambiente de desenvolvimento.

Para mais detalhes, consulte o Blueprint Arquitetural.
```

---

## 10. Arquivo `LICENSE` Proposto

A licença **MIT** é uma excelente escolha padrão, pois é permissiva e amplamente compatível.

```
MIT License

Copyright (c) 2024 IABANK Project

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

---

## 11. Arquivo `CONTRIBUTING.md` Proposto

```markdown
# Como Contribuir para o IABANK

Agradecemos seu interesse em contribuir! Para garantir a qualidade e a consistência do projeto, pedimos que siga estas diretrizes.

## Processo de Desenvolvimento

1.  **Siga o Blueprint Arquitetural:** Todas as contribuições devem estar alinhadas com a arquitetura, padrões e tecnologias definidos no Blueprint.
2.  **Crie uma Issue:** Antes de iniciar um trabalho significativo, abra uma issue para discutir a mudança proposta.
3.  **Crie um Pull Request:** Desenvolva sua funcionalidade em um branch separado e abra um Pull Request para o branch `main`. Descreva claramente as mudanças e vincule o PR à issue correspondente.

## Qualidade de Código

A qualidade do código é fundamental. Automatizamos a verificação de qualidade usando ferramentas de linting e formatação.

-   **Backend (Python):**
    -   **Linter:** Ruff
    -   **Formatador:** Black
-   **Frontend (TypeScript/React):**
    -   **Linter:** ESLint
    -   **Formatador:** Prettier

### Ganchos de Pre-commit

Recomendamos fortemente o uso de `pre-commit` para executar essas checagens automaticamente antes de cada commit.

1.  Instale o `pre-commit`: `pip install pre-commit`
2.  Instale os ganchos no repositório: `pre-commit install`

Agora, a cada `git commit`, os formatadores e linters serão executados nos arquivos modificados.

## Documentação de Código

-   **Docstrings:** Todas as funções públicas, classes e métodos devem ter docstrings no estilo Google.
    ```python
    def minha_funcao(param1: int, param2: str) -> bool:
        """
        Esta é uma breve descrição da função.

        Args:
            param1: Descrição do primeiro parâmetro.
            param2: Descrição do segundo parâmetro.

        Returns:
            True se for bem-sucedido, False caso contrário.
        """
        # ...
    ```
-   **Comentários:** Use comentários para explicar o "porquê" de um código complexo, não o "o quê".

## Testes

-   Novas funcionalidades devem ser acompanhadas de testes unitários e/ou de integração.
-   Correções de bugs devem incluir um teste que falhava antes da correção e passa depois dela.
-   Todos os testes devem passar no pipeline de CI para que um PR seja aceito.
```

---

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

## [0.1.0] - YYYY-MM-DD

### Added
-   Estrutura inicial do projeto e Blueprint Arquitetural.
-   Configuração de Docker, CI/CD inicial e ferramentas de qualidade.
```

---

## 13. Estratégia de Configuração e Ambientes

-   **Ferramenta:** `django-environ` será utilizada no backend.
-   **Método:** As configurações serão lidas de variáveis de ambiente. Para desenvolvimento local, um arquivo `.env` na raiz do diretório `backend/` será usado para simular essas variáveis.
-   **Segredos:** Chaves de API, senhas e outros segredos **NUNCA** serão commitados no repositório. Eles serão gerenciados exclusivamente por variáveis de ambiente, que em produção serão injetadas pelo sistema de orquestração (ex: Kubernetes Secrets, Váriaveis de Ambiente do serviço de PaaS).
-   **Ambientes:**
    -   `development`: Configurações para depuração fácil (`DEBUG=True`), banco de dados local.
    -   `testing`: Banco de dados em memória ou separado para execução de testes.
    -   `production`: Configurações otimizadas para performance e segurança (`DEBUG=False`, logging robusto, domínios permitidos, etc.).

---

## 14. Estratégia de Observabilidade Completa

-   **Logging Estruturado:**
    -   Toda a aplicação (Django) será configurada para emitir logs no formato **JSON**.
    -   Cada log conterá um contexto rico, como `tenant_id`, `user_id`, `request_id`, para facilitar a filtragem e correlação de eventos.
    -   Em produção, os logs serão coletados por um serviço de agregação (ex: Datadog, Sentry, ELK Stack).
-   **Métricas de Negócio:**
    -   Usaremos `django-prometheus` para expor um endpoint `/metrics`.
    -   Métricas a serem coletadas:
        -   `loans_created_total`: Contador de novos empréstimos.
        -   `loan_principal_amount_sum`: Valor total emprestado.
        -   `active_users`: Gauge de usuários ativos.
        -   `api_request_duration_seconds`: Histograma da latência das APIs.
-   **Distributed Tracing:**
    -   Embora seja um monólito, a base para tracing será estabelecida usando **OpenTelemetry**. Cada requisição receberá um `trace_id` único, que será incluído em todos os logs e chamadas de tarefas Celery relacionadas a essa requisição. Isso será crucial quando futuras integrações forem adicionadas.
-   **Health Checks e SLIs/SLOs:**
    -   Um endpoint `/health` será criado, verificando a conectividade com o Banco de Dados e Redis.
    -   **SLI (Indicador):** Disponibilidade da API (taxa de sucesso de requisições). Latência da API (percentil 95).
    -   **SLO (Objetivo):** Disponibilidade > 99.9%. Latência P95 < 500ms.
-   **Alerting Inteligente:**
    -   Alertas serão configurados na ferramenta de monitoramento (ex: Prometheus Alertmanager, Datadog Monitors).
    -   Os alertas serão acionados por:
        -   Taxa de erro da API > 1% em 5 minutos.
        -   Latência P99 > 2 segundos.
        -   Fila do Celery com mais de 100 tarefas por mais de 10 minutos.

---

## 15. Estratégia de Testes Detalhada

-   **Estrutura e Convenção de Nomenclatura:**
    -   Os testes para cada app Django residirão em seu diretório `tests/`.
    -   Arquivos de teste seguirão o padrão `test_<modulo>.py` (ex: `loans/tests/test_services.py`, `loans/tests/test_api.py`).
-   **Tipos de Teste:**
    -   **Unitários:** Testarão a lógica pura em serviços, repositórios e funções utilitárias, com dependências mockadas. Ferramenta: `pytest` com `unittest.mock`.
    -   **Integração:** Testarão o fluxo completo através das camadas para um caso de uso, desde a view da API até o banco de dados. O foco é garantir que os componentes interajam corretamente.
    -   **End-to-End (API):** Usaremos o `APIClient` do DRF para simular requisições HTTP completas aos endpoints, validando a resposta, o status code e os efeitos colaterais no banco de dados.
-   **Padrões de Teste de Integração:**
    -   **Uso de Factories:** A biblioteca `factory-boy` será utilizada para criar instâncias de modelos Django nos testes. Isso torna os testes mais legíveis e fáceis de manter.
        ```python
        # loans/factories.py
        import factory
        from .models import Customer

        class CustomerFactory(factory.django.DjangoModelFactory):
            class Meta:
                model = Customer
            full_name = factory.Faker('name')
            # ...
        ```
    -   **Simulação de Autenticação:** Nos testes de API que exigem autenticação, usaremos o método `APIClient.force_authenticate(user=user)` do DRF. Isso evita a necessidade de simular o fluxo de login em cada teste.
    -   **Escopo de Teste:** Cada teste de integração focará em um único caso de uso. A configuração inicial (criação de tenant, usuário, etc.) será feita no `setUp` do teste usando as factories.

---

## 16. Estratégia de CI/CD

-   **Ferramenta:** **GitHub Actions**.
-   **Gatilhos:** Em cada `push` para `main` e em cada abertura/atualização de `Pull Request`.
-   **Estágios do Pipeline (`.github/workflows/main.yml`):**
    1.  **Setup:** Checkout do código e configuração do ambiente (Python, Node.js, cache de dependências).
    2.  **Lint & Format Check (Paralelo):**
        -   Job 1 (Backend): `ruff check` e `black --check`.
        -   Job 2 (Frontend): `npm run lint` e `npm run format:check`.
    3.  **Test (Paralelo):**
        -   Job 1 (Backend): `pytest --cov` (com coverage report).
        -   Job 2 (Frontend): `npm test`.
    4.  **Build:**
        -   Construção das imagens Docker para o backend e frontend.
    5.  **Push (Somente em `main`):**
        -   Tag das imagens com o hash do commit e/ou versão.
        -   Push das imagens para um container registry (ex: Docker Hub, GHCR, AWS ECR).
    6.  **Deploy (Somente em `main`):**
        -   Gatilho para um processo de deploy no ambiente de produção (ex: `helm upgrade`, `eb deploy`).
    -   **Rollback:** A estratégia de rollback será baseada em re-implantar a versão estável anterior da imagem Docker, que estará tagueada e disponível no registry.

---

## 17. Estratégia de Versionamento da API

A API será versionada via URL para garantir clareza e evitar breaking changes para os clientes.
-   **Formato:** `/api/v1/resource`
-   **Implementação:** Usaremos o `URLPathVersioning` do DRF ou um `Namespace` no `urls.py` do Django.
-   Quando uma mudança que quebra o contrato for necessária, uma nova versão (`v2`) será criada, e a `v1` será mantida por um período de deprecação.

---

## 18. Padrão de Resposta da API e Tratamento de Erros

-   **Resposta de Sucesso (`2xx`):**
    ```json
    {
      "data": { ... } // Objeto único ou array de objetos
    }
    // Para listagens paginadas:
    {
      "count": 100,
      "next": "http://.../?page=3",
      "previous": "http://.../?page=1",
      "results": [ ... ]
    }
    ```
-   **Resposta de Erro (`4xx`, `5xx`):**
    -   Um `exception handler` customizado do DRF será implementado.
    -   **Formato:**
        ```json
        {
          "error": {
            "code": "validation_error", // Ex: "not_found", "authentication_failed"
            "message": "Ocorreu um erro de validação.",
            "details": { // Opcional, para erros de validação
              "cpf_cnpj": ["Este campo não pode ser em branco."],
              "email": ["Insira um email válido."]
            }
          }
        }
        ```

---

## 19. Estratégia de Segurança Abrangente

-   **Threat Modeling Básico:**
    -   **Ameaça 1: Acesso não autorizado a dados de outro tenant.**
        -   **Mitigação:** Implementação de um middleware e um manager customizado (`TenantAwareManager`) que injeta `WHERE tenant_id = ?` em **TODAS** as queries SQL automaticamente. Testes de integração garantirão que um usuário do tenant A não possa acessar dados do tenant B, mesmo que saiba o ID do objeto.
    -   **Ameaça 2: Injeção de SQL (SQLi).**
        -   **Mitigação:** Uso exclusivo do ORM do Django, que parametriza todas as consultas por padrão, prevenindo esta classe de ataque.
    -   **Ameaça 3: Vazamento de senhas.**
        -   **Mitigação:** Uso do sistema de hashing de senhas padrão do Django (PBKDF2), que é robusto e seguro.
-   **Estratégia de Secrets Management:**
    -   Para produção, utilizaremos um serviço de gerenciamento de segredos, como **AWS Secrets Manager** ou **HashiCorp Vault**. A aplicação receberá apenas uma role/identidade com permissão para ler os segredos em tempo de execução, em vez de armazená-los em variáveis de ambiente.
-   **Compliance Framework (LGPD):**
    -   **Controles:**
        -   **Logs de Auditoria:** O modelo `AuditLog` registrará todas as operações críticas (CRUD) e quem as realizou.
        -   **RBAC:** O sistema de permissões do Django permitirá a aplicação do princípio do menor privilégio.
        -   **Criptografia:** TLS/HTTPS obrigatório para todo o tráfego. Dados sensíveis em repouso (se houver, como documentos) serão criptografados.
        -   **Direito ao Esquecimento:** A arquitetura com `on_delete=models.CASCADE` e `PROTECT` facilita a implementação de rotinas de anonimização ou exclusão de dados de um titular (`Customer`).

---

## 20. Justificativas e Trade-offs

-   **Monólito vs. Microsserviços:** A escolha do Monólito Modular no início reduz a complexidade operacional e de desenvolvimento. O trade-off é um acoplamento maior entre os módulos, mas a organização interna em apps Django mitiga esse risco e mantém a porta aberta para uma futura extração de serviços.
-   **Monorepo vs. Multi-repo:** O monorepo simplifica o setup e o CI/CD para uma equipe pequena/média. O trade-off é que o repositório pode crescer bastante, mas ferramentas modernas lidam bem com isso.

---

## 21. Exemplo de Bootstrapping/Inicialização

O ponto de entrada da aplicação (`asgi.py`/`wsgi.py`) e os arquivos de configuração (`settings.py`) do Django já fornecem um bootstrapping claro. A injeção de dependência será explícita, como no exemplo do `LoanService`.

**Exemplo conceitual da View da API:**
```python
# iabank/loans/api/views.py
from rest_framework.views import APIView
from iabank.loans.services import LoanService
from iabank.loans.repositories import LoanRepository

class LoanCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # 1. Instanciação e injeção de dependência
        repo = LoanRepository()
        service = LoanService(loan_repo=repo)

        # 2. Criação do DTO a partir dos dados da request
        dto = LoanCreateDTO(**request.data)

        # 3. Chamada do serviço
        new_loan = service.create_loan(dto)

        # 4. Serialização da resposta
        serializer = LoanDetailSerializer(new_loan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

---

## 22. Estratégia de Evolução do Blueprint

-   **Versionamento:** Este Blueprint seguirá o Versionamento Semântico (ex: v1.0.0, v1.1.0).
-   **Processo de Evolução:**
    1.  **Proposta:** Mudanças significativas devem ser propostas através de uma **ADR (Architecture Decision Record)**.
    2.  **Documentação:** As ADRs serão armazenadas em um diretório `/docs/adr` no formato `NNN-titulo-da-decisao.md`.
    3.  **Revisão:** A ADR será revisada pela equipe de engenharia em um Pull Request.
    4.  **Implementação:** Após a aprovação, o Blueprint é atualizado para uma nova versão, e a implementação pode começar.

---

## 23. Métricas de Qualidade e Quality Gates

-   **Cobertura de Código:** Meta mínima de **85%** para a lógica de negócio nos apps Django. Medido com `pytest-cov`.
-   **Complexidade Ciclomática:** Limite máximo de **10** por função/método. Verificado com `radon` ou ferramentas similares.
-   **Quality Gates Automatizados (no CI):**
    1.  **Linting:** 100% de aprovação nos linters (sem erros).
    2.  **Testes:** 100% dos testes devem passar.
    3.  **Cobertura:** A cobertura de código não pode diminuir em um Pull Request.
    4.  **Análise de Segurança:** Nenhuma vulnerabilidade de severidade `HIGH` ou `CRITICAL` pode ser introduzida (verificado por ferramentas como Snyk ou Dependabot).

---

## 24. Análise de Riscos e Plano de Mitigação

| Categoria | Risco Identificado | Probabilidade (1-5) | Impacto (1-5) | Score (P×I) | Estratégia de Mitigação |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Segurança** | **Vazamento de dados entre tenants** | 3 | 5 | **15** | Implementação rigorosa do isolamento de tenant na camada de dados (middleware + manager), com testes de integração específicos para validar a proteção contra acesso cruzado. |
| **Técnico** | Débito técnico acumulado devido a prazos, dificultando a manutenção futura | 4 | 3 | **12** | Adoção de Quality Gates no CI/CD (lint, testes, cobertura). Alocação de tempo para refatoração técnica em cada ciclo de desenvolvimento. Uso de ADRs para decisões importantes. |
| **Performance**| Degradação da performance da API e do banco de dados com o aumento do volume de dados | 3 | 4 | **12** | Otimização de queries (uso de `select_related`, `prefetch_related`), indexação estratégica de colunas no DB, implementação de cache (Redis) para dados de leitura frequente e relatórios. |
| **Negócio** | Baixa adoção do produto por dificuldade de uso ou falta de funcionalidades chave | 3 | 4 | **12** | Ciclos de desenvolvimento curtos e iterativos (Agile), com coleta contínua de feedback dos usuários. Foco na UX desde o início, como os assistentes (wizards) e tabelas inteligentes. |

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
