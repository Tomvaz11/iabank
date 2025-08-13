# **Blueprint Arquitetural: IABANK v1.0**

## **1. Visão Geral da Arquitetura**

A arquitetura escolhida para o `IABANK` é uma **Arquitetura em Camadas (Layered Architecture)**, fortemente inspirada nos princípios da Clean Architecture e da Arquitetura Hexagonal. Esta abordagem desacopla o Frontend (SPA) do Backend (API Monolítica), comunicando-se exclusivamente via uma API RESTful.

**Justificativa:**

*   **Modularidade e Manutenibilidade:** A separação estrita em camadas (Apresentação, Aplicação, Domínio, Infraestrutura) garante que a lógica de negócio (Domínio) permaneça pura e independente de frameworks (Django) e detalhes de implementação (PostgreSQL). Isso é vital para a longevidade e evolução do sistema.
*   **Testabilidade:** Cada camada pode ser testada de forma isolada. A lógica de negócio pode ser testada sem um banco de dados ou servidor web, e a camada de API pode ser testada com serviços "mockados".
*   **Pronto para o Futuro:** Esta arquitetura facilita a integração futura com Agentes de IA e sistemas externos. Um novo "adaptador" de IA pode ser conectado à Camada de Aplicação sem alterar o core do sistema. A lógica para interagir com o WhatsApp, por exemplo, seria apenas mais um adaptador na camada de infraestrutura.
*   **Multi-tenancy Simplificada:** A abordagem permite injetar o contexto do *tenant* de forma centralizada na camada de acesso a dados, garantindo o isolamento de forma robusta e auditável.

## **2. Diagrama de Componentes (Simplificado)**

```mermaid
graph TD
    subgraph Frontend [Painel Web - React SPA]
        UI_Components[Componentes de UI - React]
        State_Management[Gerenciamento de Estado - TanStack Query]
        API_Client[Cliente API - Axios/Fetch]
    end

    subgraph Backend [Servidor - Python/Django]
        subgraph Presentation_Layer [Camada de Apresentação/API]
            A1[Django REST Framework - Views & Serializers]
            A2[Autenticação/Autorização - JWT & RBAC Middleware]
        end

        subgraph Application_Layer [Camada de Aplicação]
            B1[Serviços de Aplicação (Use Cases)]
            B2[Interfaces/Portas (ex: ILoanRepository)]
            B3[DTOs (Data Transfer Objects)]
        end

        subgraph Domain_Layer [Camada de Domínio]
            C1[Modelos de Domínio (Entidades)]
            C2[Regras de Negócio & Validações]
            C3[Eventos de Domínio (opcional)]
        end

        subgraph Infrastructure_Layer [Camada de Infraestrutura]
            D1[ORM Django & PostgreSQL (Adapters de Repositório)]
            D2[Celery & Redis (Filas de Tarefas)]
            D3[Adapters para APIs Externas (Bureaus, Open Finance)]
            D4[Logs & Auditoria]
        end
    end

    %% Conexões
    UI_Components --> State_Management;
    State_Management --> API_Client;
    API_Client -- HTTP/REST --> A1;

    A1 --> B1;
    B1 --> B2;
    B1 --> C1;
    B1 --> C2;

    D1 -- implements --> B2;
    D2 -- implements --> B2;

    B1 -- usa --> D1;
    B1 -- usa --> D2;
```

## **3. Descrição dos Componentes, Interfaces e Modelos de Domínio**

### **3.1. Camada de Domínio (`src/iabank/domain`) - SSOT do Domínio**

Esta camada contém a lógica de negócio pura e os modelos canônicos do sistema. É o coração do IABANK e não tem dependências de frameworks externos.

*   **Responsabilidade Principal:** Definir as entidades de negócio, suas regras, estados e comportamentos. Servir como a Fonte Única da Verdade para todas as estruturas de dados.
*   **Tecnologias Chave:** Pydantic `BaseModel` para definição dos modelos. Python (Lógica Pura) para regras.

#### **Modelos de Domínio (SSOT):**

```python
# Em: src/iabank/domain/models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

class Tenant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    email: EmailStr
    hashed_password: str
    role: str # Ex: 'admin', 'manager', 'consultant'
    is_active: bool = True

class Customer(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    document_number: str # CPF/CNPJ
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_zip_code: Optional[str] = None
    address_street: Optional[str] = None
    # ... outros campos de cliente
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Loan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    customer_id: UUID
    consultant_id: Optional[UUID] = None
    principal_amount: Decimal
    interest_rate: Decimal # Taxa mensal, ex: 0.05 para 5%
    number_of_installments: int
    status: str # 'active', 'paid', 'late', 'default'
    origination_date: date
    # ... outros detalhes do empréstimo

class LoanInstallment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    loan_id: UUID
    installment_number: int
    due_date: date
    amount_due: Decimal
    amount_paid: Decimal = Field(default=Decimal(0))
    payment_date: Optional[date] = None
    status: str # 'pending', 'paid', 'late'

# ... outros modelos como `Payment`, `Consultant`, `AuditLog`, etc.
```

### **3.2. Camada de Aplicação (`src/iabank/application`)**

Orquestra os casos de uso, utilizando os modelos de domínio para executar as tarefas. Define as interfaces (Portas) que a camada de infraestrutura deve implementar.

#### **Componente: `LoanApplicationService`**
*   **Responsabilidade Principal:** Orquestrar o caso de uso "Novo Empréstimo", incluindo a criação do cliente se necessário, validação das condições do empréstimo e geração das parcelas.
*   **Tecnologias Chave:** Python (Lógica Pura).
*   **Dependências Diretas:**
    *   `iabank.domain.models`
    *   `iabank.application.ports` (para as interfaces de repositório)

#### **Componente: `CollectionService`**
*   **Responsabilidade Principal:** Gerenciar a lógica de cobrança, identificando empréstimos em atraso, registrando interações de cobrança e processando renegociações.
*   **Tecnologias Chave:** Python (Lógica Pura).
*   **Dependências Diretas:**
    *   `iabank.domain.models`
    *   `iabank.application.ports`

### **3.3. Camada de Infraestrutura (`src/iabank/infrastructure`)**

Implementações concretas das interfaces definidas na camada de aplicação. Lida com banco de dados, APIs externas, filas, etc.

#### **Componente: `PostgresLoanRepository`**
*   **Responsabilidade Principal:** Implementar a interface `ILoanRepository` para persistir e recuperar dados de empréstimos do PostgreSQL. **Crucialmente, todas as queries DEVERÃO ser filtradas pelo `tenant_id` do usuário logado.**
*   **Tecnologias Chave:** Django ORM.
*   **Dependências Diretas:**
    *   `django.db.models`
    *   `iabank.application.ports.ILoanRepository`
    *   `iabank.domain.models` (para mapeamento entre ORM e Domínio)

#### **Componente: `CeleryTaskQueue`**
*   **Responsabilidade Principal:** Implementar a interface `ITaskQueue` para enfileirar tarefas assíncronas, como envio de e-mails, geração de relatórios pesados ou comunicação via WhatsApp.
*   **Tecnologias Chave:** `Celery`.
*   **Dependências Diretas:**
    *   `celery`
    *   `iabank.application.ports.ITaskQueue`

### **3.4. Camada de Apresentação (`src/iabank/api` e `frontend/`)**

A interface com o mundo exterior. No backend, é a API RESTful. No frontend, a Single-Page Application (SPA).

#### **3.4.1. API Backend (`src/iabank/api`)**

*   **Tecnologias Chave:** Django, Django REST Framework.

#### **3.4.2. Painel Web Frontend (`frontend/`)**

*   **Tecnologias Chave:** React, TypeScript, TanStack Query, Tailwind CSS.

#### **Decomposição da UI e Contratos de Dados (ViewModels)**

##### **Componente UI: `EmprestimosPainel` (`frontend/src/features/loans/components/LoansPanel.tsx`)**
*   **Propósito:** Exibir a tabela principal de gestão de empréstimos (Item 4.2 do mapeamento).
*   **Interage com:** `LoanApplicationService` (através dos endpoints da API).
*   **Contrato de Dados da View (ViewModel):**
    *   A API (`/api/loans/`) deve retornar uma lista de objetos com a seguinte estrutura:

        ```typescript
        // Definição em: frontend/src/features/loans/types.ts
        // Derivado dos modelos Loan, Customer e LoanInstallment no backend.
        
        interface LoanViewRow {
          id: string; // UUID
          customerName: string;
          customerDocument: string;
          principalAmountFormatted: string; // Ex: "R$ 10.000,00"
          status: 'finalizado' | 'em_andamento' | 'em_cobranca';
          statusLabel: string; // Ex: "Em Andamento"
          statusColor: 'green' | 'yellow' | 'red'; // Para o badge de status
          installmentsSummary: string; // Ex: "3/12 pagas"
          nextDueDate: string; // "dd/mm/aaaa" ou "N/A"
          consultantName: string | null;
        }
        ```
    *   **Mapeamento de Origem:** No backend, um `LoanSerializer` (DRF) será responsável por consultar o modelo `Loan` e seus relacionamentos (`Customer`, `LoanInstallment[]`) para construir e formatar cada objeto `LoanViewRow`. Por exemplo, `statusColor` é derivado do `Loan.status`. `installmentsSummary` é calculado contando as parcelas pagas vs. o total. `principalAmountFormatted` é formatado para a moeda local.

##### **Componente UI: `NovoEmprestimoWizard` (`frontend/src/features/loans/components/NewLoanWizard.tsx`)**
*   **Propósito:** Implementar o assistente de "Novo Empréstimo" (Item 4.1).
*   **Interage com:** `CustomerService` e `LoanApplicationService` (via API).
*   **Contrato de Dados da View (ViewModel):**
    *   **Passo 1 (Busca Cliente):** A API (`/api/customers/search/?q=...`) deve retornar uma lista de:
        ```typescript
        interface CustomerSearchResult {
          id: string; // UUID
          name: string;
          documentNumber: string;
        }
        ```
    *   **Passo 2 (Cálculo):** A API (`/api/loans/calculate-plan/`) recebe `valor`, `taxa`, etc., e retorna:
        ```typescript
        interface InstallmentPlan {
          totalPayable: string;
          installments: Array<{
            number: int;
            dueDate: string;
            amount: string;
          }>;
        }
        ```
    *   **Mapeamento de Origem:** O backend usa a lógica do `LoanApplicationService` para realizar os cálculos (sem persistir) e retorna a estrutura de dados formatada para exibição direta na UI.

## **4. Definição das Interfaces Principais**

As interfaces (Portas) são definidas na camada de aplicação para desacoplar a lógica de negócio da infraestrutura.

```python
# Em: src/iabank/application/ports.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from iabank.domain.models import Loan, Customer
from uuid import UUID

class IUnitOfWork(ABC):
    @abstractmethod
    def begin(self): ...

    @abstractmethod
    def commit(self): ...

    @abstractmethod
    def rollback(self): ...

class ILoanRepository(ABC):
    @abstractmethod
    def add(self, loan: Loan): ...

    @abstractmethod
    def get_by_id(self, tenant_id: UUID, loan_id: UUID) -> Optional[Loan]: ...
    
    @abstractmethod
    def list_all(self, tenant_id: UUID, filters: dict) -> List[Loan]: ...

# ... outras interfaces como ICustomerRepository, ITaskQueue, etc.

# Exemplo de serviço usando as interfaces e injeção de dependência via __init__
# Em: src/iabank/application/services.py

class LoanApplicationService:
    def __init__(self, uow: IUnitOfWork, loan_repo: ILoanRepository, customer_repo: ICustomerRepository):
        self.uow = uow
        self.loan_repo = loan_repo
        self.customer_repo = customer_repo

    def create_new_loan(self, tenant_id: UUID, loan_data: dict) -> Loan:
        with self.uow:
            # Lógica para criar cliente (se não existir), validar, criar o Loan
            # loan = Loan(...)
            # self.loan_repo.add(loan)
            # ...
            self.uow.commit()
        return loan
```

## **5. Gerenciamento de Dados**

*   **Persistência:** O **PostgreSQL** será o banco de dados principal, acessado através do **ORM do Django**.
*   **Padrão:** O acesso aos dados na camada de infraestrutura seguirá o **Padrão Repository** combinado com o padrão **Unit of Work** para garantir a atomicidade das operações financeiras (ACID). Um `UnitOfWork` gerenciará a transação do banco de dados, e os repositórios operarão dentro dessa transação.
*   **Isolamento de Dados (Multi-tenancy):** Será implementado um **middleware** no Django que injeta o `tenant_id` do usuário autenticado em cada requisição. A camada de repositório (infraestrutura) terá a responsabilidade OBRIGATÓRIA de usar esse `tenant_id` para filtrar TODAS as consultas ao banco de dados, garantindo que um tenant nunca acesse dados de outro.
*   **Cache:** **Redis** será usado para cachear dados frequentemente acessados e de baixa volatilidade (ex: parâmetros do sistema, perfis de permissão) através de uma implementação da interface `ICacheService`.

## **6. Estrutura de Diretórios Proposta (`src` layout)**

```
iabank/
├── .docker/                # Configurações do Nginx, etc.
├── .github/                # Workflows de CI/CD
├── frontend/               # Código da SPA React
│   ├── public/
│   └── src/
│       ├── app/
│       ├── components/     # Componentes reutilizáveis
│       ├── features/       # Módulos de funcionalidade (loans, customers)
│       ├── lib/
│       ├── types/
│       └── main.tsx
├── src/
│   └── iabank/             # Pacote Python principal
│       ├── __init__.py
│       ├── api/            # Camada de Apresentação (Django REST Framework)
│       │   ├── urls.py
│       │   ├── views.py
│       │   └── serializers.py
│       ├── application/    # Camada de Aplicação
│       │   ├── __init__.py
│       │   ├── services.py # Implementação dos Use Cases
│       │   └── ports.py    # Interfaces (Portas)
│       ├── domain/         # Camada de Domínio
│       │   ├── __init__.py
│       │   └── models.py   # Modelos Pydantic (SSOT)
│       ├── infrastructure/ # Camada de Infraestrutura
│       │   ├── __init__.py
│       │   ├── repositories.py # Implementações de repositórios (Django ORM)
│       │   ├── tasks.py      # Tarefas Celery
│       │   └── adapters.py   # Adapters para serviços externos
│       ├── core/           # Configurações centrais do Django
│       │   ├── settings.py
│       │   └── urls.py
│       └── manage.py
├── tests/                  # Testes unitários e de integração
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── README.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## **7. Arquivo `.gitignore` Proposto**

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

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# VS Code
.vscode/
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# PyCharm
.idea/

# Mac
.DS_Store

# Frontend (Node.js)
node_modules/
dist/
.vite/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

```

## **8. Arquivo `README.md` Proposto**

```markdown
# IABANK

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)](https://github.com/your-org/iabank)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-darkgreen?logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18+-blue?logo=react)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue?logo=postgresql)](https://www.postgresql.org/)

Sistema de gestão de empréstimos moderno e eficiente.

## Sobre o Projeto

O **IABANK** é uma plataforma Web SaaS robusta e segura, desenvolvida em Python e React, projetada para a gestão completa de empréstimos (end-to-end). Foi concebida para ser escalável, intuitiva e adaptável às necessidades de financeiras, fintechs, bancos e qualquer organização cujo modelo de negócio dependa do ciclo de emprestar, cobrar e reinvestir.

A visão de futuro inclui a automação do ciclo de vida do empréstimo através de agentes de IA e integrações profundas com o ecossistema financeiro (Bureaus de Crédito, Pix, Open Finance) e de comunicação (WhatsApp).

## Stack Tecnológica

*   **Backend:** Python 3.10+, Django, Django REST Framework
*   **Frontend:** React 18+, TypeScript, Vite, TanStack Query, Tailwind CSS
*   **Banco de Dados:** PostgreSQL
*   **Tarefas Assíncronas:** Celery, Redis
*   **Containerização:** Docker, Docker Compose
*   **Servidor Web:** Nginx

## Como Começar

Para executar o projeto localmente, você precisa ter o Docker e o Docker Compose instalados.

1.  **Clone o repositório:**
    ```sh
    git clone https://github.com/your-org/iabank.git
    cd iabank
    ```

2.  **Crie um arquivo de ambiente:**
    Copie o arquivo de exemplo `.env.example` para `.env` e ajuste as variáveis se necessário.
    ```sh
    cp .env.example .env
    ```

3.  **Construa e inicie os containers:**
    Este comando irá construir as imagens do backend e frontend, e iniciar todos os serviços (web, api, db, redis, worker).
    ```sh
    docker-compose up --build
    ```

4.  **Execute as migrações do banco de dados:**
    Em um novo terminal, execute o seguinte comando para criar as tabelas no banco de dados.
    ```sh
    docker-compose exec api python src/iabank/manage.py migrate
    ```

5.  **Acesse a aplicação:**
    *   **Frontend:** [http://localhost:3000](http://localhost:3000)
    *   **Backend API:** [http://localhost:8000/api/](http://localhost:8000/api/)

## Como Executar os Testes

Para executar a suíte de testes do backend:
```sh
docker-compose exec api pytest
```

## Estrutura do Projeto

O projeto segue uma arquitetura em camadas para garantir a separação de responsabilidades e a manutenibilidade.

*   `frontend/`: Contém a Single-Page Application desenvolvida em React.
*   `src/iabank/`: O pacote principal Python, organizado em:
    *   `domain/`: Lógica de negócio e modelos puros (Pydantic).
    *   `application/`: Casos de uso e interfaces (serviços).
    *   `infrastructure/`: Implementações de acesso a dados, APIs externas, etc.
    *   `api/`: A camada da API REST (Django REST Framework).
*   `tests/`: Testes unitários e de integração para o backend.

```

## **9. Arquivo `LICENSE` Proposto**

Sugestão: Licença MIT.

```
MIT License

Copyright (c) 2024 Your Name / Your Company

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

## **10. Arquivo `CONTRIBUTING.md` Proposto**

```markdown
# Como Contribuir para o IABANK

Agradecemos o seu interesse em contribuir! Para garantir a qualidade e a consistência do projeto, pedimos que siga estas diretrizes.

## Processo de Desenvolvimento

1.  **Siga o Blueprint Arquitetural:** Todas as novas funcionalidades e refatorações devem aderir aos princípios e estruturas definidos no Blueprint. Isso inclui a separação de camadas, o uso de interfaces e a definição de modelos de domínio.
2.  **Crie uma Issue:** Antes de começar a trabalhar em uma nova funcionalidade ou correção de bug, por favor, verifique se existe uma *Issue* correspondente. Se não houver, crie uma descrevendo a mudança proposta.
3.  **Crie um Branch:** Crie um branch a partir do `main` com um nome descritivo (ex: `feature/novo-relatorio-lucro` ou `fix/calculo-juros-atraso`).
4.  **Desenvolva com Testes:** A lógica de negócio na camada de domínio e aplicação deve ter cobertura de testes unitários. Novos endpoints de API devem ter testes de integração.
5.  **Mantenha o Código Limpo:** Siga os padrões de estilo (PEP 8 para Python, Prettier para TypeScript/React) e escreva um código claro e documentado.
6.  **Abra um Pull Request (PR):** Ao concluir o desenvolvimento, abra um PR para o branch `main`. No PR, referencie a Issue que ele resolve.
7.  **Revisão de Código:** Aguarde a revisão do seu PR. Esteja preparado para discutir sua implementação e fazer os ajustes necessários.

## Configuração do Ambiente

Siga as instruções na seção "Como Começar" do `README.md` para configurar o seu ambiente de desenvolvimento com Docker.
```

## **11. Estrutura do `CHANGELOG.md`**

```markdown
# Changelog

Todos as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Estrutura inicial do projeto baseada no Blueprint Arquitetural v1.0.

## [0.1.0] - YYYY-MM-DD

### Added
- Lançamento inicial.
```

## **12. Considerações de Segurança**

*   **Autenticação e Autorização:** A autenticação será via tokens **JWT** (com curta duração e mecanismo de refresh). A autorização será baseada em papéis (**RBAC**), implementada como um middleware no Django que verifica o `role` do `User` contra as permissões necessárias para cada endpoint.
*   **Isolamento de Dados (Multi-tenancy):** A filtragem obrigatória por `tenant_id` em toda a camada de acesso a dados é a principal medida de segurança para o modelo SaaS.
*   **Validação de Input:** Todas as entradas da API serão rigorosamente validadas usando os Serializers do DRF e os modelos Pydantic para proteger contra ataques de injeção.
*   **Proteção de Dados:** Senhas serão armazenadas usando o hasher padrão e robusto do Django (PBKDF2). Todo o tráfego será forçado para **HTTPS** em produção (configurado no Nginx). Dados sensíveis em repouso (se houver, além do padrão) podem usar o `django-cryptography`.
*   **Auditoria:** Uma tabela `AuditLog` registrará todas as operações críticas (Criação, Edição, Exclusão), armazenando o `user_id`, `tenant_id`, ação, timestamp e os dados alterados (antes e depois).

## **13. Justificativas e Trade-offs**

*   **Monolith vs. Microservices:** A escolha de um "Monolito Modular" com Django em vez de microserviços é intencional para a fase inicial. Reduz drasticamente a complexidade operacional (deploy, monitoramento, comunicação entre serviços) e acelera o desenvolvimento. A arquitetura em camadas adotada permite, no futuro, extrair um serviço (ex: `CollectionService`) para um microserviço separado com esforço controlado.
*   **Pydantic no Domínio:** Usar Pydantic em vez de classes Python puras adiciona uma leve dependência, mas o ganho em validação de tipos em tempo de execução e clareza na definição dos modelos de dados (nosso SSOT) supera em muito o custo, prevenindo bugs e garantindo a integridade dos dados que fluem entre as camadas.

## **14. Exemplo de Bootstrapping/Inicialização (Conceitual)**

A "colagem" dos componentes ocorre na camada de Apresentação (API Views).

```python
# Em: src/iabank/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Importando os serviços e repositórios concretos
from iabank.application.services import LoanApplicationService
from iabank.infrastructure.repositories import PostgresLoanRepository, DjangoUnitOfWork
from iabank.infrastructure.auth import get_tenant_from_request # Função helper

class LoanCreateAPIView(APIView):
    # A injeção de dependência pode ser feita de forma mais elegante com um container de DI,
    # mas para simplicidade inicial, a instanciação pode ocorrer aqui.
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Instanciando os componentes conforme o contrato
        uow = DjangoUnitOfWork()
        loan_repo = PostgresLoanRepository()
        customer_repo = PostgresCustomerRepository() # Supondo que exista
        
        self.loan_service = LoanApplicationService(
            uow=uow,
            loan_repo=loan_repo,
            customer_repo=customer_repo
        )

    def post(self, request, *args, **kwargs):
        # 1. Validação do input com Serializer
        serializer = LoanCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Obter o tenant
        tenant_id = get_tenant_from_request(request)
        
        # 3. Chamar o serviço da camada de aplicação
        try:
            new_loan = self.loan_service.create_new_loan(
                tenant_id=tenant_id,
                loan_data=serializer.validated_data
            )
            
            # 4. Mapear o resultado para o ViewModel/DTO de resposta
            response_serializer = LoanDetailSerializer(new_loan)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except BusinessRuleException as e: # Exceção customizada do domínio
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

```