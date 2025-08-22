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

## 20. Justificativas e Trade-offs

- **Monólito vs. Microsserviços:**

  - **Decisão:** Adotar uma arquitetura monolítica (Majestic Monolith).
  - **Justificativa:** Para a fase inicial do projeto, a complexidade operacional de uma arquitetura de microsserviços (deploy, monitoramento, comunicação inter-serviços) superaria os benefícios. O monolito permite um desenvolvimento mais rápido, transações ACID mais simples e um único ponto de implantação. A modularização interna em apps Django (operational, financial, etc.) prepara o terreno para uma futura extração para microsserviços, se necessário.
  - **Trade-off:** Escalabilidade granular é sacrificada. Se um módulo (ex: relatórios) se tornar um gargalo, toda a aplicação precisa ser escalada. Este é um trade-off aceitável no início.

- **Monorepo vs. Multi-repo:**
  - **Decisão:** Monorepo.
  - **Justificativa:** Simplifica o setup do ambiente e a consistência entre frontend e backend. Facilita refatorações que afetam ambas as bases de código.
  - **Trade-off:** O pipeline de CI/CD pode se tornar mais lento com o tempo, pois testa e constrói tudo a cada mudança. Isso pode ser mitigado com pipelines inteligentes que executam jobs apenas para as partes do código que foram alteradas.

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
