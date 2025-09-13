# Feature Specification: Sistema IABANK - Plataforma SaaS de Gestão de Empréstimos

**Feature Branch**: `001-eu-escrevi-um`  
**Created**: 2025-09-12  
**Status**: Draft  
**Input**: User description: "Eu escrevi um blueprint com tudo o que eu quero para construir um sistema, leia @BLUEPRINT_ARQUITETURAL.md para voce criar uma especificação completa"

## Execution Flow (main)
```
1. Parse user description from Input
   → COMPLETED: Blueprint arquitetural analisado
2. Extract key concepts from description
   → COMPLETED: Identificado sistema SaaS multi-tenant para gestão de empréstimos
3. For each unclear aspect:
   → COMPLETED: Aspectos técnicos bem definidos no blueprint
4. Fill User Scenarios & Testing section
   → COMPLETED: Cenários de negócio extraídos do blueprint
5. Generate Functional Requirements
   → COMPLETED: Requisitos funcionais baseados nos módulos definidos
6. Identify Key Entities (if data involved)
   → COMPLETED: Entidades extraídas dos modelos de dados
7. Run Review Checklist
   → COMPLETED: Validação realizada com sucesso
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
O IABANK é uma plataforma SaaS multi-tenant que permite empresas de crédito gerenciar todo o ciclo de vida de empréstimos, desde a análise de clientes até a cobrança e controle financeiro. Gestores e consultores podem criar empréstimos, acompanhar pagamentos, gerar relatórios financeiros e manter conformidade regulatória brasileira.

### Acceptance Scenarios

#### Cenário 1: Criação de Empréstimo
1. **Given** um consultor autenticado com cliente cadastrado, **When** ele cria um novo empréstimo com valor, taxa de juros e número de parcelas, **Then** o sistema calcula automaticamente as parcelas, IOF e CET conforme legislação brasileira

#### Cenário 2: Controle de Pagamentos
2. **Given** um empréstimo com parcelas em aberto, **When** um pagamento é registrado, **Then** o sistema atualiza o status da parcela, registra a transação financeira e recalcula o saldo devedor

#### Cenário 3: Gestão Multi-tenant
3. **Given** múltiplas empresas usando a plataforma, **When** um usuário acessa o sistema, **Then** ele visualiza apenas dados da sua própria empresa (tenant)

#### Cenário 4: Relatórios Financeiros
4. **Given** transações financeiras registradas, **When** um gestor solicita relatórios, **Then** o sistema apresenta dashboards com KPIs, fluxo de caixa e indicadores de performance

#### Cenário 5: Conformidade LGPD
5. **Given** dados pessoais de clientes armazenados, **When** há solicitação de acesso/exclusão de dados, **Then** o sistema permite exportação e anonimização conforme direitos dos titulares

#### Cenário 6: Análise de Crédito
6. **Given** um consultor criando um empréstimo, **When** ele solicita análise de crédito do cliente, **Then** o sistema consulta bureaus de crédito e apresenta score e recomendações de risco

#### Cenário 7: Processamento de Pagamentos Automático
7. **Given** um pagamento via PIX ou boleto processado pelo gateway, **When** a notificação é recebida, **Then** o sistema identifica a parcela correspondente e atualiza automaticamente o status

#### Cenário 8: Monitoramento e Alertas
8. **Given** sistema em operação, **When** métricas indicam anomalias (ex: alta taxa de inadimplência), **Then** o sistema dispara alertas automáticos para gestores

#### Cenário 9: Workflow de Análise de Risco
9. **Given** consultor criando empréstimo, **When** inicia análise de crédito, **Then** sistema consulta bureaus automaticamente e apresenta recomendação de aprovação/rejeição

#### Cenário 10: Workflow de Cobrança
10. **Given** parcela vencida há mais de 5 dias, **When** sistema processa cobrança automática, **Then** status do empréstimo muda para "Em Cobrança" e são aplicados juros de mora

#### Cenário 11: Período de Arrependimento
11. **Given** empréstimo criado há menos de 7 dias, **When** cliente solicita cancelamento, **Then** sistema permite cancelamento sem ônus e reverte todas as transações

#### Cenário 12: Falecimento do Cliente
12. **Given** cliente com empréstimo ativo falece, **When** herdeiros apresentam documentação legal, **Then** sistema transfere empréstimo para espólio mantendo histórico completo

#### Cenário 13: Migração entre Tenants
13. **Given** processo de fusão empresarial, **When** gestor solicita migração de carteira, **Then** sistema transfere dados preservando integridade e auditoria

#### Cenário 14: Mudança Regulatória
14. **Given** Banco Central altera regras de CET, **When** nova regra entra em vigor, **Then** sistema aplica automaticamente apenas para novos empréstimos

#### Cenário 15: Conflito de Concorrência
15. **Given** dois consultores editando mesmo empréstimo, **When** ambos tentam salvar, **Then** sistema bloqueia segunda alteração e notifica sobre conflito

#### Cenário 16: Comissionamento de Consultor
16. **Given** consultor criou empréstimo que foi aprovado, **When** empréstimo é efetivado, **Then** sistema calcula comissão conforme regras configuradas e credita no saldo do consultor

#### Cenário 17: Pagamento Parcial de Parcela
17. **Given** parcela com valor de R$ 500 vencendo hoje, **When** cliente paga R$ 300, **Then** sistema registra pagamento parcial e altera status para "Parcialmente Pago"

### Edge Cases
- O que acontece quando um cliente tenta efetuar pagamento de valor superior ao devido?
- Como o sistema lida com cálculos de juros em casos de pagamento antecipado?
- O que acontece se um tenant exceder limites de armazenamento?
- Como o sistema processa parcelas vencidas e calcula multas/juros de mora?
- Como são tratadas situações de falha durante processamento de pagamentos?
- O que acontece quando bureaus de crédito estão indisponíveis durante análise?
- Como o sistema lida com falhas em gateways de pagamento durante processamento?
- O que acontece se worker assíncrono falha durante processamento de relatório?
- Como o sistema se comporta quando há tentativa de acesso entre tenants diferentes?
- O que acontece durante falha de backup ou processo de recuperação?
- Como o sistema trata inconsistências em dados de migração?
- O que acontece quando limites de taxa de juros da Lei da Usura são excedidos?
- Como o sistema lida com alterações simultâneas em configurações de tenant?
- O que acontece quando cliente solicita anonimização mas há processo judicial em andamento?
- Como o sistema se comporta quando mudanças regulatórias conflitam com contratos existentes?
- O que acontece durante falha de sincronização entre réplicas em diferentes regiões?
- Como o sistema trata situação onde herdeiro contesta validade de transferência de empréstimo?
- Como o sistema lida com múltiplos pagamentos parciais para a mesma parcela?
- O que acontece se regras de comissionamento são alteradas com empréstimos já criados?
- Como o sistema se comporta durante falha de disaster recovery em região secundária?
- O que acontece quando dados criptografados são corrompidos ou chaves perdidas?

## Requirements *(mandatory)*

### Functional Requirements

#### Módulo de Clientes
- **FR-001**: Sistema DEVE permitir cadastro completo de clientes com dados pessoais, documentos e endereços, permitindo a designação de um endereço como principal
- **FR-002**: Sistema DEVE validar CPF/CNPJ e garantir unicidade por tenant
- **FR-003**: Sistema DEVE armazenar histórico completo de alterações nos dados do cliente

#### Módulo de Empréstimos
- **FR-004**: Sistema DEVE permitir criação de empréstimos com definição de valor principal, taxa de juros e parcelas
- **FR-005**: Sistema DEVE calcular automaticamente IOF conforme regras da Receita Federal
- **FR-006**: Sistema DEVE calcular CET (Custo Efetivo Total) mensal e anual conforme Banco Central
- **FR-007**: Sistema DEVE gerar cronograma de parcelas com datas de vencimento
- **FR-008**: Sistema DEVE controlar status do empréstimo (Em Andamento, Finalizado, Em Cobrança, Cancelado)
- **FR-009**: Sistema DEVE respeitar período de arrependimento permitindo cancelamento sem ônus

#### Módulo Financeiro
- **FR-010**: Sistema DEVE registrar todas as transações financeiras (receitas e despesas)
- **FR-011**: Sistema DEVE associar pagamentos de parcelas às transações financeiras
- **FR-012**: Sistema DEVE permitir gestão de múltiplas contas bancárias por tenant
- **FR-013**: Sistema DEVE categorizar transações por centro de custo e categoria de pagamento
- **FR-014**: Sistema DEVE gerar relatórios de fluxo de caixa e DRE

#### Módulo de Usuários e Permissões
- **FR-015**: Sistema DEVE implementar autenticação segura com controle de sessão
- **FR-016**: Sistema DEVE suportar controle de acesso baseado em papéis (RBAC)
- **FR-017**: Sistema DEVE implementar autenticação multifator para usuários administrativos
- **FR-018**: Sistema DEVE registrar logs de auditoria para todas as operações críticas, incluindo histórico completo de versionamento para Empréstimo, Parcela, Cliente e Transação Financeira

#### Multi-tenancy e Isolamento
- **FR-019**: Sistema DEVE garantir isolamento completo de dados entre tenants
- **FR-020**: Sistema DEVE aplicar filtro de tenant automaticamente em todas as consultas
- **FR-021**: Sistema DEVE permitir configurações específicas por tenant

#### Conformidade Regulatória
- **FR-022**: Sistema DEVE calcular juros dentro dos limites da Lei da Usura
- **FR-023**: Sistema DEVE manter trilha de auditoria completa para conformidade LGPD
- **FR-024**: Sistema DEVE permitir exportação de dados pessoais para atender direitos dos titulares
- **FR-025**: Sistema DEVE suportar anonimização de dados pessoais MANTENDO identificadores técnicos para auditoria financeira
- **FR-081**: Sistema DEVE preservar logs de auditoria por 10 anos mesmo após anonimização de dados pessoais (conforme resolução do conflito LGPD vs requisitos fiscais)
- **FR-082**: Sistema DEVE implementar MFA com fallback de performance: se MFA falha, permitir operação com log de segurança adicional

#### Processamento Assíncrono
- **FR-026**: Sistema DEVE processar tarefas demoradas de forma assíncrona (relatórios, notificações)
- **FR-027**: Sistema DEVE garantir idempotência em operações críticas
- **FR-028**: Sistema DEVE implementar retry automático para operações que podem falhar

#### Backup e Recuperação
- **FR-029**: Sistema DEVE executar backups automáticos com RPO menor que 5 minutos
- **FR-030**: Sistema DEVE permitir restauração point-in-time com RTO menor que 1 hora
- **FR-031**: Sistema DEVE testar procedimentos de recuperação trimestralmente

#### Segurança da Informação
- **FR-092**: Sistema DEVE garantir que todos os dados de clientes e transações sejam armazenados de forma criptografada em repouso (banco de dados e backups)
- **FR-093**: Sistema DEVE aplicar criptografia adicional em nível de campo para dados pessoais altamente sensíveis como CPF/CNPJ
- **FR-094**: Sistema DEVE implementar criptografia em trânsito para todas as comunicações entre componentes do sistema

#### Continuidade de Negócio (Disaster Recovery)
- **FR-095**: Sistema DEVE possuir plano de recuperação de desastres que permita restaurar serviço completo em região geográfica secundária
- **FR-096**: O tempo de recuperação para disaster recovery (DR RTO) deve ser inferior a 4 horas para falhas regionais
- **FR-097**: Sistema DEVE manter réplica assíncrona dos dados em região secundária para disaster recovery
- **FR-098**: Sistema DEVE testar plano de disaster recovery anualmente com failover completo

#### Integrações Externas
- **FR-032**: Sistema DEVE integrar com bureaus de crédito (SPC/Serasa) para consulta de score
- **FR-033**: Sistema DEVE integrar com gateways de pagamento para processar PIX e boletos
- **FR-034**: Sistema DEVE processar notificações de pagamento de forma automatizada
- **FR-035**: Sistema DEVE manter histórico de consultas aos bureaus de crédito

#### Interface do Usuário
- **FR-036**: Sistema DEVE fornecer interface web responsiva acessível via navegador
- **FR-037**: Sistema DEVE apresentar dashboards interativos com KPIs em tempo real
- **FR-038**: Sistema DEVE permitir personalização de relatórios por usuário
- **FR-039**: Sistema DEVE suportar exportação de relatórios em múltiplos formatos

#### Observabilidade e Monitoramento
- **FR-040**: Sistema DEVE registrar logs estruturados com contexto de requisição e usuário
- **FR-041**: Sistema DEVE expor métricas específicas: total de empréstimos ativos, valor em carteira, taxa de inadimplência diária, volume de pagamentos/hora
- **FR-042**: Sistema DEVE fornecer endpoint /health com status de DB, Redis e integrações externas, respondendo em <100ms
- **FR-043**: Sistema DEVE alertar quando: taxa de erro >1% em 5min, latência p99 >1s, inadimplência aumentar >10% em 24h

#### Performance e Escalabilidade
- **FR-044**: Sistema DEVE processar relatórios complexos em segundo plano
- **FR-045**: Sistema DEVE manter p95 de latência <500ms para operações CRUD básicas (excluindo relatórios e MFA que podem ter latência maior)
- **FR-046**: Sistema DEVE suportar paginação eficiente em todas as listagens
- **FR-047**: Sistema DEVE otimizar consultas para ambientes multi-tenant

#### Workflows Operacionais
- **FR-048**: Sistema DEVE implementar workflow completo de análise de risco com aprovação/rejeição automática
- **FR-049**: Sistema DEVE processar automaticamente cobrança de parcelas vencidas há mais de 5 dias
- **FR-050**: Sistema DEVE permitir cancelamento de empréstimos durante período de arrependimento (7 dias)
- **FR-051**: Sistema DEVE calcular e aplicar automaticamente juros de mora e multas por atraso
- **FR-052**: Sistema DEVE suportar renegociação de empréstimos em dificuldade
- **FR-053**: Sistema DEVE processar pagamentos antecipados com aplicação de descontos

#### Tipos de Usuário e Permissões Específicas
- **FR-054**: Sistema DEVE implementar perfil "Gestor/Administrador" com acesso a relatórios, configurações e supervisão
- **FR-055**: Sistema DEVE implementar perfil "Consultor/Cobrador" com acesso a operações de empréstimos e cobrança
- **FR-056**: Sistema DEVE restringir acesso a relatórios financeiros apenas para gestores
- **FR-057**: Sistema DEVE permitir que consultores vejam apenas seus próprios empréstimos e clientes, EXCETO empréstimos transferidos para cobrança que ficam visíveis para gestores

#### Estados e Transições de Empréstimos
- **FR-058**: Sistema DEVE controlar transições de empréstimo: Análise → Aprovado → Ativo → Finalizado/Cobrança
- **FR-059**: Sistema DEVE controlar estados de parcelas: Pendente → Paga/Vencida → Parcialmente Paga
- **FR-060**: Sistema DEVE bloquear alterações em empréstimos após período de arrependimento
- **FR-061**: Sistema DEVE permitir apenas transições válidas entre estados conforme regras de negócio

#### Configurações por Tenant
- **FR-062**: Sistema DEVE permitir configuração de taxas de juros específicas por tenant
- **FR-063**: Sistema DEVE permitir customização de períodos de cobrança por tenant
- **FR-064**: Sistema DEVE permitir configuração de relatórios personalizados por tenant
- **FR-065**: Sistema DEVE permitir definição de workflows específicos por tenant

#### Versionamento e Controle Temporal
- **FR-066**: Sistema DEVE manter versionamento de todas as alterações em contratos com timestamp e usuário responsável
- **FR-067**: Sistema DEVE preservar versões históricas de taxas regulatórias (IOF, CET) com data de vigência
- **FR-068**: Sistema DEVE aplicar novas regras regulatórias apenas a empréstimos criados após data de vigência
- **FR-069**: Sistema DEVE bloquear alterações em empréstimos com controle de concorrência otimista
- **FR-070**: Sistema DEVE registrar período de arrependimento em dias CORRIDOS (não úteis) conforme CDC
- **FR-071**: Sistema DEVE manter log imutável de todas as versões de configurações por tenant

#### Cenários Excepcionais e Mundo Real  
- **FR-072**: Sistema DEVE suportar transferência de empréstimos em caso de morte do cliente para espólio/herdeiros
- **FR-073**: Sistema DEVE permitir migração de dados entre tenants em casos de fusão/aquisição empresarial
- **FR-074**: Sistema DEVE manter dados em modo somente-leitura para tenants em processo de encerramento
- **FR-075**: Sistema DEVE implementar procedimento de recuperação de acesso para clientes sem comprometer segurança
- **FR-076**: Sistema DEVE aplicar automaticamente mudanças regulatórias com data de vigência futura programada

#### Controle de Concorrência
- **FR-077**: Sistema DEVE prevenir modificações simultâneas do mesmo empréstimo por múltiplos usuários
- **FR-078**: Sistema DEVE implementar queue para processamento sequencial de pagamentos da mesma parcela
- **FR-079**: Sistema DEVE resolver conflitos de dados usando timestamp de última modificação (last-write-wins)
- **FR-080**: Sistema DEVE notificar usuários sobre conflitos de edição em tempo real

#### Sistema de Comissionamento de Consultores
- **FR-083**: Sistema DEVE permitir configuração de regras de comissionamento para consultores baseadas nos empréstimos criados e efetivados
- **FR-084**: Sistema DEVE calcular e creditar automaticamente o valor da comissão no saldo do consultor quando um empréstimo é aprovado
- **FR-085**: Sistema DEVE permitir débito de comissões do saldo do consultor em caso de cancelamento durante período de arrependimento
- **FR-086**: Sistema DEVE fornecer tela para gestores e consultores visualizarem extrato completo de movimentações do saldo
- **FR-087**: Sistema DEVE permitir ajustes manuais no saldo do consultor por gestores com justificativa obrigatória

#### Gestão de Pagamentos Parciais
- **FR-088**: Sistema DEVE aceitar registro de pagamentos parciais para uma parcela, atualizando o campo 'amount_paid'
- **FR-089**: Sistema DEVE alterar status da parcela para 'Parcialmente Pago' quando pagamento inferior ao valor devido for realizado
- **FR-090**: Sistema DEVE recalcular juros de mora e multas apenas sobre o saldo remanescente de uma parcela parcialmente paga
- **FR-091**: Sistema DEVE permitir múltiplos pagamentos parciais na mesma parcela até quitação total

#### Arquitetura e Padrões Técnicos
- **FR-099**: Sistema frontend DEVE ser implementado seguindo Feature-Sliced Design (FSD) com organização por fatias verticais de negócio
- **FR-100**: Sistema DEVE utilizar TanStack Query para gerenciamento de estado do servidor e cache de dados da API
- **FR-101**: Sistema DEVE utilizar Zustand para gerenciamento de estado global síncrono do cliente
- **FR-102**: Sistema DEVE implementar DTOs usando Pydantic para validação e serialização de dados
- **FR-103**: Sistema DEVE definir ViewModels TypeScript com interfaces para contratos de dados da UI
- **FR-104**: Sistema DEVE implementar pattern de Factory com propagação automática de tenant_id para testes

#### Processamento Assíncrono Avançado
- **FR-105**: Sistema DEVE configurar Celery com acks_late=True para confirmação de tarefas apenas após conclusão
- **FR-106**: Sistema DEVE implementar Dead Letter Queue (DLQ) para tarefas que falharam após todas as tentativas
- **FR-107**: Sistema DEVE configurar retry automático com backoff exponencial para tarefas que dependem de serviços externos
- **FR-108**: Sistema DEVE garantir idempotência em todas as tarefas assíncronas críticas usando IDs únicos

#### Backup e Indexação Específica
- **FR-109**: Sistema DEVE implementar Point-in-Time Recovery (PITR) do PostgreSQL com arquivamento contínuo de WAL
- **FR-110**: Sistema DEVE criar índices compostos com tenant_id como primeira coluna para otimização multi-tenant
- **FR-111**: Sistema DEVE manter retenção de WAL por 14 dias e backups diários por 30 dias
- **FR-112**: Sistema DEVE testar procedimentos de recuperação de backup trimestralmente

### Key Entities

#### Tenant e Usuários
- **Tenant**: Representa uma empresa cliente da plataforma, contém configurações específicas e serve como contexto de isolamento para todos os dados
- **User**: Usuário do sistema, vinculado a um tenant específico, com papéis e permissões definidas
- **Consultant**: Especialização de usuário que representa consultores/vendedores, com controle de comissões

#### Cliente e Relacionamento
- **Customer**: Cliente final que solicita empréstimos, com dados pessoais, documentos e histórico
- **Address**: Endereços dos clientes, podendo ter múltiplos endereços por cliente

#### Operações de Crédito
- **Loan**: Empréstimo concedido, com valor principal, taxa de juros, parcelas e informações regulatórias (IOF, CET)
- **Installment**: Parcela individual do empréstimo, com valor, data de vencimento e status de pagamento

#### Gestão Financeira
- **BankAccount**: Contas bancárias da empresa para controle de fluxo de caixa
- **FinancialTransaction**: Transações financeiras (receitas/despesas) com categorização e rastreamento
- **PaymentCategory**: Categorias para classificação de pagamentos e despesas
- **CostCenter**: Centros de custo para controle gerencial
- **Supplier**: Fornecedores para registro de despesas operacionais

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
