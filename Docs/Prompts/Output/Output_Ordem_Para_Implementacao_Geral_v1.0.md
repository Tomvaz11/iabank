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

**Alvo 4:** `iabank.users`: Fase 2 - API de Gestão de Usuários (CRUD)

- **Responsabilidade:** Implementar os Serializers e Views para os endpoints de gerenciamento de usuários, como `GET /api/v1/users/`, `POST /api/v1/users/`, e `GET /api/v1/users/me/`.

**Alvo 5:** `iabank.core`: Lógica de Multi-Tenancy

- **Responsabilidade:** Implementar a lógica de isolamento de dados, provavelmente através de um `Manager` customizado no `TenantAwareModel` e/ou um middleware que associa o `Tenant` correto a cada requisição baseada no `request.user`.

**Alvo 6:** `iabank.administration`: Modelos e Migrações

- **Responsabilidade:** Implementar os modelos `AuditLog` e `SystemParameter` e gerar suas migrações.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T2** (Gestão de Usuários e Isolamento de Tenant) <<<

- **Módulos no Grupo:** `users` (CRUD), `core` (Multi-Tenancy), `administration`.
- **Objetivo do Teste:** Validar que os endpoints de gerenciamento de usuários funcionam corretamente e que a lógica de isolamento de dados previne vazamento de informações entre tenants.
- **Cenários Chave:**
  1.  **Isolamento de Listagem:** Criar usuários em dois tenants distintos (`Tenant A` e `Tenant B`). Usando um usuário autenticado simulado do `Tenant A`, fazer uma requisição `GET` para `/api/v1/users/` e verificar se a lista contém _apenas_ os usuários do `Tenant A`.
  2.  **Prevenção de Acesso Direto:** Usando um usuário autenticado simulado do `Tenant A`, tentar fazer um `GET` para `/api/v1/users/{id_usuario_tenant_b}/` e verificar se a resposta é `404 Not Found`.
  3.  **Criação de Usuário no Tenant Correto:** Usando um usuário autenticado simulado do `Tenant A`, fazer um `POST` para `/api/v1/users/` para criar um novo usuário. Verificar no banco de dados se o novo usuário foi corretamente associado ao `Tenant A`.
  4.  **Endpoint do Próprio Usuário:** Usando um usuário autenticado simulado, fazer um `GET` para `/api/v1/users/me/` e verificar se os dados retornados correspondem aos do usuário logado.

**Alvo 7:** `iabank.operational`: Modelos `Customer` e `CustomerDocument`

- **Responsabilidade:** Implementar os modelos para representar clientes e seus documentos, herdando de `TenantAwareModel`. Gerar as migrações.

**Alvo 8:** `iabank.operational`: Serviços de Aplicação para `Customer`

- **Responsabilidade:** Implementar a classe de serviço que conterá a lógica de negócio para as operações de `Customer`.

**Alvo 9:** `iabank.operational`: Serializers para `Customer`

- **Responsabilidade:** Implementar os serializers (DTOs) para validação de entrada (`CustomerCreateDTO`) e formatação de saída (`CustomerListDTO`).

**Alvo 10:** `iabank.operational`: Views e URLs para `Customer`

- **Responsabilidade:** Implementar os endpoints da API para o ciclo de vida completo (CRUD) de um `Customer`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T3** (CRUD de Clientes) <<<

- **Módulos no Grupo:** `operational` (foco em Customer).
- **Objetivo do Teste:** Validar o gerenciamento completo de entidades `Customer` através da API, garantindo que todas as operações respeitem o isolamento de tenant.
- **Cenários Chave:**
  1.  **Criação de Cliente:** Usando um usuário autenticado simulado, fazer uma requisição `POST` para `/api/v1/customers/` com dados válidos. Verificar se a resposta é `201 Created` e se o cliente foi criado no banco associado ao tenant correto.
  2.  **Validação de Dados:** Tentar criar um cliente com um `document` (CPF/CNPJ) que já existe no mesmo tenant e verificar se a API retorna um erro de validação (`400 Bad Request`).
  3.  **Listagem por Tenant:** Criar clientes em dois tenants diferentes. Usando um usuário autenticado do `Tenant A`, listar os clientes e verificar se apenas os do `Tenant A` são retornados.
  4.  **Atualização de Cliente:** Fazer uma requisição `PATCH` para atualizar o telefone de um cliente existente e verificar se o dado foi alterado corretamente no banco de dados.

**Alvo 11:** `iabank.operational`: Modelos `Consultant`, `Loan`, `Installment`

- **Responsabilidade:** Implementar os modelos centrais para o negócio de empréstimos, incluindo suas relações e status. Gerar as migrações.

**Alvo 12:** `iabank.financial`: Modelos

- **Responsabilidade:** Implementar todos os modelos do módulo financeiro (`BankAccount`, `PaymentCategory`, `FinancialTransaction`, etc.), pois estão interligados e a transação financeira está ligada à parcela. Gerar as migrações.

**Alvo 13:** `iabank.operational`: Serviço de Aplicação para `Loan`

- **Responsabilidade:** Implementar a lógica de negócio no `LoanService`, focando no método `create_loan`, que deve criar o empréstimo e gerar todas as suas parcelas (`Installment`) de forma atômica.

**Alvo 14:** `iabank.operational`: Serializers e Views para `Loan`

- **Responsabilidade:** Implementar os serializers `LoanCreateDTO`, `LoanListDTO` e as Views para criação (`POST /api/v1/loans/`) e listagem (`GET /api/v1/loans/`).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T4** (Criação de Empréstimos) <<<

- **Módulos no Grupo:** `operational` (Loan, Installment), `financial` (Modelos).
- **Objetivo do Teste:** Validar que o processo de criação de um empréstimo gera corretamente o registro principal (`Loan`) e todos os seus registros filhos (`Installment`) conforme as regras de negócio.
- **Cenários Chave:**
  1.  **Criação de Empréstimo com Sucesso:** Dado um cliente existente criado via `CustomerFactory`, fazer um `POST` para `/api/v1/loans/` com dados válidos (valor, juros, nº de parcelas). Verificar se a resposta é `201 Created`, se um registro `Loan` foi criado e se exatamente o `number_of_installments` de registros `Installment` foram criados e associados a ele.
  2.  **Validação de Negócio:** Tentar criar um empréstimo para um `customer_id` que pertence a outro tenant e verificar se a API retorna um erro `404 Not Found`.
  3.  **Cálculo de Parcelas (Simplificado):** Verificar se o campo `due_date` da primeira parcela corresponde ao `first_installment_date` informado e se as datas das parcelas subsequentes estão com o intervalo de um mês.
  4.  **Atomicidade da Criação:** Simular um erro durante a criação das parcelas (ex: mockando um método para levantar uma exceção) e verificar, usando `@transaction.atomic`, que nem o registro `Loan` nem nenhuma `Installment` foram persistidos no banco.

**Alvo 15:** `iabank.financial`: Serviço de Aplicação para `FinancialTransaction`

- **Responsabilidade:** Implementar a lógica de serviço para registrar transações financeiras, com foco especial no caso de uso de registrar um pagamento para uma `Installment`.

**Alvo 16:** `iabank.financial`: Serializers e Views para `FinancialTransaction`

- **Responsabilidade:** Implementar os DTOs e endpoints da API para gerenciar transações, incluindo um endpoint específico para registrar o pagamento de uma parcela (ex: `POST /api/v1/installments/{id}/pay/`).

**Alvo 17:** `iabank.operational`: Modelo `CollectionLog` e sua API CRUD

- **Responsabilidade:** Implementar o modelo `CollectionLog` e seus endpoints básicos para permitir o registro de interações de cobrança.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T5** (Registro de Pagamentos e Cobrança) <<<

- **Módulos no Grupo:** `financial` (Serviços e API), `operational` (CollectionLog).
- **Objetivo do Teste:** Validar o fluxo de registro de pagamento de uma parcela, incluindo a criação da transação financeira correspondente e a atualização de status da parcela e do empréstimo.
- **Cenários Chave:**
  1.  **Pagamento Total da Parcela:** Dado um empréstimo com uma parcela `PENDING`, fazer uma requisição ao endpoint de pagamento. Verificar se o status da `Installment` muda para `PAID`, se seu campo `amount_paid` é atualizado e se uma `FinancialTransaction` do tipo `INCOME` é criada e vinculada à parcela.
  2.  **Pagamento Parcial da Parcela:** Fazer uma requisição de pagamento com um valor menor que o total da parcela. Verificar se o status da `Installment` muda para `PARTIALLY_PAID` e se `amount_paid` reflete o valor pago.
  3.  **Finalização do Empréstimo:** Realizar o pagamento da última parcela pendente de um empréstimo. Verificar se o status do `Loan` é automaticamente atualizado para `PAID_OFF` (lógica a ser implementada no serviço).
  4.  **Registro de Cobrança:** Dado um empréstimo em atraso, fazer um `POST` para `/api/v1/collection_logs/` e verificar se a anotação de cobrança foi criada com sucesso e associada ao empréstimo correto.

**Alvo 18:** UI - Alvo UI-1: Camada `shared/ui`

- **Responsabilidade:** Criar a biblioteca de componentes de UI puros e reutilizáveis (ex: `Button`, `Input`, `Table`, `Modal`, `Badge`) com base no design system.

**Alvo 19:** UI - Alvo UI-2: Camada `shared/api` e `shared/lib`

- **Responsabilidade:** Configurar o cliente HTTP (Axios) com interceptors para autenticação. Criar funções utilitárias para formatação de datas, moedas, etc.

**Alvo 20:** UI - Alvo UI-3: Camada `entities`

- **Responsabilidade:** Implementar os componentes, tipos (ViewModels) e hooks de busca de dados (TanStack Query) para cada entidade principal: `user`, `customer`, `loan`, `financialTransaction`. Ex: `useGetLoans`, `LoanStatusBadge`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T6** (Fundação da UI e Conectividade com API) <<<

- **Módulos no Grupo:** Frontend (`shared`, `entities`).
- **Objetivo do Teste:** Validar que a base da UI está funcional, os componentes de entidade renderizam corretamente e os hooks de dados conseguem buscar informações da API backend.
- **Cenários Chave:**
  1.  **(Component Test/Storybook):** Isolar e renderizar componentes como `LoanStatusBadge` e `CustomerListViewModel` com dados mocados para garantir que a lógica de formatação e visualização está correta.
  2.  **Conectividade da API (Login):** Montar um componente de teste que utiliza um hook `useLogin`. Simular a submissão do formulário e verificar se uma chamada `POST` é feita para `/api/v1/token/` e se o token JWT retornado é salvo no estado global (Zustand).
  3.  **Busca de Dados Autenticada:** Em um ambiente de teste onde um token de login já foi simulado no estado global, montar um componente que usa o hook `useGetLoans`. Verificar se o hook dispara uma requisição `GET` para `/api/v1/loans/` com o `Authorization header` correto.
  4.  **Manipulação de Estado (Loading/Error):** Para o hook `useGetCustomers`, mocar a resposta da API para simular um estado de carregamento e depois um erro. Verificar se o componente que consome o hook renderiza corretamente os indicadores de `loading` e `error`.

**Alvo 21:** UI - Alvo UI-4: Camada `features`

- **Responsabilidade:** Implementar a lógica de interação do usuário, como o formulário de login (`features/auth`), o wizard de criação de empréstimo (`features/create-loan`) e os filtros da tabela (`features/filter-loans`).

**Alvo 22:** UI - Alvo UI-5: Camada `widgets`, `app` e `pages`

- **Responsabilidade:** Compor os componentes das camadas inferiores para construir widgets complexos (`LoansTable`, `Header`) e montar as telas finais (`LoansPage`, `DashboardPage`). Configurar o roteamento da aplicação na camada `app`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T7** (Fluxos de Usuário End-to-End) <<<

- **Módulos no Grupo:** Frontend (todas as camadas).
- **Objetivo do Teste:** Validar os fluxos de negócio completos da perspectiva do usuário, garantindo que a interação na UI se traduza nas operações corretas no backend e que a UI reaja adequadamente às respostas da API.
- **Cenários Chave:**
  1.  **Login e Visualização de Dados:** Acessar a página de login, preencher credenciais válidas e submeter. Verificar se o usuário é redirecionado para a `LoansPage`, se o `Header` exibe o nome do usuário e se a `LoansTable` é preenchida com os dados de empréstimos vindos da API.
  2.  **Criação de Empréstimo (E2E):** Na `LoansPage`, clicar no botão "Novo Empréstimo". Preencher o formulário no wizard `create-loan`, selecionar um cliente existente, e submeter. Verificar se a UI exibe uma notificação de sucesso, a tabela de empréstimos é automaticamente atualizada (revalidada pelo TanStack Query) e o novo empréstimo aparece na lista.
  3.  **Interação com a Tabela:** Na `LoansTable`, usar os filtros de status (ex: "Em Cobrança"). Verificar se uma nova chamada à API é feita com os parâmetros de filtro corretos e se a tabela é re-renderizada para mostrar apenas os resultados filtrados.
  4.  **Navegação Protegida:** Sem estar logado, tentar acessar diretamente a URL `/loans`. Verificar se o sistema de roteamento redireciona o usuário para a página de login.
