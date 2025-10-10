# Feature Specification: Indice de Features do IABANK

**Feature Branch**: `001-indice-features-template`  
**Created**: 2025-10-08  
**Status**: Draft  
**Input**: User description: "prompt.md (ver repositorio)"

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituicao v5.2.0 (Art. I-XVIII) e ADRs aplicaveis. Toda lacuna deve ser marcada com `[NEEDS CLARIFICATION]` e adicionada ao `/clarify`.

## Contexto

Os anexos descrevem uma plataforma SaaS multi-tenant para gestao de emprestimos com monolito Django, SPA React e governanca rigorosa de compliance. A operacao exige fatias verticais que combinem experiencia do usuario, regras regulatorias (CET, IOF, LGPD) e guard rails de SRE (SLOs, observabilidade, pipelines seguros).

Esta especificacao consolida o indice de features, avaliacoes de prontidao e o plano execucional inicial solicitado em `prompt.md`, respeitando o fluxo Spec-Kit. Cada secao referencia explicitamente `BLUEPRINT_ARQUITETURAL.md` e `adicoes_blueprint.md` para garantir aderencia tecnica e de negocio.

### 1. Indice de Features (Tabela)

| ID | Nome da Feature | Persona | Valor de Negocio | Risco (reg/tec) | Dependencias | MVP/Pós-MVP | Observacoes |
|----|-----------------|---------|------------------|-----------------|--------------|-------------|-------------|
| F-01 | Governanca de Tenants e RBAC Zero-Trust | Gestor/Administrador do tenant | Onboarding seguro e isolamento de dados habilitando monetizacao multi-tenant | Reg alto (LGPD, RLS) | Modelos core (`Tenant`, `User`), PostgreSQL RLS, política MFA (Blueprint §19) | MVP | Garante baseline de permissoes, MFA TOTP dedicado mandatório e auditoria para todas as demais fatias |
| F-02 | Cadastro e KYC de Clientes e Consultores | Consultor de credito / Backoffice | Qualidade de dados e conformidade KYC para pipeline de emprestimos | Reg alto (LGPD, KYC) | F-01, `customers` e `operations` DTOs, contratos Pact `/api/v1` | MVP | Exige coleta segura de PII, controle de concorrencia otimista e sincronizacao com auditoria |
| F-03 | Originacao de Emprestimo com Score e CET/IOF | Consultor de credito | Contratos conformes (CET, IOF) e aprovacao assistida por score externo | Reg alto (Banco Central) | F-01, F-02, F-10, `LoanCreateDTO`, integrações externas (bureau, Pact) | MVP | Integracao inicial com Serasa Experian define contratos e cronograma do MVP. |
| F-04 | Gestao de Parcelas e Recebimentos Automatizados | Gestor financeiro | Liquidez previsivel via agendas, cobranca PIX/Boleto e conciliacao | Reg alto (pagamentos) | F-03, modelos `Installment`/`FinancialTransaction`, Celery resiliente (acks_late), rate limiting | MVP | Priorizado o gateway SaaS Asaas para PIX/Boleto no MVP. |
| F-05 | Gestao de Contas a Pagar e Despesas Operacionais | Gestor financeiro / Backoffice | Controle de caixa de saida, compliance fiscal e previsibilidade de despesas | Reg medio (fiscal/FinOps) | F-01, F-04, modelos `finance`, índices multi-tenant (Blueprint §6.3) | MVP | Politica de aprovacao em duas etapas (solicitante -> gestor centro de custo -> financeiro) e integracao banco-fornecedor alinhadas ao MVP |
| F-06 | Cobranca, Renegociacao e Pipeline de Inadimplencia | Consultor/Cobrador | Reduz churn e inadimplencia com trilhas multi-canal e renegociacao | Reg medio (LGPD contato) | F-04, F-05, runbooks de cobranca, Celery (acks_late), pactos API | MVP | Canal primario: WhatsApp Business API; requer auditoria de interacoes, limites LGPD e politicas de contato transparente |
| F-07 | Painel Executivo de Performance e Telemetria SLO | Gestor executivo | Visibilidade de KPIs (CET, inadimplencia, DORA, SLO) para decisoes rapidas | Tec alto (observabilidade, dados) | F-02 a F-06, catálogo SLO, Data Mart, OTEL padronizado | v1.1 | Metas SLO iniciais: p95 600 ms, p99 1 s, MTTR 1 h, erro <1%; dashboards calibram alertas e budgets com esses targets. |
| F-08 | Conformidade LGPD e Trilhas de Auditoria Imutaveis | Auditor/Compliance Officer | Evidencias LGPD (RIPD/ROPA), WORM e direito ao esquecimento auditavel | Reg critico (LGPD, auditoria) | F-01, F-02, F-04, F-05, `django-simple-history`, Object Lock, Vault/KMS | MVP | Retencao WORM: 30 dias legais + 5 anos adicionais; inclui automatizacao de artefatos LGPD, rotacao de segredos e rastreabilidade cruzada |
| F-09 | Observabilidade, Resiliencia e Gestao de Incidentes | SRE/Platform | Garantia de estabilidade (SLO, error budget, Chaos/GameDay) | Tec alto (SRE) | F-01 a F-08, pipelines CI/CD, OTEL, Argo CD (GitOps), Renovate | v2.0 | Sustenta operacao contendo DORA, testes de carga, feature flags e playbooks; GameDays bimestrais definidos |
| F-10 | Fundacao Frontend FSD e UI Compartilhada | Tech Lead Frontend / Squad UI | Base consistente FSD (features/entities/shared) habilitando entrega vertical rápida e segura | Tec alto (frontend) | Blueprint §4, design system baseline, Pact FE/BE, Storybook/Chromatic | MVP | Design system base: Tailwind CSS + componentes proprietarios; garante scaffolding inicial da SPA, contratos de UI e telemetria client-side |
| F-11 | Automacao de Seeds, Dados de Teste e Factories | QA / Engenharia de Plataforma | Dados confiaveis para TDD/integração e ambientes realistas com isolamento multi-tenant | Tec medio (TestOps) | Art. III/IV, factory-boy, comandos `seed_data`, pipelines CI, Argo CD | MVP | Mantém suites TDD verdes, executa load seeds em ambientes e reforça DR rehearsals |

## Clarifications

### Session 2025-10-10
- Q: Para o MVP da originacao (F-03), qual bureau de credito devemos priorizar para integracao? → A: Serasa Experian (Option B)
- Q: Para as cobrancas automatizadas do F-04, qual gateway PIX/Boleto devemos priorizar? → A: Gateway SaaS especializado (Asaas) (Option B)
- Q: Para os dashboards executivos (F-07/F-09), qual conjunto de metas SLO iniciais devemos adotar? → A: Option B — p95 600 ms / p99 1 s / MTTR 1 h / erro <1%
- Q: Para F-01, qual estratégia de MFA devemos adotar para o perfil TenantOwner? → A: TOTP dedicado (Option A)
- Q: Para F-02 (KYC), qual provedor de validação documental devemos priorizar para o MVP? → A: Abordagem híbrida (Option C)
- Q: Para F-05, qual política de aprovação de despesas adotamos no MVP? → A: Fluxo em duas etapas (solicitante -> gestor centro de custo -> financeiro) (Option B)
- Q: Para F-06, qual canal devemos priorizar para cobrança ativa no MVP? → A: WhatsApp Business API (Option A)
- Q: Para F-08, qual retenção WORM mínima além dos 30 dias legais devemos adotar? → A: 5 anos adicionais (Option B)
- Q: Para F-09, qual periodicidade de GameDays devemos adotar no MVP? → A: Bimestral (Option B)
- Q: Para F-10, qual design system base devemos adotar no MVP? → A: Tailwind CSS + componentes proprietários (Option C)
- Q: Para as seeds sintéticas multi-tenant (F-11), qual volumetria alvo devemos garantir já no seed inicial? → A: Option C (configurável por ambiente)

## User Scenarios & Testing *(mandatorio)*

### 2. Auditoria de Qualidade do Indice

### User Story 1 - Governanca de Tenants e RBAC Zero-Trust (F-01)

- Alinhamento Spec-Kit: OK - fatia vertical cobre cadastro de tenant, provisionamento RBAC e auditoria como valor direto para gestores (ver `BLUEPRINT_ARQUITETURAL.md` §3.1 e §6.2).
- INVEST: I Pass (valor claro de onboarding); N Pass (escopo restrito a governanca); V Pass (evidenciavel por tenant ativado); E Pass (interfaces definidas `Tenant`, `User`); S Pass (restricoes LGPD explicitas); T Pass (criterios de auditoria e RLS verificaveis).
- DoR: Persona Pass (gestor identificado); Objetivo Pass (ativar tenant conforme Art. XIII); Valor Pass (libera monetizacao); Restricoes Pass (RLS, RBAC, auditoria WORM); Dependencias Pass (infra padrao do blueprint); Metrica Pass (tempo de ativacao e auditorias logadas).
- Story Map: Etapa inicial da jornada "Onboard tenant" evitando lacunas; habilita todas as demais features.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 2 - Cadastro e KYC de Clientes e Consultores (F-02)

- Alinhamento Spec-Kit: OK - entrega formulario completo, validacao KYC e sincroniza entidades `Customer`, `Consultant` com LGPD.
- INVEST: I Pass; N Pass (dados apenas de onboarding); V Pass (dados limpos habilitam pipeline); E Pass (regras padronizadas); S Pass (respeita limites LGPD); T Pass (ACs de validacao documental).
- DoR: Persona Pass; Objetivo Pass (capturar dados confiaveis); Valor Pass (habilita credito responsavel); Restricoes Pass (criptografia pgcrypto, mascaramento logs); Dependencias Pass (tenant ativo); Metrica Pass (percentual de cadastros aprovados sem retrabalho).
- Story Map: Segundo passo da jornada "Preparar cliente" sem sobrepor F-03.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 3 - Originacao de Emprestimo com Score e CET/IOF (F-03)

- Alinhamento Spec-Kit: OK - wizard vertical integra contrato, analise e compliance (CET/IOF) conforme §2.A.
- INVEST: I Pass; N Pass (foco em uma operacao por fluxo); V Pass (contrato gerado com CET/IOF); E Pass (usa DTOs definidos); S Pass (regulacao Banco Central); T Pass (ACs cobrem cenarios de arrependimento e rejeicao).
- DoR: Persona Pass (consultor credenciado); Objetivo Pass (aprovar emprestimo conforme regua); Valor Pass (receita via juros); Restricoes Pass (Lei da Usura, arrependimento); Dependencias Pass (dados KYC, credit bureau); Metrica Pass (tempo medio de aprovacao e aderencia CET).
- Story Map: Fase "Conceder emprestimo" cobrindo simulacao, aprovacao e contrato.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 4 - Gestao de Parcelas e Recebimentos Automatizados (F-04)

- Alinhamento Spec-Kit: OK - fatia vertical combina schedule, notificacoes e conciliacao com Contas a Receber (`FinancialTransaction`) (§3.1, §6.1).
- INVEST: I Pass; N Pass (escopo restrito a cobranca automatizada); V Pass (metrica de adimplencia); E Pass (depende apenas de dados do emprestimo); S Pass (respeita requisitos de pagamento); T Pass (ACs tratam idempotencia, reconciliacao e falhas gateway).
- DoR: Persona Pass (gestor financeiro); Objetivo Pass (garantir fluxo de caixa); Valor Pass (reduz inadimplencia); Restricoes Pass (PIX/Boleto, idempotency-key); Dependencias Pass (contratos ativos); Metrica Pass (taxa de confirmacao automatica).
- Story Map: Fase "Receber parcelas" com integracoes externas.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 5 - Gestao de Contas a Pagar e Despesas Operacionais (F-05)

- Alinhamento Spec-Kit: OK - verticaliza o modulo `finance` (BankAccount, Supplier, CostCenter, FinancialTransaction) entregando controle de despesas e compliance fiscal.
- INVEST: I Pass (valor concreto de economia); N Pass (escopo restrito a despesas/fornecedores); V Pass (métrica de previsibilidade de caixa); E Pass (se apoia em modelos dedicados); S Pass (limites fiscais/LGPD); T Pass (ACs auditaveis).
- DoR: Persona Pass (gestor financeiro); Objetivo Pass (governar contas a pagar); Valor Pass (reduz risco fiscal e atrasos); Restricoes Pass (politica de aprovacao, segregacao de funcoes); Dependencias Pass (tenants/governanca, recebimentos); Metrica Pass (forecast de saidas e aging fornecedores).
- Story Map: Completa a etapa "Administrar caixa" cuidando de fornecedores, centros de custo e conciliacao de despesas.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 6 - Cobranca, Renegociacao e Pipeline de Inadimplencia (F-06)

- Alinhamento Spec-Kit: OK - entrega trilhas multicanal, renegociacao e SLA de follow-up em cima de dados de atrasos.
- INVEST: I Pass; N Pass (somente inadimplencia); V Pass (KPIs de recuperacao); E Pass (usa status do emprestimo e eventos financeiros); S Pass (limites LGPD de contato); T Pass (ACs para escalonamento e auditoria).
- DoR: Persona Pass; Objetivo Pass (recuperar credito); Valor Pass (melhora recuperacao); Restricoes Pass (registro de interacoes, consentimentos); Dependencias Pass (parcelas liquidadas F-04, despesas F-05 para comissao); Metrica Pass (taxa de recuperacao e aging).
- Story Map: Fase "Cobrar" com sub-passos de contato, renegociacao e fechamento.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 7 - Painel Executivo de Performance e Telemetria SLO (F-07)

- Alinhamento Spec-Kit: ATENCAO - entrega vertical mas depende de dados das fatias anteriores; precisa garantir feeds consistentes (catalogo SLO + ETL) antes do planejamento.
- INVEST: I Pass; N Pass parcial (pode crescer alem de KPIs MVP, monitorar escopo); V Pass (dashboards DORA e SLO); E Falha (necessita pipelines preparados em F-04/F-06 e despesas F-05); S Pass (audiencia executiva); T Pass (criterios medidos via Grafana/Looker).
- DoR: Persona Pass; Objetivo Pass (comando e controle); Valor Pass (decisoes baseadas em dados); Restricoes Falha (metas SLO indefinidas -> ver Q3); Dependencias Falha (depende de consolidacao de dados e OTEL).
- Story Map: Camada transversal "Monitorar operacao" pos fluxo transacional.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 8 - Conformidade LGPD e Trilhas de Auditoria Imutaveis (F-08)

- Alinhamento Spec-Kit: OK - fatia vertical gera valor direto a auditores com export, WORM e direito ao esquecimento (§6.2, adicoes itens 5,6).
- INVEST: I Pass; N Pass (escopo LGPD/Auditoria); V Pass (auditoria verificavel); E Pass (usa `django-simple-history` e Object Lock); S Pass (critico regulatorio); T Pass (ACs focam em evidencia).
- DoR: Persona Pass; Objetivo Pass (compliance); Valor Pass (evita sancoes); Restricoes Pass (criptografia, politicas de retencao); Dependencias Pass (eventos F-01 a F-07 geram dados para auditar); Metrica Pass (auditorias aprovadas).
- Story Map: Fluxo transversal "Garantir compliance" habilitado apos dados existirem.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 9 - Observabilidade, Resiliencia e Gestao de Incidentes (F-09)

- Alinhamento Spec-Kit: OK - entrega circuito completo de SLO, alertas, chaos e runbooks seguindo adicoes itens 1,2,3,10.
- INVEST: I Pass; N Pass (foco em operacao); V Pass (error budget e MTTR); E Falha (depende de features transacionais e compliance F-08 para logs mascarados); S Pass (exigencia SRE); T Pass (criterios de monitoracao e GameDay bimestral).
- DoR: Persona Pass; Objetivo Pass (estabilidade); Valor Pass (reduz downtime); Restricoes Pass (OpenTelemetry, budgets, DORA); Dependencias Falha (precisa de dados instrumentados e dashboards); Metrica Pass (MTTR <= metas).
- Story Map: Camada "Operar & Evoluir" sustentando roadmap continuo.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 10 - Fundacao Frontend FSD e UI Compartilhada (F-10)

- Alinhamento Spec-Kit: OK - estabelece base tecnica indispensavel para features verticais de UI (Blueprint §4).
- INVEST: I Pass; N Pass (escopo restrito a fundacao); V Pass (reduz lead time de novas telas); E Pass (contratos claros entre camadas FSD); S Pass (governanca de UX, acessibilidade); T Pass (lint, Storybook/Chromatic, Pact FE/BE).
- DoR: Persona Pass (Tech Lead Frontend); Objetivo Pass (scaffolding da SPA); Valor Pass (padroniza entrega); Restricoes Pass (OTEL client-side, Tailwind CSS baseline, design tokens); Dependencias Pass (repositorio, pipeline CI); Metrica Pass (tempo de bootstrap <= 30 min, cobertura visual >= 90%).
- Story Map: Camada "Fundacao" anterior a F-02/F-03/F-07.

### User Story 11 - Automacao de Seeds, Dados de Teste e Factories (F-11)

- Alinhamento Spec-Kit: OK - cumpre Arts. III/IV fornecendo dados realistas para TDD e integrações.
- INVEST: I Pass; N Pass (foco em seeds/factories); V Pass (qualidade de testes); E Pass (dependencias explicitas); S Pass (dados sintéticos, LGPD); T Pass (scripts automatizados e monitorados).
- DoR: Persona Pass (QA/Plataforma); Objetivo Pass (dados consistentes); Valor Pass (reduz flakiness, acelera onboarding); Restricoes Pass (RLS, RateLimit, anonimização); Dependencias Pass (pipelines CI/CD, GitOps); Metrica Pass (reset < 5 min, cobertura seeds > 95%).
- Story Map: Fluxo transversal "Garantir qualidade" sustentando todo o roadmap.

### 3. Detalhamento das Features (com prompts `/speckit.specify`)

#### F-01 Governanca de Tenants e RBAC Zero-Trust
Contexto: Provisiona tenant, usuarios e politicas RBAC garantindo isolamento multi-tenant (`BaseTenantModel`, RLS) e auditoria WORM conforme `BLUEPRINT_ARQUITETURAL.md` §3.1 e §6.2.
Acceptance criteria:
- Cenario 1: Dado um superusuario com papel TenantOwner, quando registra um novo tenant, entao o sistema cria registros `Tenant`, perfis default (Owner, Gestor, Operador) e aplica RLS ativo em todos os modelos derivados de `BaseTenantModel`, registrando evento WORM com usuario, tenant e timestamp.
- Cenario 2: Dado o provisionamento do tenant, quando as politicas RLS sao aplicadas, entao o sistema executa `CREATE POLICY` com escopo `tenant_id`, amarra o `SET local tenant.id` na sessao e valida (teste negativo) que consultas sem o binding retornam vazio.
- Cenario 3: Dado um gestor ajustando RBAC, quando habilita ou revoga escopos nas roles padrao, entao a mudanca respeita controle de concorrencia via `ETag`/`If-Match`, e e versionada via `django-simple-history` com hash de integridade e replicada ao front (FSD) sem conceder acesso cross-tenant.
- Cenario 4: Dado um usuario sem permissao adequada, quando tenta acessar recurso de outro tenant, entao recebe 403 padronizado (RFC 9457) e o evento e logado com mascaramento de PII.
- Cenario 5: Dado um tenant inativo, quando qualquer solicitacao de API chega, entao o middleware tenant-aware bloqueia e registra audit trail conforme Art. XI.
- Cenario 6: Dado onboarding de tenant, quando o fluxo encerra, entao o tempo total e exibido no painel de execucao e triggers de compliance (RIPD, ROPA) sao inicializados automaticamente.
- Cenario 7: Dado revisao trimestral, quando auditor solicita evidencias de RBAC, entao exportacao consolidada das roles e logs e gerada com Object Lock.
- Cenario 8: Dado um TenantOwner autenticado com MFA TOTP, quando acessa os endpoints `/api/v1/tenants/` e `/api/v1/roles/`, entao a API exige prefixo de versao, valida o segundo fator, emite novo `refresh_token` armazenado em cookie `HttpOnly`/`Secure`/`SameSite=Strict` e retorna Problem Details (RFC 9457) adequados para erros de autenticacao.
- Cenario 9: Dado uma regra de acesso baseada em atributos (ABAC), quando um operador solicita acesso condicionado (ex.: escopo `cost_center=financas`), entao o motor de autorizacoes avalia atributos do usuario, do recurso e do contexto e os testes automatizados (`pytest`/`spectacular`) garantem cobertura de object-level permissions.
- Cenario 10: Dado pipeline CI, quando executado, entao falha se detectar endpoints RBAC/ABAC sem testes de isolacao multi-tenant ou se politicas RLS sofrerem drift (comparacao declarativa com migrações).
Prompt `/speckit.specify`:
```text
F-01 Governanca de Tenants e RBAC Zero-Trust. Use BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.2,19 e adicoes_blueprint.md itens 4,5,12,13. Produza a especificacao seguindo o template oficial (contexto, historias, requisitos, metricas, riscos) sem definir stack adicional. Garanta RLS com `CREATE POLICY` e binding de sessao, RBAC+ABAC com testes automatizados, MFA obrigatoria, auditoria WORM, controle de concorrencia com `ETag`/`If-Match`, versionamento `/api/v1`, refresh tokens seguros (`HttpOnly`/`Secure`/`SameSite=Strict`) e Problem Details (RFC 9457), alinhado aos Arts. III, V, IX, XIII. Marque duvidas criticas com [NEEDS CLARIFICATION] e inclua BDD para ativacao de tenant, bloqueio cross-tenant, versionamento de roles, MFA/refresh seguro, atributos de autorizacao e logs S3 Object Lock, referenciando OpenAPI 3.1 contract-first.
```

#### F-02 Cadastro e KYC de Clientes e Consultores
Contexto: Centraliza captura e validacao de dados de clientes/consultores, incluindo documentos, enderecos e consentimentos LGPD (`customers.models`, DTOs `CustomerCreateDTO`), suportando verificacoes KYC.
Acceptance criteria:
- Cenario 1: Dado um consultor autenticado, quando envia dados completos de cliente com CPF unico por tenant, entao o sistema valida formato, verifica unicidade (`unique_together`) e aplica mascaramento nas respostas de auditoria.
- Cenario 2: Dado upload de documento KYC, quando o arquivo e armazenado, entao metadados sao vinculados ao audit trail e o consentimento LGPD e registrado com hash de verificacao.
- Cenario 3: Dado um cliente com consentimento de marketing negado, quando um operador tenta marcar lead como apto a notificacoes, entao o sistema bloqueia e registra tentativa em trilha WORM.
- Cenario 4: Dado cadastro de consultor, quando o usuario e associado a `Consultant` e saldo inicial configurado, entao RBAC adiciona escopos de operacao conforme matriz (adicoes item 12).
- Cenario 5: Dado direito ao esquecimento acionado, quando auditor aprova requisicao, entao dados sensiveis sao anonimizados e logs registram operador, timestamp e motivo.
- Cenario 6: Dado fluxo de criacao massiva via CSV, quando registros invalidos sao detectados, entao o arquivo retorna com lista de erros por linha mantendo isolamento por tenant.
- Cenario 7: Dado um operador atualizando um cliente existente, quando envia `If-Match` com o `ETag` correto, entao a atualizacao e aplicada e a resposta inclui novo `ETag`; quando o cabeçalho esta ausente ou desatualizado, o sistema responde `428 Precondition Required` com Problem Details.
- Cenario 8: Dado processamento KYC em andamento, quando a API automatizada aprova o documento dentro do SLA, entao o status e atualizado e a auditoria registra a referencia externa; quando a API retorna erro ou sinaliza alerta, entao o caso e roteado para fila de revisao manual auditada com SLA distinto e bloqueio de prosseguimento ate decisao humana.
- Cenario 9: Dado consumidor utilizando a API REST, quando realiza requisicoes aos recursos `/api/v1/customers/` e `/api/v1/consultants/`, entao os headers `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` e `Retry-After` sao retornados e validados no limite de tenant.
- Cenario 10: Dado pipeline CI, quando valida o contrato OpenAPI 3.1 e os DTOs/serializers, entao assegura que apenas campos minimamente necessários sao expostos ao frontend e falha caso PII nao mascarada seja detectada pelo lint de DTO.
Prompt `/speckit.specify`:
```text
F-02 Cadastro e KYC de Clientes e Consultores. Referencie BLUEPRINT_ARQUITETURAL.md §§2,3.1,3.2 e adicoes_blueprint.md itens 4,5,7,13. Gere especificacao completa (template Spec-Kit) focada em captura de PII, validacao KYC, consentimentos LGPD e integracao com trilha de auditoria. Proiba decisoes de implementacao, detalhe historias para cadastro manual, importacao em massa e direito ao esquecimento. Exija controle de concorrencia (`ETag`/`If-Match` + `428`), headers de rate limiting, versionamento `/api/v1`, contrato OpenAPI 3.1 com lint/diff, Pact producer/consumer e metricas de qualidade/minimizacao de dados (lint de DTO contra PII). Mantenha [NEEDS CLARIFICATION] para politicas pendentes.
```

#### F-03 Originacao de Emprestimo com Score e CET/IOF
Contexto: Viabiliza simulacao, analise e aprovacao de emprestimos com calculo CET/IOF, verificacoes de Lei da Usura e consulta ao bureau externo Serasa Experian (`LoanCreateDTO`, wizard `NewLoanWizard`). APIs e workflows devem sustentar os SLOs iniciais definidos (p95 600 ms, p99 1 s).
Acceptance criteria:
- Cenario 1: Dado um consultor com cliente elegivel, quando executa simulacao preenchendo montante, taxa e parcelas, entao o sistema calcula CET mensal/anual, IOF e exibe detalhes antes da aprovacao garantindo latencia p95 <= 600 ms.
- Cenario 2: Dado integracao com Serasa Experian disponivel, quando solicitada analise, entao a resposta (score, flags) e anexada ao processo e armazenada com idempotency-key e timeout controlado dentro do p99 de 1 s.
- Cenario 3: Dado juros acima do limite legal, quando simulacao ocorre, entao o sistema bloqueia aprovacao e fornece mensagem com referencias legais (Lei da Usura).
- Cenario 4: Dado direito de arrependimento em ate 7 dias, quando pedido e registrado, entao o contrato muda para status `CANCELED`, parcelas sao anuladas e auditoria registra motivo.
- Cenario 5: Dado falha no servico da Serasa Experian, quando o consultor tenta reprocessar, entao o sistema usa retry com backoff exponencial e permite fallback manual com justificativa.
- Cenario 6: Dado consultor tenta emitir contrato sem consentimento LGPD, quando fluxo avanca, entao e bloqueado ate consentimento ser registrado.
- Cenario 7: Dado `NewLoanWizard` no frontend, quando a jornada e carregada, entao os componentes seguem o padrão FSD (camadas `features/loan-origination`, `entities/customer`, `shared/ui`) com gerenciamento de estado definido e telemetria OTEL configurada.
- Cenario 8: Dado requisicao REST para `/api/v1/loans/`, quando simulacao ou aprovacao e executada, entao a API responde com `RateLimit-*` headers, `Retry-After` quando aplicavel e Problem Details padronizados para erros de negocio.
- Cenario 9: Dado pipeline CI em execucao, quando contrato Pact com a Serasa Experian e atualizado, entao o job valida compatibilidade producer/consumer e bloqueia merge em caso de quebra.
Prompt `/speckit.specify`:
```text
F-03 Originacao de Emprestimo com Score e CET/IOF. Utilize BLUEPRINT_ARQUITETURAL.md §§2,3.1.1,3.2 e adicoes_blueprint.md itens 1,4,7. Escreva especificacao orientada ao usuario cobrindo simulacao, integracao com o bureau Serasa Experian definido para o MVP, calculos CET/IOF e processo de arrependimento. Proiba escolhas de stack; detalhe requisitos regulatorios, estrutura frontend FSD (`features`/`entities`/`shared`), versionamento `/api/v1`, contrato OpenAPI 3.1 com lint/diff, RateLimit headers, Pact para integrações externas e tratativas de falhas (circuit breaker, backoff, fallback manual). Detalhe contratos e SLAs esperados com a Serasa Experian e garanta aderencia aos SLOs de latencia p95 600 ms / p99 1 s / MTTR 1 h / taxa de erro <1%.
```

#### F-04 Gestao de Parcelas e Recebimentos Automatizados
Contexto: Automatiza agenda de parcelas, integracao com o gateway PIX/Boleto Asaas, conciliacao financeira (`FinancialTransaction`, Celery) e falhas tolerantes (`adicoes` itens 7,8) aderentes aos SLOs definidos (p95 600 ms, p99 1 s, MTTR 1 h, erro <1%).
Acceptance criteria:
- Cenario 1: Dado emprestimo aprovado, quando primeiro cronograma e gerado, entao parcelas recebem status inicial, datas e valores com CET aplicado e RLS garantido dentro do p95 de 600 ms.
- Cenario 2: Dado integracao com o Asaas, quando cobranca e emitida, entao o sistema gera QR-code ou boleto com `Idempotency-Key`, registra evento e atualiza status apos conciliacao automatica.
- Cenario 3: Dado pagamento recebido, quando gateway envia webhook, entao conciliacao usa `retry_backoff` em Celery com `acks_late=True`, atualiza `FinancialTransaction` e `Installment` de forma idempotente, registra o `Idempotency-Key` resolvido e recupera incidentes com MTTR <= 1 h.
- Cenario 4: Dado limite de rate limiting do Asaas, quando excedido, entao o sistema respeita `429` com `Retry-After`, retorna `RateLimit-Limit/Remaining/Reset` por tenant e reprograma tarefa mantendo orcamento de erro.
- Cenario 5: Dado falha de conciliacao, quando tentativa falha 3 vezes, entao tarefa migra para DLQ com contexto completo para analise manual.
- Cenario 6: Dado tenant com auditoria ativa, quando parcelas sao liquidadas, entao logs exportam eventos para WORM e dashboard financeiro.
- Cenario 7: Dado uma parcela sendo atualizada via API, quando requisicao inclui `If-Match` coerente com o `ETag`, entao a atualizacao e aplicada; quando o cabecalho falta ou diverge, entao retorna `428` com Problem Details.
- Cenario 8: Dado pipeline CI, quando PR altera payload de webhook ou rota `/api/v1/installments`, entao os contratos Pact producer/consumer com o Asaas sao validados antes do merge.
Prompt `/speckit.specify`:
```text
F-04 Gestao de Parcelas e Recebimentos Automatizados. Referencie BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.1,26 e adicoes_blueprint.md itens 3,7,8. Produza especificacao que cubra schedule de parcelas, integracao com o gateway SaaS Asaas definido para o MVP, conciliacao idempotente, `acks_late`, controle de concorrencia (`ETag`/`If-Match`), versionamento `/api/v1`, contrato OpenAPI 3.1 com lint/diff, RateLimit headers e tratamento de erros conforme RFC 9457. Inclua criterios de sucesso para taxas de adimplencia, DLQ, Pact de webhooks e rotinas de FinOps alinhadas ao Asaas.
```

#### F-05 Gestao de Contas a Pagar e Despesas Operacionais
Contexto: Orquestra cadastros de fornecedores, contas bancarias, centros de custo e registro de despesas (tipo `EXPENSE`), vinculando comprovantes e aprovacoes antes de efetivar pagamentos.
Acceptance criteria:
- Cenario 1: Dado um gestor financeiro, quando cadastra fornecedor com CNPJ unico por tenant, entao o sistema valida documento, vincula categoria/cost center e gera log de auditoria.
- Cenario 2: Dado uma despesa recorrente, quando agendamento e criado, entao `FinancialTransaction` registra status `PENDING`, associa `BankAccount` correto e agenda tarefa Celery para lembrete de pagamento.
- Cenario 3: Dado uma despesa criada via `/api/v1/payables/`, quando o cliente envia `Idempotency-Key` inedito, entao o registro e persistido; quando o mesmo `Idempotency-Key` reaparece, entao a API responde com 200/Problem Details idempotente sem duplicar pagamentos.
- Cenario 4: Dado um fluxo de aprovacao em duas etapas, quando um operador solicita pagamento acima do limite definido, entao o sistema exige aprovacao de Gestor, registra justificativa e bloqueia execucao ate confirmacao.
- Cenario 5: Dado comprovante anexado, quando despesa e marcada como paga, entao evidencias (arquivo + hash) sao vinculadas ao audit trail e dados sensiveis sao mascarados nos logs.
- Cenario 6: Dado limite orcamentario de centro de custo, quando nova despesa excede headroom, entao alerta e enviado ao painel FinOps e a aprovacao exige justificativa extra.
- Cenario 7: Dado integracao com instalmento de emprestimo (comissao de consultor), quando despesa referenciada e liquidada, entao `Installment.payments` recebe referencia e conciliacao e atualizada.
- Cenario 8: Dado webhook de pagamento recebido do banco, quando `Idempotency-Key` já reconcilia transacao anterior, entao o processamento marca tentativa como duplicada e nao cria nova movimentacao.
- Cenario 9: Dado uma requisicao de atualizacao de despesa via `/api/v1/payables/<id>`, quando o cliente envia `If-Match` coerente com o `ETag`, entao a alteracao e persistida; quando o cabecalho esta ausente ou incorreto, o sistema responde `428` com Problem Details e nao persiste a mudanca.
- Cenario 10: Dado job de migracao, quando comandos de monitoramento rodam, entao garantem que indices compostos com `tenant_id` estejam ativos (`tenant, supplier`, `tenant, cost_center`) usando `CREATE INDEX CONCURRENTLY` quando necessario.
- Cenario 11: Dado consumo da API `/api/v1/payables/`, quando o limite de requisicoes por tenant e aproximado, entao os headers `RateLimit-*` refletem o consumo e `Retry-After` orienta retentativas.
- Cenario 12: Dado pipeline CI, quando executa lint OpenAPI 3.1/Pact, entao falha ao detectar novas rotas sem `Idempotency-Key` ou sem testes de autorizacao multi-tenant associados.
Prompt `/speckit.specify`:
```text
F-05 Gestao de Contas a Pagar e Despesas Operacionais. Utilize BLUEPRINT_ARQUITETURAL.md §§3.1,6.1,6.3 e adicoes_blueprint.md itens 3,8,11. Gere especificacao cobrindo cadastro de fornecedores/contas bancarias, politicas de aprovacao, controle de centros de custo e auditoria fiscal. Proiba decisoes de stack; inclua historias para despesas recorrentes, aprovacao em niveis, anexos de comprovantes e alertas de budget. Exija versionamento `/api/v1`, contrato OpenAPI 3.1 com lint/diff, `Idempotency-Key` para criacao e webhooks, controle de concorrencia (`ETag`/`If-Match`), RateLimit por tenant, indices multi-tenant, deduplicacao de pagamentos e Pact FE/BE. Registre politica de aprovacao em duas etapas (solicitante -> gestor centro de custo -> financeiro) conforme clarificacao atual.
```

#### F-06 Cobranca, Renegociacao e Pipeline de Inadimplencia
Contexto: Garante trilhas de cobranca multicanal (WhatsApp Business API como canal primario), esteiras de renegociacao e governance de contato alinhada a LGPD e runbooks de cobranca (`docs/runbooks/governanca-api.md`).
Acceptance criteria:
- Cenario 1: Dado parcela em atraso, quando SLA de X dias expira, entao sistema dispara tarefa Celery que agenda notificacoes multicanal e registra auditoria com justificativa.
- Cenario 2: Dado negociacao proposta, quando consultor registra acordo via `/api/v1/collections/renegotiations/<id>`, entao o novo cronograma e gerado com `expand/contract`, controles `ETag`/`If-Match` e auditoria WORM.
- Cenario 3: Dado tentativa de contato fora da janela legal, quando consultor aciona fluxo, entao sistema bloqueia acao e registra motivo.
- Cenario 4: Dado cliente paga renegociacao parcial, quando baixa e registrada, entao regra de distribuicao aplica e recalcula saldo remanescente.
- Cenario 5: Dado falha Celery, quando fila atinge limite, entao alerta e disparado (adicoes item 2) e runbook orienta contingencia manual, mantendo tarefas configuradas com `acks_late=True` e limites de fila documentados.
- Cenario 6: Dado tenant quer exportar pipeline, quando requisitado, entao export e entregue sem PII em claro e com filtros por aging.
- Cenario 7: Dado trafego elevado nos endpoints de cobranca, quando consumo se aproxima do limite, entao headers `RateLimit-*` e `Retry-After` sao retornados por tenant e as tentativas excessivas sao bloqueadas.
- Cenario 8: Dado pipeline CI, quando pactos de cobranca multicanal sao atualizados, entao os contratos producer/consumer sao verificados antes do merge.
Prompt `/speckit.specify`:
```text
F-06 Cobranca, Renegociacao e Pipeline de Inadimplencia. Use BLUEPRINT_ARQUITETURAL.md §§3.1,6.2,26 e adicoes_blueprint.md itens 2,3,8,10. Especifique jornadas de cobranca, renegociacao e exports auditaveis, sem definir stack. Inclua ACs para limites LGPD, consentimento por canal, DLQ, fallback manual, Pact producer/consumer, `acks_late`, RateLimit por tenant, controle de concorrencia (`ETag`/`If-Match`), versionamento `/api/v1` e contrato OpenAPI 3.1 com lint/diff, mantendo alinhamento com runbooks.
```

#### F-07 Painel Executivo de Performance e Telemetria SLO
Contexto: Fornece dashboards executivos com KPIs de credito (CET medio, inadimplencia), SLOs (latencia p95/p99, erro) e metricas DORA (`docs/slo/catalogo-slo.md`, adicoes itens 1,2,11).
Acceptance criteria:
- Cenario 1: Dado dados de emprestimos ativos, quando painel carrega, entao apresenta CET medio, carteira por status e aging com filtros por tenant.
- Cenario 2: Dado pipelines OTEL configurados, quando eventos de API chegam, entao dashboards exibem p95/p99 e consumo de error budget em tempo quase real.
- Cenario 3: Dado deploy em producao, quando pipeline CI roda, entao DORA lead time e taxa de falha atualizam automaticamente.
- Cenario 4: Dado incidentes, quando MTTR excede budget, entao painel destaca alerta e sugere GameDay conforme adicoes item 10.
- Cenario 5: Dado FinOps, quando custo excede orcamento, entao painel exibe variacao versus budget com tags de custo.
- Cenario 6: Dado metas SLO definidas (p95 600 ms, p99 1 s, MTTR 1 h, erro <1%), quando feature publica dashboards, entao os painéis mostram budgets calculados com base nesses targets e bloqueiam deploy se projeções indicarem violação.
- Cenario 7: Dado ingestion de dados SLO/FinOps, quando divergencias entre fonte primária e painel são detectadas, entao o sistema sinaliza integridade quebrada, bloqueia atualização e exige reconciliação automática antes de liberar o dashboard.
Prompt `/speckit.specify`:
```text
F-07 Painel Executivo de Performance e Telemetria SLO. Referencie BLUEPRINT_ARQUITETURAL.md §§2,6.3, docs/slo/catalogo-slo.md e adicoes_blueprint.md itens 1,2,11. Elabore especificacao descrevendo dashboards, integrações OTEL, DORA e FinOps, sem decidir stack. Destaque dependencia de dados consolidados, integrações com a fundação FSD (F-10) e utilize os SLOs iniciais definidos (p95 600 ms, p99 1 s, MTTR 1 h, erro <1%) como baseline para budgets, alertas e governanca de desempenho. Inclua criterios para atualizar automaticamente error budgets e acionamentos, verificações de integridade de métricas (late-binding) e geração de painéis FinOps por tenant/feature.
```

#### F-08 Conformidade LGPD e Trilhas de Auditoria Imutaveis
Contexto: Implementa governanca LGPD (RIPD, ROPA, direito ao esquecimento), trilha `django-simple-history` com armazenamento WORM (S3 Object Lock) e controles de segredos (Vault, pgcrypto).
Acceptance criteria:
- Cenario 1: Dado evento de alteracao em `Loan`, quando persistido, entao historia completa e salva com usuario, motivo e hash verificavel.
- Cenario 2: Dado pedido de exportacao LGPD, quando atendido, entao plataforma gera pacote criptografado com campos mascarados e log imutavel.
- Cenario 3: Dado pedido de exclusao, quando aprovado, entao dados sao anonimizados, politicas de retencao atualizadas e evidencia anexada ao ROPA.
- Cenario 4: Dado acesso a trilha por usuario sem papel Auditor, quando tenta baixar, entao sistema bloqueia e registra tentativa.
- Cenario 5: Dado pipeline CI, quando build roda, entao verifica SBOM, SAST/DAST/SCA e falha caso CVSS alto (adicoes item 5).
- Cenario 6: Dado plano de DR, quando failover ocorre, entao trilhas WORM permanecem intactas e reconciliadas.
- Cenario 7: Dado rotacao programada de segredos, quando Vault gera nova chave e KMS realiza envelope encryption, entao aplicacoes atualizam credenciais sem downtime e auditoria registra a rotacao.
- Cenario 8: Dado pedido de exclusao aprovado, quando dados sao anonimizados, entao chaves tecnicas persistem como hashes salinizados permitindo conciliacao contábil sem reidentificar titulares.
- Cenario 9: Dado politica de retencao configurada para 5 anos adicionais alem dos 30 dias legais, quando expira o prazo minimo, entao a plataforma executa pseudonimizacao/expurgo conforme categoria de dado, preservando artefatos contabeis e registrando evidencia legal em WORM.
Prompt `/speckit.specify`:
```text
F-08 Conformidade LGPD e Trilhas de Auditoria Imutaveis. Utilize BLUEPRINT_ARQUITETURAL.md §§6.2,27 e adicoes_blueprint.md itens 4,5,6,12. Escreva especificacao cobrindo RLS, direito ao esquecimento, export LGPD, SBOM, trilhas WORM, rotacao automática de segredos (Vault/KMS) e politicas de pseudonimizacao vs. anonimização com retenção legal configurada para 5 anos adicionais além dos 30 dias obrigatórios. Proiba decisoes de stack adicionais e exija historias para auditoria, export, exclusao, reconciliacao contábil, DR e verificação de drift de conformidade no CI. Mantenha alinhamento com Art. XIII e ADR-010.
```

#### F-09 Observabilidade, Resiliencia e Gestao de Incidentes
Contexto: Reforca SRE com pipelines OTEL, limites de fila, testes de carga (k6), feature flags, GameDays bimestrais e runbooks (adicoes itens 1,2,3,8,10).
Acceptance criteria:
- Cenario 1: Dado deploy em producao, quando pipelines CI executam, entao stages de SAST/DAST/SCA, SBOM, performance (k6), OpenAPI lint/diff e Pact producer/consumer precisam passar antes do release.
- Cenario 2: Dado evento de saturacao, quando metricas excedem limiar, entao autoscaling dispara com base em SLO definido e notifica error budget policy.
- Cenario 3: Dado GameDay bimestral agendado, quando incidente simulado e executado, entao runbook e atualizado com achados, MTTR registrado e backlog de melhorias priorizado.
- Cenario 4: Dado feature flag critica, quando toggled, entao logs auditados mostram autor, justificativa e rollback path.
- Cenario 5: Dado fila Celery atinge limite, quando backlog supera threshold, entao alerta e gerado e tasks non-critical sao rebaixadas conforme politica.
- Cenario 6: Dado integracao externa indisponivel, quando circuito abre, entao fallback degrade graciosamente e orcamento de erro reduzido e recalculado.
- Cenario 7: Dado job programado do Renovate ou sync do Argo CD, quando novas dependencias ou manifests sao aplicados, entao o fluxo GitOps registra a mudanca, executa politicas OPA e bloqueia divergencias.
- Cenario 8: Dado pipeline de release, quando imagens e artefatos sao gerados, entao sao assinados (cosign/SLSA) e verificados antes do deploy, bloqueando publicacao sem proveniencia.
- Cenario 9: Dado job de qualidade de codigo, quando avalia cobertura e complexidade, entao falha se complexidade ciclomática exceder 10 ou cobertura TDD < 85%, conforme Art. IX.
Prompt `/speckit.specify`:
```text
F-09 Observabilidade, Resiliencia e Gestao de Incidentes. Referencie BLUEPRINT_ARQUITETURAL.md §§6,26,27 e adicoes_blueprint.md itens 1,2,3,8,9,10,14, alem dos ADRs 008 e 009. Gere especificacao cobrindo pipelines CI/CD, SLOs, error budgets, chaos, feature flags, GitOps (Argo CD) e Renovate. Sem decisoes de stack; detalhe metricas de saturacao, thresholds k6, planos de DR, politicas de escalonamento, gates de OpenAPI 3.1 diff/Pact, assinatura/proveniência (cosign/SLSA), complexidade <= 10, cobertura mínima e validação Policy-as-Code (OPA). Marque dependencias das fatias de negocio e mantenha perguntas abertas conforme necessario.
```

#### F-10 Fundacao Frontend FSD e UI Compartilhada
Contexto: Garante a implementacao da arquitetura Feature-Sliced Design descrita no blueprint (§4), criando scaffolding de pastas (`app/`, `features/`, `entities/`, `shared/`), conectando o estado (TanStack Query, Zustand) e estabelecendo bibliotecas compartilhadas de UI e telemetria.
Acceptance criteria:
- Cenario 1: Dado repositório frontend, quando a feature e entregue, entao a estrutura FSD e gerada com camadas `app`, `features`, `entities`, `shared` e `widgets`, incluindo alias de importacao e convencoes documentadas.
- Cenario 2: Dado componente core de UI, quando publicado, entao Storybook/Chromatic registra variações e testes visuais automatizados asseguram regressao <= 0.1%.
- Cenario 3: Dado consumo de API `/api/v1`, quando hooks TanStack Query sao executados, entao reutilizam contratos tipados gerados (OpenAPI) e propagam contexto OTEL no frontend.
- Cenario 4: Dado novo módulo de negocio (ex.: loans), quando scaffolding `features/loan-list` e criado, entao há integração com a camada `entities` correspondente e restrição de import cross-layer respeitada pelo lint.
- Cenario 5: Dado pipeline CI do frontend, quando executado, entao validações de lint FSD, testes de interface e pactos FE/BE (via Pact ou msw contract tests) rodam e bloqueiam merge em caso de quebra.
- Cenario 6: Dado requisito de acessibilidade, quando componente shared e renderizado, entao os checks Axe automatizados aprovam AA por padrão.
- Cenario 7: Dado roteamento e telemetria configurados, quando URLs ou spans sao gerados, entao nenhum identificador PII aparece na rota/atributos e as políticas CSP com nonce/hash e Trusted Types são aplicadas e testadas automaticamente.
- Cenario 8: Dado o design system base em Tailwind CSS, quando componentes `shared/ui` sao construidos, entao utilizam tokens configurados no `tailwind.config.ts`, documentam variações multi-tenant e passam validação automática de consistência (lint + Storybook).
Prompt `/speckit.specify`:
```text
F-10 Fundacao Frontend FSD e UI Compartilhada. Referencie BLUEPRINT_ARQUITETURAL.md §4, docs de design system internos e adicoes_blueprint.md itens 1,2,13. Produza especificacao detalhando scaffolding FSD, Storybook/Chromatic, integrações com TanStack Query/Zustand, propagacao de OTEL no cliente, pactos FE/BE e critérios de acessibilidade. Reforce o uso de Tailwind CSS como base oficial do design system (conforme blueprint), permitindo theming multi-tenant via tokens personalizados. Inclua métricas de cobertura visual, lint FSD, governança de imports, prevenção de PII em URLs/telemetria e política CSP rigorosa (nonce/hash + Trusted Types).
```

#### F-11 Automacao de Seeds, Dados de Teste e Factories
Contexto: Assegura que o princípio Test-First (Art. III) e o uso de testes de integração-realista (Art. IV) sejam suportados por seeds consistentes, factories (`factory-boy`), scripts de carga e dados anonimizados multi-tenant.
Acceptance criteria:
- Cenario 1: Dado comando `python manage.py seed_data`, quando executado, entao popula tenants, clientes, emprestimos e despesas consistentes com isolamento por tenant e logs de auditoria.
- Cenario 2: Dado pipeline CI, quando roda, entao testa factories (`test_factories.py`) garantindo que relacionamentos respeitam `tenant` e que dados PII sao mascarados antes de export de fixtures.
- Cenario 3: Dado ambiente de staging, quando sincronizado via Argo CD, entao seeds versionados sao aplicados automaticamente e divergencias são reportadas como drift.
- Cenario 4: Dado teste de carga (k6), quando necessita dados massivos, entao comando gera dataset sintético paginado preservando limites regulatórios (CET/IOF) e quotas de RateLimit.
- Cenario 5: Dado exercício de DR, quando réplicas sao promovidas, entao script de verificação confirma integridade das seeds e sinaliza desvios.
- Cenario 6: Dado necessidade de reset local, quando desenvolvedor executa script, entao dados são recriados sem vazar PII real (usa dados sintéticos) e relatórios de cobertura TDD se mantêm >= 85%.
- Cenario 7: Dado o perfil `dev`, quando comando `seed_data` e executado, entao gera 100 clientes e 200 emprestimos por tenant; dado o perfil `staging`, entao gera 1.000 clientes e 5.000 emprestimos; dado o perfil `carga`, entao gera volumetria configuravel declarada via variavel de ambiente sem quebrar RateLimit nem exceder quotas de armazenamento, registrando estatisticas no CI.
Prompt `/speckit.specify`:
```text
F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`.
```

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do código cobrindo fluxos felizes/tristes | ACs BDD em F-01 a F-11, seeds automatizadas (F-11) e lint FSD (F-10) reforçam TDD |
| Art. V (Documentação & Versionamento) | API versionada (`/api/v1`) e contratos atualizados | Prompts de F-01 a F-06 e F-10 exigem prefixo de versão, Problem Details e contratos OpenAPI 3.1 com lint/diff |
| Art. VII (Observabilidade) | OTEL, logs estruturados, mascaramento | F-03, F-07, F-09 e F-10 propagam contexto OTEL, mascaram PII e expõem métricas |
| Art. VIII (Entrega) | Releases seguros (feature flags, canary, rollback) | F-04 e F-09 tratam feature flags, canários e DLQ; F-10 exige rollout controlado de UI |
| Art. IX (CI) | Cobertura ≥85%, SAST/DAST/SCA, SBOM, k6 | Gates descritos em F-09, lint/Storybook em F-10 e validação de seeds em F-11 |
| Art. X (Zero-downtime) | Parallel change, índices `CONCURRENTLY` | F-04, F-05 e F-06 incorporam expand/contract, DLQ e criação de índices sem downtime |
| Art. XI (API) | OpenAPI 3.1, Pact, RateLimit, ETag/If-Match | F-01 a F-06 reforçam contratos Pact, controle de concorrência e RateLimit headers |
| Art. XIII (LGPD/RLS) | RLS, direito ao esquecimento, pgcrypto | F-01, F-02, F-05, F-08 e F-11 cobrem RLS, pgcrypto, anonimização e WORM |
| Art. XVI (FinOps) | Custos rastreados, budgets e alertas | F-04, F-05, F-07 e F-09 incluem monitoramento de custos e RateLimit por tenant |
| ADR-008 (Renovate) | Atualização contínua de dependências | F-09 adiciona Renovate no pipeline com gates de segurança |
| ADR-009 (GitOps) | Deploy via Argo CD e drift detection | F-09 e F-11 descrevem Argo CD, execução de policies e detecção de drift |
| ADR-010 (Proteção de Dados) | pgcrypto, Vault, mascaramento de PII | F-02, F-08 e F-11 abordam criptografia, rotação automática e anonimização |
| ADR-011 (Governança de API) | Lint/diff, Pact, RateLimit, Idempotência | F-02 a F-06 exigem Pact, RateLimit headers, `Idempotency-Key` e `ETag` |
| ADR-012 (Observabilidade Padronizada) | structlog, django-prometheus, Sentry | F-07, F-09 e F-10 especificam telemetria padronizada e dashboards SLO |
| Runbooks, DR, GameDays | Ensaios de DR e incidentes | F-06, F-09 e F-11 vinculam runbooks, DR piloto light e GameDays bimestrais |

### Functional Requirements

- FR-001: O sistema deve permitir cadastro e ativacao de tenants com RLS aplicado automaticamente em todos os modelos que herdam `BaseTenantModel`, disponibilizando RBAC/ABAC auditável com testes automatizados de object-level permissions e exigindo MFA TOTP dedicado para TenantOwner com auditoria automatizada.
- FR-002: Processos de KYC devem validar CPF/CNPJ por tenant, armazenar consentimentos LGPD, combinar verificacao automatizada via API oficial com revisao manual auditada e disponibilizar exportacoes anonimizadas.
- FR-003: A originacao de emprestimos deve calcular CET e IOF conforme regulacao, registrar interacoes com bureau externo e bloquear juros acima do limite legal.
- FR-004: A gestao de parcelas deve gerar agendas com status rastreados, emitir cobrancas PIX/Boleto com `Idempotency-Key` e conciliar pagamentos via webhooks idempotentes.
- FR-005: O modulo financeiro deve controlar contas a pagar, fornecedores e centros de custo com aprovacao em duas etapas (operador → gestor), anexos auditaveis e integracao com contas bancarias.
- FR-006: A pipeline de cobranca deve automatizar notificacoes, renegociacoes e escalonamentos com logs auditaveis e limites de contato configuraveis.
- FR-007: Dashboards executivos devem consolidar KPIs de carteira, SLOs e DORA com filtros por tenant e alertas de budget.
- FR-008: Trilhas de auditoria devem armazenar alteracoes em WORM com integridade verificavel e suportar direito ao esquecimento sem vazamento de PII.
- FR-009: Pipelines de operacao devem executar gates de CI (SAST/DAST/SCA, SBOM, k6), validar Policy-as-Code (OPA), verificar proveniência (cosign/SLSA) e acionar runbooks e feature flags conforme politicas definidas.
- FR-010: O frontend deve prover scaffolding Feature-Sliced Design (`app/`, `features/`, `entities/`, `shared/`, `widgets/`) com components compartilhados testados (Storybook/Chromatic) e telemetria OTEL cliente.
- FR-011: Seeds, factories (`factory-boy`) e scripts `seed_data` devem gerar dados sintéticos multi-tenant, mascarar PII e ser validados automaticamente no CI/CD e nos fluxos de DR.

### Non-Functional Requirements

- NFR-001 (SLO): Fluxos criticos (login, simulacao, emissao de parcela) devem manter p95 <= 1.5s, p99 <= 2.5s e disponibilidade mensal >= 99.5%, com budgets e alertas documentados.
- NFR-002 (Performance): Testes de carga k6 devem provar que conceder 500 emprestimos/hora e conciliar 5.000 pagamentos/dia permanecem dentro dos SLOs.
- NFR-003 (Observabilidade): Toda requisicao deve propagar contexto OTEL, gerar logs JSON mascarados e publicar metricas de saturacao por fila/tenant.
- NFR-004 (Seguranca): Pipelines precisam bloquear CVSS >= 7, rotacionar segredos via Vault, aplicar RBAC/ABAC e validar RLS automatizada.
- NFR-005 (FinOps): Custos de gateway e infraestrutura devem ser tagueados por tenant e mantidos dentro do budget mensal definido, com alertas de 80% e 100%.
- NFR-006 (Governanca de API): Endpoints mutadores devem expor `RateLimit-*`, exigir `Idempotency-Key` quando pertinente e aplicar `ETag`/`If-Match` com respostas `428` em caso de conflito.
- NFR-007 (UX & Acessibilidade): Componentes compartilhados do frontend devem cumprir WCAG 2.1 AA com verificacoes automatizadas (Axe) e histórico de regressao visual controlado.
- NFR-008 (Qualidade de Código): Pipelines de CI devem garantir cobertura ≥85%, complexidade ciclomática ≤10 e assinatura/proveniência verificada antes de deploy.

### Dados Sensiveis & Compliance

Campos PII (CPF, RG, endereco, telefone, contas bancarias) devem ser criptografados com pgcrypto no Postgres, mascarados em logs e removidos de exports nao auditados. Serializadores/DTOs devem aplicar minimizacao de dados e validacoes automatizadas (lint no CI) para impedir vazamentos para o frontend (ADR-010). Politicas de retencao seguem LGPD: dados de clientes ativos retidos por 5 anos apos quitacao, com suporte a direito ao esquecimento em ate 30 dias. Trilhas WORM permanecem bloqueadas por 5 anos adicionais alem dos 30 dias legais, com expiracoes automatizadas auditadas e alertas de proximidade. Evidencias necessarias: RIPD/DPIA por feature, ROPA atualizado por tenant, Object Lock configurado para auditoria, provas de mascaramento em pipelines de observabilidade e auditorias de anonimização pós-exclusão.

### 4. Duvidas para `/speckit.clarify` (por feature)

#### F-01 Governanca de Tenants e RBAC Zero-Trust
- Resolvido: MFA TOTP dedicado obrigatório para TenantOwner com enforcement documentado e auditoria periódica.

#### F-02 Cadastro e KYC de Clientes e Consultores
- Resolvido: MVP adota abordagem hibrida (upload auditado + API automatizada) para validacao documental, balanceando SLA e compliance.

#### F-03 Originacao de Emprestimo com Score e CET/IOF
- Resolvido: Bureau inicial = Serasa Experian; alinhar contratos, custos e SLA de aprovacao com esse provedor.

#### F-04 Gestao de Parcelas e Recebimentos Automatizados
- Resolvido: Gateway SaaS Asaas priorizado para PIX/Boleto; alinhar homologacoes, SLA e custos recorrentes com esse parceiro.

#### F-05 Gestao de Contas a Pagar e Despesas Operacionais
- Resolvido: MVP adota fluxo de aprovacao em duas etapas (operador → gestor) com limites auditaveis por faixa de valor.

#### F-06 Cobranca, Renegociacao e Pipeline de Inadimplencia
- Resolvido: Canal primario de cobranca ativa sera WhatsApp Business API, com consentimentos e auditoria alinhados a LGPD.

#### F-07 Painel Executivo de Performance e Telemetria SLO
- Resolvido: SLOs iniciais = p95 600 ms, p99 1 s, MTTR 1 h, erro <1%; calibrar alertas e error budget policy com estes targets.

#### F-08 Conformidade LGPD e Trilhas de Auditoria Imutaveis
- Resolvido: Trilhas WORM manterao 5 anos adicionais alem dos 30 dias legais para equilibrar auditoria e custos.

#### F-09 Observabilidade, Resiliencia e Gestao de Incidentes
- Resolvido: GameDays bimestrais garantem cadencia de melhoria continua sem sobrecarregar squads.

#### F-10 Fundacao Frontend FSD e UI Compartilhada
- Resolvido: Design system base sera Tailwind CSS com componentes proprietarios conforme blueprint; tokens multi-tenant devem derivar desta fundacao.

#### F-11 Automacao de Seeds, Dados de Teste e Factories
- Resolvido: Seeds sintéticas devem suportar perfis `dev` (100 clientes/200 empréstimos), `staging` (1.000/5.000) e `carga` configurável por ambiente com proteção de RateLimit.

### 5. Riscos & Dependencias

| Feature | Depende de | Comentario |
|---------|------------|------------|
| F-02 | F-01 | Precisa de tenant ativo, RBAC e politica MFA antes de coletar PII |
| F-03 | F-01, F-02, F-10 | Requer dados KYC validados, roles corretas e componentes FSD (`NewLoanWizard`) |
| F-04 | F-03 | Necessita contratos e cronogramas para gerar cobrancas automatizadas |
| F-05 | F-01, F-04 | Depende de isolamento tenant-aware e fluxos de caixa para conciliar despesas |
| F-06 | F-04, F-05 | Usa status de parcelas e eventos financeiros (recebiveis/pagaveis) para trilhas |
| F-07 | F-02 a F-06, F-10 | Dashboards dependem de dados consistentes e alimentacao OTEL proveniente do frontend |
| F-08 | F-01 a F-07 | Trilhas auditam eventos gerados pelas fatias anteriores e politicas de segredo |
| F-09 | F-01 a F-08, F-11 | Observabilidade e GitOps dependem de eventos, seeds realistas e compliance |
| F-10 | F-01 a F-03 | Precisa de APIs versionadas e contratos tipados para estruturar hooks FSD |
| F-11 | F-01 a F-06 (integra com F-09) | Seeds refletem dados de produção, alimentam testes/DR e integram com observabilidade sem depender do go-live de F-09 |

| Risco | Categoria | Impacto | Mitigacao alinhada ao blueprint |
|-------|-----------|---------|--------------------------------|
| RLS mal configurado permitindo vazamento cross-tenant | Reg/Seguranca | Multas LGPD e perda de clientes | Testes automatizados de RBAC (adicoes item 12), auditoria WORM e revisao por TenantOwner (F-01, F-08) |
| Vazamento de PII via serializer/DTO | Seguranca/Compliance | Exposicao de dados sensiveis ao frontend | Lint de DTO, mascaramento automatizado e pactos FE/BE garantindo campos mínimos (F-02, F-10, F-11) |
| Integracao com bureau indisponivel ou cara | Reg/Negocio | Atraso na aprovacao e risco de fraude | Implementar fallback manual com justificativa, monitorar SLA e contrato escalavel (F-03) |
| Falha de conciliacao PIX/Boleto | Financeiro | Fluxo de caixa impreciso | Retentativas Celery com backoff, `acks_late` e alertas FinOps (F-04) |
| Aprovação de despesas sem segregacao adequada | Financeiro/Fiscal | Pagamentos indevidos, risco de fraude e penalidades fiscais | Fluxo em duas etapas (solicitante -> gestor centro de custo -> financeiro), limites por centro de custo e auditoria WORM de aprovadores (F-05) |
| Contato de cobranca em desacordo com LGPD | Reg | Multas e reputacao | Configurar politicas de consentimento, logs auditados e limitadores por canal (F-06) |
| Dashboards sem metas SLO definidas | Operacional | Alertas irrelevantes e decisoes equivocadas | Clarificar Q3, alinhar com catalogo SLO e publicar budgets (F-07, F-09) |
| Quebra de contrato FE/BE por falta de Pact | Arquitetura | Deploys quebrados e regressao no frontend | Pact producer/consumer obrigatório em F-03, F-04, F-05 e F-10 com gate no CI |
| Parallel change incompleto em migrações | Operacional | Inconsistência de dados e downtime | Seguir padrão expand/backfill/contract com `CREATE INDEX CONCURRENTLY` e ensaios de DR (F-04, F-05, F-11) |
| Pipelines sem gates de seguranca | Tec | Bugs graves em prod | Exigir SAST/DAST/SCA, SBOM, OpenAPI diff e pactos (F-09) |
| Supply chain sem assinatura/proveniência | Segurança | Artefatos adulterados indo para produção | Assinar/verificar imagens com cosign/SLSA no pipeline (F-09) |
| Configuração inadequada de Vault/Argo/Terraform | Operacional/Segurança | Vazamento de segredos ou indisponibilidade | Policy-as-Code (OPA), peer-review e testes em staging antes de produção (F-08, F-09) |
| Drift de conformidade (PII sem pgcrypto/RLS) | Compliance | Quebra de requisitos LGPD e auditoria | Gates automáticos no CI para detectar campos PII sem criptografia e ausência de testes de isolamento (F-01, F-08) |
| Performance degradada em larga escala | Performance | Consultas lentas e degradação de UX | Revisões periódicas de `EXPLAIN ANALYZE`, índices `CONCURRENTLY` e monitoramento de slow queries (F-04, F-07, F-09) |
| Custos cloud descontrolados (FinOps) | Financeiro | Estouro de orçamento operacional | Dashboards FinOps por tenant/feature, alertas de 80/100% e revisões trimestrais (F-07, F-09) |
| PII em URLs/telemetria frontend | Segurança/Privacidade | Vazamento de dados sensíveis | Lint de rotas, processadores OTEL de redaction e testes automatizados no frontend (F-10) |

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- SC-001: 95% dos tenants concluem onboarding (F-01) em ate 2 horas com RBAC auditado.
- SC-002: 98% dos cadastros KYC (F-02) passam na primeira submissao; erros sao tratados em ate 1 dia util.
- SC-003: 90% dos emprestimos aprovados (F-03) exibem CET/IOF corretos e documentados, com taxa de arrependimento < 5%.
- SC-004: Taxa de adimplencia automatica (F-04) >= 92% em 60 dias, com conciliacao idempotente registrada.
- SC-005: 95% das despesas aprovadas (F-05) seguem fluxo em duas etapas (solicitante -> gestor centro de custo -> financeiro) em ate 2 dias uteis, com zero ocorrencias de aprovacao fora de politica.
- SC-006: Inadimplencia >30 dias (F-06) reduzida em 20% apos 3 ciclos, com renegociacoes documentadas.
- SC-007: Dashboards executivos (F-07) apresentam p95 de API atualizado e error budget em tempo real para 100% dos tenants ativos.
- SC-008: 100% das solicitacoes LGPD (F-08) atendidas em ate 30 dias com evidencia WORM.
- SC-009: MTTR mediano (F-09) <= 1h e lead time de deploy <= 1 dia, monitorados por DORA.
- SC-010: Custos combinados de recebiveis e despesas (F-04, F-05) mantidos dentro de +/-10% do budget trimestral FinOps.
- SC-011: Fundacao FSD (F-10) reduz tempo de bootstrap de nova feature para <= 30 minutos e mantém regressão visual < 0.1% em builds Chromatic.
- SC-012: Seeds automatizadas (F-11) executam em < 5 minutos, com coverage de cenarios críticos >= 95% e zero vazamento de PII real em ambientes compartilhados.

### 6. Plano de Execucao Anotado

- Passo 0 (Fundacao Técnica): Entregar F-10 (scaffolding FSD) e F-11 (seeds/factories) antes das demais features para suportar TDD, UI compartilhada e observabilidade.
- Passo 1 (MVP Core): Executar F-01 -> F-02 -> F-03 garantindo base multi-tenant, dados KYC e originacao regulatoria. Cada feature deve seguir o handshake `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks`.
- Passo 2 (Fluxo Financeiro MVP): Implementar F-04, F-05 e F-06 em paralelo controlado, pois compartilham agenda de parcelas, despesas e cobrancas. Integracao com gateway Asaas priorizada; aplicar fluxo de aprovacao em duas etapas ja validado.
- Passo 3 (Compliance MVP): Entregar F-08 em paralelo ao Passo 2 para garantir cobertura LGPD e auditoria antes do go-live.
- Passo 4 (Incremento v1.1): Planejar F-07 apos consolidar dados transacionais (incluindo telemetria do frontend via F-10) usando SLOs definidos (p95 600 ms, p99 1 s, MTTR 1 h, erro <1%); alimenta visao executiva.
- Passo 5 (Incremento v2.0): Tratar F-09 para elevar maturidade SRE, incorporando GameDays bimestrais, Renovate e GitOps (Argo CD).
- MVP declarado: F-10, F-11, F-01, F-02, F-03, F-04, F-05, F-06 e F-08 concluidos e validados. Incremento v1.1: F-07. Incremento v2.0: F-09.
- Reforcar handshake Spec-Kit por feature antes de evoluir para `/speckit.plan` e `/speckit.tasks`, garantindo checklist completo e clarificacoes respondidas.

## Outstanding Questions & Clarifications
Nenhuma pendência aberta; referências consolidadas na seção `## Clarifications`.
