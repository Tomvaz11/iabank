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

**Alvo 5:** `iabank.users`: Modelo (`User` customizado com `ForeignKey` para `Tenant`) e Migrações.
**Alvo 6:** `iabank.users`: Registrar a app `users` em `settings.py`.
**Alvo 7:** `iabank.users`: Implementar Serializers, Views e URLs para Autenticação JWT (`/api/v1/token/`, `/api/v1/token/refresh/`) usando `djangorestframework-simplejwt`.
**Alvo 8:** `iabank.users`: Registrar as URLs de Autenticação no `urls.py` principal sob o prefixo `/api/v1/`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T2** (Validação do Fluxo de Autenticação) <<<

- **Módulos no Grupo:** `iabank.users`
- **Objetivo do Teste:** Validar que um usuário pode se autenticar com sucesso e que o token JWT gerado está corretamente associado ao seu tenant.
- **Cenários Chave:**
  1.  **Login com Sucesso:** Dado um usuário pré-existente associado ao Tenant A, fazer uma requisição POST para `/api/v1/token/` com credenciais válidas e verificar se a resposta é `200 OK` e contém os tokens de acesso e refresh.
  2.  **Login com Falha:** Fazer uma requisição POST para `/api/v1/token/` com credenciais inválidas e verificar se a resposta é `401 Unauthorized`.
  3.  **Token Refresh:** Usar um token de refresh válido para obter um novo token de acesso e verificar se a operação é bem-sucedida.

**Alvo 9:** `iabank.customers`: Modelos (`Customer`) e Migrações.
**Alvo 10:** `iabank.customers`: Registrar a app `customers` em `settings.py`.
**Alvo 11:** `iabank.customers`: Implementar Factories (`TenantFactory`, `UserFactory`, `CustomerFactory`) e seus meta-testes (`test_factories.py`).
**Alvo 12:** `iabank.customers`: Implementar Serializers (`CustomerCreateDTO`, `CustomerSerializer`).
**Alvo 13:** `iabank.customers`: Implementar Views (`CustomerViewSet` para CRUD completo).
**Alvo 14:** `iabank.customers`: Implementar Roteamento (`urls.py` para `CustomerViewSet`).
**Alvo 15:** `iabank.customers`: Registrar as URLs de Clientes no `urls.py` principal.
**Alvo 16:** `DRF`: Implementar o Handler de Exceção customizado para padronizar as respostas de erro da API.
**Alvo 17:** `DRF`: Registrar o Handler de Exceção customizado em `settings.py`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T3** (Validação do CRUD de Clientes com Segurança Multi-Tenant) <<<

- **Módulos no Grupo:** `iabank.customers`, DRF (Error Handling)
- **Objetivo do Teste:** Garantir que o CRUD de clientes funciona corretamente via API e, crucialmente, que as regras de isolamento de tenant são aplicadas.
- **Cenários Chave:**
  1.  **Criação de Cliente:** Usando um usuário autenticado (simulado) do Tenant A, fazer um POST para `/api/v1/customers/` com dados válidos e verificar se o cliente é criado com o `tenant_id` correto e a resposta é `201 Created`.
  2.  **Acesso Permitido:** Usando o mesmo usuário do Tenant A, fazer um GET para `/api/v1/customers/<id_cliente_A>/` e verificar se os dados do cliente são retornados com sucesso.
  3.  **Acesso Negado (Isolamento de Tenant):** Usando o mesmo usuário do Tenant A, tentar fazer um GET para um cliente que pertence ao Tenant B e verificar se a resposta é `404 Not Found`.
  4.  **Validação de Erro:** Fazer um POST para `/api/v1/customers/` com dados inválidos (ex: `document_number` duplicado) e verificar se a resposta é `422 Unprocessable Entity` com o formato de erro customizado definido.

**Alvo 18:** `iabank.operations`: Modelos (`Consultant`, `Loan`, `Installment`) e Migrações.
**Alvo 19:** `iabank.operations`: Registrar a app `operations` em `settings.py`.
**Alvo 20:** `iabank.operations`: Implementar Factories (`ConsultantFactory`, `LoanFactory`) e seus meta-testes, garantindo a propagação de tenant para o `Customer` relacionado.
**Alvo 21:** `iabank.operations`: Implementar a camada de Infraestrutura/Repositório (`DjangoLoanRepository`).
**Alvo 22:** `iabank.operations`: Implementar a camada de Aplicação/Serviços (`LoanService`), incluindo a lógica de cálculo e geração de parcelas.
**Alvo 23:** `iabank.operations`: Implementar Serializers (`LoanCreateDTO`, `LoanListDTO`, `LoanDetailSerializer` com parcelas aninhadas).
**Alvo 24:** `iabank.operations`: Implementar Views (`LoanViewSet`).
**Alvo 25:** `iabank.operations`: Implementar Roteamento (`urls.py` para `LoanViewSet`).
**Alvo 26:** `iabank.operations`: Registrar URLs de Operações no `urls.py` principal.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T4** (Validação do Fluxo Central de Negócio: Criação de Empréstimo) <<<

- **Módulos no Grupo:** `iabank.operations`
- **Objetivo do Teste:** Validar o fluxo end-to-end de criação de um empréstimo, que envolve a orquestração entre múltiplos modelos (`Loan`, `Installment`), lógica de serviço e persistência no banco de dados.
- **Cenários Chave:**
  1.  **Criação de Empréstimo com Sucesso:** Dado um usuário autenticado (Consultor do Tenant A) e um cliente pré-existente (do Tenant A), fazer um POST para `/api/v1/loans/` com dados válidos. Verificar se o Empréstimo é criado com status `IN_PROGRESS`, se o número correto de Parcelas (`Installment`) foi gerado com os valores e datas corretas, e se a resposta é `201 Created`.
  2.  **Falha por Cliente de Outro Tenant:** Tentar criar um empréstimo para um cliente que pertence ao Tenant B e verificar se o `LoanService` levanta uma exceção de validação e a API retorna um erro `4xx` (ex: `404` ou `422`).
  3.  **Listagem de Empréstimos:** Fazer um GET para `/api/v1/loans/` e verificar se a resposta contém apenas os empréstimos do Tenant A, serializados com o `LoanListDTO`.
  4.  **Detalhamento de Empréstimo:** Fazer um GET para `/api/v1/loans/<id_emprestimo_A>/` e verificar se os detalhes do empréstimo e a lista de suas parcelas são retornados corretamente.

**Alvo 27:** `iabank.finance`: Modelos (`BankAccount`, `FinancialTransaction`, etc.) e Migrações.
**Alvo 28:** `iabank.finance`: Registrar a app `finance` em `settings.py`.
**Alvo 29:** `iabank.finance`: Implementar Factories e seus meta-testes.
**Alvo 30:** `iabank.finance`: Implementar CRUD completo (Serializers, Views, URLs) para `BankAccount`, `Supplier`, `PaymentCategory`, e `CostCenter`.
**Alvo 31:** `iabank.finance`: Modificar o `LoanService` para, após criar um empréstimo, gerar automaticamente a `FinancialTransaction` de receita correspondente, vinculada à primeira parcela.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T5** (Validação da Integração Financeira) <<<

- **Módulos no Grupo:** `iabank.finance`
- **Objetivo do Teste:** Garantir que as operações de negócio (`operations`) disparam corretamente os eventos financeiros (`finance`), mantendo a consistência dos dados.
- **Cenários Chave:**
  1.  **Geração de Transação Financeira na Criação do Empréstimo:** Repetir o cenário de sucesso da T4 e verificar, adicionalmente, se uma `FinancialTransaction` do tipo `INCOME` foi criada e associada à primeira parcela do empréstimo.
  2.  **CRUD Financeiro:** Validar os endpoints de CRUD para `BankAccount` para garantir que um usuário autenticado pode gerenciar as contas bancárias do seu tenant.

**Alvo 32:** `iabank.core`: Implementar comando de gerenciamento `seed_data` usando `factory-boy` para popular o ambiente de desenvolvimento.
**Alvo 33:** `Observabilidade`: Implementar e configurar `structlog` para logs estruturados em JSON, incluindo um middleware para adicionar `request_id` e `tenant_id` ao contexto.
**Alvo 34:** `Observabilidade`: Implementar e configurar `django-prometheus` com métricas de negócio chave (ex: `loans_created_total`) e endpoint `/metrics`.
**Alvo 35:** `Observabilidade`: Implementar endpoint `/health` que verifica a conexão com o banco de dados e Redis.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T6** (Validação dos Requisitos Não-Funcionais) <<<

- **Módulos no Grupo:** `iabank.core` (seeding), Observabilidade
- **Objetivo do Teste:** Verificar se as ferramentas de observabilidade e utilitários de desenvolvimento estão corretamente configurados e funcionais.
- **Cenários Chave:**
  1.  **Execução do Seeder:** Executar o comando `manage.py seed_data` e verificar se o banco de dados é populado com dados consistentes entre os tenants.
  2.  **Logs Estruturados:** Fazer uma requisição a qualquer endpoint e verificar se a saída do log está em JSON e contém os campos `request_id` e `tenant_id`.
  3.  **Endpoint de Métricas:** Fazer um GET para `/metrics` e verificar se a resposta é `200 OK` e contém as métricas Prometheus definidas.
  4.  **Endpoint de Health Check:** Fazer um GET para `/health` e verificar se a resposta é `200 OK`.

**Alvo 36:** `Frontend`: Setup do projeto com Vite, TypeScript, Tailwind e estrutura de diretórios `Feature-based`.
**Alvo 37:** `Frontend`: Implementação da camada **`shared/ui`** (Componentes puros: Button, Input, Table, StatusBadge, DatePicker, etc).
**Alvo 38:** `Frontend`: Implementação da camada **`shared/api`** (Cliente Axios com interceptors para JWT) e **`shared/lib`** (Utilitários de formatação).
**Alvo 39:** `Frontend`: Implementação da camada **`entities`** (Componentes de entidade como `LoanRow`, `CustomerInfoCard` e seus respectivos hooks e tipos TypeScript).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T7** (Validação da Biblioteca de Componentes da UI) <<<

- **Módulos no Grupo:** `Frontend (shared, entities)`
- **Objetivo do Teste:** Validar (preferencialmente com testes visuais/Storybook) que a base de componentes da UI está funcional e que a comunicação inicial com a API (sem autenticação) está configurada.
- **Cenários Chave:**
  1.  **Renderização de Componentes:** Verificar se os componentes da `shared/ui` (ex: `SmartTable`) renderizam corretamente com dados mockados.
  2.  **Configuração do Cliente API:** Fazer uma chamada a um endpoint público (se houver, como `/health`) usando o cliente Axios configurado para garantir que a base de comunicação está funcionando.

**Alvo 40:** `Frontend`: Implementação da camada **`features`** para Autenticação (Login Form, hooks `useLogin` do TanStack Query).
**Alvo 41:** `Frontend`: Implementação da camada **`features`** para Clientes (`CustomerList` com tabela, filtros e paginação; `CustomerForm`).
**Alvo 42:** `Frontend`: Implementação da camada **`features`** para Empréstimos (`LoanList`, `LoanDetails`, `NewLoanWizard`).
**Alvo 43:** `Frontend`: Implementação da camada **`app`** (Router, Providers, Store Zustand para usuário logado) e **`pages`** (Composição das telas finais a partir das features).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T8** (Validação do Fluxo de Usuário End-to-End) <<<

- **Módulos no Grupo:** `Frontend (features, app, pages)`
- **Objetivo do Teste:** Realizar um teste de fumaça completo nos principais fluxos de usuário, integrando a UI com a API backend já implementada.
- **Cenários Chave:**
  1.  **Fluxo de Login e Acesso:** Acessar a página de login, inserir credenciais válidas, ser redirecionado para o dashboard e verificar se as informações do usuário estão no estado global (Zustand).
  2.  **Fluxo de CRUD de Cliente:** Navegar para a lista de clientes, verificar se a tabela é preenchida com dados da API, criar um novo cliente através do formulário, vê-lo aparecer na lista e, por fim, excluí-lo.
  3.  **Fluxo de Criação de Empréstimo:** Navegar para o "Wizard" de novo empréstimo, selecionar um cliente existente, preencher os dados do empréstimo, submeter e ser redirecionado para a lista de empréstimos, onde o novo contrato deve aparecer.
