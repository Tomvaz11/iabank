# Ordem de Implementação Lógica e Cenários de Teste para IABANK v1.0.0

## Ordem de Implementação

**Alvo 0:** Setup do Projeto Profissional

- **Responsabilidade:** Criar a estrutura do monorepo, configurar Docker (`docker-compose.yml`) e Dockerfiles, inicializar os projetos Django e React, configurar CI/CD (GitHub Actions), ferramentas de qualidade (`ruff`, `black`, `eslint`, `prettier`), `pre-commit`, e criar os arquivos de projeto (`README.md`, `.gitignore`, `LICENSE`, etc.).

**Alvo 1:** iabank.core: Modelos e Estrutura Multi-Tenancy

- **Responsabilidade:** Implementar os modelos `Tenant` e `TenantAwareModel`, e o `TenantAwareManager`.

**Alvo 2:** iabank.users: Modelos e Migrações

- **Responsabilidade:** Implementar os modelos `User` e `AuditLog` e gerar as migrações iniciais.

**Alvo 3:** iabank.users: API de Autenticação JWT (Fase 1)

- **Responsabilidade:** Implementar os serializers, views e URLs necessários para os endpoints de obtenção e refresh de token JWT (ex: `/api/v1/token/`).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T1** (Validação do Fluxo de Autenticação Básico) <<<

- **Módulos no Grupo:** `iabank.core` (Modelos), `iabank.users` (Modelos, API de Autenticação).
- **Objetivo do Teste:** Garantir que um usuário pode ser criado no sistema e pode se autenticar com sucesso para obter um token de acesso JWT válido.
- **Cenários Chave:**
  1. **Cenário de Sucesso:** Criar um `Tenant` e um `User` associado a ele diretamente no banco de dados. Enviar uma requisição `POST` para `/api/v1/token/` com as credenciais corretas e verificar se a resposta é `200 OK` e contém os tokens `access` and `refresh`.
  2. **Cenário de Falha (Credenciais Inválidas):** Enviar uma requisição `POST` para `/api/v1/token/` com uma senha incorreta e verificar se a resposta é `401 Unauthorized` com a mensagem de erro apropriada.
  3. **Cenário de Refresh de Token:** Usando o token `refresh` obtido no cenário 1, enviar uma requisição `POST` para `/api/v1/token/refresh/` e verificar se um novo token `access` é retornado com sucesso.

---

**Alvo 4:** iabank.users: Serializers para Gestão de Usuários

- **Responsabilidade:** Implementar os serializers DRF para criar, listar, atualizar e visualizar usuários.

**Alvo 5:** iabank.users: Views e URLs para Gestão de Usuários e Autorização (Fase 2)

- **Responsabilidade:** Implementar os endpoints da API (ex: `/api/v1/users/`, `/api/v1/users/{id}/`, `/api/v1/users/me/`) para o CRUD de usuários, aplicando o isolamento de dados via `TenantAwareManager` e a lógica de permissões.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T2** (Validação do CRUD de Usuários e Isolamento Multi-Tenancy) <<<

- **Módulos no Grupo:** `iabank.users` (API de CRUD), `iabank.core` (Lógica Multi-Tenancy).
- **Objetivo do Teste:** Validar que um usuário autenticado pode gerenciar outros usuários dentro do seu próprio tenant, e que o sistema impede rigorosamente o acesso a dados de outros tenants.
- **Cenários Chave:**
  1. **Cenário de Sucesso (Listagem):** Usando um usuário autenticado simulado do `Tenant A`, fazer uma requisição `GET` para `/api/v1/users/`. Verificar se a resposta `200 OK` contém apenas os usuários pertencentes ao `Tenant A` e nenhum do `Tenant B`.
  2. **Cenário de Sucesso (Criação):** Usando um usuário autenticado simulado do `Tenant A`, fazer uma requisição `POST` para `/api/v1/users/` com dados de um novo usuário. Verificar se a resposta é `201 Created` e se o novo usuário foi criado e associado corretamente ao `Tenant A`.
  3. **Cenário de Segurança (Acesso Cruzado):** Criar um `User` no `Tenant B` e obter seu ID. Usando um usuário autenticado simulado do `Tenant A`, tentar fazer uma requisição `GET` para `/api/v1/users/{id_usuario_tenant_b}/`. Verificar se a resposta é `404 Not Found`.

---

**Alvo 6:** iabank.financials: Modelos de Suporte e Cadastros Gerais

- **Responsabilidade:** Implementar os modelos `Supplier`, `PaymentCategory`, `CostCenter`, `PaymentMethod` e `BankAccount`.

**Alvo 7:** iabank.financials: API (CRUD Básico) para Cadastros Gerais

- **Responsabilidade:** Implementar serializers e views (ex: usando `ModelViewSet`) para fornecer operações CRUD básicas para os modelos de suporte, garantindo a aplicação do `TenantAwareManager`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T3** (Validação dos Módulos de Suporte Financeiro) <<<

- **Módulos no Grupo:** `iabank.financials` (Modelos e API de CRUD).
- **Objetivo do Teste:** Assegurar que as entidades de suporte do módulo financeiro podem ser criadas, lidas, atualizadas e excluídas através da API, respeitando o isolamento de tenant.
- **Cenários Chave:**
  1. **Cenário de Criação e Listagem:** Usando um usuário autenticado simulado, criar uma `BankAccount` via `POST /api/v1/bank-accounts/`. Em seguida, fazer um `GET` no mesmo endpoint e verificar se a conta recém-criada está na lista.
  2. **Cenário de Vínculo e Proteção:** Criar uma `BankAccount` e uma `PaymentCategory`. Tentar deletar a `BankAccount` via `DELETE` e verificar sucesso. Em seguida, criar uma `FinancialTransaction` (modelo a ser criado no futuro) vinculada a essa conta e tentar deletar a conta novamente. O teste (a ser adaptado no futuro) deve verificar se a deleção é bloqueada (`409 Conflict` ou similar) devido à relação `on_delete=models.PROTECT`.

---

**Alvo 8:** iabank.loans: Modelos e Migrações

- **Responsabilidade:** Implementar os modelos `Customer`, `Consultant`, `Lender`, `Loan` e `Installment` e gerar as migrações.

**Alvo 9:** iabank.loans: Repositórios

- **Responsabilidade:** Implementar a camada de repositório (`LoanRepository`, `InstallmentRepository`, etc.) para encapsular a lógica de acesso a dados e consultas complexas ao ORM do Django.

**Alvo 10:** iabank.loans: Serviços de Aplicação

- **Responsabilidade:** Implementar a lógica de negócio na camada de serviço (`LoanService`), como o caso de uso `create_loan`, que orquestra a criação do empréstimo e a geração de todas as suas parcelas de forma atômica.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T4** (Validação da Lógica de Negócio Core - Empréstimos) <<<

- **Módulos no Grupo:** `iabank.loans` (Modelos, Repositórios, Serviços).
- **Objetivo do Teste:** Validar a lógica de negócio central do sistema (criação de empréstimos e cálculo de parcelas) em nível de serviço, sem depender da camada de API.
- **Cenários Chave:**
  1. **Cenário de Criação de Empréstimo:** Instanciar o `LoanService` diretamente no teste. Chamar o método `create_loan` com um DTO válido. Verificar se um objeto `Loan` é criado no banco de dados e se o número correto de objetos `Installment` é gerado, com valores e datas de vencimento calculados corretamente.
  2. **Cenário de Transação Atômica:** Simular um erro (ex: lançar uma exceção) no meio da geração de parcelas dentro do `LoanService`. Verificar se a transação é revertida (rollback) e que nenhum objeto `Loan` ou `Installment` parcial foi persistido no banco de dados.

---

**Alvo 11:** iabank.loans: Serializers

- **Responsabilidade:** Implementar os serializers para a API de empréstimos, incluindo o `LoanCreateSerializer` (para o DTO), `LoanListSerializer` (otimizado para listagem) e `LoanDetailSerializer` (com detalhes completos e parcelas aninhadas).

**Alvo 12:** iabank.loans: Views e URLs

- **Responsabilidade:** Implementar os endpoints da API para todas as operações de empréstimo (`POST /loans/`, `GET /loans/`, `GET /loans/{id}/`), conectando os DTOs e a camada de serviço.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T5** (Validação da API de Gestão de Empréstimos End-to-End) <<<

- **Módulos no Grupo:** `iabank.loans` (Toda a stack: Modelos, Repositórios, Serviços, Serializers, Views).
- **Objetivo do Teste:** Garantir que o fluxo completo de criação e consulta de um empréstimo funciona corretamente através da API REST, desde a requisição HTTP até a persistência no banco de dados.
- **Cenários Chave:**
  1. **Cenário de Criação (Cliente Novo):** Usando um usuário autenticado simulado, enviar uma requisição `POST` para `/api/v1/loans/` contendo os dados do empréstimo e um objeto aninhado `new_customer`. Verificar se a resposta é `201 Created`, e se os objetos `Customer`, `Loan` e `Installment` foram criados corretamente no banco de dados.
  2. **Cenário de Listagem e Filtragem:** Criar múltiplos empréstimos com status diferentes (`IN_PROGRESS`, `PAID_OFF`). Fazer uma requisição `GET` para `/api/v1/loans/?status=IN_PROGRESS` e verificar se a resposta `200 OK` contém apenas os empréstimos com esse status e se os dados estão formatados conforme o `LoanListItemViewModel`.
  3. **Cenário de Detalhe:** Fazer uma requisição `GET` para `/api/v1/loans/{id}/` e verificar se a resposta `200 OK` contém todos os detalhes do empréstimo e a lista completa de suas parcelas aninhadas.

---

**Alvo 13:** iabank.financials: Modelo `FinancialTransaction` e Lógica de Integração

- **Responsabilidade:** Implementar o modelo `FinancialTransaction` e evoluir os serviços para criar automaticamente uma transação de receita quando uma parcela (`Installment`) é marcada como paga.

**Alvo 14:** iabank.financials: API para Transações Financeiras

- **Responsabilidade:** Implementar os serializers e views para o CRUD de `FinancialTransaction` e o endpoint para registrar o pagamento de uma parcela que dispara a criação da transação financeira.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T6** (Validação da Integração entre Módulos Loans e Financials) <<<

- **Módulos no Grupo:** `iabank.financials` (Modelo e API de Transações), `iabank.loans` (Serviço atualizado).
- **Objetivo do Teste:** Verificar se as ações no domínio de Empréstimos (pagamento de parcela) disparam corretamente os eventos esperados no domínio Financeiro (criação de transação).
- **Cenários Chave:**
  1. **Cenário de Pagamento de Parcela:** Dado um empréstimo existente com parcelas `PENDING`, fazer uma requisição `POST` para um endpoint como `/api/v1/installments/{id}/pay/`. Verificar se o status da `Installment` muda para `PAID`, a `payment_date` é preenchida e, crucialmente, se uma nova `FinancialTransaction` do tipo `INCOME` foi criada e vinculada a esta parcela.
  2. **Cenário de Estorno (Exclusão):** Após o cenário 1, simular um estorno deletando a `FinancialTransaction` associada. Verificar se a lógica de negócio reverte o status da `Installment` para `PENDING` (ou outro estado apropriado).

---

**Alvo 15:** UI-1: Camada `shared/ui` (UI Kit)

- **Responsabilidade:** Implementar a biblioteca de componentes visuais puros e reutilizáveis (`Button`, `Input`, `Table`, `Badge`, `Modal`, etc.) com base no design system.

**Alvo 16:** UI-2: Camada `shared/api` e `shared/lib` (Base da UI)

- **Responsabilidade:** Configurar o cliente HTTP (Axios), a instância do TanStack Query, gerar tipos TypeScript a partir dos DTOs do backend, e criar funções utilitárias (formatação de data/moeda).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T7** (Validação da Base da UI e Componentes) <<<

- **Módulos no Grupo:** `frontend/src/shared`.
- **Objetivo do Teste:** Garantir que os componentes base da UI estão funcionais e visualmente corretos, e que a camada de comunicação com a API está pronta para ser consumida.
- **Cenários Chave:**
  1. **Cenário de Teste de Componentes (Visual):** Usar uma ferramenta como Storybook para renderizar cada componente do UI Kit em vários estados (ex: botão primário, secundário, desabilitado) e validar sua aparência e responsividade.
  2. **Cenário de Hook de API:** Criar um teste de unidade para um hook customizado que usa TanStack Query (ex: `useLoansList`). Mockar a resposta da API e verificar se o hook gerencia corretamente os estados `isLoading`, `isSuccess`, `data` e `error`.

---

**Alvo 17:** UI-3: Camada `entities`

- **Responsabilidade:** Implementar os componentes que representam entidades de negócio, como `LoanRow` (uma linha na tabela de empréstimos), `CustomerCard`, e os hooks específicos para buscar dados dessas entidades (ex: `useLoanById`).

**Alvo 18:** UI-4: Camada `features`

- **Responsabilidade:** Implementar componentes que orquestram a interação do usuário, como `CreateLoanForm` (que contém a lógica de estado do formulário e a mutação para a API) e `LoansFilterPanel`.

**Alvo 19:** UI-5: Camada `app` e `pages`

- **Responsabilidade:** Configurar o roteador da aplicação, provedores globais (React Query, Zustand) e compor as páginas finais (ex: `LoansPage`, `CreateLoanPage`) juntando os componentes das camadas `features` e `entities`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T8** (Validação do Fluxo de Usuário Completo na UI) <<<

- **Módulos no Grupo:** `frontend/src/entities`, `frontend/src/features`, `frontend/src/pages`.
- **Objetivo do Teste:** Validar os principais fluxos de usuário de ponta a ponta, desde a interação na interface até a confirmação de que os dados foram corretamente processados e persistidos pelo backend.
- **Cenários Chave:**
  1. **Cenário de Login e Navegação:** Simular um usuário preenchendo o formulário de login. Após o sucesso, verificar se o token é salvo, o usuário é redirecionado para o dashboard e se os dados do usuário (ex: nome) são exibidos corretamente na UI.
  2. **Cenário de Listagem e Filtragem de Empréstimos:** Navegar para a página de empréstimos. Verificar se a tabela é preenchida com dados do backend. Interagir com um filtro (ex: selecionar status "Pago") e verificar se a lista de empréstimos é atualizada na tela para refletir a chamada de API correspondente.
  3. **Cenário de Criação de Empréstimo (End-to-End):** Navegar para a página de criação de empréstimo. Preencher todos os campos do formulário `CreateLoanForm` e submeter. Verificar se uma mensagem de sucesso é exibida e se, ao navegar de volta para a lista de empréstimos, o novo empréstimo aparece na tabela.
