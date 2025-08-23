# **Blueprint Arquitetural: IABANK v1.0**

## 1. Visão Geral da Arquitetura

A arquitetura do `IABANK` será baseada em uma abordagem de **Monólito Modular em Camadas**. Esta escolha visa equilibrar a velocidade de desenvolvimento inicial com a manutenibilidade e escalabilidade futuras.

- **Backend:** Um único serviço Django que expõe uma API RESTful. Internamente, o código será organizado em "apps" Django que representam os domínios de negócio (ex: `loans`, `customers`, `finance`), promovendo alta coesão e baixo acoplamento entre os módulos. A arquitetura interna seguirá o padrão de Camadas (Apresentação, Aplicação, Domínio, Infraestrutura) para uma clara separação de responsabilidades.
- **Frontend:** Uma Single Page Application (SPA) desenvolvida em React/TypeScript, que consome a API do backend. Ela será responsável por toda a renderização e experiência do usuário.
- **Comunicação:** A comunicação entre Frontend e Backend será síncrona, via API RESTful (JSON sobre HTTPS). Tarefas assíncronas (como envio de e-mails) serão delegadas ao Celery com um broker Redis.
- **Multi-tenancy:** A arquitetura será multi-tenant desde o início, utilizando uma estratégia de **isolamento de dados por chave estrangeira (`tenant_id`)**. Todos os dados de negócio serão particionados por Tenant no nível do banco de dados, e a camada de acesso a dados garantirá que nenhuma query possa vazar dados entre tenants.

**Organização do Código-Fonte:** Será utilizado um **monorepo**, gerenciado com ferramentas de workspace se necessário. Esta abordagem simplifica o desenvolvimento e o CI/CD, garantindo que o contrato entre a API do backend e o consumidor do frontend permaneça sempre sincronizado no mesmo commit. O repositório conterá duas pastas principais na raiz: `backend/` e `frontend/`.

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
