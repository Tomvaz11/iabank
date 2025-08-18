# Output: Ordem de Implementação e Cenários de Teste

## Para: Coordenador de Projeto

A seguir, a ordem de implementação sequencial e os pontos de verificação para os Testes de Integração, derivados do `Blueprint_Arquitetural.md`.

---

## Módulos Base Identificados

*   `iabank.core`
*   `iabank.domain.models`
*   `iabank.application.ports`
*   `iabank.infrastructure.auth` (Representando o middleware de Auth/Tenant)
*   `iabank.infrastructure.repositories`
*   `iabank.application.services`
*   `iabank.api` (Views, Serializers, URLs)
*   `iabank.infrastructure.tasks` (Celery)
*   `iabank.infrastructure.adapters`
*   `frontend.setup` (Estrutura base, libs, API client)
*   `frontend.features.loans.components.NewLoanWizard`
*   `frontend.features.loans.components.LoansPanel`

---

## Ordem de Implementação e Pontos de Teste

1.  **Alvo 0: Setup do Projeto Profissional**
2.  `iabank.domain.models`
3.  `iabank.application.ports`
4.  `iabank.core` (Configuração do Django, settings)
5.  `iabank.infrastructure.auth` (Implementação do middleware de Autenticação JWT, Autorização RBAC e Injeção do `tenant_id`)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (SETUP, SEGURANÇA E MULTI-TENANCY) <<<`
*   **Módulos no Grupo:** `iabank.domain.models`, `iabank.application.ports`, `iabank.core`, `iabank.infrastructure.auth`.
*   **Objetivo do Teste:** Validar que a estrutura base do projeto está funcional e que os mecanismos de segurança e isolamento de dados (multi-tenancy) estão operando corretamente a nível de requisição, antes de implementar qualquer lógica de negócio.
*   **Cenários Chave:**
    1.  **Cenário de Acesso Negado:** Realizar uma requisição a um endpoint protegido (mesmo que um placeholder) sem um token JWT válido. A API DEVE retornar um status `401 Unauthorized`.
    2.  **Cenário de Autorização Falha (RBAC):** Realizar uma requisição com um token JWT válido de um usuário com `role='consultant'` a um endpoint que exija `role='admin'`. A API DEVE retornar um status `403 Forbidden`.
    3.  **Cenário de Contexto de Tenant:** Criar dois tenants (Tenant A, Tenant B) e dois usuários (Usuário A no Tenant A, Usuário B no Tenant B) no banco de dados. Realizar uma requisição autenticada com o Usuário A e verificar, através de um ponto de depuração no middleware, que o `tenant_id` do Tenant A foi corretamente associado à requisição.
    4.  **Cenário de Inicialização:** Verificar se o projeto Django inicializa sem erros e que as configurações básicas (banco de dados, static files) estão carregadas corretamente.

6.  `iabank.infrastructure.repositories`
7.  `iabank.application.services`
8.  `iabank.api` (Views, Serializers, URLs para o fluxo de Empréstimos)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (FLUXO DE CRIAÇÃO DE EMPRÉSTIMO - API) <<<`
*   **Módulos no Grupo:** `iabank.infrastructure.repositories`, `iabank.application.services`, `iabank.api`.
*   **Objetivo do Teste:** Validar o fluxo funcional completo de criação e consulta de um empréstimo, desde o recebimento da requisição na API até a persistência correta dos dados no banco de dados, respeitando o isolamento de tenants.
*   **Cenários Chave:**
    1.  **Cenário de Criação bem-sucedida:** Autenticado como um usuário do Tenant A, enviar uma requisição `POST` para `/api/loans/` com dados válidos para um novo empréstimo. Verificar se a API retorna `201 Created` com os dados do empréstimo criado e se os registros correspondentes (`Loan`, `LoanInstallment`, `Customer`) foram salvos no banco de dados com o `tenant_id` correto do Tenant A.
    2.  **Cenário de Violação de Regra de Negócio:** Enviar uma requisição `POST` para criar um empréstimo com dados que violem uma regra de negócio (ex: `principal_amount` negativo). Verificar se o `LoanApplicationService` impede a criação e a API retorna um status `400 Bad Request` com uma mensagem de erro clara.
    3.  **Cenário de Isolamento de Dados na Consulta:** Criar empréstimos para o Tenant A e para o Tenant B. Autenticado como um usuário do Tenant A, fazer uma requisição `GET` para `/api/loans/`. A resposta DEVE conter apenas os empréstimos do Tenant A e NUNCA os do Tenant B.
    4.  **Cenário de Consulta por ID:** Autenticado como usuário do Tenant A, fazer uma requisição `GET` para `/api/loans/{loan_id_do_tenant_A}/`. A API DEVE retornar os detalhes do empréstimo. Fazer uma requisição `GET` para `/api/loans/{loan_id_do_tenant_B}/`. A API DEVE retornar `404 Not Found`.

9.  `iabank.infrastructure.tasks`
10. `iabank.infrastructure.adapters`

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (SERVIÇOS ASSÍNCRONOS E EXTERNOS) <<<`
*   **Módulos no Grupo:** `iabank.infrastructure.tasks`, `iabank.infrastructure.adapters`.
*   **Objetivo do Teste:** Validar que a integração com o broker de mensagens (Celery/Redis) está funcional e que os serviços de aplicação conseguem enfileirar tarefas assíncronas corretamente.
*   **Cenários Chave:**
    1.  **Cenário de Enfileiramento de Tarefa:** Modificar o `LoanApplicationService` para, após criar um empréstimo, chamar um método `task_queue.enqueue("send_welcome_email", customer_id)`. Realizar o teste de criação de empréstimo e verificar se uma tarefa correspondente foi adicionada à fila do Celery.
    2.  **Cenário de Execução de Tarefa:** Executar um worker do Celery. Enfileirar uma tarefa simples (ex: de log) e verificar se o worker a processa e executa com sucesso, confirmando a conexão com o Redis.
    3.  **Cenário de Adapter Mockado:** Chamar um serviço da camada de aplicação que utilize um adapter para uma API externa (ex: consulta de bureau de crédito). O teste de integração deve "mockar" a chamada HTTP externa e verificar se o adapter processa a resposta mockada corretamente e a repassa para o serviço.

11. `frontend.setup` (Estrutura base, libs, API client)
12. `frontend.features.loans.components.NewLoanWizard`
13. `frontend.features.loans.components.LoansPanel`

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (UI E FLUXO END-TO-END) <<<`
*   **Módulos no Grupo:** `frontend.setup`, `frontend.features.loans.components.NewLoanWizard`, `frontend.features.loans.components.LoansPanel`.
*   **Objetivo do Teste:** Validar o fluxo completo da aplicação do ponto de vista do usuário final, desde a interação com a UI no navegador até a comunicação com o backend e a correta renderização dos dados.
*   **Cenários Chave:**
    1.  **Cenário de Criação via UI:** No navegador, preencher o formulário do `NewLoanWizard` e submeter. Verificar se a chamada à API é feita corretamente, o empréstimo é criado no backend, e o usuário é redirecionado ou recebe uma mensagem de sucesso.
    2.  **Cenário de Listagem e Renderização:** Após criar alguns empréstimos para um tenant, navegar para o `EmprestimosPainel`. Verificar se a UI faz a chamada `GET /api/loans/` e renderiza a tabela com os dados corretos, incluindo os campos formatados (`principalAmountFormatted`, `statusColor`, `installmentsSummary`) conforme o contrato de ViewModel especificado no Blueprint.
    3.  **Cenário de Validação de Input na UI:** Tentar submeter o formulário do `NewLoanWizard` com dados inválidos (ex: campos em branco, valores não numéricos). Verificar se a UI exibe mensagens de erro apropriadas sem enviar uma requisição à API.
    4.  **Cenário de Estado de Carregamento e Erro:** Simular uma resposta lenta ou de erro da API para o `EmprestimosPainel`. Verificar se a UI exibe um indicador de carregamento ("loading spinner") enquanto espera e uma mensagem de erro amigável caso a requisição falhe.