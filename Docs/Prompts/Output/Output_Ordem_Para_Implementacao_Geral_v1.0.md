### **Ordem de Implementação Lógica e Pontos de Teste de Integração**

**Alvo 0:** Setup do Projeto Profissional

**Alvo 1:** `iabank.core`: Modelos (`Tenant`, `BaseTenantModel`) e Migrações iniciais.
**Alvo 2:** `iabank.core`: Registrar a app `core` em `settings.py`.
**Alvo 3:** `iabank.core`: Implementar o Middleware de Isolamento de Tenant.
**Alvo 4:** `iabank.core`: Registrar o Middleware de Tenant em `settings.py`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T1** (Validação da Base Multi-Tenancy) <<<

- **Módulos no Grupo:** `iabank.core`
- **Objetivo do Teste:** Garantir que o modelo `Tenant` e o middleware de isolamento estão funcionalmente corretos em um nível básico, antes de qualquer lógica de negócio ser adicionada.
- **Cenários Chave:**
  1.  **Criação de Tenants:** Criar programaticamente dois tenants distintos (Tenant A, Tenant B) no banco de dados.
  2.  **Middleware de Acesso:** Simular uma requisição HTTP com um header ou token que identifique o Tenant A e verificar se o middleware associa corretamente o `request.tenant` ao objeto do Tenant A.
  3.  **Middleware de Bloqueio:** Simular uma requisição para um tenant inexistente e verificar se o middleware retorna uma resposta de erro apropriada (ex: 404 Not Found).
