# Ordem de Implementação e Cenários de Teste de Integração

**Alvo 0:** Setup do Projeto Profissional

- **Responsabilidades:** Criar a estrutura do monorepo (`backend/`, `frontend/`), configurar Docker (`docker-compose.yml`, `Dockerfile`), Git (`.gitignore`, `CONTRIBUTING.md`), CI/CD (`.github/workflows/main.yml`), e ferramentas de qualidade de código (`.pre-commit-config.yaml`). Configurar `django-environ` e `settings.py` para múltiplos ambientes.

**Alvo 1:** iabank.core: Modelos de Tenancy e Usuários

- **Responsabilidades:** Implementar os modelos `Tenant` e `User` em `core/models.py` e gerar as migrações iniciais.

**Alvo 2:** iabank.core: Serializers de Autenticação JWT

- **Responsabilidades:** Implementar os serializers do DRF Simple JWT para obter e atualizar tokens.

**Alvo 3:** iabank.core: Views/URLs de Autenticação JWT

- **Responsabilidades:** Configurar os endpoints `/api/v1/token/` e `/api/v1/token/refresh/`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T1** (Validação da Autenticação Básica) <<<

- **Módulos no Grupo:** `iabank.core` (Modelos, Serializers e Views de Autenticação)
- **Objetivo do Teste:** Garantir que um usuário existente pode se autenticar com sucesso e receber um par de tokens JWT (acesso e refresh) válidos.
- **Cenários Chave:**
  1. **Autenticação com Sucesso:** Enviar uma requisição POST para `/api/v1/token/` com credenciais válidas e verificar se a resposta é `200 OK` e contém as chaves `access` e `refresh`.
  2. **Autenticação com Falha:** Enviar uma requisição POST para `/api/v1/token/` com senha incorreta e verificar se a resposta é `401 Unauthorized` com a mensagem de erro apropriada.
  3. **Atualização de Token com Sucesso:** Enviar uma requisição POST para `/api/v1/token/refresh/` com um token de refresh válido e verificar se a resposta é `200 OK` e contém uma nova chave `access`.

**Alvo 4:** iabank.core: Middleware de Isolamento de Tenant

- **Responsabilidades:** Implementar a lógica (middleware ou manager customizado) que filtra automaticamente todas as queries pelo `tenant_id` do usuário autenticado.

**Alvo 5:** iabank.core: CRUD de Usuários e Permissões

- **Responsabilidades:** Implementar os Serializers, Services e Views para o CRUD completo de usuários (`/users/`, `/users/me/`) e a base para o controle de acesso (RBAC).

**Alvo 6:** iabank.core: Modelos de Auditoria e Apoio

- **Responsabilidades:** Implementar os modelos `AuditLog` e `Holiday` e gerar as migrações.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T2** (Validação da Gestão de Usuários e Isolamento de Tenants) <<<

- **Módulos no Grupo:** `iabank.core` (CRUD de Usuários, Middleware de Tenant)
- **Objetivo do Teste:** Validar que a gestão de usuários funciona corretamente e que o isolamento de dados entre tenants é estritamente aplicado em todas as requisições.
- **Cenários Chave:**
  1. **Criação de Usuário:** Usando um superusuário autenticado, criar um novo usuário dentro do mesmo tenant e verificar se a resposta é `201 Created`.
  2. **Acesso Negado Entre Tenants:** Criar dois tenants (A e B) e um usuário em cada. Autenticar como o usuário do Tenant A e tentar listar os usuários do Tenant B. A resposta DEVE ser uma lista vazia ou um erro `404/403`, provando que o usuário do Tenant A não pode ver dados do Tenant B.
  3. **Endpoint /me/:** Um usuário autenticado faz uma requisição GET para `/api/v1/users/me/` e verifica se os dados retornados são os seus próprios.

**Alvo 7:** iabank.operations: Modelos de Clientes

- **Responsabilidades:** Implementar o modelo `Customer` em `operations/models.py` e gerar a migração.

**Alvo 8:** iabank.operations: Serviços e Serializers de Clientes

- **Responsabilidades:** Implementar os serviços para lógica de negócio de clientes e os serializers (`CustomerCreateDTO`, `CustomerUpdateDTO`, `CustomerListSerializer`).

**Alvo 9:** iabank.operations: Views/URLs de Clientes

- **Responsabilidades:** Implementar os endpoints da API REST para o CRUD completo de Clientes (`/api/v1/customers/`).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T3** (Validação do CRUD de Clientes com Multi-Tenancy) <<<

- **Módulos no Grupo:** `iabank.operations` (CRUD de Clientes)
- **Objetivo do Teste:** Assegurar que as operações de CRUD para a entidade `Customer` funcionam corretamente e respeitam o isolamento de dados por tenant.
- **Cenários Chave:**
  1. **Criar Cliente com Sucesso:** Usando um usuário autenticado, enviar uma requisição POST para `/api/v1/customers/` com dados válidos e verificar se a resposta é `201 Created` e o cliente foi associado ao tenant correto no banco de dados.
  2. **Violação de Unicidade de Documento por Tenant:** Tentar criar um segundo cliente com o mesmo `document_number` no mesmo tenant e verificar se a API retorna um erro de validação `400 Bad Request`.
  3. **Isolamento de Acesso a Clientes:** Autenticar como um usuário do Tenant A, que possui clientes. Autenticar como um usuário do Tenant B (que não possui clientes) e fazer um GET em `/api/v1/customers/`. Verificar se a resposta é `200 OK` com uma lista de resultados vazia.

**Alvo 10:** iabank.operations: Modelos de Empréstimos e Relacionados

- **Responsabilidades:** Implementar os modelos `Consultant`, `Loan`, `Installment`, `CollectionLog` e `PromissoryNoteHolder` e gerar as migrações.

**Alvo 11:** iabank.finance: Modelos do Módulo Financeiro

- **Responsabilidades:** Implementar todos os modelos do módulo `finance` (`BankAccount`, `PaymentCategory`, `CostCenter`, `Supplier`, `FinancialTransaction`, `PeriodClosing`) para dar suporte à criação de empréstimos.

**Alvo 12:** iabank.operations & iabank.finance: Serviços de Criação de Empréstimo

- **Responsabilidades:** Implementar o `LoanService` que orquestra a criação atômica de um `Loan`, suas `Installments` e as `FinancialTransactions` correspondentes (débito do principal, taxas, etc.).

**Alvo 13:** iabank.operations: Serializers e Views/URLs de Empréstimos

- **Responsabilidades:** Implementar `LoanCreateDTO`, o `LoanListSerializer` (que gera o `LoanListItemViewModel`) e os endpoints para criar e listar empréstimos (`/api/v1/loans/`).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T4** (Validação do Fluxo de Criação de Empréstimos) <<<

- **Módulos no Grupo:** `iabank.operations`, `iabank.finance` (Modelos e Serviços de Empréstimo/Financeiro)
- **Objetivo do Teste:** Validar que o caso de uso principal do sistema - criar um empréstimo - funciona de ponta a ponta, gerando corretamente todas as entidades relacionadas (parcelas, transações financeiras) de forma atômica.
- **Cenários Chave:**
  1. **Criação de Empréstimo Válido:** Usando um usuário autenticado e um cliente pré-existente, enviar uma requisição POST para `/api/v1/loans/` com dados válidos. Verificar se a resposta é `201 Created` e se o número correto de `Installment` e `FinancialTransaction` (saída do principal) foram criados no banco de dados.
  2. **Falha Atômica na Criação:** Simular um erro durante a geração de `FinancialTransaction` (ex: conta bancária inválida) e verificar se a transação inteira do banco de dados sofre rollback (nenhum `Loan` ou `Installment` é persistido).
  3. **Listagem de Empréstimos Formatada:** Fazer uma requisição GET para `/api/v1/loans/` e verificar se a resposta contém uma lista de empréstimos no formato exato do `LoanListItemViewModel`, incluindo campos calculados como `installmentsProgress` e `customerName`.

**Alvo 14:** Frontend: Camada `shared/ui`

- **Responsabilidades:** Implementar a biblioteca de componentes de UI puros e reutilizáveis (Button, Input, Table, Badge, etc.) seguindo o design system.

**Alvo 15:** Frontend: Camadas `shared/api` e `shared/lib`

- **Responsabilidades:** Configurar o cliente HTTP (Axios), o provider do TanStack Query, e criar utilitários e hooks genéricos (ex: `useDebounce`, formatadores de data/moeda).

**Alvo 16:** Frontend: Camada `entities`

- **Responsabilidades:** Implementar os componentes, tipos TypeScript e hooks relacionados às entidades de negócio (ex: `CustomerCard`, `LoanRow`, `useCustomerQuery`).

> > > **PARADA DE TESTES DE INTEGRAÇÃO T5** (Validação da Base da UI e Componentes de Entidade) <<<

- **Módulos no Grupo:** Frontend (`shared/ui`, `shared/api`, `entities`)
- **Objetivo do Teste:** Garantir que os componentes de UI estão funcionais e que os componentes de entidade conseguem buscar e exibir dados de uma API mockada com sucesso.
- **Cenários Chave:**
  1. **Renderização de Componentes `shared`:** Usando uma ferramenta como Storybook, verificar se todos os componentes da `shared/ui` renderizam corretamente com diferentes props.
  2. **Hook de Entidade com Mock:** Testar um hook como `useCustomer(customerId)` isoladamente, mockando a resposta da API, e verificar se ele gerencia corretamente os estados de `isLoading`, `isSuccess` e `data`.
  3. **Renderização de Componente de Entidade:** Montar um componente como `CustomerCard` passando dados mockados e verificar se ele exibe todas as informações formatadas corretamente (ex: `cityState`, `phoneNumberFormatted`).

**Alvo 17:** Frontend: Camada `features`

- **Responsabilidades:** Implementar a lógica de interação do usuário, como o formulário de criação de empréstimo (`feature/create-loan`) e a funcionalidade de busca e filtro de clientes (`feature/filter-customers`).

**Alvo 18:** Frontend: Camadas `app` e `pages`

- **Responsabilidades:** Configurar o roteador, o store global (Zustand para estado do usuário/UI), e montar as páginas finais (`LoansPage`, `CustomersPage`) compondo os widgets e features.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T6** (Validação dos Fluxos de Usuário End-to-End na UI) <<<

- **Módulos no Grupo:** Frontend (`features`, `pages`, `app`)
- **Objetivo do Teste:** Validar que as principais jornadas do usuário funcionam de ponta a ponta, desde a navegação, passando pela interação com formulários e listagens, até a correta exibição dos dados vindos da API real.
- **Cenários Chave:**
  1. **Fluxo de Login:** O usuário insere credenciais na página de login, é redirecionado para o dashboard após o sucesso, e os dados do usuário são armazenados no Zustand.
  2. **Listar e Filtrar Clientes:** O usuário navega para a página de clientes, vê a lista carregada pela API, digita um nome no campo de busca e verifica se a lista é atualizada para mostrar apenas os resultados correspondentes.
  3. **Criar um Novo Empréstimo:** O usuário navega para a página de criação de empréstimo, preenche o formulário, submete, e verifica se é redirecionado para a lista de empréstimos e o novo empréstimo aparece no topo da lista.

**Alvo 19:** Infraestrutura: Estratégia de Observabilidade

- **Responsabilidades:** Implementar o logging estruturado com `structlog`, expor métricas com `django-prometheus` e configurar os endpoints de `health-check`.

> > > **PARADA DE TESTES DE INTEGRAÇÃO T7** (Validação da Observabilidade) <<<

- **Módulos no Grupo:** Backend (`structlog`, `django-prometheus`)
- **Objetivo do Teste:** Garantir que a aplicação está emitindo logs, métricas e health checks nos formatos e endpoints esperados.
- **Cenários Chave:**
  1. **Formato de Log JSON:** Fazer uma requisição à API que gere um log (ex: login falho) e verificar se a saída de log no console do container está em formato JSON estruturado.
  2. **Endpoint de Health Check:** Fazer uma requisição GET para `/health/` e verificar se a resposta é `200 OK` com o status dos serviços conectados (ex: `database: "ok"`).
  3. **Endpoint de Métricas:** Fazer uma requisição GET para `/metrics` e verificar se a resposta contém métricas do Prometheus, como `django_http_requests_total_by_method_path`.
