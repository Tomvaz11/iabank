# Ordem de Implementação e Cenários de Teste

**Alvo 0:** Setup do Projeto Profissional

**Alvo 1:** `iabank.core`: Modelos e Migrações (`Tenant`, `TenantAwareModel`, `AuditableModel`).

**Alvo 2:** `iabank.users`: Modelo e Migração (`User` com referência ao `Tenant`).

**Alvo 3:** `iabank.users`: Serializers e Views para Autenticação JWT (Endpoints `/token/` e `/token/refresh/`).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T1** (Autenticação Básica e Estrutura de Tenancy) <<<

- **Módulos no Grupo:** `iabank.core` (Modelos), `iabank.users` (Modelo, Autenticação).
- **Objetivo do Teste:** Validar que a estrutura fundamental de multi-tenancy está no lugar e que o sistema de autenticação via token JWT está funcional.
- **Cenários Chave:**
  1.  **Obtenção de Token:** Um POST para `/api/v1/token/` com credenciais válidas de um usuário pré-cadastrado deve retornar um `access` e um `refresh` token.
  2.  **Falha de Autenticação:** Um POST para `/api/v1/token/` com credenciais inválidas deve retornar um status `401 Unauthorized`.
  3.  **Refresh de Token:** Um POST para `/api/v1/token/refresh/` com um `refresh` token válido deve retornar um novo `access` token.
  4.  **Associação de Tenant:** Validar no banco de dados que um `User` recém-criado (via script de teste) está corretamente associado a um `Tenant`.
