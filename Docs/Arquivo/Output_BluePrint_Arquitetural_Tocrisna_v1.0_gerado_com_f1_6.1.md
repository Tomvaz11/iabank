# **Blueprint Arquitetural: IABANK v1.0.0**

Este documento serve como a fonte única da verdade (Single Source of Truth - SSOT) para a arquitetura técnica e de produto do `IABANK`. Ele define a estrutura, componentes, interfaces e padrões a serem seguidos durante o desenvolvimento, garantindo a construção de um produto de engenharia robusto, escalável e manutenível.

## 1. Visão Geral da Arquitetura

A arquitetura do `IABANK` será baseada em uma abordagem de **Monorepo** contendo duas aplicações principais: um **Backend API** seguindo os princípios da **Arquitetura em Camadas (Clean Architecture)** e um **Frontend SPA (Single Page Application)**.

- **Arquitetura do Backend (Clean Architecture):** Esta escolha desacopla a lógica de negócio das frameworks e da infraestrutura. Teremos camadas bem definidas (Domínio, Aplicação, Apresentação, Infraestrutura), o que maximiza a testabilidade, a manutenibilidade e facilita a evolução futura para incorporar agentes de IA e integrações complexas. A lógica de negócio reside no núcleo, pura e independente.
- **Arquitetura do Frontend:** Seguirá o padrão **Feature-Sliced Design**, uma abordagem escalável para organizar o código em torno de funcionalidades de negócio, promovendo o baixo acoplamento e a alta coesão.
- **Estratégia de Repositório (Monorepo):** Um único repositório Git conterá o código do backend (`backend/`) e do frontend (`frontend/`).
  - **Justificativa:** No estágio atual do projeto, um monorepo simplifica o setup do ambiente de desenvolvimento, a gestão de dependências e a configuração do pipeline de CI/CD. Ele permite commits atômicos que afetam tanto a API quanto a UI, garantindo consistência.

## 2. Diagramas da Arquitetura (Modelo C4)

### 2.1. Nível 1: Diagrama de Contexto do Sistema (C1)

Este diagrama mostra o `IABANK` como uma caixa preta, interagindo com seus usuários e sistemas externos.

```mermaid
graph TD
    subgraph "Ecossistema IABANK"
        A[Sistema IABANK]
    end

    U1[Gestor / Administrador] -->|Gerencia operações via [Web App]| A
    U2[Consultor / Cobrador] -->|Executa tarefas via [Web App]| A

    subgraph "Integrações Futuras"
        A -.->|Consulta Risco| SE1[Bureaus de Crédito]
        A -.->|Realiza Transações| SE2[Sistemas Bancários (Pix, Open Finance)]
        A -.->|Notifica Clientes| SE3[Plataformas de Comunicação (WhatsApp, SMS)]
    end

    style A fill:#007bff,stroke:#0056b3,stroke-width:2px,color:#fff
```

### 2.2. Nível 2: Diagrama de Containers (C2)

Este diagrama faz um "zoom" no sistema, mostrando os principais blocos tecnológicos.

```mermaid
graph TD
    U[Usuário] -->|HTTPS via Navegador| F[Frontend SPA <br> [React + Vite]]

    subgraph "Infraestrutura em Produção"
        N[Nginx <br> [Reverse Proxy]]
        B[Backend API <br> [Python + Django]]
        DB[(Banco de Dados <br> [PostgreSQL])]
        C[(Cache & Fila <br> [Redis])]
    end

    F -->|API REST (JSON) via HTTPS| N
    N -->|/api/*| B
    N -->|/*| F
    B -->|Leitura/Escrita| DB
    B -->|Tarefas Assíncronas & Cache| C

    style F fill:#61DAFB,stroke:#20232A,stroke-width:2px,color:#20232A
    style B fill:#3478a8,stroke:#1e4866,stroke-width:2px,color:#fff
    style DB fill:#336791,stroke:#1e4866,stroke-width:2px,color:#fff
    style C fill:#DC382D,stroke:#a4241a,stroke-width:2px,color:#fff
```

### 2.3. Nível 3: Diagrama de Componentes (C3) - Backend API

Um "zoom" no container do Backend API, mostrando suas camadas internas.

```mermaid
graph TD
    subgraph "Container: Backend API (Django)"
        direction LR
        A[<b>Camada de Apresentação</b> <br> DRF Views & Serializers <br> <i>(Controllers)</i>]
        B[<b>Camada de Aplicação</b> <br> Lógica de Casos de Uso <br> <i>(Services)</i>]
        C[<b>Camada de Domínio</b> <br> Modelos de Negócio & Regras <br> <i>(Models)</i>]
        D[<b>Camada de Infraestrutura</b> <br> Acesso a Dados & Serviços Externos <br> <i>(Repositories, Gateways)</i>]
    end

    A --> B
    B --> C
    B --> D

    style A fill:#f0f8ff
    style B fill:#e6f2ff
    style C fill:#d5e8ff
    style D fill:#f0f0f0
```

## 3. Descrição dos Componentes, Interfaces e Modelos de Domínio

### 3.1. Consistência dos Modelos de Dados (SSOT do Domínio)

Esta é a Fonte Única da Verdade para todas as estruturas de dados do projeto. Os modelos de domínio serão implementados como `models.Model` do Django, que servem como a base canônica. Para DTOs e validação na camada de serviço, usaremos Pydantic.

- **Módulo:** `backend/src/iabank/domain/models/`
- **Tecnologia Chave:** Django ORM (`models.Model`), Pydantic `BaseModel` para DTOs.
- **Modelos Principais (Estrutura Conceitual):**

  ```python
  # Usando sintaxe Pydantic para clareza conceitual
  # A implementação real será com Django models.Model

  class Tenant(BaseModel):
      id: UUID
      name: str
      created_at: datetime

  class User(BaseModel):
      id: UUID
      tenant: Tenant
      email: str
      role: str # 'admin', 'manager', 'consultant'
      # ... outros campos de autenticação

  class Client(BaseModel):
      id: UUID
      tenant: Tenant
      full_name: str
      document_number: str # CPF/CNPJ
      address: dict # { cep, street, ... }
      # ... outros dados

  class Loan(BaseModel):
      id: UUID
      tenant: Tenant
      client: Client
      consultant: User
      principal_amount: Decimal
      interest_rate: Decimal
      status: str # 'pending', 'active', 'paid', 'overdue'
      created_at: datetime

  class Installment(BaseModel):
      id: UUID
      tenant: Tenant
      loan: Loan
      installment_number: int
      due_date: date
      amount: Decimal
      status: str # 'pending', 'paid', 'overdue'
      payment_date: Optional[date]

  # ... outros modelos como `FinancialTransaction`, `Consultant`, `AuditLog`, etc.
  ```

### 3.2. Decomposição em Componentes/Módulos

#### Camada de Domínio (`backend/src/iabank/domain/`)

- **Responsabilidade:** Contém a lógica de negócio central, modelos de dados (entidades) e regras de negócio. É o coração do sistema, totalmente independente de frameworks.
- **Componentes:**
  - `models/`: Define as entidades de negócio (Cliente, Empréstimo, Parcela) usando o Django ORM.
  - `services/` (opcional): Lógica de domínio pura que não se encaixa em um único modelo (ex: `LoanCalculatorService`).
- **Tecnologias Chave:** Python (Lógica Pura), Django ORM.
- **Dependências Diretas:** Nenhuma outra camada do projeto.

#### Camada de Aplicação (`backend/src/iabank/application/`)

- **Responsabilidade:** Orquestra os casos de uso do sistema (use cases). Coordena a camada de domínio e a camada de infraestrutura para executar ações.
- **Componentes:**
  - `services/`: Classes de serviço que implementam os casos de uso (ex: `LoanApplicationService`, `ClientManagementService`).
  - `dtos/`: Data Transfer Objects (Pydantic) para comunicação entre camadas.
- **Tecnologias Chave:** Python (Lógica Pura), Pydantic `BaseModel`.
- **Dependências Diretas:** `iabank.domain`, `iabank.infrastructure.repositories`.

#### Camada de Infraestrutura (`backend/src/iabank/infrastructure/`)

- **Responsabilidade:** Implementa os detalhes técnicos para acesso a dados, comunicação com serviços externos, etc.
- **Componentes:**
  - `repositories/`: Implementação do padrão Repository para abstrair o acesso ao banco de dados (ex: `DjangoLoanRepository` implementando `ILoanRepository`). Responsável por **mapear** os dados do ORM para os modelos de domínio, se necessário.
  - `tasks/`: Definição de tarefas assíncronas (Celery) para processos em background.
  - `cache/`: Wrappers para interação com o Redis.
- **Tecnologias Chave:** Django ORM, Celery, Redis client.
- **Dependências Diretas:** `iabank.domain`.

#### Camada de Apresentação (`backend/src/iabank/api/`)

- **Responsabilidade:** Expõe a funcionalidade do sistema via uma API RESTful. Lida com requisições HTTP, autenticação, serialização e validação de entrada/saída.
- **Componentes:**
  - `views/`: DRF `APIView` ou `ViewSet` que recebem as requisições HTTP.
  - `serializers/`: DRF `Serializers` para validar e converter dados entre JSON e objetos Python.
  - `urls.py`: Mapeamento de rotas da API.
- **Tecnologias Chave:** Django REST Framework.
- **Dependências Diretas:** `iabank.application.services`.

#### Camada de Apresentação (UI - Frontend)

- **Módulo:** `frontend/src/features/loans/components/LoanManagementPanel`
- **Propósito:** Componente principal para a tela "Empréstimos (Painel de Gestão)". Exibe uma tabela inteligente de empréstimos com filtros avançados e ações.
- **Interage com:** `LoanApiService` (abstração na camada `shared/api`).
- **Contrato de Dados da View (ViewModel):**

  - `LoanViewRow(ViewModel)`: Representa uma única linha na tabela de empréstimos.

    ```typescript
    // frontend/src/entities/loan/model/types.ts
    interface LoanViewRow {
      id: string;
      clientName: string;
      consultantName: string;
      principalAmountFormatted: string; // Ex: "R$ 1.500,00"
      status: "finalizado" | "em_andamento" | "em_cobranca";
      statusLabel: string; // Ex: "Finalizado"
      createdAt: string; // Ex: "15/08/2023"
    }
    ```

  - **Mapeamento de Origem:** Um hook customizado (ex: `useLoansQuery`) na camada de `features` será responsável por chamar a API (`/api/v1/loans/`), receber a lista de `Loan` (modelo do backend) e mapear cada item para uma instância de `LoanViewRow`. A formatação de valores e a tradução de `status` ocorrem nesta etapa de mapeamento, mantendo os componentes de UI (`shared/ui`) "burros".

## 4. Descrição Detalhada da Arquitetura Frontend

- **Padrão Arquitetural:** **Feature-Sliced Design**. O código é organizado por escopo de negócio (`features`, `entities`, `pages`), o que melhora a escalabilidade e a manutenibilidade. A distinção entre componentes de lógica (containers, dentro de `features`) e componentes de UI (puros/burros, em `shared/ui`) é um princípio central.

- **Estrutura de Diretórios Proposta (`frontend/src/`):**

  ```markdown
  src/
  ├── app/ # Configuração global da aplicação (providers, router, styles)
  ├── pages/ # Componentes de página (ex: LoanListPage, DashboardPage)
  ├── features/ # Funcionalidades de negócio (ex: CreateLoanWizard, LoanFiltering)
  ├── entities/ # Entidades de negócio (ex: LoanCard, ClientProfile)
  │ └── loan/
  │ ├── model/ # Lógica, tipos, hooks (ex: useLoan)
  │ └── ui/ # Componentes de UI (ex: LoanRow, LoanStatusBadge)
  └── shared/ # Código reutilizável e agnóstico de negócio
  ├── api/ # Configuração do cliente Axios/Fetch e instâncias de API
  ├── lib/ # Helpers, hooks genéricos (ex: useDebounce)
  └── ui/ # Biblioteca de componentes de UI puros (Button, Input, Table)
  ```

- **Estratégia de Gerenciamento de Estado:**

  - **Estado do Servidor:** **TanStack Query (React Query)** será a fonte da verdade para todos os dados assíncronos vindos da API. Ele gerenciará caching, revalidação, e estados de loading/error.
  - **Estado Global do Cliente:** **Zustand**. Utilizado para estados síncronos globais e de baixo volume, como informações do usuário autenticado, tema da UI ou estado de um menu lateral. Sua simplicidade e API mínima são ideais.
  - **Estado Local do Componente:** Mecanismos nativos do React (`useState`, `useReducer`) serão usados para estado efêmero e não compartilhado (ex: estado de um input de formulário, visibilidade de um modal).

- **Fluxo de Dados:**
  1. O usuário interage com um componente em uma `page`.
  2. A ação dispara um evento que é tratado por um componente de `feature`.
  3. A `feature` utiliza um hook do TanStack Query para chamar a API (definida em `shared/api`).
  4. TanStack Query gerencia o ciclo de vida da requisição (fetch, cache, etc.).
  5. Após o sucesso, os dados são cacheados e disponibilizados para os componentes.
  6. Componentes (`entities`, `shared/ui`) re-renderizam com os novos dados.

## 5. Definição das Interfaces Principais

Interfaces serão definidas como classes abstratas ou `typing.Protocol` para garantir o desacoplamento e facilitar os testes com mocks.

- **Exemplo: Interface do Repositório de Empréstimos**

  ```python
  # backend/src/iabank/domain/ports.py
  from typing import Protocol, Optional
  from .models import Loan, Tenant

  class ILoanRepository(Protocol):
      def get_by_id(self, tenant: Tenant, loan_id: UUID) -> Optional[Loan]:
          ...

      def save(self, loan: Loan) -> Loan:
          ...
      # ... outros métodos
  ```

- **Exemplo: Interface do Serviço de Aplicação de Empréstimos**

  ```python
  # backend/src/iabank/application/services.py
  from iabank.domain.ports import ILoanRepository, IClientRepository

  class LoanApplicationService:
      # Configuração/Dependências injetadas via construtor
      def __init__(self, loan_repo: ILoanRepository, client_repo: IClientRepository):
          self.loan_repo = loan_repo
          self.client_repo = client_repo

      def create_new_loan(self, tenant: Tenant, loan_data: LoanCreationDTO) -> Loan:
          """
          Orquestra a criação de um novo empréstimo.
          1. Valida dados do DTO.
          2. Busca ou cria o cliente.
          3. Cria a entidade Loan.
          4. Persiste via repositório.
          5. Retorna o empréstimo criado.
          """
          # ... implementação do caso de uso ...
  ```

## 6. Gerenciamento de Dados

- **Persistência:** Os dados serão persistidos no PostgreSQL através do **ORM do Django**. O padrão Repository será usado na camada de infraestrutura para abstrair o acesso direto ao ORM pela camada de aplicação.
- **Gerenciamento de Schema:** O sistema de **migrações nativo do Django** (`makemigrations`, `migrate`) será a única fonte da verdade para a evolução do schema do banco de dados.
- **Seed de Dados:** Para o ambiente de desenvolvimento, serão criados **comandos de gerenciamento customizados do Django** (ex: `python manage.py seed_data`) para popular o banco de dados com dados fictícios consistentes, utilizando bibliotecas como `factory-boy`.

## 7. Estrutura de Diretórios Proposta

```markdown
iabank-monorepo/
├── .github/
│ └── workflows/
│ └── ci.yml # Pipeline de Integração Contínua
├── backend/
│ ├── src/
│ │ └── iabank/ # Pacote principal do Django
│ │ ├── api/
│ │ ├── application/
│ │ ├── domain/
│ │ ├── infrastructure/
│ │ └── settings/ # Configurações do Django
│ ├── manage.py
│ └── requirements.txt
├── frontend/
│ ├── src/
│ │ ├── app/
│ │ ├── pages/
│ │ ├── features/
│ │ ├── entities/
│ │ └── shared/
│ ├── package.json
│ └── vite.config.ts
├── docker-compose.yml
├── .gitignore
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## 8. Arquivo `.gitignore` Proposto

```markdown
# Byte-compiled / optimized / DLL files

**pycache**/
_.py[cod]
_$py.class

# C extensions

\*.so

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
_.egg-info/
.installed.cfg
_.egg
MANIFEST

# PyInstaller

# Usually these files are written by a python script from a template

# before PyInstaller builds the exe, so as to inject date/other infos into it.

_.manifest
_.spec

# Installer logs

pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports

htmlcov/
.tox/
.nox/
.coverage
.coverage._
.cache
nosetests.xml
coverage.xml
_.cover
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

# IDEs

.idea/
.vscode/
\*.swp

# Django specific

\*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Frontend

frontend/node*modules/
frontend/dist/
frontend/.env
frontend/.env.*
frontend/npm-debug.log\_
frontend/yarn-debug.log*
frontend/yarn-error.log*
frontend/.pnp
frontend/.pnp.js

# OS specific

.DS_Store
Thumbs.db
```

## 9. Arquivo `README.md` Proposto

````markdown
# IABANK

[![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)](...)
[![CI](https://github.com/your-org/iabank-monorepo/actions/workflows/ci.yml/badge.svg)](...)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Sistema de gestão de empréstimos moderno e eficiente.

## Sobre o Projeto

O **IABANK** é uma plataforma Web SaaS robusta e segura, desenvolvida em Python e React, projetada para a gestão completa de empréstimos (end-to-end). Foi concebida para ser escalável, intuitiva e adaptável às necessidades de financeiras, fintechs ou bancos.

## Stack Tecnológica

- **Backend:** Python, Django, Django REST Framework, PostgreSQL, Celery, Redis
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query
- **Infraestrutura:** Docker, Nginx

## Como Começar

### Pré-requisitos

- Docker e Docker Compose
- Node.js e npm/yarn (para o frontend, opcional se usar apenas Docker)

### Instalação e Execução

1.  Clone o repositório:

    ```bash
    git clone https://github.com/your-org/iabank-monorepo.git
    cd iabank-monorepo
    ```

2.  Crie os arquivos de ambiente a partir dos exemplos:

    ```bash
    cp backend/.env.example backend/.env
    cp frontend/.env.example frontend/.env
    ```

3.  Suba os contêineres com Docker Compose:
    ```bash
    docker-compose up --build
    ```

A aplicação estará disponível em `http://localhost:80`.

- O Frontend React roda em `http://localhost:3000` (servidor de dev).
- A API Django roda em `http://localhost:8000`.

## Como Executar os Testes

Para executar os testes do backend:

```bash
docker-compose exec backend pytest
```
````

Para executar os testes do frontend:

```bash
docker-compose exec frontend npm test
```

## Estrutura do Projeto

O projeto é um monorepo com as seguintes pastas principais:

- `backend/`: Contém a aplicação Django API.
- `frontend/`: Contém a aplicação React SPA.
- `.github/`: Contém os workflows de CI/CD (GitHub Actions).

## 10. Arquivo `LICENSE` Proposto

A licença **MIT** é uma excelente escolha padrão, pois é permissiva e amplamente compatível.

```markdown
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
```

## 11. Arquivo `CONTRIBUTING.md` Proposto

````markdown
# Como Contribuir para o IABANK

Agradecemos o seu interesse em contribuir! Para manter a qualidade e consistência do projeto, por favor, siga estas diretrizes.

## Processo de Contribuição

1.  Crie uma `issue` descrevendo a `feature` ou `bug`.
2.  Faça um `fork` do repositório e crie um `branch` a partir do `main`.
3.  Implemente suas mudanças, seguindo as diretrizes de código abaixo.
4.  Adicione testes que cubram suas mudanças.
5.  Abra um `Pull Request` para o branch `main`.

## Diretrizes de Código e Qualidade

Nosso objetivo é manter um código limpo, testável e bem documentado.

### Padrões de Código

- **Backend (Python):**
  - **Formatação:** `Black`
  - **Linting:** `Ruff`
  - **Estilo:** PEP 8
- **Frontend (TypeScript/React):**
  - **Formatação:** `Prettier`
  - **Linting:** `ESLint`

### Automação com Pre-commit

Utilizamos `pre-commit` para automatizar a verificação de qualidade antes de cada commit. Para instalar:

```bash
pip install pre-commit
pre-commit install
```

Isso garantirá que seu código esteja formatado e sem erros de linting antes de ser enviado.

### Documentação de Código

- **Funções e Métodos Públicos:** Devem ter `docstrings` no estilo Google.
- **Classes:** Devem ter uma `docstring` descrevendo sua responsabilidade.
- **Código Complexo:** Adicione comentários para explicar o "porquê", não o "o quê".

### Testes

Toda nova funcionalidade deve ser acompanhada de testes unitários e/ou de integração. O pipeline de CI irá falhar se a cobertura de testes diminuir.
````

## 12. Estrutura do `CHANGELOG.md`

```markdown
# Changelog

Todos as mudanças notáveis neste projeto serão documentadas neste arquivo.

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

-   Versão inicial do Blueprint Arquitetural.
````

## 13. Estratégia de Configuração e Ambientes

- **Ferramenta:** `django-environ` para o backend e arquivos `.env` para o frontend.
- **Abordagem:**
  1. Um arquivo `.env.example` será versionado no repositório com todas as variáveis de ambiente necessárias, mas com valores vazios ou de exemplo.
  2. No ambiente local, cada desenvolvedor criará seu próprio arquivo `.env`, que é ignorado pelo Git.
  3. Em ambientes de homologação e produção, as variáveis de ambiente serão injetadas diretamente no ambiente de execução do contêiner (ex: via segredos do GitHub Actions, variáveis do Kubernetes/ECS, etc.).
- **Exemplo (`backend/.env`):**
  
  ```markdown
  SECRET_KEY='seu_segredo_aqui'
  DEBUG=True
  DATABASE_URL='postgres://user:password@db:5432/iabank'
  REDIS_URL='redis://redis:6379/0'
  ```

## 14. Estratégia de Observabilidade Completa

- **Logging Estruturado:**
  - **Backend:** A configuração `LOGGING` do Django será modificada para usar um `JSONFormatter`. Todos os logs serão emitidos como objetos JSON, contendo timestamp, nível, mensagem e contexto (ex: `tenant_id`, `user_id`, `request_id`).
  - **Frontend:** Utilizaremos uma biblioteca como `pino.js` para enviar logs estruturados para um serviço de coleta.
- **Métricas de Negócio:**
  - **Ferramenta:** Exposição de métricas via um endpoint `/metrics` no formato Prometheus, usando a biblioteca `django-prometheus`.
  - **Métricas Chave:** `loans_created_total`, `payments_processed_total`, `active_users`, `api_request_duration_seconds`.
- **Distributed Tracing:**
  - **Estratégia:** Implementação do padrão **OpenTelemetry**. Cada requisição receberá um `trace_id` único no Nginx. Este ID será propagado do frontend para o backend e entre tarefas do Celery, permitindo rastrear o fluxo completo de uma operação em ferramentas como Jaeger ou Datadog.
- **Health Checks e SLIs/SLOs:**
  - **Endpoint:** A API exporá um endpoint `/api/health/` que verifica a conectividade com o banco de dados e o Redis.
  - **SLI:** Disponibilidade da API (resposta 200 no health check).
  - **SLO:** 99.9% de disponibilidade mensal.
- **Alerting Inteligente:** Alertas serão configurados em uma ferramenta como Grafana ou Sentry, baseados em anomalias (ex: aumento súbito na latência da API P95, pico de erros 5xx) e não apenas em limiares fixos.

## 15. Estratégia de Testes Detalhada

- **Testes Unitários:**
  - **O quê:** Testam a menor unidade de código (uma função, uma classe) de forma isolada.
  - **Onde:** Lógica de negócio na camada de Domínio, Serviços na camada de Aplicação (com repositórios mockados), componentes de UI puros no frontend.
  - **Ferramentas:** `pytest` (Backend), `Vitest` + `React Testing Library` (Frontend).
- **Testes de Integração:**
  - **O quê:** Testam a interação entre componentes.
  - **Onde:** Testam se os Serviços da Camada de Aplicação interagem corretamente com os Repositórios e o banco de dados de teste (usando um BD em memória como SQLite ou um BD de teste dedicado).
  - **Ferramentas:** `pytest` com fixtures para gerenciar o estado do banco de dados.
- **Testes de API (End-to-End):**
  - **O quê:** Testam o sistema completo através da sua interface externa (a API REST).
  - **Onde:** Simulam um cliente HTTP fazendo requisições para os endpoints da API e verificando as respostas, status codes e efeitos colaterais no banco de dados.
  - **Ferramentas:** `APIClient` do Django REST Framework e `pytest`.

## 16. Estratégia de CI/CD

- **Ferramenta:** GitHub Actions, com o workflow definido em `.github/workflows/ci.yml`.
- **Gatilhos:** Em cada `push` para o branch `main` e em cada abertura/atualização de `Pull Request`.
- **Estágios do Pipeline:**
  1. **Setup:** Checkout do código e instalação de dependências (Python/Node).
  2. **Qualidade do Código (Lint & Format):**
      - Executa `ruff`, `black --check` no backend.
      - Executa `eslint`, `prettier --check` no frontend.
  3. **Testes:**
      - Executa a suíte de testes do backend (`pytest`).
      - Executa a suíte de testes do frontend (`npm test`).
  4. **Build:**
      - Constrói as imagens Docker para o backend e o frontend.
  5. **Push (apenas no merge em `main`):**
      - Tagueia as imagens com a versão (ex: `v1.2.3`) e o hash do commit.
      - Envia as imagens para um registro de contêineres (ex: Docker Hub, GHCR).
  6. **Deploy (apenas no merge em `main`):**
      - Um job separado (acionado pelo sucesso do push) se conecta ao ambiente de produção (ex: Kubernetes, Servidor VPS) e atualiza a aplicação para a nova imagem. Estratégias como Blue-Green ou Canary podem ser adotadas no futuro.
      - **Rollback:** O plano inicial de rollback é manual, reimplantando a tag da versão anterior estável do contêiner.

## 17. Estratégia de Versionamento da API

A API será versionada via URL para garantir clareza e evitar quebras de contrato com clientes futuros.

- **Formato:** `/api/v1/...`
- **Implementação:** Utilizaremos o sistema de `namespace` e `versioning` do Django REST Framework para rotear as requisições para o código da versão correta.

## 18. Padrão de Resposta da API e Tratamento de Erros

- **Resposta de Sucesso (2xx):**

  ```json
  {
    "data": {
      /* objeto ou array de objetos */
    }
  }
  ```

- **Resposta de Erro (4xx, 5xx):** Um middleware customizado do Django capturará todas as exceções e as formatará em uma resposta padronizada.

  ```json
  {
    "errors": [
      {
        "status": "422",
        "code": "validation_error",
        "title": "Erro de Validação",
        "detail": "O campo 'email' já está em uso.",
        "source": { "pointer": "/data/attributes/email" }
      }
    ]
  }
  ```

  Este padrão é inspirado na especificação [JSON:API](https://jsonapi.org/format/#error-objects).

## 19. Estratégia de Segurança Abrangente

- **Threat Modeling Básico:**
  - **Ameaça 1: Vazamento de Dados entre Tenants.**
    - **Mitigação:** Implementar um middleware que injeta o `tenant_id` do usuário logado em todas as queries do ORM, garantindo isolamento de dados no nível mais baixo. Testes de integração rigorosos para validar essa lógica.
  - **Ameaça 2: Acesso Não Autorizado a Funcionalidades.**
    - **Mitigação:** Utilizar o sistema de permissões do DRF, aplicando verificações de permissão granulares em cada `APIView` para garantir que o RBAC definido seja cumprido.
  - **Ameaça 3: Injeção de SQL/XSS.**
    - **Mitigação:** Uso exclusivo do ORM do Django (que parametriza queries) e do sistema de templates do React (que escapa saídas por padrão). Aplicar validação rigorosa de dados de entrada com DRF Serializers e Zod.
- **Estratégia de Secrets Management:**
  - **Ambiente:** Variáveis de ambiente, conforme descrito na Seção 13.
  - **Produção:** Utilização de um serviço de gerenciamento de segredos como **AWS Secrets Manager**, **HashiCorp Vault** ou os segredos criptografados do provedor de nuvem. A aplicação receberá os segredos em tempo de execução, nunca os armazenando em código ou arquivos de configuração.
- **Compliance Framework (LGPD):**
  - **Auditoria:** O módulo "Logs de Atividade" criará um registro imutável de todas as operações CRUD em dados sensíveis (Clientes, Empréstimos), registrando quem, o quê e quando.
  - **RBAC:** O sistema de "Usuários e Permissões" garante o princípio do menor privilégio.
  - **Retenção de Dados:** A arquitetura suportará a implementação futura de políticas de retenção e anonimização de dados para atender aos direitos dos titulares.

## 20. Justificativas e Trade-offs

- **Clean Architecture vs. Padrão Django (MTV):**
  - **Decisão:** Clean Architecture.
  - **Justificativa:** Promove testabilidade e manutenibilidade a longo prazo, essencial para um produto SaaS complexo e com planos de evolução para IA.
  - **Trade-off:** Maior boilerplate inicial e uma curva de aprendizado ligeiramente maior para desenvolvedores acostumados apenas com o padrão Django.
- **Monorepo vs. Multi-repo:**
  - **Decisão:** Monorepo.
  - **Justificativa:** Simplifica o desenvolvimento e a CI/CD no estágio atual.
  - **Trade-off:** Pode se tornar mais lento e complexo de gerenciar à medida que a equipe e o projeto crescem. A migração para multi-repo é uma evolução planejada para o futuro.

## 21. Exemplo de Bootstrapping/Inicialização

Em Django, a inicialização é gerenciada pelo framework. O exemplo abaixo demonstra como as dependências seriam injetadas em uma View, seguindo os princípios de DI.

```python
# backend/src/iabank/api/views.py

from iabank.application.services import LoanApplicationService
from iabank.infrastructure.repositories import DjangoLoanRepository, DjangoClientRepository
from rest_framework.views import APIView
from rest_framework.response import Response

# Em um cenário de DI mais avançado, um container de injeção de dependência
# seria responsável por construir essas instâncias.
# Para simplificar, instanciamos manualmente aqui.
loan_repository = DjangoLoanRepository()
client_repository = DjangoClientRepository()
loan_service = LoanApplicationService(
    loan_repo=loan_repository,
    client_repo=client_repository
)

class LoanCreateAPIView(APIView):
    # As dependências são "injetadas" na view.
    # Em um projeto real, isso seria gerenciado por um framework de DI.
    _loan_service: LoanApplicationService = loan_service

    def post(self, request, *args, **kwargs):
        # 1. Obter o tenant do usuário autenticado (via middleware)
        tenant = request.user.tenant

        # 2. Validar e criar o DTO a partir dos dados da requisição
        serializer = LoanCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan_dto = LoanCreationDTO(**serializer.validated_data)

        # 3. Chamar o serviço da camada de aplicação
        new_loan = self._loan_service.create_new_loan(tenant, loan_dto)

        # 4. Serializar a resposta
        response_data = LoanDetailSerializer(new_loan).data
        return Response(response_data, status=201)
```

## 22. Estratégia de Evolução do Blueprint

- **Versionamento Semântico do Blueprint:** Este documento será versionado seguindo o SemVer (ex: `v1.0.0`, `v1.1.0`). Mudanças que quebram a arquitetura (ex: mudar de Monorepo para Multi-repo) resultarão em um incremento de `major`. Adições de novos componentes ou camadas, em `minor`. Correções, em `patch`.
- **Processo de Evolução:** Mudanças significativas devem ser propostas através de **Architectural Decision Records (ADRs)**. Um ADR é um documento curto que descreve o contexto, a decisão tomada e as consequências. Ele é revisado pela equipe técnica antes de ser aprovado e mesclado, criando um histórico de decisões.
- **Compatibilidade e Deprecação:** Interfaces de API e componentes principais seguirão um ciclo de vida de deprecação. Uma interface marcada como `deprecated` na v1.1.0 só poderá ser removida na v2.0.0, garantindo tempo para migração.

## 23. Métricas de Qualidade e Quality Gates

- **Métricas de Cobertura de Código:**
  - **Meta:** Mínimo de **85%** de cobertura de testes para todo o código do backend.
  - **Exceções:** Arquivos de configuração do Django (`settings.py`, `wsgi.py`), código de migrações gerado automaticamente.
- **Métricas de Complexidade:**
  - **Ferramenta:** `radon` (Python).
  - **Limites:**
    - Complexidade Ciclomática por função: **<= 10** (Aviso), **> 15** (Erro).
    - Linhas de código por função: **<= 50**.
- **Quality Gates Automatizados (no pipeline de CI):**
  1. Todos os linters devem passar sem erros.
  2. Todos os testes (unitários, integração) devem passar.
  3. A cobertura de testes não pode diminuir em relação ao branch `main`.
  4. A análise de complexidade não pode relatar erros.
  5. Nenhuma vulnerabilidade de segurança de criticidade alta/crítica pode ser encontrada pela análise de dependências (ex: `Snyk`, `Dependabot`).

## 24. Análise de Riscos e Plano de Mitigação

| Categoria       | Risco Identificado                                                                                 | Probabilidade (1-5) | Impacto (1-5)    | Score (P×I) | Estratégia de Mitigação                                                                                                                                                                                                                                        |
| :-------------- | :------------------------------------------------------------------------------------------------- | :------------------ | :--------------- | :---------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Segurança**   | Falha no isolamento de dados multi-tenant, permitindo que um cliente veja dados de outro.          | 2 (Baixa)           | 5 (Catastrófico) | 10          | Implementar camada de acesso a dados que aplica `tenant_id` em **todas** as queries. Criar testes de integração específicos para validar o isolamento. Revisão de código por pares para toda lógica de acesso a dados.                                         |
| **Performance** | Lentidão em relatórios e dashboards com o crescimento do volume de dados (milhões de empréstimos). | 4 (Alta)            | 4 (Maior)        | 16          | Design de queries otimizadas desde o início. Uso agressivo de índices de banco de dados. Implementar cache (Redis) para dados frequentemente acessados. Para relatórios complexos, planejar o uso de desnormalização ou um banco de dados analítico no futuro. |
| **Técnico**     | Acoplamento excessivo do frontend com a estrutura da API, dificultando a evolução de ambos.        | 3 (Média)           | 3 (Moderado)     | 9           | Adoção rigorosa da arquitetura frontend proposta, com uma camada de `api` (`shared/api`) que atua como um "anti-corruption layer", mapeando as respostas da API para os modelos do frontend.                                                                   |
| **Negócio**     | Baixa adoção do produto devido a uma experiência de usuário (UX) complexa ou ineficiente.          | 3 (Média)           | 4 (Maior)        | 12          | Seguir os princípios de UX definidos no mapeamento de funcionalidades (assistentes, tabelas inteligentes, drill-down). Realizar ciclos de feedback com usuários-alfa/beta antes do lançamento. Investir em um design system no `shared/ui`.                    |
