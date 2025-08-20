# Output: Ordem de Implementação e Cenários de Teste

## Instruções para o Coordenador

Este documento define a ordem de implementação sequencial e os pontos de verificação para os Testes de Integração. A sequência foi derivada do `@Blueprint_Arquitetural.md` e deve ser seguida para garantir uma construção lógica e incremental do sistema.

## Ordem de Implementação

1. **Alvo 0: Setup do Projeto Profissional**
2. `backend.src.iabank.settings` (Configuração base do Django e `django-environ`)
3. `backend.src.iabank.domain.models` (Foco inicial em `Tenant` e `User`)
4. `backend.src.iabank.api` (Autenticação, tratamento de erro padronizado e versionamento `v1`)
5. `backend.src.iabank.infrastructure` (Middleware e managers para isolamento de Tenant)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (SUBSISTEMA DE FUNDAÇÃO E CORE) <<<`

- **Módulos no Grupo:** `Alvo 0`, `iabank.settings`, `iabank.domain.models (Tenant, User)`, `iabank.api (Auth, Errors)`, `iabank.infrastructure (Tenancy)`
- **Objetivo do Teste:** Validar que a estrutura base da aplicação está operacional, segura e pronta para a lógica de negócio, garantindo que a autenticação, o tratamento de erros e o isolamento de dados por tenant funcionem corretamente como uma fundação.
- **Cenários Chave:**
  1. **Autenticação e Obtenção de Token:** Um usuário com credenciais válidas faz uma requisição a um endpoint de login e recebe um token de acesso JWT. Uma tentativa com credenciais inválidas retorna um erro `401 Unauthorized` padronizado.
  2. **Acesso Protegido e Não Autorizado:** Uma requisição a um endpoint protegido sem um token válido falha com um erro `401/403` padronizado. Uma requisição com um token válido é bem-sucedida.
  3. **Criação com Isolamento de Tenant:** Um usuário autenticado do `Tenant A` cria um recurso (ex: um `User` ou `Client` inicial). Verificar diretamente no banco de dados que o novo registro foi criado com o `tenant_id` correto (`A`).
  4. **Leitura com Isolamento de Tenant:** Um usuário autenticado do `Tenant B` tenta acessar o recurso criado pelo usuário do `Tenant A` e recebe uma resposta `404 Not Found`, confirmando que não consegue "ver" dados de outros tenants.

6. `backend.src.iabank.domain.models` (Modelos restantes: `Client`, `Loan`, `Installment`)
7. `backend.src.iabank.domain.ports` (Definição das interfaces de repositório, ex: `ILoanRepository`)
8. `backend.src.iabank.infrastructure.repositories` (Implementações concretas dos repositórios com Django ORM)
9. `backend.src.iabank.application.dtos` (Data Transfer Objects com Pydantic para os casos de uso)
10. `backend.src.iabank.application.services` (Implementação dos casos de uso, ex: `LoanApplicationService`)
11. `backend.src.iabank.api.serializers` (Serializers do DRF para `Client`, `Loan`, `Installment`)
12. `backend.src.iabank.api.views` (Endpoints `ViewSet` para as operações CRUD de Empréstimos)
13. `backend.src.iabank.api.urls` (Mapeamento das novas rotas da API v1)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (FLUXO CRUD DE EMPRÉSTIMOS) <<<`

- **Módulos no Grupo:** `iabank.domain`, `iabank.infrastructure.repositories`, `iabank.application`, `iabank.api.serializers`, `iabank.api.views`, `iabank.api.urls`
- **Objetivo do Teste:** Validar o fluxo de dados completo (end-to-end), desde a requisição HTTP na API até a persistência no banco de dados, para a funcionalidade principal de gestão de empréstimos, garantindo que todas as camadas (Apresentação, Aplicação, Domínio, Infra) interajam corretamente.
- **Cenários Chave:**
  1. **Criação de Empréstimo End-to-End:** Enviar uma requisição `POST` para `/api/v1/loans/` com dados válidos. Verificar se (a) o `Loan` e suas `Installments` são criados corretamente no banco de dados, associados ao `Client` e ao `Tenant` corretos, (b) a resposta é `201 Created` e contém os dados serializados do empréstimo.
  2. **Listagem de Empréstimos com Isolamento:** Dois usuários de tenants diferentes (`A` e `B`) fazem uma requisição `GET` para `/api/v1/loans/`. Validar que cada um recebe na resposta **apenas** a lista de empréstimos pertencentes ao seu respectivo tenant.
  3. **Validação de Regra de Negócio na API:** Tentar criar um empréstimo com dados que violam uma regra de negócio (ex: `principal_amount` como zero ou negativo). Verificar se a API retorna um erro `422 Unprocessable Entity` (ou `400 Bad Request`) com uma mensagem clara sobre o erro de validação.
  4. **Consulta de Detalhe:** Fazer uma requisição `GET` para `/api/v1/loans/{loan_id}/` para um empréstimo existente. Verificar se a resposta `200 OK` contém todos os detalhes esperados do empréstimo, incluindo informações do cliente associado.

14. `frontend.shared.ui` (Biblioteca de componentes de UI puros: `Button`, `Input`, `Table`)
15. `frontend.shared.api` (Configuração do cliente de API e `TanStack Query`)
16. `frontend.entities.loan.model` (Definição de tipos e hooks, como `LoanViewRow`)
17. `frontend.entities.loan.ui` (Componentes de UI específicos, como `LoanRow` e `LoanStatusBadge`)
18. `frontend.features.LoanFiltering` (Componentes e lógica para a filtragem da tabela de empréstimos)
19. `frontend.pages.LoanListPage` (Composição da página que exibe o painel de gestão, integrando features e entities)

`>>> PARADA PARA TESTES DE INTEGRAÇÃO (PAINEL DE GESTÃO DE EMPRÉSTIMOS UI) <<<`

- **Módulos no Grupo:** `frontend.shared`, `frontend.entities.loan`, `frontend.features.LoanFiltering`, `frontend.pages.LoanListPage`
- **Objetivo do Teste:** Garantir que a interface do usuário consiga se comunicar com a API do backend, buscar dados, renderizá-los corretamente conforme o view model e responder a interações do usuário, como a filtragem, atualizando a visualização de forma consistente.
- **Cenários Chave:**
  1. **Carregamento e Renderização de Dados:** Ao acessar a página do painel de gestão, verificar se uma requisição `GET` é disparada para `/api/v1/loans/`. Após o recebimento dos dados, validar que a tabela na tela é preenchida e que os dados estão formatados corretamente (ex: `principalAmountFormatted` como "R$ X.XXX,XX", `statusLabel` como "Em Andamento").
  2. **Filtragem de Dados e Nova Requisição:** O usuário digita um termo no campo de busca/filtro. Verificar se, após um debounce, uma nova requisição `GET` é enviada à API com os parâmetros de query apropriados (ex: `?client_name=...`). A tabela deve se atualizar para exibir apenas os resultados retornados.
  3. **Tratamento de Estado de Carregamento e Erro:** Simular uma resposta lenta da API e verificar se um indicador de carregamento (spinner) é exibido na UI. Em seguida, simular uma falha na API (erro 500) e verificar se uma mensagem de erro amigável é exibida no lugar da tabela.
