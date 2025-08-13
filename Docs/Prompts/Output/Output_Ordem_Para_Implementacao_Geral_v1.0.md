# Ordem de Implementação e Testes de Integração para o IABANK v1.0

## Instruções para o Coordenador

Este documento define a ordem de implementação sequencial e os pontos de parada para Testes de Integração (TI). Cada tarefa na lista numerada representa um "Módulo Principal" a ser implementado. Siga a ordem estritamente. Ao encontrar um `>>> PARADA PARA TESTES... <<<`, a equipe de desenvolvimento deve pausar novas implementações e focar na execução dos cenários de teste detalhados para garantir a estabilidade do subsistema recém-concluído.

## Módulos Base

*   `README.md`
*   `LICENSE`
*   `CONTRIBUTING.md`
*   `CHANGELOG.md`
*   `.gitignore`

---

## Ordem de Implementação e Paradas de Teste

1.  **Alvo 0: Setup do Projeto Profissional**
2.  `iabank.domain.models`
3.  `iabank.application.ports`
4.  `iabank.infrastructure.repositories` (incluindo a implementação `DjangoUnitOfWork`)
5.  `iabank.application.services` (foco inicial no `LoanApplicationService`)
6.  `iabank.api` (Endpoints e Serializers para o fluxo de criação de empréstimo)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (CORE BACKEND & CRIAÇÃO DE EMPRÉSTIMO) <<<`
*   **Módulos no Grupo:** `iabank.domain.models`, `iabank.application.ports`, `iabank.infrastructure.repositories`, `iabank.application.services`, `iabank.api`.
*   **Objetivo do Teste:** Validar que as camadas do backend (Domínio, Aplicação, Infraestrutura, Apresentação) estão corretamente integradas para processar a criação de um novo empréstimo, desde a requisição na API até a persistência no banco de dados, respeitando as regras de negócio.
*   **Cenários Chave:**
    1.  **Cenário de Sucesso:** Enviar uma requisição `POST` para o endpoint de criação de empréstimos com dados válidos. Verificar se a API retorna `201 Created` e se os registros correspondentes para `Loan`, `Customer` (se novo) e todas as `LoanInstallment` foram criados corretamente no banco de dados.
    2.  **Cenário de Validação de Dados:** Enviar uma requisição com dados sintaticamente inválidos (ex: valor não-numérico). Verificar se a API retorna `400 Bad Request` com uma mensagem de erro clara do serializer, sem persistir nenhuma informação no banco.
    3.  **Cenário de Regra de Negócio:** (Assumindo uma regra no `LoanApplicationService`, ex: valor do empréstimo excede limite). Enviar uma requisição com dados que violem essa regra. Verificar se o serviço lança uma exceção de negócio, a API retorna `400 Bad Request` com a mensagem apropriada, e a transação é revertida (rollback).

7.  `iabank.core` (Middleware de autenticação JWT e RBAC)
8.  `iabank.infrastructure` (Atualização dos Repositórios e do `get_tenant_from_request` para forçar o filtro por `tenant_id`)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (ISOLAMENTO DE DADOS MULTI-TENANCY) <<<`
*   **Módulos no Grupo:** `iabank.core` (Middleware), `iabank.infrastructure` (Repositórios atualizados).
*   **Objetivo do Teste:** Garantir que o mecanismo de multi-tenancy está funcionando corretamente em toda a camada de acesso a dados, prevenindo estritamente que um tenant acesse os dados de outro.
*   **Cenários Chave:**
    1.  **Cenário de Isolamento de Leitura:** Criar dados para `Tenant A` (ex: Empréstimo X) e `Tenant B` (ex: Empréstimo Y). Autenticar como um usuário do `Tenant A` e fazer uma requisição para listar todos os empréstimos. Verificar se a resposta contém apenas o Empréstimo X e nunca o Empréstimo Y.
    2.  **Cenário de Prevenção de Acesso Direto:** Autenticar como um usuário do `Tenant B`. Tentar acessar o Empréstimo X (pertencente ao `Tenant A`) diretamente pela sua UUID via API (ex: `GET /api/loans/{uuid_emprestimo_x}`). Verificar se a API retorna `404 Not Found`, não `403 Forbidden`, para não vazar a informação da existência do recurso.
    3.  **Cenário de Isolamento de Escrita:** Autenticar como um usuário do `Tenant A`. Tentar criar um novo recurso (ex: Cliente) associando-o explicitamente ao `tenant_id` do `Tenant B` no corpo da requisição. Verificar se a lógica de negócio (no serviço ou repositório) ignora/sobrescreve o `tenant_id` do payload com o `tenant_id` da sessão autenticada, garantindo que o novo cliente seja criado para o `Tenant A`.

9.  `frontend/src/features/loans/components/NewLoanWizard.tsx`
10. `frontend/src/features/loans/components/LoansPanel.tsx`

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (FLUXO END-TO-END: NOVO EMPRÉSTIMO) <<<`
*   **Módulos no Grupo:** `frontend/src/features/loans/components/NewLoanWizard.tsx`, `frontend/src/features/loans/components/LoansPanel.tsx` e toda a stack de backend previamente testada.
*   **Objetivo do Teste:** Validar o fluxo funcional completo, da interface do usuário à base de dados, para o caso de uso de criação de um novo empréstimo, garantindo que o contrato da API é corretamente implementado pelo backend e consumido pelo frontend.
*   **Cenários Chave:**
    1.  **Cenário E2E de Sucesso:** No navegador, utilizar o `NewLoanWizard` para preencher todos os dados de um novo empréstimo. Submeter o formulário. Verificar se a UI exibe uma mensagem de sucesso, o wizard é fechado/resetado, e o novo empréstimo aparece corretamente na `LoansPanel` com os dados formatados (status, valores, etc.) conforme o ViewModel.
    2.  **Cenário de Validação na UI:** No `NewLoanWizard`, tentar submeter o formulário com campos obrigatórios vazios ou com dados inválidos (ex: texto no campo de valor). Verificar se a UI exibe mensagens de erro junto aos campos correspondentes e impede o envio da requisição à API.
    3.  **Cenário de Tratamento de Erro da API:** Simular uma resposta de erro do servidor (ex: `500 Internal Server Error` ou `400 Bad Request`) na chamada de criação do empréstimo. Verificar se a UI do `NewLoanWizard` captura o erro, não trava, e exibe uma notificação amigável para o usuário (ex: "Falha ao criar empréstimo, por favor tente novamente.").

11. `iabank.application.services` (Implementação do `CollectionService`)
12. `iabank.infrastructure.tasks` (Implementação de tarefas assíncronas com `CeleryTaskQueue`)
13. `iabank.api` (Endpoints e Serializers para o `CollectionService`)