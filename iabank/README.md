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

## Estrutura do Projeto

O projeto é um monorepo com duas pastas principais:

- `/backend`: Contém a aplicação Django (API).
- `/frontend`: Contém a Single Page Application (SPA) em React.

Consulte o [Blueprint Arquitetural](BluePrint_Arquitetural.md) para mais detalhes.