# AGV Prompt Template: Tocrisna v7.4 - Definição da Arquitetura Técnica e de Produto

## Tarefa Principal

Definir e documentar uma proposta de arquitetura de alto nível, cobrindo tanto os **aspectos técnicos (software)** quanto os de **produto (experiência do usuário)**. O resultado deve ser um Blueprint que sirva como a fonte única da verdade para a estrutura, componentes, contratos de serviço e, crucialmente, os contratos de apresentação de dados da UI. O foco é na modularidade, clareza, manutenibilidade e na criação de um "produto de engenharia" completo e profissional.

## Contexto e Definições Iniciais do Projeto: (Fornecido pelo usuário)

- **Nome do Projeto:** `IABANK`

- **Visão Geral / Objetivo Principal:**
  Sistema de gestão de empréstimos moderno e eficiente
  Plataforma Web SaaS robusta e segura, desenvolvida em Python, projetada para a gestão completa de empréstimos (end-to-end). Foi concebida para ser escalável, intuitiva e adaptável às necessidades específicas de cada instituição — desde um pequeno gestor independente até financeiras, fintechs ou bancos — bem como de qualquer organização cujo modelo de negócio dependa do ciclo de emprestar, cobrar e reinvestir.

  No futuro, nosso sistema deverá ser capaz de integrar-se a um ecossistema de múltiplos agentes de IA, amplamente autônomos, capazes de automatizar todo o ciclo de vida de um empréstimo — da originação self-service pelo cliente final, passando pela análise de risco e liberação, até a cobrança e recuperação automatizadas — minimizando a intervenção humana, reduzindo a fricção e otimizando a eficiência operacional e a conformidade regulatória. E também será capaz de integrar-se a diversos sistemas, como bureaus de crédito, plataformas bancárias (Pix, Open Finance, etc.) e sistemas de comunicação, como WhatsApp, entre outros. Haverá, inclusive, a opção de gestão do sistema diretamente pelo WhatsApp ou similares, por meio de chatbot ou agente de IA.

- **Funcionalidades Chave (Alto Nível):**

  ## **Mapeamento Completo do Sistema**

  ### **Índice**

  1. **Metodologia e Estrutura do Menu**
     - 1.1. Princípios de Design
     - 1.2. Estrutura Otimizada do Menu
  2. **Telas Globais**
     - 2.1. Tela de Login
  3. **Dashboard (Tela Inicial)**
  4. **Operacional**
     - 4.1. Novo Empréstimo (Assistente)
     - 4.2. Empréstimos (Painel de Gestão)
     - 4.3. Clientes
     - 4.4. Consultores
     - 4.5. Cobrança (Gestão de Inadimplência)
     - 4.6. Transferência de Rotas (Assistente)
     - 4.7. Credor Promissória
  5. **Financeiro**
     - 5.1. Contas a Pagar
     - 5.2. Contas a Receber
     - 5.3. Caixa e Bancos (Extrato de Contas)
     - 5.4. Transferência entre Contas
     - 5.5. Fechamento por Período
     - 5.6. Histórico de Fechamentos
  6. **Relatórios e Análises**
     - 6.1. Análise Financeira Geral
     - 6.2. Análise de Empréstimos
     - 6.3. Análise de Lucro
     - 6.4. Análise de Consultores
     - 6.5. Análise de Novos Clientes
     - 6.6. Relatório Analítico de IOF
  7. **Cadastros Gerais**
     - 7.1. Fornecedores
     - 7.2. Categorias de Pagamento
     - 7.3. Centros de Custo
     - 7.4. Formas de Pagamento
     - 7.5. Tipo de Estabelecimento
  8. **Administração**
     - 8.1. Usuários e Permissões
     - 8.2. Contas Bancárias
     - 8.3. Parâmetros de IOF
     - 8.4. Feriados
     - 8.5. Logs de Atividade
     - 8.6. Histórico de Sincronismo (Apps)

  ***

  ### **1. Metodologia e Estrutura do Menu**

  #### **1.1. Princípios de Design**

  1. **Orientado ao Processo:** Os menus são agrupados por contexto de negócio, não por tipo técnico (Cadastro, Movimentação). Isso otimiza o fluxo de trabalho do usuário.
  2. **Eficiência e Clareza:** As telas são projetadas para minimizar cliques e apresentar informações de forma visual e intuitiva, usando componentes inteligentes e feedback em tempo real.
  3. **Inteligência Acionável:** Os dados não são apenas exibidos; eles são interativos, permitindo que o usuário explore e "mergulhe" nos números para obter insights (drill-down).

  #### **1.2. Estrutura Otimizada do Menu Lateral**

  - **Dashboard**
  - **Operacional**
    - Novo Empréstimo
    - Empréstimos
    - Clientes
    - Consultores
    - Cobrança
    - Transferência de Rotas
    - Credor Promissória
  - **Financeiro**
    - Contas a Pagar
    - Contas a Receber
    - Caixa e Bancos
    - Transferência entre Contas
    - Fechamento por Período
    - Histórico de Fechamentos
  - **Relatórios e Análises**
    - Análise Financeira Geral
    - Análise de Empréstimos
    - Análise de Lucro
    - Análise de Consultores
    - Análise de Novos Clientes
    - Relatório Analítico de IOF
  - **Cadastros Gerais**
    - Fornecedores
    - Categorias de Pagamento
    - Centros de Custo
    - Formas de Pagamento
    - Tipo de Estabelecimento
  - **Administração**
    - Usuários e Permissões
    - Contas Bancárias
    - Parâmetros de IOF
    - Feriados
    - Logs de Atividade
    - Histórico de Sincronismo (Apps)
  - **LogOut**

  ***

  ### **2. Telas Globais**

  #### **2.1. Tela de Login**

  1. **Cabeçalho:** Logo, Título "LOGIN DE ACESSO".
  2. **Campos:** "Nome ou email" e "Senha".
  3. **Ação:** Botão "ENTRAR".
  4. **Recuperação:** Link "Esqueceu sua senha?".
  5. **Segurança (Melhoria):** Opção para "Lembrar-me" e recomendação de implementação de Autenticação de Dois Fatores (2FA) nas configurações de usuário.

  ***

  ### **3. Dashboard (Tela Inicial)**

  Página de visualização de dados interativa.

  1. **Estrutura:** Composta por múltiplos widgets personalizáveis.
  2. **Componentes:**
     - **KPIs Principais:** Cartões de resumo (Empréstimos em andamento, Total recebido, Total gasto, Lucro líquido).
     - **Gráficos Temporais:** Gráficos de barras e de área para análise de despesas, recebimentos e lucro ao longo do tempo.
     - **Banners Rotativos:** Espaço para anúncios de funcionalidades (ex: IAConnect), se necessário.
  3. **Melhoria: Interatividade (Drill-Down)**
     - Ao clicar em um KPI (ex: no número de "Empréstimos em andamento"), o usuário é redirecionado para a tela `Operacional > Empréstimos`, já com o filtro de status correspondente aplicado.
     - Ao clicar em uma barra de um gráfico (ex: a barra de "Recebimentos" de Maio), uma tabela detalhada com os lançamentos de Maio é exibida em um popup ou abaixo do gráfico.

  ***

  ### **4. Operacional**

  O coração do sistema, focado na atividade principal de conceder e gerenciar empréstimos.

  \<details\>
  \<summary\>\<strong\>4.1. Novo Empréstimo (Assistente)\</strong\>\</summary\>

  Substitui o fluxo separado de cadastrar cliente e depois empréstimo. É um assistente (wizard) que guia o usuário.

  1. **Passo 1: Cliente**
     - Campo de busca "Pesquisar Cliente por Nome ou CPF".
     - Ao digitar, o sistema busca e exibe resultados. Se o cliente é selecionado, avança para o Passo 2.
     - Se o cliente não existe, um botão **"Cadastrar Novo Cliente"** abre um formulário simplificado (em popup) para os dados essenciais. Após salvar, avança para o Passo 2.
  2. **Passo 2: Detalhes do Empréstimo**
     - Formulário com campos para `Valor`, `Taxas`, `Nº de Parcelas`, `Consultor Responsável`, `Data da primeira parcela`, etc.
     - O sistema calcula e exibe o plano de parcelamento em tempo real.
  3. **Passo 3: Documentos e Contrato**
     - Seção para upload de documentos (se necessário).
     - Botão para **"Gerar Contrato/Promissória"** com base nos dados inseridos.
  4. **Passo 4: Resumo e Confirmação**
     - Exibe um resumo completo da operação.
     - Botão **"Confirmar e Ativar Empréstimo"**.

  \</details\>

  \<details\>
  \<summary\>\<strong\>4.2. Empréstimos (Painel de Gestão)\</strong\>\</summary\>

  1. **Listagem:** Tabela detalhada com os empréstimos.
  2. **Melhoria: Filtros Avançados:**
     - Busca rápida por nome/nº do empréstimo.
     - Botão "Filtros Avançados" que revela opções: `Intervalo de Datas`, `Status` (dropdown), `Consultor`, `Faixa de Valor`.
  3. **Melhoria: Tabela Inteligente:**
     - **Badges de Status:** Coluna "Status" exibe tags visuais coloridas (ex: \<span style="background-color: \#28a745; color: white; padding: 2px 6px; border-radius: 4px;"\>Finalizado\</span\>, \<span style="background-color: \#ffc107; color: black; padding: 2px 6px; border-radius: 4px;"\>Em Andamento\</span\>, \<span style="background-color: \#dc3545; color: white; padding: 2px 6px; border-radius: 4px;"\>Em Cobrança\</span\>).
     - **Visualização Customizável:** Ícone que permite ao usuário selecionar e reordenar as colunas da tabela.
  4. **Melhoria: Ações em Lote:**
     - Checkboxes em cada linha para selecionar múltiplos empréstimos.
     - Menu de Ações em Lote com opções como "Alterar Status dos Selecionados", "Exportar para Excel".
  5. **Ações por Linha:** "Exibir Detalhes", "Editar", "Antecipar Finalização", "Excluir" (com confirmação por senha).

  \</details\>

  \<details\>
  \<summary\>\<strong\>4.3. Clientes\</strong\>\</summary\>

  1. **Listagem:** Painel similar ao de Empréstimos, com filtros avançados e ações em lote (ex: "Atribuir clientes a uma rota").
  2. **Melhoria: Formulário Organizado em Abas (Novo/Editar):**
     - **Aba 1: Dados Pessoais:** Nome, CPF/CNPJ, Data de Nascimento, etc.
     - **Aba 2: Endereço e Contato:**
       - Campo "CEP" com **autopreenchimento** de rua, bairro, cidade e estado.
       - Campos de Telefone e E-mail com validação em tempo real.
     - **Aba 3: Informações Profissionais/Financeiras:** Renda, Profissão, etc.
     - **Aba 4: Documentos (GED):**
       - Área para upload e visualização de arquivos (RG, CPF, Comprovante de Renda, Contrato Assinado) vinculados ao cliente.
     - **Aba 5: Histórico:**
       - Lista somente leitura de todos os empréstimos, pagamentos e interações do cliente.
  3. **Visualizar (Exibir):** Apresenta os dados no mesmo formato de abas, mas em modo de leitura.

  \</details\>

  \<details\>
  \<summary\>\<strong\>4.4. Consultores\</strong\>\</summary\>

  1. **Listagem:** Tabela com dados principais, saldo e ações. Botão "Zerar Saldo de Todos".
  2. **Formulário (Novo/Editar):**
     - Organizado em abas: `Dados Pessoais` e `Configurações do Aplicativo`.
     - Aba `Configurações do Aplicativo` com checkboxes e dropdowns para permissões granulares.
  3. **Ações:** "Adição/Retirada de Saldo", "Exibir", "Editar", "Excluir".

  \</details\>

  \<details\>
  \<summary\>\<strong\>4.5. Cobrança (Gestão de Inadimplência)\</strong\>\</summary\>
  (Evolução do "Empréstimos Vencidos")

  1. **Painel de Cobrança:** Dashboard com KPIs focados em inadimplência (Total Vencido, Nº de Clientes Vencidos, Dias Médio de Atraso).
  2. **Listagem:** Tabela de empréstimos vencidos, com filtros avançados (ex: `Dias de Atraso`, `Região`). Ações por linha: "Ver Detalhes", "Negociar".
  3. **Melhoria: Tela de Detalhe da Cobrança:**
     - Ao clicar em "Negociar", abre uma tela específica para aquele empréstimo.
     - **Histórico de Contatos:** Área para registrar interações ("Ligação realizada em 12/08", "WhatsApp enviado em 13/08").
     - **Agendamento de Ações:** Função para agendar um próximo contato (ex: "Ligar novamente em 15/08"), que pode gerar lembretes.
     - **Ferramentas de Negociação:** Opções para "Lançar Pagamento Parcial", "Gerar Boleto Avulso", "Renegociar Dívida" (que abriria um fluxo para criar um novo plano de parcelamento).

  \</details\>

  \<details\>
  \<summary\>\<strong\>4.6. Transferência de Rotas (Assistente)\</strong\>\</summary\>

  Interface no formato de wizard para evitar erros.

  1. **Passo 1: Seleção de Origem:** Dropdown para selecionar o "Consultor de Origem".
  2. **Passo 2: Seleção de Empréstimos:** O sistema exibe a lista de empréstimos do consultor de origem. O usuário seleciona os que deseja transferir usando checkboxes.
  3. **Passo 3: Seleção de Destino:** Dropdown para selecionar o "Consultor de Destino".
  4. **Passo 4: Resumo e Confirmação:** Exibe um resumo da operação ("Você irá transferir X empréstimos..."). Botão "Confirmar Transferência".

  \</details\>

  \<details\>
  \<summary\>\<strong\>4.7. Credor Promissória\</strong\>\</summary\>
  (Mantido como um cadastro de apoio dentro do módulo operacional)

  1. **Listagem:** Tabela com "Nome", "CPF/CNPJ", "Endereço", e Ações ("Exibir", "Editar", "Excluir"). Botão "NOVO".
  2. **Formulário (Novo/Editar):** Campos correspondentes aos da tabela, com autopreenchimento por CEP.

  \</details\>

  ***

  ### **5. Financeiro**

  Módulo focado na gestão do fluxo de dinheiro da empresa.

  _(As telas de Contas a Pagar e Receber seguem o padrão de listagem inteligente, com filtros, badges e ações em lote, já descritos anteriormente.)_

  \<details\>
  \<summary\>\<strong\>5.1. Contas a Pagar\</strong\>\</summary\>
  \<summary\>\<strong\>5.2. Contas a Receber\</strong\>\</summary\>
  \<summary\>\<strong\>5.3. Caixa e Bancos (Extrato de Contas)\</strong\>\</summary\>
  \<summary\>\<strong\>5.4. Transferência entre Contas\</strong\>\</summary\>
  \<summary\>\<strong\>5.5. Fechamento por Período\</strong\>\</summary\>
  \<summary\>\<strong\>5.6. Histórico de Fechamentos\</strong\>\</summary\>
  As seções do Financeiro, Relatórios, Cadastros Gerais e Administração seguirão a mesma estrutura detalhada, aplicando as melhorias de forma consistente. O detalhamento completo para cada um pode ser gerado. Devido à limitação de tamanho, abaixo segue o esqueleto com as principais mudanças anotadas.

  ***

  ### **6. Relatórios e Análises**

  Módulo centralizado para toda a inteligência de negócio (BI). Todas as telas aqui devem ser altamente interativas (drill-down) e com filtros avançados.

  ***

  ### **7. Cadastros Gerais**

  Cadastros de apoio que alimentam outros módulos. São telas de CRUD (Criar, Ler, Atualizar, Deletar) simples e diretas.

  ***

  ### **8. Administração**

  Configurações críticas e ferramentas de auditoria, acessadas principalmente por administradores.

  \<details\>
  \<summary\>\<strong\>8.1. Usuários e Permissões\</strong\>\</summary\>

  1. **Listagem:** Tabela de usuários com Nome, Email, Perfil de Acesso.
  2. **Formulário (Novo/Editar):**
     - **Aba 1: Dados do Usuário:** Nome, email, etc.
     - **Aba 2: Permissões de Acesso:** Matriz de checkboxes detalhada, organizada por módulo (Operacional, Financeiro, etc.), permitindo controle granular sobre o que cada usuário pode ver e fazer.

  \</details\>
  _(O restante das seções (Contas Bancárias, Parâmetros de IOF, etc.) seria detalhado de forma similar, mantendo a consistência.)_

- **Público Alvo / Ambiente de Uso:**

  - Usuários Primários (Gestores/Administradores): Utilizarão um Painel Web (Desktop) para gestão estratégica, controle total e supervisão das operações.
  - Usuários Secundários (Cobradores/Consultores): Utilizarão um Painel Web (Desktop) para a gestão execução de cobranças em campo.
  - Contexto: B2B SaaS para pequenas e médias financeiras, gestores de carteiras de crédito e operações de empréstimo que podem ou não ter uma força de cobrança em campo.

- **Stack Tecnológica Definida:**

  - **Backend (Servidor e API):**

    - **Linguagem Principal:** `Python 3.10+`
    - **Framework Principal:** `Django` (com Django REST Framework para a API).
      - **Justificativa:** Django é ideal. Seu ORM robusto, admin embutido (ótimo para debug inicial) e o ecossistema maduro aceleram a construção do core relacional e das regras de negócio que mapeamos. É a fundação perfeita sobre a qual os agentes de IA serão construídos depois.
    - **Bibliotecas Essenciais:**
      - `djangorestframework`: Para construir a API RESTful que servirá o frontend.
      - `django-filter`: Para facilitar a implementação dos filtros complexos que vimos nas listagens.
      - `Pydantic`: Pode ser usado dentro do Django para validações de dados complexas, garantindo consistência com futuras integrações de IA.
      - `Celery` com `Redis`: Mesmo que nessa fase não haja muitas tarefas assíncronas, já é importante incluir para tarefas como o envio de e-mails de notificação (ex: geração de contrato). Estabelece a base futura para os agentes.
    - **Banco de Dados:** `PostgreSQL`.
      - **Justificativa:** É a escolha natural para aplicações Django robustas. Desde o início, já teremos a base de dados que suportará `pgvector` nas fases futuras, sem necessidade de migração.

  - **Frontend (Painel Web - SPA):**

    - **Framework Principal:** `React 18+`.
    - **Linguagem:** `TypeScript`.
    - **Ferramenta de Build:** `Vite`.
    - **Gerenciamento de Estado (API):** `TanStack Query (React Query)`.
      - **Justificativa:** Essencial para gerenciar a grande quantidade de dados de tabelas e dashboards que vêm do backend.
    - **Estilização:** `Tailwind CSS`.
    - **Formulários e Validação:** `React Hook Form` + `Zod`.
      - **Justificativa:** A melhor combinação para os múltiplos e complexos formulários de cadastro do sistema.
    - **Roteamento:** `React Router`.
    - **Gráficos e Dashboards:** `Recharts`.

  - **Infraestrutura e DevOps:**
    - **Containerização:** `Docker` e `Docker Compose`.
      - **Justificativa:** Essencial para criar um ambiente de desenvolvimento padronizado, que espelhe a produção e facilite o onboarding de futuros desenvolvedores. Você terá um contêiner para o backend Django, um para o frontend React (em modo de desenvolvimento), um para o PostgreSQL e um para o Redis.
    - **Servidor Web em Produção:** `Nginx`.
      - **Justificativa:** Servirá como reverse proxy, direcionando requisições `/api/*` para o Django e o restante para os arquivos estáticos do React.

- **Requisitos Não Funcionais Iniciais (se houver):**

  - **Multi-tenancy e Escalabilidade:** A arquitetura **deve ser multi-tenant desde o início**, mesmo que o primeiro "tenant" seja apenas a sua própria operação. Os dados de cada tenant devem ser estritamente isolados na camada de acesso a dados (ex: filtragem obrigatória por `tenant_id` em todas as queries). Isso é crucial para a viabilidade futura como SaaS.
  - **Performance:** A UI deve ser fluida. APIs de consulta de dados devem responder em < 500ms para consultas padrão, com otimização de queries e uso de índices no banco de dados.
  - **Segurança (Nível FinTech Essencial):**
    - **Autenticação:** Sistema seguro baseado em tokens (JWT) com expiração e refresh.
    - **Autorização:** Controle de acesso granular baseado em papéis (RBAC) imposto no backend, replicando as permissões do módulo "Usuários".
    - **Proteção de Dados:** Hashing forte para senhas; criptografia para dados sensíveis em trânsito (HTTPS) e em repouso.
  - **Confiabilidade e Consistência:** Transações financeiras (criação/pagamento de empréstimos) devem ser atômicas (ACID) para garantir a integridade dos dados.
  - **Auditoria:** Implementação de uma trilha de auditoria completa para todas as ações críticas (Criação, Edição, Exclusão), conforme mapeado no módulo "Log de Atividades".
  - **Compliance (Fundação LGPD):** A plataforma deve ser construída com os princípios da LGPD em mente (ex: todos os dados pertencem a um "titular"). Embora a gestão completa de consentimento seja para fases futuras, a base de dados já deve suportar essa estrutura.

- **Principais Restrições (se houver):** `[Ex: Orçamento limitado, Prazo curto, Deve integrar com API X existente, etc.]`

- **Definição de Escopo (Opcional - Recomendado para projetos complexos):**
  - **Dentro do Escopo:** A implementação completa da plataforma SaaS web, conforme descrito no "Mapeamento Completo do Sistema". Isso inclui todos os módulos, do Dashboard à Administração, para os usuários via navegador web.
  - **Fora do Escopo:** A implementação de funcionalidades que dependem de integrações futuras. Especificamente, **NÃO** devem ser implementados nesta fase:
    - Agentes de IA autônomos para análise de risco ou cobrança.
    - Integrações diretas com bureaus de crédito, Open Finance ou Pix.
    - Gestão do sistema via chatbot (WhatsApp ou similares).
      A arquitetura deve, no entanto, ser projetada de forma a **não impedir** a adição dessas funcionalidades no futuro.

## Diretrizes e Princípios Arquiteturais (Filosofia AGV)

1. **Completude e Consistência (Diretriz Mestra):** Ao gerar os artefatos (Modelos, DTOs, ViewModels), sua tarefa não é apenas dar exemplos, mas ser **exaustivo**. Para **CADA** módulo de negócio principal definido no "Mapeamento Completo do Sistema" (Operacional, Financeiro, Cadastros Gerais, etc.), você **DEVE** aplicar os padrões de detalhamento solicitados. Se um padrão é definido para "Empréstimos", ele deve ser consistentemente aplicado para "Clientes", "Contas a Pagar", e assim por diante, para todas as entidades relevantes mapeadas.
2. **Modularidade e Separação de Responsabilidades (SRP):** Proponha uma divisão clara em módulos/componentes lógicos, cada um com uma responsabilidade bem definida. Minimize o acoplamento entre eles e maximize a coesão interna.
3. **Clareza e Manutenibilidade:** A arquitetura deve ser fácil de entender, manter e evoluir. Prefira soluções mais simples (KISS) quando apropriado.
4. **Definição Explícita de Interfaces e Construção de Componentes:** **CRUCIAL:**
   - **Interfaces de Serviço (Contratos Funcionais):** Para os principais pontos de interação entre os módulos identificados, defina claramente as interfaces (contratos) que eles expõem ou consomem.
     - **Abstração da Infraestrutura:** Isto inclui, obrigatoriamente, abstrair interações com a infraestrutura. Prefira definir componentes wrapper (ex: `FileSystemService`, `ConcurrencyService`, `BackupService`) na camada de infraestrutura com interfaces claras, em vez de usar bibliotecas de baixo nível (como `pathlib`, `shutil`, `concurrent.futures`) diretamente nas camadas superiores (Core, Application) onde possível.
     - A definição da interface de serviço deve incluir:
       - Assinaturas de funções/métodos públicos chave (com tipos de parâmetros e retorno).
       - Estruturas de dados (Dataclasses, Pydantic Models) usadas para troca de informações através desses métodos.
       - Uma breve descrição do propósito de cada método exposto.
   - **Configuração e Construção de Componentes:** Para cada componente/serviço principal proposto (especialmente aqueles que não são puramente modelos de dados):
     - Se o componente depender de valores de configuração externos essenciais para seu funcionamento (ex: caminhos de arquivo padrão, URLs de API, chaves secretas, níveis de log, etc.), **indique explicitamente como esses valores de configuração seriam fornecidos ao componente em sua inicialização.**
     - **Priorize a passagem de parâmetros de configuração através do construtor (`__init__`) do componente.** Detalhe os parâmetros de configuração chave que o construtor deve aceitar.
     - Se, alternativamente, a configuração for obtida de um serviço de configuração centralizado ou por um método de configuração dedicado, mencione essa abordagem e a interface relevante.
     - O objetivo é garantir que o blueprint deixe claro como os componentes são instanciados com suas configurações necessárias, promovendo desacoplamento e testabilidade.
5. **Listagem Explícita de Dependências Diretas:** **IMPORTANTE:** Para cada componente/módulo principal descrito, liste explicitamente os **outros arquivos `.py` ou módulos específicos** dos quais ele depende diretamente para importar e usar funcionalidades. Use caminhos relativos à raiz do projeto (ex: `fotix.domain.models`, `utils.helpers`).
6. **Testabilidade:** A arquitetura deve facilitar a escrita de testes unitários e de integração (ex: permitir injeção de dependência, usar funções puras, etc.).
7. **Segurança Fundamental:** Incorpore princípios básicos de segurança desde o design (ex: onde a validação de input deve ocorrer, como dados sensíveis podem ser tratados – sugerir hashing/criptografia, necessidade de autenticação/autorização, etc.).
8. **Aderência à Stack:** Utilize primariamente as tecnologias definidas na Stack Tecnológica. Se sugerir uma tecnologia _adicional_, justifique claramente a necessidade.
9. **Padrões de Design:** Sugira e aplique padrões de design relevantes (ex: Repository, Service Layer, Observer, Strategy, etc.) onde eles agregarem valor à estrutura e manutenibilidade. Justifique brevemente a escolha.
10. **Escalabilidade (Básica):** Considere como a arquitetura pode suportar um crescimento moderado no futuro (ex: design sem estado para serviços, possibilidade de paralelizar tarefas, uso de caching, etc.).
11. **Especificação de Tecnologias para Tipos de Componentes:** Para garantir consistência e aderência à stack definida, ao descrever os componentes/módulos, você DEVE especificar a tecnologia ou biblioteca principal a ser utilizada para certos tipos de artefatos, quando aplicável e relevante para a arquitetura. Por exemplo:
    - **Modelos de Dados (DTOs, entidades de domínio, configurações):** Especificar o uso de **Pydantic `BaseModel`** como a tecnologia padrão para sua definição, visando validação de dados e facilidades de serialização.
    - **Camada de Acesso a Dados (se houver BD):** Especificar o ORM (ex: SQLAlchemy, etc.) ou a biblioteca de acesso.
    - **APIs Web (se houver):** Especificar o framework (ex: FastAPI, Flask, etc.).
    - **Interface de Usuário (se houver):** Especificar o framework de UI (ex: PySide6, etc.).
    - Adicionar outros tipos de componentes/tecnologias conforme a necessidade do projeto.
      Estas especificações devem constar na descrição de cada componente relevante no Blueprint Arquitetural.

## Resultado Esperado (Blueprint Arquitetural)

Um documento (preferencialmente em Markdown) descrevendo a arquitetura proposta, incluindo:

1. **Visão Geral da Arquitetura:** Um breve resumo da abordagem arquitetural escolhida (ex: Arquitetura em Camadas, Microsserviços simples, Baseada em Eventos, etc.) e uma justificativa. Esta seção também deve definir a estratégia de organização do código-fonte, esclarecendo se será utilizado um monorepo (com backend e frontend no mesmo repositório) ou múltiplos repositórios, e justificar a escolha.
2. **Diagramas da Arquitetura (Modelo C4):** Gere os diagramas utilizando a sintaxe do Mermaid.js, seguindo os 3 níveis principais do Modelo C4 para uma visualização clara e em camadas.

   - **2.1. Nível 1: Diagrama de Contexto do Sistema (C1)**

     - **Objetivo:** Mostrar como o sistema se encaixa no mundo, interagindo com usuários e sistemas externos. É a visão mais macro, mostrando o sistema como uma "caixa preta" e suas interações externas.
     - **Elementos a incluir:** Sistema principal (como um único bloco), tipos de usuários, sistemas externos que interagem.
     - **Exemplo de estrutura Mermaid:**

       ```mermaid
       graph TD
           subgraph "Sistema [NOME_DO_PROJETO]"
               A[Sistema Principal]
           end
           U1[Tipo Usuário 1] -->|interage via| A
           U2[Tipo Usuário 2] -->|interage via| A
           A -->|conecta com| SE1[Sistema Externo 1]
       ```

   - **2.2. Nível 2: Diagrama de Containers (C2)**

     - **Objetivo:** Dar um "zoom" no Sistema, mostrando as principais "caixas" tecnológicas (containers) que o compõem e como elas se comunicam. Um container é uma unidade executável/implantável (ex: aplicação web, banco de dados, API, etc.).
     - **Elementos a incluir:** Frontend, Backend API, Banco de Dados, Cache, Filas, etc.
     - **Exemplo de estrutura Mermaid:**

       ```mermaid
       graph TD
           U[Usuários] -->|HTTPS| F[Frontend SPA]
           F -->|API REST| B[Backend API]
           B -->|SQL| DB[(Banco de Dados)]
           B -->|Pub/Sub| Q[Fila de Mensagens]
       ```

   - **2.3. Nível 3: Diagrama de Componentes (C3) - Exemplo para o Container Principal**

     - **Objetivo:** Dar um "zoom" em um container específico (geralmente o Backend API) para mostrar seus principais componentes/módulos internos e suas responsabilidades.
     - **Elementos a incluir:** Camadas internas (Apresentação, Aplicação, Domínio, Infraestrutura) ou componentes principais do container escolhido.
     - **Nota:** Este nível é opcional mas recomendado para o container mais complexo do sistema.
     - **Exemplo de estrutura Mermaid:**

       ```mermaid
       graph TD
           subgraph "Container: Backend API"
               C1[Camada de Apresentação/API]
               C2[Camada de Aplicação/Serviços]
               C3[Camada de Domínio/Negócio]
               C4[Camada de Infraestrutura/Dados]
           end
           C1 --> C2
           C2 --> C3
           C2 --> C4
       ```

3. **Descrição dos Componentes, Interfaces e Modelos de Domínio:**

   - Para cada componente principal:

     - Nome claro (ex: `iabank.loans.services`).
     - Responsabilidade principal.
     - **Tecnologias Chave da Stack que Serão Usadas Nele:** Conforme a Diretriz 10 ("Especificação de Tecnologias para Tipos de Componentes"), indique a biblioteca ou framework principal para este componente (ex: "Modelos Django" para módulos de modelos de dados; "React/TypeScript" para componentes de UI; "DRF" para um serviço de API). Se for apenas lógica Python pura sem uma biblioteca externa dominante, indique "Python (Lógica Pura)".
     - **Dependências Diretas (Lista explícita - Diretriz 4).**

   - **3.1. Consistência dos Modelos de Dados (SSOT do Domínio):**

     - Defina todos os seus modelos de dados principais (entidades de domínio do Django) em uma única seção dedicada (ex: "Camada de Domínio/Core - Models"). **Esta seção é a Fonte Única da Verdade (SSOT) para todas as estruturas de dados do projeto.**
     - Você **DEVE** analisar o mapeamento detalhado das funcionalidades e telas fornecido. Para cada entidade principal (Cliente, Empréstimo, Consultor, Conta a Pagar, etc.), você **DEVE** derivar e detalhar **TODOS os campos de dados necessários** para suportar as funcionalidades descritas.
       - Especifique os tipos de campo do Django (`CharField`, `DecimalField`, `ForeignKey`, etc.).
       - Inclua opções importantes (`null=True`, `blank=True`, `default=...`).
       - Para campos de status com opções fixas (ex: status do empréstimo), defina explicitamente as `choices` usando uma classe `TextChoices` do Django.
     - Sua análise deve ser recursiva. Se um modelo principal (ex: `FinancialTransaction`) precisa de um relacionamento com um modelo de apoio (ex: `PaymentCategory` ou `Supplier` dos "Cadastros Gerais"), você **NÃO PODE** deixar esse relacionamento como um comentário ou placeholder. Você **DEVE** criar a definição completa do modelo de apoio (`PaymentCategory`, `Supplier`, etc.) na mesma seção, garantindo que todas as dependências de modelo sejam resolvidas e definidas explicitamente dentro do Blueprint. **Nenhuma chave estrangeira (ForeignKey) deve apontar para um modelo não definido.**

   - **3.1.1. Detalhamento dos DTOs e Casos de Uso:**

     - Para cada entidade principal, defina a estrutura dos DTOs (Data Transfer Objects) que serão usados pela API, utilizando `pydantic.BaseModel`. Crie DTOs específicos para os principais casos de uso, quando necessário. Por exemplo:
       - `CustomerCreateDTO`: Campos necessários para criar um novo cliente.
       - `CustomerUpdateDTO`: Campos que podem ser atualizados em um cliente existente.
       - `LoanListDTO`: Estrutura de dados retornada na listagem de empréstimos (pode ser similar ao ViewModel).
     - Isso estabelece o contrato de dados explícito para a comunicação entre as camadas de serviço e a API.

   - **Para a Camada de Apresentação (UI):**

     - Além da descrição geral da UI, **proponha uma decomposição em principais Telas/Views ou Componentes de UI reutilizáveis significativos.**
     - Para cada Tela/View/Componente de UI proposto:

       - Descreva brevemente seu propósito principal.
       - Liste os principais serviços da Camada de Aplicação com os quais ele provavelmente interagirá.
       - **Contrato de Dados da View (ViewModel):**

         - Para **CADA TELA DE LISTAGEM PRINCIPAL** descrita no mapeamento (Empréstimos, Clientes, Consultores, Contas a Pagar, etc.), você **DEVE** criar um `ViewModel` correspondente.
         - **Estrutura de Dados da View:** Defina a estrutura em TypeScript para cada ViewModel. Esta estrutura deve ser otimizada para exibição, contendo apenas os dados necessários para a tabela ou componente, já pré-formatados quando possível (ex: `principalAmountFormatted: "R$ 5.000,00"`).
         - **Mapeamento de Origem:** Para cada ViewModel, explique brevemente como ele é derivado dos modelos de domínio do backend e montado pelo Serializer da API.

4. **Descrição Detalhada da Arquitetura Frontend:** Descreva a arquitetura e a organização de diretórios propostas para a aplicação cliente (SPA). O objetivo é garantir modularidade, escalabilidade e uma clara separação de responsabilidades, independentemente do framework de UI escolhido. A descrição deve incluir:

   - **Padrão Arquitetural:** Adote e explique um padrão de design ou filosofia para a organização do código. Justifique como o padrão escolhido ajuda a separar as responsabilidades. Exemplos de conceitos a serem abordados:

     - **Separação por Funcionalidade (Feature-based):** Organizar o código em torno de funcionalidades de negócio em vez de tipos de arquivo (ex: uma pasta `novo-emprestimo/` contendo seus componentes, estado e lógica de API, em vez de pastas separadas `components/`, `hooks/`, `api/`).
     - **Componentes de UI vs. Componentes de Lógica (Presentational vs. Container):** Como a arquitetura distingue componentes "burros" que apenas exibem dados de componentes "inteligentes" que gerenciam estado e lógica.

   - **Estrutura de Diretórios Proposta:** Proponha uma estrutura de diretórios `src` que reflita o padrão arquitetural. Detalhe o propósito de cada camada ou pasta principal de forma conceitual, por exemplo:

     - **Camada de Aplicação (`app/` ou `core/`):** Configuração global (roteamento, injeção de dependência, provedores de estado, estilos globais).
     - **Camada de Roteamento/Páginas (`pages/`, `views/` ou `routes/`):** Os pontos de entrada para as diferentes telas do sistema.
     - **Camada de Funcionalidades (`features/`):** Módulos que encapsulam uma funcionalidade de negócio completa, orquestrando a lógica e a UI.
     - **Camada de Entidades (`entities/`):** Lógica de negócio e componentes relacionados a entidades de domínio do cliente (ex: um card de `Cliente`, um modelo de `Empréstimo`).
     - **Camada Compartilhada (`shared/` ou `lib/`):** Código totalmente reutilizável e agnóstico de negócio:
       - `ui/`: A biblioteca de componentes de UI puros (Botão, Input, Tabela, etc.).
       - `api/`: Configuração do cliente HTTP e definições de contrato com o backend.
       - `lib/`: Funções utilitárias, helpers, hooks genéricos, etc.

   - **Estratégia de Gerenciamento de Estado:** Especifique claramente a abordagem para os diferentes tipos de estado:

     - **Estado do Servidor (Server State):** Como os dados vindos da API serão buscados, cacheados e sincronizados. Mencione o uso de bibliotecas especializadas (como TanStack Query, SWR, Apollo Client) como a fonte da verdade para esses dados.
     - **Estado Global do Cliente (Global Client State):** Se e como o estado síncrono compartilhado entre diferentes partes da UI será gerenciado (ex: informações do usuário logado, tema da UI). Sugira ferramentas apropriadas para o ecossistema do framework (ex: Zustand, Jotai para React; Pinia para Vue; Stores para Svelte, etc.).
     - **Estado Local do Componente (Local Component State):** Confirme que o estado efêmero e não compartilhado deve ser mantido localmente nos componentes usando os mecanismos nativos do framework.

   - **Fluxo de Dados:** Descreva brevemente o fluxo de dados típico na aplicação, desde a interação do usuário, passando pela camada de funcionalidades, a chamada à API, a atualização do estado do servidor, até a renderização final nos componentes de UI.

5. **Definição das Interfaces Principais:** Detalhamento dos contratos de comunicação entre os componentes chave (conforme Diretriz 3), incluindo como os componentes recebem suas configurações iniciais (priorizando `__init__`).
6. **Gerenciamento de Dados (se aplicável):** Como os dados serão persistidos e acessados (ex: Módulo data_access usando SQLAlchemy com padrão Repository, ou especificando Pydantic `BaseModel` para modelos de dados se não houver persistência complexa). Além da persistência, a seção deve descrever a estratégia para: Gerenciamento de Schema (confirmando o uso de migrações automáticas como as do Django) e Seed de Dados (como popular o banco de dados de desenvolvimento com dados iniciais/fictícios, ex: usando scripts customizados, fixtures ou bibliotecas como factory-boy).
7. **Estrutura de Diretórios Proposta:** Uma sugestão inicial, preferencialmente utilizando o layout `src` moderno, mostrando a organização das
   pastas e arquivos principais. **Esta seção é crítica para a consistência do projeto. Ao listar os exemplos de arquivos de teste, você DEVE  
   aplicar a seguinte convenção de nomenclatura padrão do mercado:**
   - **Formato Padrão:** `test_<nome_do_modulo_ou_funcionalidade>.py`.
   - **Exemplo de Aplicação:** Os testes para `iabank/loans/models.py` devem ser mostrados na estrutura como `iabank/loans/tests/test_models.py`.
     O isolamento por diretório (`app/tests/`) já previne conflitos de nomenclatura, tornando desnecessário incluir o nome do app no arquivo. Esta  
     convenção padrão deve ser aplicada a todos os exemplos de arquivos de teste na estrutura de diretórios que você gerar.
     A estrutura deve refletir as melhores práticas para a stack tecnológica definida. Para projetos Python, isso significa priorizar o uso de pyproject.toml para gerenciamento de dependências e configuração de ferramentas (ex: Poetry, Ruff, Black, etc.), em vez de múltiplos arquivos de configuração legados.
8. **Arquivo `.gitignore` Proposto:** Um conteúdo sugerido, **completo e pronto para uso**, para o arquivo `.gitignore` na raiz do projeto, apropriado para a "Stack Tecnológica Definida". Ele deve ser abrangente, cobrindo caches, ambientes virtuais, arquivos de IDEs comuns (VS Code, PyCharm), e arquivos específicos do SO.
9. **Arquivo `README.md` Proposto:** A geração do **conteúdo completo** para um arquivo `README.md` inicial e profissional. O README deve seguir uma estrutura padrão, contendo, no mínimo:
   - O nome do projeto e uma descrição concisa.
   - Badges de status (pode usar placeholders).
   - Seção "Sobre o Projeto".
   - Seção "Stack Tecnológica".
   - Seção "Como Começar" (com instruções para instalar dependências e rodar o projeto).
   - Seção "Como Executar os Testes".
   - Seção "Estrutura do Projeto" (uma breve explicação das pastas principais).
10. **Arquivo `LICENSE` Proposto:** Uma sugestão de licença de software (ex: MIT, Apache 2.0, etc.) e a geração do **texto completo** correspondente para o arquivo `LICENSE` na raiz do projeto. Se nenhuma for especificada, sugira a MIT como um padrão seguro.
11. **Arquivo `CONTRIBUTING.md` Proposto:** A geração de um **template de conteúdo** para o `CONTRIBUTING.md`, descrevendo como contribuir para um projeto que segue o Método AGV (ex: seguir o blueprint, garantir testes, etc.). O documento deve também mencionar as políticas de qualidade de código, como o uso de linters (ex: Ruff, ESLint, etc.) e formatadores (ex: Black, Prettier, etc.), e sugerir a automação dessas checagens através de ganchos de pre-commit (mencionando o arquivo .pre-commit-config.yaml). Adicionalmente, o documento deve estabelecer um padrão mínimo para a documentação de código (ex: estilo de docstrings para funções públicas e classes, etc.) para garantir a manutenibilidade do projeto a longo prazo.
12. **Estrutura do `CHANGELOG.md`:** A geração de um arquivo `CHANGELOG.md` inicial, contendo apenas a estrutura padrão (ex: `## [Unreleased]`, `## [0.1.0] - YYYY-MM-DD`) para ser preenchido futuramente.
13. **Estratégia de Configuração e Ambientes:** Descreva como as configurações da aplicação (segredos, conexões de banco de dados, etc.) serão gerenciadas em diferentes ambientes (desenvolvimento, homologação, produção). Sugira o uso de variáveis de ambiente e arquivos de configuração específicos por ambiente (ex: usando python-decouple, django-environ, etc.).
14. **Estratégia de Observabilidade Completa:** Detalhe uma abordagem abrangente para observabilidade do sistema em produção. A descrição deve incluir:

    - **Logging Estruturado:** Defina a abordagem para logging de eventos e erros. Sugira o uso de logs estruturados (JSON) para facilitar a análise por ferramentas externas (ex: Sentry, Datadog, ELK Stack, etc.). Defina diferentes níveis de log para produção e desenvolvimento.

    - **Métricas de Negócio:** Defina métricas específicas do domínio que devem ser coletadas e como elas serão expostas e visualizadas. Especifique métricas que permitam monitorar a saúde do negócio, não apenas da infraestrutura.

    - **Distributed Tracing:** Para arquiteturas com múltiplos serviços, defina a estratégia de rastreamento distribuído para debugar problemas de performance e identificar gargalos entre componentes.

    - **Health Checks e SLIs/SLOs:** Defina indicadores de saúde do sistema (Service Level Indicators) e objetivos de nível de serviço (Service Level Objectives) mensuráveis. Especifique endpoints de health check e critérios de disponibilidade.

    - **Alerting Inteligente:** Defina estratégia de alertas baseada em anomalias e tendências, não apenas limites fixos, para reduzir ruído e focar em problemas reais que impactem usuários ou negócio.

15. **Estratégia de Testes Detalhada:** Elabore sobre a seção "Como Executar os Testes". Detalhe os diferentes tipos de testes a serem implementados (Unitários, Integração, End-to-End/API), em quais camadas da arquitetura cada um se aplica e as ferramentas recomendadas (pytest, APIClient do DRF, etc.). **Esta seção deve também incluir:**

    - **Estrutura e Convenção de Nomenclatura de Testes:** Defina a estrutura de diretórios para os testes. **Os testes unitários**, que validam a lógica interna de um único módulo, **devem residir dentro de cada app Django (`<app_name>/tests/`)**, mantendo-os próximos ao código-fonte que testam. **Os testes de integração**, que validam a colaboração entre múltiplos módulos ou apps, **devem residir em um diretório de alto nível dedicado (`tests/integration/`)** para evitar ambiguidades de dependência. Para garantir clareza e seguir as melhores práticas do mercado, estabeleça a convenção de nomenclatura padrão para os arquivos de teste: **`test_<nome_do_modulo_ou_funcionalidade>.py`** (ex: `test_models.py`, `test_views.py`, `test_serializers.py` dentro de cada app, e `test_loan_workflow.py`, `test_payment_integration.py` para testes de integração). O pytest e Python identificam testes pelo caminho completo, eliminando conflitos mesmo quando arquivos têm o mesmo nome em apps diferentes. Esta convenção padrão **DEVE** ser aplicada a todos os arquivos de teste.
    - **Padrões de Teste de Integração:** Defina as convenções para escrever testes de integração robustos e de fácil manutenção:
      - **Uso de Factories:** Recomende o uso de uma biblioteca de "factories" (ex: `factory-boy` para Python, `Faker.js` para Node, etc.) para a criação de dados de teste complexos e consistentes, evitando a configuração manual de objetos em cada teste.
      - **Simulação de Autenticação:** Para testes que requerem um usuário autenticado, especifique o uso de métodos de simulação fornecidos pelo framework (ex: `force_authenticate` no DRF, `TestSecurityContextHolder` no Spring Security, etc.) em vez de simular o fluxo de login completo em cada teste. Isso isola o teste da lógica de autenticação.
      - **Escopo de Teste:** Enfatize que os testes de integração de uma funcionalidade (ex: CRUD de Empréstimos) devem focar em validar **essa** funcionalidade, tratando dependências já testadas (como autenticação e multi-tenancy) como "caixas-pretas" que podem ser simuladas ou pré-configuradas.
    - **Padrões Obrigatórios para Test Data Factories:** Defina regras rigorosas para garantir consistência de dados em factories, especialmente crítico para sistemas multi-tenant:

      - **Princípio da Herança Explícita de Contexto:**

        - **Regra:** Factories que criam objetos aninhados (sub-factories) **DEVEM** garantir que o contexto principal (como tenant) seja explicitamente propagado para todos os objetos filhos
        - **Implementação:** Use `factory.SelfAttribute('..tenant')` para propagar contexto da factory pai para as filhas
        - **Exemplo Mandatório para Multi-tenancy:**

          ```python
          class LoanFactory(factory.django.DjangoModelFactory):
              tenant = factory.SubFactory(TenantFactory)
              # CRÍTICO: Propagar tenant para sub-factories
              customer = factory.SubFactory(CustomerFactory, tenant=factory.SelfAttribute('..tenant'))
              consultant = factory.SubFactory(ConsultantFactory, tenant=factory.SelfAttribute('..tenant'))
          ```

      - **Princípio da Derivação Lógica de Contexto:**

        - **Regra:** Se o contexto de um modelo é derivado de um relacionamento (ex: tenant de Consultant vem do User), a factory **DEVE** implementar essa lógica usando `factory.LazyAttribute`
        - **Exemplo:**

          ```python
          class ConsultantFactory(factory.django.DjangoModelFactory):
              user = factory.SubFactory(UserFactory)
              # Derivar tenant do user relacionado
              tenant = factory.LazyAttribute(lambda o: o.user.tenant)
          ```

      - **Testes Obrigatórios para Factories (Meta-testes):**

        - **Regra:** Para cada `factories.py` complexo, **DEVE** haver um `test_factories.py` correspondente que valide a consistência dos dados gerados
        - **Objetivo:** Detectar problemas de inconsistência nas factories antes que afetem os testes de negócio
        - **Exemplo de teste crítico:**

          ```python
          def test_loan_factory_tenant_consistency(self):
              """Verifica se LoanFactory propaga tenant para todos os sub-objetos."""
              tenant = TenantFactory()
              loan = LoanFactory(tenant=tenant)

              assert loan.tenant == tenant
              assert loan.customer.tenant == tenant
              assert loan.consultant.tenant == tenant
              assert loan.consultant.user.tenant == tenant
          ```

        - **Benefício:** Falhas nestes testes apontam imediatamente para problemas nas factories, evitando horas de depuração em testes de integração

16. **Estratégia de CI/CD (Integração e Implantação Contínuas):** Descreva uma estratégia de CI/CD de alto nível para automatizar a construção, teste e implantação da aplicação. A descrição deve incluir:

    - **Ferramenta Sugerida:** Recomende uma ferramenta de CI/CD (ex: GitHub Actions, GitLab CI, Jenkins, etc) e a criação de um arquivo de configuração de pipeline na raiz do projeto (ex: `.github/workflows/main.yml, etc.`).

    - **Gatilhos do Pipeline:** Defina quando o pipeline deve ser executado (ex: em cada push para o branch `main` e em cada abertura de Pull Request).

    - **Estágios do Pipeline:** Defina uma estratégia de CI/CD que cubra os aspectos essenciais do ciclo de vida do software:
      - **Integração Contínua:** Como o código será validado automaticamente (build, qualidade, testes)
      - **Entrega Contínua:** Como os artefatos serão empacotados e versionados
      - **Implantação:** Estratégia conceitual para deploy em diferentes ambientes
      - **Rollback:** Mecanismo de reversão em caso de problemas

17. **Estratégia de Versionamento da API:** Proponha uma estratégia para versionar a API (ex: via URL, como /api/v1/...) para permitir futuras evoluções sem quebrar os clientes existentes (como o frontend ou apps móveis).
18. **Padrão de Resposta da API e Tratamento de Erros:** Defina um formato de resposta JSON padrão e consistente para todos os endpoints da API, tanto para sucesso quanto para erros. Descreva como as exceções (ex: validação, não encontrado, erro de servidor) serão capturadas e mapeadas para respostas de erro padronizadas.
19. **Estratégia de Segurança Abrangente:** Detalhe uma abordagem estruturada para segurança que vai além dos princípios básicos. A descrição deve incluir:

    - **Threat Modeling Básico:** Identifique e documente as principais ameaças ao sistema baseadas no modelo de negócio e arquitetura proposta. Para cada ameaça identificada, sugira controles de mitigação específicos que devem ser implementados na arquitetura.

    - **Estratégia de Secrets Management:** Defina como dados sensíveis (chaves de API, senhas de banco, certificados) serão armazenados, rotacionados e acessados em diferentes ambientes. Especifique se será usado um serviço dedicado (ex: HashiCorp Vault, AWS Secrets Manager, etc.) ou variáveis de ambiente criptografadas.

    - **Compliance Framework (se aplicável):** Se o projeto está sujeito a regulamentações específicas (LGPD, PCI DSS, SOX, HIPAA), detalhe os controles arquiteturais necessários para conformidade, incluindo:

      - Estratégia de auditoria e logs de compliance
      - Controles de acesso baseados em papéis (RBAC) granulares
      - Criptografia de dados em repouso e em trânsito
      - Políticas de retenção e purga de dados

    - **Security by Design:** Descreva como os princípios de segurança serão incorporados desde o design inicial, incluindo validação de entrada, sanitização de dados, princípio do menor privilégio e defesa em profundidade.

20. **Justificativas e Trade-offs:** Breve explicação das principais decisões arquiteturais e por que alternativas foram descartadas (se relevante).
21. **Exemplo de Bootstrapping/Inicialização (se aplicável e útil para clareza):** Um pequeno trecho de código exemplo (conceitual, como um `main.py` simplificado) demonstrando como os principais serviços seriam instanciados e configurados, especialmente focando em como as configurações são injetadas (via `__init__` ou métodos `configure()`).
22. **Estratégia de Evolução do Blueprint:** Para projetos de longo prazo, defina como o próprio blueprint arquitetural será versionado e evoluído. A descrição deve incluir:

    - **Versionamento Semântico do Blueprint:** Estabeleça uma convenção para versionar o blueprint (ex: v1.0.0 para a arquitetura inicial, v1.1.0 para adições de componentes, v2.0.0 para mudanças breaking na arquitetura).

    - **Processo de Evolução Arquitetural:** Defina o processo para propor, avaliar e implementar mudanças arquiteturais significativas, incluindo:

      - Critérios para determinar quando uma mudança requer nova versão do blueprint
      - Processo de validação de impacto em componentes existentes
      - Estratégia de migração para mudanças breaking

    - **Documentação de Decisões Arquiteturais (ADRs):** Estabeleça o formato e processo para documentar decisões arquiteturais importantes, suas justificativas e trade-offs, criando um histórico de evolução do sistema.

    - **Compatibilidade e Deprecação:** Defina políticas para manter compatibilidade entre versões e processo de deprecação de componentes ou interfaces obsoletas.

23. **Métricas de Qualidade e Quality Gates:** Defina métricas objetivas de qualidade e os gates de qualidade que devem ser aplicados para garantir consistência e excelência técnica. A descrição deve incluir:

    - **Métricas de Cobertura de Código:** Estabeleça metas específicas de cobertura (ex: mínimo 80% para lógica de negócio, 95% para componentes críticos de segurança). Defina quais tipos de código podem ser excluídos da cobertura (ex: código gerado, interfaces de terceiros).

    - **Métricas de Complexidade:** Defina limites para complexidade ciclomática (ex: máximo 10 por função), profundidade de aninhamento (ex: máximo 4 níveis) e tamanho de funções/classes. Especifique as ferramentas que serão usadas para medir essas métricas.

    - **Quality Gates Automatizados:** Defina os critérios objetivos que devem ser atendidos para que código seja aceito em produção:

      - Cobertura de testes acima do limite definido
      - Zero vulnerabilidades de segurança de alta severidade
      - Complexidade dentro dos limites estabelecidos
      - Todos os testes passando
      - Conformidade com padrões de código (linting)

    - **Métricas de Performance:** Para componentes críticos, defina benchmarks de performance que devem ser mantidos (ex: tempo de resposta de APIs, throughput de processamento, uso de memória, etc.).

24. **Análise de Riscos e Plano de Mitigação (Opcional - Recomendado para projetos críticos):** Para projetos de alta criticidade, compliance regulatório ou sistemas financeiros, forneça uma análise estruturada dos principais riscos técnicos e de negócio que podem impactar o projeto. Use uma matriz de riscos para priorização.

    **Formato sugerido:**

    | Categoria   | Risco Identificado                      | Probabilidade (1-5) | Impacto (1-5) | Score (P×I) | Estratégia de Mitigação    |
    | ----------- | --------------------------------------- | :-----------------: | :-----------: | :---------: | -------------------------- |
    | Técnico     | [Descrever risco técnico principal]     |        [1-5]        |     [1-5]     |    [P×I]    | [Plano de ação preventivo] |
    | Negócio     | [Descrever risco de negócio]            |        [1-5]        |     [1-5]     |    [P×I]    | [Plano de ação preventivo] |
    | Segurança   | [Descrever risco de segurança]          |        [1-5]        |     [1-5]     |    [P×I]    | [Plano de ação preventivo] |
    | Performance | [Descrever risco de performance/escala] |        [1-5]        |     [1-5]     |    [P×I]    | [Plano de ação preventivo] |

    **Legendas:**

    - **Probabilidade:** 1=Muito Baixa, 2=Baixa, 3=Média, 4=Alta, 5=Muito Alta
    - **Impacto:** 1=Insignificante, 2=Menor, 3=Moderado, 4=Maior, 5=Catastrófico
    - **Score:** Multiplicação para priorização (scores ≥12 são críticos)

    **Nota:** Foque nos 3-5 riscos mais relevantes. Esta análise deve ser revisada e atualizada periodicamente durante o projeto.

25. **Conteúdo dos Arquivos de Ambiente e CI/CD:** A geração do **conteúdo completo** para arquivos que definem o ambiente de desenvolvimento e o pipeline.

    - **`pyproject.toml` Proposto:** Um conteúdo inicial para o `pyproject.toml`, definindo as dependências principais da stack (django, djangorestframework, etc.) e a configuração inicial para ferramentas como `ruff`, `black`, etc.
    - **`.pre-commit-config.yaml` Proposto:** A configuração inicial para os ganchos de pre-commit, alinhada com as ferramentas de qualidade definidas.
    - **`Dockerfile`s Propostos:** O conteúdo completo para o `Dockerfile` do backend e do frontend, preferencialmente usando `multi-stage builds`, por exemplo.
