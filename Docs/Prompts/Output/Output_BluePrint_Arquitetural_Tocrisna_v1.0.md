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
├── .docker-compose.yml
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

## 22. Estratégia de Evolução do Blueprint

- **Versionamento:** O próprio Blueprint será versionado usando **Semantic Versioning**. Mudanças que não quebram a estrutura (adição de um novo módulo) são `MINOR`. Mudanças que alteram a arquitetura fundamental (ex: mudança de monolito para microserviços) são `MAJOR`.
- **Processo de Evolução:** Mudanças arquiteturais significativas devem ser propostas através de um **Architectural Decision Record (ADR)**. Um ADR é um documento curto em markdown que descreve o contexto, a decisão tomada e as consequências.
- **Documentação (ADRs):** Será criada uma pasta `docs/adr/` no repositório para armazenar os ADRs, criando um registro histórico das decisões de arquitetura.

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
