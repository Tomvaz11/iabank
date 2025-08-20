# Ordem de Implementação e Cenários de Teste de Integração

1.  **Alvo 0:** Setup do Projeto Profissional

2.  **Alvo 1:** `iabank.users` (Autenticação JWT e Autorização baseada em Perfis)

> > > **PARADA DE TESTES DE INTEGRAÇÃO T1** (AUTENTICAÇÃO & AUTORIZAÇÃO) <<<

- **Módulos no Grupo:** `iabank.users`
- **Objetivo do Teste:** Validar que o sistema de autenticação via API está funcional e que os endpoints protegidos só podem ser acessados por usuários autenticados com os perfis corretos.
- **Cenários Chave:**
  1.  **Login Bem-Sucedido:** Um POST em `/api/v1/token/` com credenciais válidas retorna um par de tokens (access e refresh) e um status 200.
  2.  **Acesso a Recurso Protegido:** Uma requisição a um endpoint protegido (ex: `/api/v1/users/me/`) com um token de acesso válido no header `Authorization` retorna os dados do usuário e um status 200.
  3.  **Falha de Acesso Sem Token:** A mesma requisição ao endpoint protegido sem o header `Authorization` retorna um status 401 Unauthorized.
  4.  **Falha de Autorização por Perfil:** (Conceitual) Um usuário com perfil 'consultant' tenta acessar um endpoint administrativo e recebe um status 403 Forbidden.

3.  **Alvo 2:** `iabank.core` (Estrutura de Multi-tenancy e Modelos Base)

> > > **PARADA DE TESTES DE INTEGRAÇÃO T2** (ISOLAMENTO DE DADOS - MULTI-TENANCY) <<<

- **Módulos no Grupo:** `iabank.users`, `iabank.core`
- **Objetivo do Teste:** Garantir que o middleware ou manager de multi-tenancy isola completamente os dados entre diferentes tenants.
- **Cenários Chave:**
  1.  **Isolamento de Listagem:** Usando um usuário autenticado simulado do `Tenant A`, uma requisição GET a um recurso (ex: `/api/v1/customers/`) retorna apenas clientes pertencentes ao `Tenant A` e nunca do `Tenant B`.
  2.  **Isolamento de Criação:** Usando um usuário autenticado simulado do `Tenant A`, um POST para criar um novo recurso (ex: Cliente) associa-o automaticamente ao `Tenant A`.
  3.  **Bloqueio de Acesso Cruzado:** Usando um usuário autenticado simulado do `Tenant A`, uma tentativa de acesso direto a um recurso do `Tenant B` por seu ID (ex: `GET /api/v1/customers/{id_do_tenant_b}/`) resulta em um erro 404 Not Found.

4.  **Alvo 3:** `iabank.finance` (Gestão de Contas Financeiras e Transações)

> > > **PARADA DE TESTES DE INTEGRAÇÃO T3** (MÓDULO FINANCEIRO BASE) <<<

- **Módulos no Grupo:** `iabank.finance`
- **Objetivo do Teste:** Validar a criação e manipulação de entidades financeiras básicas, garantindo que as operações de crédito e débito funcionam como esperado.
- **Cenários Chave:**
  1.  **Criação de Conta Financeira:** Usando um usuário autenticado simulado, um POST em `/api/v1/financial-accounts/` com dados válidos cria uma nova conta com o saldo inicial correto.
  2.  **Registro de Transação de Crédito:** Uma chamada de serviço para registrar um crédito em uma conta financeira aumenta corretamente o campo `balance` da `FinancialAccount` correspondente.
  3.  **Registro de Transação de Débito:** Uma chamada de serviço para registrar um débito em uma conta financeira diminui corretamente o campo `balance` da `FinancialAccount` correspondente.

5.  **Alvo 4:** `iabank.loans` (Lógica de Negócio para Originação e Gestão de Empréstimos)

> > > **PARADA DE TESTES DE INTEGRAÇÃO T4** (FLUXO DE NEGÓCIO END-TO-END: ORIGINAÇÃO DE EMPRÉSTIMO) <<<

- **Módulos no Grupo:** `iabank.loans`, `iabank.finance`, `iabank.users`, `iabank.core`
- **Objetivo do Teste:** Validar o fluxo de negócio principal de criação de um empréstimo, verificando a correta interação entre os módulos `loans` e `finance` e a persistência de todas as entidades relacionadas (Empréstimo, Cliente, Parcelas, Transação Financeira).
- **Cenários Chave:**
  1.  **Criação de Empréstimo Bem-Sucedida:** Um POST em `/api/v1/loans/` com dados válidos de cliente e empréstimo retorna status 201, cria um registro de `Loan`, cria os registros de `Installment` correspondentes e gera uma transação de débito na conta financeira da empresa (liberação do valor).
  2.  **Validação de Dados de Entrada:** Um POST em `/api/v1/loans/` com dados inválidos (ex: `principal_amount` negativo) retorna um erro 400 Bad Request com a estrutura de erro padronizada, detalhando o campo inválido.
  3.  **Atualização de Status de Parcela:** Um POST para um endpoint de pagamento de parcela (ex: `/api/v1/installments/{id}/pay/`) atualiza o status da parcela para 'paid', define a `payment_date` e gera a transação de crédito correspondente na conta financeira da empresa.

6.  **Alvo 5:** Frontend - Camada `shared` (UI Kit, Configuração do Cliente de API, Utilitários)

7.  **Alvo 6:** Frontend - Camada `entities` (Componentes de Domínio: `LoanStatusBadge`, `CustomerAvatar`, etc.)

> > > **PARADA DE TESTES DE INTEGRAÇÃO T5** (BIBLIOTECA DE COMPONENTES DA UI) <<<

- **Módulos no Grupo:** `frontend/src/shared`, `frontend/src/entities`
- **Objetivo do Teste:** Validar que os componentes de UI puros (`shared`) e os componentes de entidade (`entities`) renderizam corretamente com diferentes props e estão visualmente consistentes (usando testes de snapshot ou ferramentas como Storybook).
- **Cenários Chave:**
  1.  **Renderização do Botão:** O componente `Button` da camada `shared/ui` renderiza corretamente com diferentes variantes (`primary`, `secondary`) e estados (`disabled`, `loading`).
  2.  **Renderização do Badge de Status:** O componente `LoanStatusBadge` da camada `entities/loan` exibe a cor e o texto corretos para cada status de empréstimo possível ('active', 'paid_off', 'in_arrears').
  3.  **Configuração do Cliente API:** O cliente Axios (`shared/api`) está configurado para incluir corretamente o token JWT do estado global (Zustand) no header `Authorization` de cada requisição.

8.  **Alvo 7:** Frontend - Camada `features` (Lógica de UI para Listagem, Filtros e Criação de Empréstimos)

9.  **Alvo 8:** Frontend - Camada `pages` (Composição final das telas `LoansPage`, `DashboardPage`)

> > > **PARADA DE TESTES DE INTEGRAÇÃO T6** (INTEGRAÇÃO FULL-STACK: GESTÃO DE EMPRÉSTIMOS) <<<

- **Módulos no Grupo:** Frontend Completo (`pages`, `features`, `entities`, `shared`), Backend Completo
- **Objetivo do Teste:** Validar o fluxo completo do usuário através da interface gráfica, desde a autenticação até a visualização e criação de dados, garantindo que o frontend interage corretamente com a API e mapeia os dados para os ViewModels esperados.
- **Cenários Chave:**
  1.  **Fluxo de Login e Listagem:** O usuário preenche o formulário de login, é redirecionado para o dashboard, navega para a página de empréstimos, e a tabela é populada com dados do endpoint `/api/v1/loans/`, com os valores formatados conforme o `LoanListItemViewModel`.
  2.  **Fluxo de Criação de Novo Empréstimo:** O usuário abre o wizard de "Novo Empréstimo", preenche o formulário com dados válidos (React Hook Form + Zod), submete, e o novo empréstimo aparece na lista sem a necessidade de recarregar a página (validação da invalidação de cache do TanStack Query).
  3.  **Tratamento de Erros da API na UI:** O usuário tenta criar um empréstimo com dados inválidos. A API retorna um erro 400. O formulário na UI exibe as mensagens de erro específicas do campo retornadas pela API.
