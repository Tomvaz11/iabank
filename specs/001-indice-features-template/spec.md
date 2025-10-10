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
| F-01 | Governanca de Tenants e RBAC Zero-Trust | Gestor/Administrador do tenant | Onboarding seguro e isolamento de dados habilitando monetizacao multi-tenant | Reg alto (LGPD, RLS) | Modelos core (`Tenant`, `User`), PostgreSQL RLS, política MFA (Blueprint §19) | MVP | Garante baseline de permissoes, MFA mandatório e auditoria para todas as demais fatias |
| F-02 | Cadastro e KYC de Clientes e Consultores | Consultor de credito / Backoffice | Qualidade de dados e conformidade KYC para pipeline de emprestimos | Reg alto (LGPD, KYC) | F-01, `customers` e `operations` DTOs, contratos Pact `/api/v1` | MVP | Exige coleta segura de PII, controle de concorrencia otimista e sincronizacao com auditoria |
| F-03 | Originacao de Emprestimo com Score e CET/IOF | Consultor de credito | Contratos conformes (CET, IOF) e aprovacao assistida por score externo | Reg alto (Banco Central) | F-01, F-02, F-10, `LoanCreateDTO`, integrações externas (bureau, Pact) | MVP | [NEEDS CLARIFICATION: Q1 - Bureau de credito prioritario (SPC, Serasa, outro)? Impacta contratos e integracao.] |
| F-04 | Gestao de Parcelas e Recebimentos Automatizados | Gestor financeiro | Liquidez previsivel via agendas, cobranca PIX/Boleto e conciliacao | Reg alto (pagamentos) | F-03, modelos `Installment`/`FinancialTransaction`, Celery resiliente (acks_late), rate limiting | MVP | [NEEDS CLARIFICATION: Q2 - Gateway PIX/Boleto preferido? Impacta SLA, certificacoes e roadmap financeiro.] |
| F-05 | Gestao de Contas a Pagar e Despesas Operacionais | Gestor financeiro / Backoffice | Controle de caixa de saida, compliance fiscal e previsibilidade de despesas | Reg medio (fiscal/FinOps) | F-01, F-04, modelos `finance`, índices multi-tenant (Blueprint §6.3) | MVP | Requer politica de aprovacao e integracao banco-fornecedor (ver Q9) |
| F-06 | Cobranca, Renegociacao e Pipeline de Inadimplencia | Consultor/Cobrador | Reduz churn e inadimplencia com trilhas multi-canal e renegociacao | Reg medio (LGPD contato) | F-04, F-05, runbooks de cobranca, Celery (acks_late), pactos API | MVP | Necessita auditoria de interacoes, limites LGPD e politicas de contato transparente |
| F-07 | Painel Executivo de Performance e Telemetria SLO | Gestor executivo | Visibilidade de KPIs (CET, inadimplencia, DORA, SLO) para decisoes rapidas | Tec alto (observabilidade, dados) | F-02 a F-06, catálogo SLO, Data Mart, OTEL padronizado | v1.1 | [NEEDS CLARIFICATION: Q3 - Metas iniciais de SLO (p95 API, MTTR) para dashboards? Necessario calibrar alertas e budgets.] |
| F-08 | Conformidade LGPD e Trilhas de Auditoria Imutaveis | Auditor/Compliance Officer | Evidencias LGPD (RIPD/ROPA), WORM e direito ao esquecimento auditavel | Reg critico (LGPD, auditoria) | F-01, F-02, F-04, F-05, `django-simple-history`, Object Lock, Vault/KMS | MVP | Inclui automatizacao de artefatos LGPD, rotação de segredos e rastreabilidade cruzada |
| F-09 | Observabilidade, Resiliencia e Gestao de Incidentes | SRE/Platform | Garantia de estabilidade (SLO, error budget, Chaos/GameDay) | Tec alto (SRE) | F-01 a F-08, pipelines CI/CD, OTEL, Argo CD (GitOps), Renovate | v2.0 | Sustenta operacao contendo DORA, testes de carga, feature flags e playbooks |
| F-10 | Fundacao Frontend FSD e UI Compartilhada | Tech Lead Frontend / Squad UI | Base consistente FSD (features/entities/shared) habilitando entrega vertical rápida e segura | Tec alto (frontend) | Blueprint §4, design system baseline, Pact FE/BE, Storybook/Chromatic | MVP | Garante scaffolding inicial da SPA, contratos de UI e telemetria client-side |
| F-11 | Automacao de Seeds, Dados de Teste e Factories | QA / Engenharia de Plataforma | Dados confiaveis para TDD/integração e ambientes realistas com isolamento multi-tenant | Tec medio (TestOps) | Art. III/IV, factory-boy, comandos `seed_data`, pipelines CI, Argo CD | MVP | Mantém suites TDD verdes, executa load seeds em ambientes e reforça DR rehearsals |

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
- INVEST: I Pass; N Pass (foco em operacao); V Pass (error budget e MTTR); E Falha (depende de features transacionais e compliance F-08 para logs mascarados); S Pass (exigencia SRE); T Pass (criterios de monitoracao e GameDay).
- DoR: Persona Pass; Objetivo Pass (estabilidade); Valor Pass (reduz downtime); Restricoes Pass (OpenTelemetry, budgets, DORA); Dependencias Falha (precisa de dados instrumentados e dashboards); Metrica Pass (MTTR <= metas).
- Story Map: Camada "Operar & Evoluir" sustentando roadmap continuo.

> Detalhamento completo (contexto, cenarios BDD e prompt) na seção 3.

### User Story 10 - Fundacao Frontend FSD e UI Compartilhada (F-10)

- Alinhamento Spec-Kit: OK - estabelece base tecnica indispensavel para features verticais de UI (Blueprint §4).
- INVEST: I Pass; N Pass (escopo restrito a fundacao); V Pass (reduz lead time de novas telas); E Pass (contratos claros entre camadas FSD); S Pass (governanca de UX, acessibilidade); T Pass (lint, Storybook/Chromatic, Pact FE/BE).
- DoR: Persona Pass (Tech Lead Frontend); Objetivo Pass (scaffolding da SPA); Valor Pass (padroniza entrega); Restricoes Pass (OTEL client-side, design tokens); Dependencias Pass (repositorio, pipeline CI); Metrica Pass (tempo de bootstrap <= 30 min, cobertura visual >= 90%).
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
- Cenario 2: Dado um gestor ajustando RBAC, quando habilita ou revoga escopos nas roles padrao, entao a mudanca respeita controle de concorrencia via `ETag`/`If-Match`, e e versionada via `django-simple-history` com hash de integridade e replicada ao front (FSD) sem conceder acesso cross-tenant.
- Cenario 3: Dado um usuario sem permissao adequada, quando tenta acessar recurso de outro tenant, entao recebe 403 padronizado (RFC 9457) e o evento e logado com mascaramento de PII.
- Cenario 4: Dado um tenant inativo, quando qualquer solicitacao de API chega, entao o middleware tenant-aware bloqueia e registra audit trail conforme Art. XI.
- Cenario 5: Dado onboarding de tenant, quando o fluxo encerra, entao o tempo total e exibido no painel de execucao e triggers de compliance (RIPD, ROPA) sao inicializados automaticamente.
- Cenario 6: Dado revisao trimestral, quando auditor solicita evidencias de RBAC, entao exportacao consolidada das roles e logs e gerada com Object Lock.
- Cenario 7: Dado um TenantOwner autenticado com MFA TOTP, quando acessa os endpoints `/api/v1/tenants/` e `/api/v1/roles/`, entao a API exige prefixo de versao, valida o segundo fator e retorna Problem Details (RFC 9457) adequados para erros de autenticacao.
Prompt `/speckit.specify`:
```text
F-01 Governanca de Tenants e RBAC Zero-Trust. Use BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.2 e adicoes_blueprint.md itens 4,5,12,13. Produza a especificacao seguindo o template oficial (contexto, historias, requisitos, metricas, riscos) sem definir stack adicional. Garanta RLS, RBAC, MFA obrigatoria, auditoria WORM, controle de concorrencia com `ETag`/`If-Match`, versionamento `/api/v1` e Problem Details (RFC 9457), alinhado aos Arts. III, V, IX, XIII. Marque duvidas criticas com [NEEDS CLARIFICATION] e inclua BDD para ativacao de tenant, bloqueio cross-tenant, versionamento de roles, MFA e logs S3 Object Lock.
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
- Cenario 8: Dado consumidor utilizando a API REST, quando realiza requisicoes aos recursos `/api/v1/customers/` e `/api/v1/consultants/`, entao os headers `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` e `Retry-After` sao retornados e validados no limite de tenant.
Prompt `/speckit.specify`:
```text
F-02 Cadastro e KYC de Clientes e Consultores. Referencie BLUEPRINT_ARQUITETURAL.md §§2,3.1,3.2 e adicoes_blueprint.md itens 4,5,7,13. Gere especificacao completa (template Spec-Kit) focada em captura de PII, validacao KYC, consentimentos LGPD e integracao com trilha de auditoria. Proiba decisoes de implementacao, detalhe historias para cadastro manual, importacao em massa e direito ao esquecimento. Exija controle de concorrencia (`ETag`/`If-Match` + `428`), headers de rate limiting, versionamento `/api/v1`, Pact producer/consumer e metricas de qualidade de dados. Mantenha [NEEDS CLARIFICATION] para politicas pendentes.
```

#### F-03 Originacao de Emprestimo com Score e CET/IOF
Contexto: Viabiliza simulacao, analise e aprovacao de emprestimos com calculo CET/IOF, verificacoes de Lei da Usura e consulta a bureau externo (`LoanCreateDTO`, wizard `NewLoanWizard`).
Acceptance criteria:
- Cenario 1: Dado um consultor com cliente elegivel, quando executa simulacao preenchendo montante, taxa e parcelas, entao o sistema calcula CET mensal/anual, IOF e exibe detalhes antes da aprovacao.
- Cenario 2: Dado integracao com bureau disponivel, quando solicitada analise, entao a resposta (score, flags) e anexada ao processo e armazenada com idempotency-key e timeout controlado.
- Cenario 3: Dado juros acima do limite legal, quando simulacao ocorre, entao o sistema bloqueia aprovacao e fornece mensagem com referencias legais (Lei da Usura).
- Cenario 4: Dado direito de arrependimento em ate 7 dias, quando pedido e registrado, entao o contrato muda para status `CANCELED`, parcelas sao anuladas e auditoria registra motivo.
- Cenario 5: Dado falha no bureau, quando o consultor tenta reprocessar, entao o sistema usa retry com backoff exponencial e permite fallback manual com justificativa.
- Cenario 6: Dado consultor tenta emitir contrato sem consentimento LGPD, quando fluxo avanca, entao e bloqueado ate consentimento ser registrado.
- Cenario 7: Dado `NewLoanWizard` no frontend, quando a jornada e carregada, entao os componentes seguem o padrão FSD (camadas `features/loan-origination`, `entities/customer`, `shared/ui`) com gerenciamento de estado definido e telemetria OTEL configurada.
- Cenario 8: Dado requisicao REST para `/api/v1/loans/`, quando simulacao ou aprovacao e executada, entao a API responde com `RateLimit-*` headers, `Retry-After` quando aplicavel e Problem Details padronizados para erros de negocio.
- Cenario 9: Dado pipeline CI em execucao, quando contrato Pact com o bureau e atualizado, entao o job valida compatibilidade producer/consumer e bloqueia merge em caso de quebra.
Prompt `/speckit.specify`:
```text
F-03 Originacao de Emprestimo com Score e CET/IOF. Utilize BLUEPRINT_ARQUITETURAL.md §§2,3.1.1,3.2 e adicoes_blueprint.md itens 1,4,7. Escreva especificacao orientada ao usuario cobrindo simulacao, consulta a bureau (Q1 em aberto), calculos CET/IOF e processo de arrependimento. Proiba escolhas de stack; detalhe requisitos regulatorios, estrutura frontend FSD (`features`/`entities`/`shared`), versionamento `/api/v1`, RateLimit headers, Pact para integrações externas e tratativas de falhas (circuit breaker, backoff, fallback manual). Preserve [NEEDS CLARIFICATION: Q1].
```

#### F-04 Gestao de Parcelas e Recebimentos Automatizados
Contexto: Automatiza agenda de parcelas, integracao com gateway PIX/Boleto, conciliacao financeira (`FinancialTransaction`, Celery) e falhas tolerantes (`adicoes` itens 7,8).
Acceptance criteria:
- Cenario 1: Dado emprestimo aprovado, quando primeiro cronograma e gerado, entao parcelas recebem status inicial, datas e valores com CET aplicado e RLS garantido.
- Cenario 2: Dado integracao PIX/Boleto, quando cobranca e emitida, entao o sistema gera QR-code ou boleto com `Idempotency-Key`, registra evento e atualiza status apos conciliacao automatica.
- Cenario 3: Dado pagamento recebido, quando gateway envia webhook, entao conciliacao usa `retry_backoff` em Celery com `acks_late=True`, atualiza `FinancialTransaction` e `Installment` de forma idempotente e registra o `Idempotency-Key` resolvido.
- Cenario 4: Dado limite de rate limiting do gateway, quando excedido, entao o sistema respeita `429` com `Retry-After`, retorna `RateLimit-Limit/Remaining/Reset` por tenant e reprograma tarefa mantendo orcamento de erro.
- Cenario 5: Dado falha de conciliacao, quando tentativa falha 3 vezes, entao tarefa migra para DLQ com contexto completo para analise manual.
- Cenario 6: Dado tenant com auditoria ativa, quando parcelas sao liquidadas, entao logs exportam eventos para WORM e dashboard financeiro.
- Cenario 7: Dado uma parcela sendo atualizada via API, quando requisicao inclui `If-Match` coerente com o `ETag`, entao a atualizacao e aplicada; quando o cabecalho falta ou diverge, entao retorna `428` com Problem Details.
- Cenario 8: Dado pipeline CI, quando PR altera payload de webhook ou rota `/api/v1/installments`, entao os contratos Pact producer/consumer sao validados antes do merge.
Prompt `/speckit.specify`:
```text
F-04 Gestao de Parcelas e Recebimentos Automatizados. Referencie BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.1,26 e adicoes_blueprint.md itens 3,7,8. Produza especificacao que cubra schedule de parcelas, integracao com gateway (Q2), conciliacao idempotente, `acks_late`, controle de concorrencia (`ETag`/`If-Match`), versionamento `/api/v1`, RateLimit headers e tratamento de erros conforme RFC 9457. Inclua criterios de sucesso para taxas de adimplencia, DLQ, Pact de webhooks e rotinas de FinOps. Mantenha [NEEDS CLARIFICATION: Q2].
```

#### F-05 Gestao de Contas a Pagar e Despesas Operacionais
Contexto: Orquestra cadastros de fornecedores, contas bancarias, centros de custo e registro de despesas (tipo `EXPENSE`), vinculando comprovantes e aprovacoes antes de efetivar pagamentos.
Acceptance criteria:
- Cenario 1: Dado um gestor financeiro, quando cadastra fornecedor com CNPJ unico por tenant, entao o sistema valida documento, vincula categoria/cost center e gera log de auditoria.
- Cenario 2: Dado uma despesa recorrente, quando agendamento e criado, entao `FinancialTransaction` registra status `PENDING`, associa `BankAccount` correto e agenda tarefa Celery para lembrete de pagamento.
- Cenario 3: Dado um fluxo de aprovacao em duas etapas, quando um operador solicita pagamento acima do limite definido, entao o sistema exige aprovacao de Gestor, registra justificativa e bloqueia execucao ate confirmacao.
- Cenario 4: Dado comprovante anexado, quando despesa e marcada como paga, entao evidencias (arquivo + hash) sao vinculadas ao audit trail e dados sensiveis sao mascarados nos logs.
- Cenario 5: Dado limite orcamentario de centro de custo, quando nova despesa excede headroom, entao alerta e enviado ao painel FinOps e a aprovacao exige justificativa extra.
- Cenario 6: Dado integracao com instalmento de emprestimo (comissao de consultor), quando despesa referenciada e liquidada, entao `Installment.payments` recebe referencia e conciliacao e atualizada.
- Cenario 7: Dado uma requisicao de atualizacao de despesa via `/api/v1/payables/<id>`, quando o cliente envia `If-Match` coerente com o `ETag`, entao a alteracao e persistida; quando o cabecalho esta ausente ou incorreto, o sistema responde `428` com Problem Details e nao persiste a mudanca.
- Cenario 8: Dado job de migracao, quando comandos de monitoramento rodam, entao garantem que indices compostos com `tenant_id` estejam ativos (`tenant, supplier`, `tenant, cost_center`) usando `CREATE INDEX CONCURRENTLY` quando necessario.
- Cenario 9: Dado consumo da API `/api/v1/payables/`, quando o limite de requisicoes por tenant e aproximado, entao os headers `RateLimit-*` refletem o consumo e `Retry-After` orienta retentativas.
Prompt `/speckit.specify`:
```text
F-05 Gestao de Contas a Pagar e Despesas Operacionais. Utilize BLUEPRINT_ARQUITETURAL.md §§3.1,6.1,6.3 e adicoes_blueprint.md itens 3,8,11. Gere especificacao cobrindo cadastro de fornecedores/contas bancarias, politicas de aprovacao, controle de centros de custo e auditoria fiscal. Proiba decisoes de stack; inclua historias para despesas recorrentes, aprovacao em niveis, anexos de comprovantes e alertas de budget. Exija versionamento `/api/v1`, controle de concorrencia (`ETag`/`If-Match`), RateLimit por tenant, indices multi-tenant e Pact FE/BE. Registre assuncao ate definirmos Q9 (politica de aprovacao).
```

#### F-06 Cobranca, Renegociacao e Pipeline de Inadimplencia
Contexto: Garante trilhas de cobranca multicanal, esteiras de renegociacao e governance de contato alinhada a LGPD e runbooks de cobranca (`docs/runbooks/governanca-api.md`).
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
F-06 Cobranca, Renegociacao e Pipeline de Inadimplencia. Use BLUEPRINT_ARQUITETURAL.md §§3.1,6.2,26 e adicoes_blueprint.md itens 2,3,8,10. Especifique jornadas de cobranca, renegociacao e exports auditaveis, sem definir stack. Inclua ACs para limites LGPD, DLQ, fallback manual, Pact producer/consumer, `acks_late`, RateLimit por tenant, controle de concorrencia (`ETag`/`If-Match`), versionamento `/api/v1` e alinhamento com runbooks.
```

#### F-07 Painel Executivo de Performance e Telemetria SLO
Contexto: Fornece dashboards executivos com KPIs de credito (CET medio, inadimplencia), SLOs (latencia p95/p99, erro) e metricas DORA (`docs/slo/catalogo-slo.md`, adicoes itens 1,2,11).
Acceptance criteria:
- Cenario 1: Dado dados de emprestimos ativos, quando painel carrega, entao apresenta CET medio, carteira por status e aging com filtros por tenant.
- Cenario 2: Dado pipelines OTEL configurados, quando eventos de API chegam, entao dashboards exibem p95/p99 e consumo de error budget em tempo quase real.
- Cenario 3: Dado deploy em producao, quando pipeline CI roda, entao DORA lead time e taxa de falha atualizam automaticamente.
- Cenario 4: Dado incidentes, quando MTTR excede budget, entao painel destaca alerta e sugere GameDay conforme adicoes item 10.
- Cenario 5: Dado FinOps, quando custo excede orcamento, entao painel exibe variacao versus budget com tags de custo.
- Cenario 6: Dado inexistencia de metas SLO definidas, quando feature tenta publicar dashboards, entao processo bloqueia ate resposta da Q3.
Prompt `/speckit.specify`:
```text
F-07 Painel Executivo de Performance e Telemetria SLO. Referencie BLUEPRINT_ARQUITETURAL.md §§2,6.3, docs/slo/catalogo-slo.md e adicoes_blueprint.md itens 1,2,11. Elabore especificacao descrevendo dashboards, integrações OTEL, DORA e FinOps, sem decidir stack. Destaque dependencia de dados consolidados, integrações com a fundação FSD (F-10) e mantenha [NEEDS CLARIFICATION: Q3] para metas SLO iniciais. Inclua criterios para atualizar automaticamente error budgets e acionamentos.
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
Prompt `/speckit.specify`:
```text
F-08 Conformidade LGPD e Trilhas de Auditoria Imutaveis. Utilize BLUEPRINT_ARQUITETURAL.md §§6.2,27 e adicoes_blueprint.md itens 4,5,6,12. Escreva especificacao cobrindo RLS, direito ao esquecimento, export LGPD, SBOM, trilhas WORM, rotacao automática de segredos (Vault/KMS) e pseudonimizacao segura. Proiba decisoes de stack adicionais e exija historias para auditoria, export, exclusao, reconciliacao contábil e DR. Mantenha alinhamento com Art. XIII e ADR-010.
```

#### F-09 Observabilidade, Resiliencia e Gestao de Incidentes
Contexto: Reforca SRE com pipelines OTEL, limites de fila, testes de carga (k6), feature flags, GameDays e runbooks (adicoes itens 1,2,3,8,10).
Acceptance criteria:
- Cenario 1: Dado deploy em producao, quando pipelines CI executam, entao stages de SAST/DAST/SCA, SBOM, performance (k6), OpenAPI lint/diff e Pact producer/consumer precisam passar antes do release.
- Cenario 2: Dado evento de saturacao, quando metricas excedem limiar, entao autoscaling dispara com base em SLO definido e notifica error budget policy.
- Cenario 3: Dado incidente simulado em GameDay, quando tarefas sao executadas, entao runbook e atualizado com achados e MTTR registrado.
- Cenario 4: Dado feature flag critica, quando toggled, entao logs auditados mostram autor, justificativa e rollback path.
- Cenario 5: Dado fila Celery atinge limite, quando backlog supera threshold, entao alerta e gerado e tasks non-critical sao rebaixadas conforme politica.
- Cenario 6: Dado integracao externa indisponivel, quando circuito abre, entao fallback degrade graciosamente e orcamento de erro reduzido e recalculado.
- Cenario 7: Dado job programado do Renovate ou sync do Argo CD, quando novas dependencias ou manifests sao aplicados, entao o fluxo GitOps registra a mudanca, executa politicas OPA e bloqueia divergencias.
Prompt `/speckit.specify`:
```text
F-09 Observabilidade, Resiliencia e Gestao de Incidentes. Referencie BLUEPRINT_ARQUITETURAL.md §§6,26,27 e adicoes_blueprint.md itens 1,2,3,8,9,10,14, alem dos ADRs 008 e 009. Gere especificacao cobrindo pipelines CI/CD, SLOs, error budgets, chaos, feature flags, GitOps (Argo CD) e Renovate. Sem decisoes de stack; detalhe metricas de saturacao, thresholds k6, planos de DR, politicas de escalonamento e gates de OpenAPI diff/Pact. Marque dependencias das fatias de negocio e mantenha perguntas abertas conforme necessario.
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
Prompt `/speckit.specify`:
```text
F-10 Fundacao Frontend FSD e UI Compartilhada. Referencie BLUEPRINT_ARQUITETURAL.md §4, docs de design system internos e adicoes_blueprint.md itens 1,2,13. Produza especificacao detalhando scaffolding FSD, Storybook/Chromatic, integrações com TanStack Query/Zustand, propagacao de OTEL no cliente, pactos FE/BE e critérios de acessibilidade. Evite definir libs alem das padronizadas; inclua métricas de cobertura visual, lint FSD e governança de imports.
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
Prompt `/speckit.specify`:
```text
F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`.
```

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do código cobrindo fluxos felizes/tristes | ACs BDD em F-01 a F-11, seeds automatizadas (F-11) e lint FSD (F-10) reforçam TDD |
| Art. V (Documentação & Versionamento) | API versionada (`/api/v1`) e contratos atualizados | Prompts de F-01 a F-06 e F-10 exigem prefixo de versão, Problem Details e sync OpenAPI |
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
| Runbooks, DR, GameDays | Ensaios de DR e incidentes | F-06, F-09 e F-11 vinculam runbooks, DR piloto light e exercícios periódicos |

### Functional Requirements

- FR-001: O sistema deve permitir cadastro e ativacao de tenants com RLS aplicado automaticamente em todos os modelos que herdam `BaseTenantModel`.
- FR-002: Processos de KYC devem validar CPF/CNPJ por tenant, armazenar consentimentos LGPD e disponibilizar exportacoes anonimizadas.
- FR-003: A originacao de emprestimos deve calcular CET e IOF conforme regulacao, registrar interacoes com bureau externo e bloquear juros acima do limite legal.
- FR-004: A gestao de parcelas deve gerar agendas com status rastreados, emitir cobrancas PIX/Boleto com `Idempotency-Key` e conciliar pagamentos via webhooks idempotentes.
- FR-005: O modulo financeiro deve controlar contas a pagar, fornecedores e centros de custo com aprovacao multinivel, anexos auditaveis e integracao com contas bancarias.
- FR-006: A pipeline de cobranca deve automatizar notificacoes, renegociacoes e escalonamentos com logs auditaveis e limites de contato configuraveis.
- FR-007: Dashboards executivos devem consolidar KPIs de carteira, SLOs e DORA com filtros por tenant e alertas de budget.
- FR-008: Trilhas de auditoria devem armazenar alteracoes em WORM com integridade verificavel e suportar direito ao esquecimento sem vazamento de PII.
- FR-009: Pipelines de operacao devem executar gates de CI (SAST/DAST/SCA, SBOM, k6) e acionar runbooks e feature flags conforme politicas definidas.
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

### Dados Sensiveis & Compliance

Campos PII (CPF, RG, endereco, telefone, contas bancarias) devem ser criptografados com pgcrypto no Postgres, mascarados em logs e removidos de exports nao auditados. Serializadores/DTOs devem aplicar minimizacao de dados e validacoes automatizadas (lint no CI) para impedir vazamentos para o frontend (ADR-010). Politicas de retencao seguem LGPD: dados de clientes ativos retidos por 5 anos apos quitacao, com suporte a direito ao esquecimento em ate 30 dias. Evidencias necessarias: RIPD/DPIA por feature, ROPA atualizado por tenant, Object Lock configurado para auditoria, provas de mascaramento em pipelines de observabilidade e auditorias de anonimização pós-exclusão.

### 4. Duvidas para `/speckit.clarify` (por feature)

#### F-01 Governanca de Tenants e RBAC Zero-Trust
- Q4: Qual estrategia de autenticao multi-fator deve ser adotada para TenantOwner? Opcoes: A) TOTP integrado; B) SSO corporativo; C) Email OTP com limite. Impacto: controles Art. V e risco de takeover.

#### F-02 Cadastro e KYC de Clientes e Consultores
- Q5: Quais provedores de validacao documental devem ser suportados no MVP? Opcoes: A) Upload manual com auditoria; B) API automatizada (ex: Serpro); C) Hibrido.

#### F-03 Originacao de Emprestimo com Score e CET/IOF
- Q1: Qual bureau de credito deve ser integrado primeiro (SPC Brasil, Serasa Experian, outro)? Impacto direto em contratos, custo e SLA de aprovacao.

#### F-04 Gestao de Parcelas e Recebimentos Automatizados
- Q2: Qual gateway PIX/Boleto deve ser priorizado (Banco Parceiro atual, Gateway SaaS, Engenharia proprietaria)? Impacta homologacoes, custos e roadmap.

#### F-05 Gestao de Contas a Pagar e Despesas Operacionais
- Q9: Qual politica de aprovacao de despesas deve reger o MVP? Opcoes: A) Aprovação unica ate limite definido; B) Fluxo em duas etapas (operador → gestor); C) Configuravel por centro de custo. Impacto em segregacao de funcoes, riscos fiscais e velocidade de pagamento.

#### F-06 Cobranca, Renegociacao e Pipeline de Inadimplencia
- Q6: Qual canal deve ser considerado prioritario para cobranca ativa? Opcoes: A) WhatsApp Business API; B) Email + SMS; C) Discador humano. Impacto em compliance LGPD e produtividade.

#### F-07 Painel Executivo de Performance e Telemetria SLO
- Q3: Quais metas SLO iniciais (latencia p95/p99, MTTR, taxa de erro) devem ser adotadas por produto? Necessario para calibrar alertas e error budget policy.

#### F-08 Conformidade LGPD e Trilhas de Auditoria Imutaveis
- Q7: Qual politica de retencao minima deve ser aplicada a trilhas WORM alem dos 30 dias legais? Opcoes: A) 1 ano; B) 5 anos; C) 10 anos, com custo associado.

#### F-09 Observabilidade, Resiliencia e Gestao de Incidentes
- Q8: Com que frequencia os GameDays devem ocorrer no MVP? Opcoes: A) Trimestral; B) Bimestral; C) Mensal. Impacta capacidade da equipe e maturidade SRE.

#### F-10 Fundacao Frontend FSD e UI Compartilhada
- Q10: Qual referencial de design system deve ser adotado inicialmente? Opcoes: A) Biblioteca proprietaria (tokens customizados); B) Material-UI (com theming multi-tenant); C) Tailwind + componentes proprietarios. Impacta acessibilidade, velocidade e lock-in.

#### F-11 Automacao de Seeds, Dados de Teste e Factories
- Q11: Qual volumetria alvo de dados sintéticos por tenant deve ser suportada no seed inicial? Opcoes: A) 100 clientes/200 emprestimos; B) 1k clientes/5k emprestimos; C) Configurável por ambiente. Impacta tempo de seed, custos e testes de carga.

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
| F-11 | F-01 a F-06, F-09 | Seeds refletem dados de produção e suportam pipelines CI/CD e DR |

| Risco | Categoria | Impacto | Mitigacao alinhada ao blueprint |
|-------|-----------|---------|--------------------------------|
| RLS mal configurado permitindo vazamento cross-tenant | Reg/Seguranca | Multas LGPD e perda de clientes | Testes automatizados de RBAC (adicoes item 12), auditoria WORM e revisao por TenantOwner (F-01, F-08) |
| Vazamento de PII via serializer/DTO | Seguranca/Compliance | Exposicao de dados sensiveis ao frontend | Lint de DTO, mascaramento automatizado e pactos FE/BE garantindo campos mínimos (F-02, F-10, F-11) |
| Integracao com bureau indisponivel ou cara | Reg/Negocio | Atraso na aprovacao e risco de fraude | Implementar fallback manual com justificativa, monitorar SLA e contrato escalavel (F-03) |
| Falha de conciliacao PIX/Boleto | Financeiro | Fluxo de caixa impreciso | Retentativas Celery com backoff, `acks_late` e alertas FinOps (F-04) |
| Aprovação de despesas sem segregacao adequada | Financeiro/Fiscal | Pagamentos indevidos, risco de fraude e penalidades fiscais | Fluxo multi-nivel configuravel, limites por centro de custo e auditoria WORM de aprovadores (F-05) |
| Contato de cobranca em desacordo com LGPD | Reg | Multas e reputacao | Configurar politicas de consentimento, logs auditados e limitadores por canal (F-06) |
| Dashboards sem metas SLO definidas | Operacional | Alertas irrelevantes e decisoes equivocadas | Clarificar Q3, alinhar com catalogo SLO e publicar budgets (F-07, F-09) |
| Quebra de contrato FE/BE por falta de Pact | Arquitetura | Deploys quebrados e regressao no frontend | Pact producer/consumer obrigatório em F-03, F-04, F-05 e F-10 com gate no CI |
| Parallel change incompleto em migrações | Operacional | Inconsistência de dados e downtime | Seguir padrão expand/backfill/contract com `CREATE INDEX CONCURRENTLY` e ensaios de DR (F-04, F-05, F-11) |
| Pipelines sem gates de seguranca | Tec | Bugs graves em prod | Exigir SAST/DAST/SCA, SBOM, OpenAPI diff e pactos (F-09) |

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- SC-001: 95% dos tenants concluem onboarding (F-01) em ate 2 horas com RBAC auditado.
- SC-002: 98% dos cadastros KYC (F-02) passam na primeira submissao; erros sao tratados em ate 1 dia util.
- SC-003: 90% dos emprestimos aprovados (F-03) exibem CET/IOF corretos e documentados, com taxa de arrependimento < 5%.
- SC-004: Taxa de adimplencia automatica (F-04) >= 92% em 60 dias, com conciliacao idempotente registrada.
- SC-005: 95% das despesas aprovadas (F-05) seguem fluxo multinivel em ate 2 dias uteis, com zero ocorrencias de aprovacao fora de politica.
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
- Passo 2 (Fluxo Financeiro MVP): Implementar F-04, F-05 e F-06 em paralelo controlado, pois compartilham agenda de parcelas, despesas e cobrancas. Priorizar integracao com gateway apos resposta da Q2 e alinhar aprovacao de despesas (Q9).
- Passo 3 (Compliance MVP): Entregar F-08 em paralelo ao Passo 2 para garantir cobertura LGPD e auditoria antes do go-live.
- Passo 4 (Incremento v1.1): Planejar F-07 apos consolidar dados transacionais (incluindo telemetria do frontend via F-10); depende das respostas da Q3 para metas SLO e alimenta visao executiva.
- Passo 5 (Incremento v2.0): Tratar F-09 para elevar maturidade SRE, incorporando GameDays, Renovate e GitOps (Argo CD).
- MVP declarado: F-10, F-11, F-01, F-02, F-03, F-04, F-05, F-06 e F-08 concluidos e validados. Incremento v1.1: F-07. Incremento v2.0: F-09.
- Reforcar handshake Spec-Kit por feature antes de evoluir para `/speckit.plan` e `/speckit.tasks`, garantindo checklist completo e clarificacoes respondidas.

## Outstanding Questions & Clarifications

- [NEEDS CLARIFICATION: Q1 - Qual bureau de credito (SPC, Serasa ou outro) deve ser integrado no MVP da originacao? Impacta contratos, custo e cronograma (F-03).]
- [NEEDS CLARIFICATION: Q2 - Qual gateway PIX/Boleto e prioridade para as cobrancas automatizadas? Define homologacoes, SLA e custos recorrentes (F-04).]
- [NEEDS CLARIFICATION: Q3 - Quais metas SLO iniciais (p95, p99, MTTR, taxa de erro) devem alimentar o painel executivo? Necessario para calibrar alertas, error budgets e planos de resposta (F-07, F-09).]
- [NEEDS CLARIFICATION: Q4 - Qual estrategia de MFA deve ser adotada para TenantOwner (TOTP dedicado, SSO corporativo ou Email OTP)? Impacta UX e compliance (F-01).]
- [NEEDS CLARIFICATION: Q5 - Qual provedor de validacao documental KYC deve ser priorizado (upload auditado, API automatizada ou hibrido)? Define custo e SLA (F-02).]
- [NEEDS CLARIFICATION: Q6 - Qual canal principal de cobranca ativa sera adotado (WhatsApp, Email/SMS, Discador)? Altera runbooks e consentimentos (F-06).]
- [NEEDS CLARIFICATION: Q7 - Qual retencao WORM minima deve ser aplicada alem dos 30 dias legais (1, 5 ou 10 anos)? Afeta custos de storage (F-08).]
- [NEEDS CLARIFICATION: Q8 - Qual periodicidade de GameDays (trimestral, bimestral, mensal) sera praticada? Impacta agenda e maturidade SRE (F-09).]
- [NEEDS CLARIFICATION: Q9 - Qual politica de aprovacao de despesas (limite unico, duas etapas, configuravel)? Afeta segregacao de funcoes (F-05).]
- [NEEDS CLARIFICATION: Q10 - Qual design system base deve nortear a fundacao FSD (proprietario, Material-UI, Tailwind custom)? Impacta acessibilidade e velocidade (F-10).]
- [NEEDS CLARIFICATION: Q11 - Qual volumetria alvo de dados sinteticos por tenant deve ser usada nas seeds (100/200, 1k/5k, configuravel)? Impacta tempo de populacao e testes (F-11).]
