# Ordem de Implementação e Cenários de Teste

**Alvo 0:** Setup do Projeto Profissional

- **Responsabilidade:** Configurar a estrutura do monorepo (`backend/`, `frontend/`), inicializar os projetos Django e React, criar os arquivos de configuração (`docker-compose.yml`, `Dockerfile.*`, `pyproject.toml`, `.pre-commit-config.yaml`), e estabelecer o pipeline de CI/CD inicial (`.github/workflows/ci-cd.yml`).

**Alvo 1:** `iabank.core`: Modelos e Migrações

- **Responsabilidade:** Implementar os modelos `Tenant` e `TenantAwareModel`, que são a base para o isolamento de dados multi-tenant. Gerar as migrações iniciais.

**Alvo 2:** `iabank.users`: Modelos e Migrações

- **Responsabilidade:** Implementar o modelo customizado `User` com a referência ao `Tenant` e gerar sua migração.

**Alvo 3:** `iabank.users`: Fase 1 - API de Autenticação JWT

- **Responsabilidade:** Implementar os Serializers e Views (usando uma biblioteca como `djangorestframework-simplejwt`) para os endpoints `/api/v1/token/` e `/api/v1/token/refresh/`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T1** (Autenticação Básica) <<<

- **Módulos no Grupo:** `core`, `users` (Modelos e API de Autenticação).
- **Objetivo do Teste:** Validar que um usuário pode ser criado no banco de dados e pode obter um par de tokens JWT (acesso e refresh) válido através da API.
- **Cenários Chave:**
  1.  **Sucesso na Autenticação:** Criar um `Tenant` e um `User` diretamente no banco de dados de teste. Fazer uma requisição `POST` para `/api/v1/token/` com as credenciais corretas e verificar se a resposta é `200 OK` e contém as chaves `access` e `refresh`.
  2.  **Falha na Autenticação:** Fazer uma requisição `POST` para `/api/v1/token/` com uma senha incorreta e verificar se a resposta é `401 Unauthorized`.
  3.  **Renovação de Token:** Usar o `refresh` token obtido no cenário 1 para fazer uma requisição `POST` para `/api/v1/token/refresh/` e verificar se a resposta é `200 OK` e contém uma nova chave `access`.
