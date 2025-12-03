# Feature Specification: Governanca de Tenants e RBAC Zero-Trust

**Feature Branch**: `004-f-01-tenant-rbac-zero-trust`  
**Created**: 2025-11-29  
**Status**: Draft  
**Input**: User description: "F-01 Governanca de Tenants e RBAC Zero-Trust. Use BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.2,19 e adicoes_blueprint.md itens 4,5,12,13. Produza a especificacao seguindo o template oficial (contexto, historias, requisitos, metricas, riscos) sem definir stack adicional. Garanta RLS com `CREATE POLICY` e binding de sessao, RBAC+ABAC com testes automatizados, MFA obrigatoria, auditoria WORM, controle de concorrencia com `ETag`/`If-Match`, versionamento `/api/v1`, refresh tokens seguros (`HttpOnly`/`Secure`/`SameSite=Strict`) e Problem Details (RFC 9457), alinhado aos Arts. III, V, IX, XIII. Marque duvidas criticas com [NEEDS CLARIFICATION] e inclua BDD para ativacao de tenant, bloqueio cross-tenant, versionamento de roles, MFA/refresh seguro, atributos de autorizacao e logs S3 Object Lock, referenciando OpenAPI 3.1 contract-first."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituicao v5.2.0 (Art. I-XVIII) e ADRs aplicaveis. Toda lacuna deve ser marcada com `[NEEDS CLARIFICATION]` e adicionada ao `/clarify`.

## Contexto

Instituicao multi-tenant precisa garantir isolamento zero-trust entre clientes corporativos e unidades internas, assegurando que cada requisição esteja vinculada a um `tenant_id` válido e que decisões de acesso combinem RBAC e atributos (ABAC). O objetivo é ativar e governar tenants com MFA obrigatoria, logs imutaveis (WORM) e auditoria rastreavel, mitigando riscos de vazamento lateral e fraudes. Modelos e managers multi-tenant devem ser fonte única de verdade, injetando `tenant_id` por padrão e com políticas RLS versionadas e testadas. A entrega deve alinhar-se aos Arts. II, III, V, VII, IX, XI, XIII, XIV, XV, XVII e XVIII, usando contratos OpenAPI 3.1 contract-first e Problem Details (RFC 9457) para consistencia e conformidade, e seguir as orientacoes do BLUEPRINT_ARQUITETURAL.md §§2 (arquitetura/monolito modular), 3.1 (SSOT dos modelos com tenant-first), 6.2 (trilha de auditoria) e 19 (estrategia de seguranca), alem dos itens 4, 5, 12 e 13 do `adicoes_blueprint.md` (RLS/query managers, OWASP/NIST/segredos/PII, RBAC/ABAC testado, privacidade no front-end).

## Clarifications

### Session 2025-11-29

- Q: Qual o fator de MFA obrigatório (TOTP, WebAuthn, push) e como tratar exceções para usuários sem dispositivo compatível? → A: MFA TOTP obrigatória; exceções manuais via helpdesk com códigos de recuperação auditados.
- Q: Qual o prazo/regime de retenção de logs WORM e de dados de sessão por tenant, e quando o direito ao esquecimento pode ser aplicado sem violar bloqueios legais? → A: WORM em modo compliance com retenção mínima de 365 dias (extensível por obrigação legal); sessões/refresh expurgados em até 30 dias; direito ao esquecimento após cumprir retenções legais.
- Q: Quais limites de rate limiting e TTL/deduplicação para `Idempotency-Key` por tenant (incluindo tenants de alto risco) e como segmentar quotas entre APIs públicas/privadas? → A: API pública 50 rps/tenant com burst 2x; API privada 200 rps/tenant com burst 2x; `Idempotency-Key` TTL 24h com dedup persistente; tenants de alto risco iniciam com 50% desses limites até revisão.
- Q: Qual o ciclo de vida/estados do tenant e transições permitidas? → A: `Pending -> Active -> Suspended -> Blocked -> Decommissioned`, transições unidirecionais; `Blocked` só retorna via revisão formal; `Decommissioned` apenas após cumprir retenções WORM/LGPD.
- Q: Qual o efeito de cada estado do tenant em sessões/tokens e escopo de acesso? → A: Active normal; Suspended read-only (sem novas mutações nem novos tokens; sessões perdem write); Blocked nega tudo, revoga tokens e pausa jobs/filas; Decommissioned é acesso zero, apenas leitura de WORM por auditoria.

### Session 2025-11-29

- Q: Quais atributos ABAC mínimos são obrigatórios e como permitir customizações por tenant sem perder consistência? → A: Baseline obrigatória com unidade, classificação, região e tipo de recurso; atributos custom só com aprovação de segurança e versionamento de esquema por tenant.
- Q: Qual a fonte canônica de `tenant_id` na requisição e como evitar spoofing/overrides? → A: `X-Tenant-Id` enviado pelo cliente, validado contra claim/session ou HMAC opcional; inconsistências falham fechado com Problem Details e RLS/managers ignoram overrides.
- Q: Como tratar acesso headless (service accounts/client_credentials/API keys) para tenants? → A: Banir service accounts; exigir delegação/impersonação controlada de usuário com MFA ativa e ABAC aplicado.
- Q: Qual a estratégia de identidade/SSO por tenant (IdP externo vs. credenciais locais)? → A: Exigir IdP externo por tenant (OIDC/SAML) com MFA no IdP, SSO obrigatório, JIT/SCIM para provisionamento e break-glass controlado.
- Q: Quais dados mínimos obrigatórios no payload para criação/ativação de um tenant? → A: Nome/slug, domínios permitidos, metadados IdP OIDC/SAML, contatos de segurança/operacionais, classificação de risco/segmento, fuso/região padrão e política de retenção WORM aplicada.

### Session 2025-12-03

- Q: Definir parâmetros do HMAC para `X-Tenant-Id` (algoritmo, tamanho/rotação de chave, escopo por ambiente e auditoria de uso)? → A: HMAC-SHA256 com chave raiz por ambiente em Vault/KMS, derivação HKDF por tenant e rotação a cada 90 dias com auditoria de uso por tenant.

## User Scenarios & Testing *(mandatorio)*

*As historias DEVEM ser fatias verticais independentes (INVEST) e testaveis de forma isolada. Mantenha o foco na jornada do usuario/persona e descreva como cada cenario prova o valor entregue.*

### User Story 1 - Ativar tenant com isolamento (Prioridade: P1)

- **Persona & Objetivo**: Admin de plataforma quer ativar um novo tenant e garantir que apenas usuarios autorizados daquele dominio acessem seus dados.  
- **Valor de Negocio**: Reduz risco de vazamento lateral e acelera onboarding seguro de clientes.  
- **Contexto Tecnico**: Backend multi-tenant, gestao de tenants e RLS aplicadas a dados de configuracao e auditoria; exposto via `/api/v1` com contratos OpenAPI 3.1.

**Independent Test**: Contratos OpenAPI 3.1 e testes de integracao verificando ativacao, RLS (`CREATE POLICY`) e bloqueios cross-tenant com Problem Details padronizado.

**Acceptance Scenarios (BDD)**:
1. **Dado** um tenant criado mas ainda pendente, **Quando** o admin solicita ativacao via `/api/v1/tenants/{id}` com `If-Match` atual e atributos obrigatorios, **Entao** o tenant fica ativo com RLS aplicada por `CREATE POLICY` e binding de sessao registrado, gerando auditoria WORM e contratos atualizados.  
2. **Dado** um usuario autenticado de outro tenant, **Quando** tenta acessar recurso fora do seu `tenant_id`, **Entao** recebe Problem Details (RFC 9457) com 403/404, auditoria em WORM e nenhum dado cruzado e o evento e rejeitado por RLS.
3. **Dado** um usuario autenticado com sessao do tenant A, **Quando** envia requisicao com `X-Tenant-Id` adulterado para o tenant B ou payload/path contendo `tenant_id` diferente, **Entao** o middleware aplica `SET LOCAL` com o `tenant_id` da sessao, o manager ignora overrides, a RLS bloqueia com Problem Details 403/404, a tentativa e registrada em WORM e o teste automatizado prova que o bypass foi impedido.

### User Story 2 - Versionar roles com RBAC+ABAC (Prioridade: P2)

- **Persona & Objetivo**: Gestor de seguranca quer publicar versoes de roles e politicas ABAC por tenant, garantindo evolucao controlada e rastreavel.  
- **Valor de Negocio**: Evita autorizacoes excessivas e permite rollback seguro de permissoes.  
- **Contexto Tecnico**: Gestao de catalogo de roles, avaliacoes RBAC+ABAC por tenant, armazenamento versionado e testes automatizados de decisao.

**Independent Test**: Testes automatizados de autorizacao (unitarios + contrato) que avaliam RBAC+ABAC com roles versionadas, matrix de autorizacao por tenant e deteccao de regressao em simulacoes cross-tenant, com contratos OpenAPI 3.1/Pact lintados.

**Acceptance Scenarios (BDD)**:
1. **Dado** uma role publicada na versao N, **Quando** o gestor altera permissoes ou atributos e envia via `/api/v1/roles/{id}` com `If-Match`, **Entao** cria-se versao N+1, a anterior permanece consultavel, requests sem `If-Match` valido sao rejeitadas com Problem Details e o contrato OpenAPI 3.1/Pact e atualizado; bindings de sujeito (RoleBinding + SubjectAttribute) são atualizados e o cache ABAC é invalidado.  
2. **Dado** um usuario com role versionada, **Quando** a avaliacao ABAC detecta que o atributo (ex.: unidade, sensibilidade do recurso) nao atende a politica do tenant, **Entao** o acesso e negado, logado em WORM, coberto por testes object-level e refletido no contrato Problem Details.

### User Story 3 - MFA e sessoes seguras auditaveis (Prioridade: P3)

- **Persona & Objetivo**: Usuario final e auditor querem que apenas sessoes multifator e tokens seguros permitam operacoes, com trilhas imutaveis para compliance.  
- **Valor de Negocio**: Reduz fraude e facilita comprovacao regulatoria.  
- **Contexto Tecnico**: Fluxos de autenticacao com MFA obrigatoria, refresh tokens com flags seguros e auditoria em WORM (S3 Object Lock).

**Independent Test**: Testes de autenticacao e sessao cobrindo MFA obrigatoria, rotacao/expiracao de refresh tokens `HttpOnly/Secure/SameSite=Strict`, verificacao de logs em WORM e conformidade de contratos OpenAPI 3.1/Problem Details.

**Acceptance Scenarios (BDD)**:
1. **Dado** um usuario com credenciais validas mas sem MFA concluida, **Quando** tenta obter access token ou refresh em `/api/v1/auth/token`, **Entao** o fluxo exige MFA, so emite tokens com flags `HttpOnly/Secure/SameSite=Strict`, e falhas retornam Problem Details com orientacao de remedio.  
2. **Dado** uma acao sensivel (ex.: troca de role ou bloqueio de tenant), **Quando** realizada por sessao autenticada, **Entao** gera evento de auditoria em WORM com S3 Object Lock, incluindo `tenant_id`, versao de role afetada e `ETag` da mudanca, validavel por teste automatizado e refletido no contrato Problem Details.

> Adicione novas historias somente se entregarem valor independente. Utilize `[NEEDS CLARIFICATION]` quando houver duvidas sobre fluxo, persona ou restricoes.

### Edge Cases & Riscos Multi-Tenant

- Requisicoes sem `tenant_id` ou com `tenant_id` divergente devem ser rejeitadas com Problem Details e logadas em WORM sem expor existencia do recurso.  
- Conflitos de versao ao atualizar tenant/roles (falta de `If-Match` ou `ETag` desatualizado) precisam de resposta 412 com orientacao de retry idempotente.  
- Tentativas de reuso de refresh token ou MFA expirado devem ser bloqueadas, registrando indicio de fraude e disparando alerta de seguranca.  
- Integracoes externas (ex.: identidade corporativa ou cofres) indisponiveis devem degradar de forma segura, mantendo bloqueio cross-tenant e auditoria.  
- Retencao e bloqueio de logs WORM devem proteger contra exclusao ou edicao antecipada, inclusive para admins do tenant.  
- Excedentes de rate limiting por tenant devem retornar 429 com `Retry-After` coerente; repeticoes sem `Idempotency-Key` em operacoes mutaveis devem ser rejeitadas ou deduplicadas com 428.  
- Erros de autorizacao/object-level devem nunca vazar PII (incluindo em URLs/telemetria) e devem ser mascarados em logs.

## Riscos & Mitigacoes

- Acesso cross-tenant por falha de binding de sessao/RLS → Mitigar com RLS via `CREATE POLICY`, managers tenant-first, testes de integracao de bloqueio e Problem Details padronizado.  
- Inconsistencia de historico/auditoria ao versionar roles ou tenants → Mitigar com historico versionado alinhado ao Blueprint §6.2, WORM com integridade e expand/contract que nao suspenda RLS.  
- Observabilidade vazando PII ou sem correlacao ponta-a-ponta → Mitigar com Trace Context W3C + mascaramento de PII em spans/logs/metricas e verificacao automatizada nos pipelines.  
- Rate limiting/Idempotency-Key mal calibrados gerando falhas legitimas → Mitigar com limites por tenant revisados em threat modeling, headers `Retry-After`/`RateLimit-*` claros e deduplicacao auditavel.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do codigo, cobrindo trajetorias felizes/tristes | Suites cobrindo ativacao de tenant, bloqueio cross-tenant e MFA/refresh tokens. |
| Art. IV (Teste de Integracao-Primeiro) | Priorizar testes de integracao com dados realistas | Fluxos de isolamento/autorizacao/MFA cobertos primeiro com factory-boy + cliente DRF. |
| Art. V (Documentacao/Versionamento) | Versionamento e documentacao formal de ativos | `/api/v1` contract-first OpenAPI 3.1, roles versionadas e matriz de autorizacao por tenant. |
| Art. II (Modularidade) | Monolito modular e separacao em apps/camadas | Governanca de tenants/RBAC centralizada em app dedicado e camada de aplicacao, seguindo SSOT de modelos (Blueprint §3.1). |
| Art. I (Stack/Arquitetura) | Monolito modular Django/DRF em camadas sobre PostgreSQL | Escopo multi-tenant em app dedicado, aderente ao monolito modular previsto no blueprint §2. |
| Art. VI (SLO/Orcamento de Erro) | SLOs com orcamentos de erro e alertas | SLO de disponibilidade/latencia por tenant com error budgets e alertas vinculados. |
| Art. VII (Observabilidade) | Telemetria rastreavel e mascaramento de PII | Trace Context W3C ponta-a-ponta com OpenTelemetry; spans/logs estruturados com `tenant_id`/decisao ABAC/MFA e PII mascarada. |
| Art. VIII (Entrega) | Trunk-Based Development e métricas DORA como gate de release | Fluxos em trunk com rollback versionado; DORA (lead time, change failure rate, deployment freq, MTTR) coletadas e usadas como critério de go/no-go. |
| Art. IX (CI) | Cobertura >=85 %, complexidade <=10, SAST/DAST/SCA, SBOM, k6 | Pipeline exige cobertura de autorizacao/RLS, SAST/DAST/SCA, SBOM, Renovate e testes de carga k6. |
| Art. XI (Governanca de API) | Contrato-primeiro OpenAPI 3.1, erros RFC 9457, rate limiting `Retry-After`, idempotencia com `Idempotency-Key`, controle de concorrencia com `ETag`/`If-Match` e deduplicacao/TTL auditable | 429/`Retry-After`, `Idempotency-Key` com TTL/deduplicacao (Redis + trilha RLS), `ETag`/`If-Match`, lint/diff OpenAPI/Pact e Problem Details padronizado. |
| Art. XIII (LGPD/RLS) | Enforcar RLS, direitos do titular, objeto-level | RLS com managers, matriz RBAC/ABAC testada, ROPA/RIPD, retenção/expurgo por tenant. |
| Art. XII (Security by Design) | RBAC/ABAC formalizado, segredos/PII protegidos, CSP/Trusted Types | Matriz RBAC/ABAC testada, PII mascarada, CSP com nonce/hash e Trusted Types quando suportado (FR-011), segredos/criptografia de campo (FR-014). |
| Art. X (Migracoes) | Mudancas zero-downtime (expand/contract) | Migracoes de roles/RLS seguindo expand/contract e validacoes de isolamento. |
| Art. XIV (IaC/GitOps) | Infra como codigo e politicas OPA/GitOps | Declarar governanca de RLS/rate limiting/WORM via IaC/GitOps; validacao OPA antes de aplicar. |
| Art. XV (Dependencias) | Gestao de dependencias e SBOM | Atualizacao automatica e SBOM para libs de seguranca/autenticacao/observabilidade. |
| Art. XVI (FinOps) | Custos rastreados, tags e budgets atualizados | Monitorar custo de logs WORM e avaliacoes de autorizacao por tenant. |
| Art. XVII (Threat Modeling/Operacao) | STRIDE/LINDDUN e GameDays | Backlog de ameaças (cross-tenant, reuse de tokens) e execucao periodica de GameDays/runbooks. |
| Art. XVIII (Fluxo SDD) | Rastreabilidade de artigos e pendencias em `/clarify` | Referencias explicitas a artigos/blueprint e marcadores [NEEDS CLARIFICATION] para duvidas criticas. |
| ADR-010/011/012 | Seguranca de dados, governanca de API, observabilidade | Logs estruturados, trilhas WORM com integridade, mascaramento de PII e metricas de decisao de acesso. |

Remova linhas nao aplicaveis apenas se justificar o motivo. Itens pendentes ficam com `[NEEDS CLARIFICATION]`.

### Functional Requirements

- **FR-001**: Toda requisição `/api/v1` deve exigir `tenant_id` vinculado à sessão; origem canônica é `X-Tenant-Id` enviado pelo cliente e validado contra claim/session ou HMAC-SHA256 (chave raiz por ambiente em Vault/KMS, derivação HKDF por tenant, rotação 90 dias com auditoria de uso por tenant), com falha fechada e Problem Details em caso de ausência/divergência; modelos multi-tenant usam base única com unicidade por tenant e managers que injetam `tenant_id` por padrão, ignorando overrides de path/body/header; binding de sessão é aplicado por middleware que seta `SET LOCAL iabank.tenant_id` (ou equivalente) a partir da sessão antes de qualquer query e é coberto por testes de bypass (alterar header/body/path ou trocar `X-Tenant-Id` não sobrescreve o valor da sessão); RLS configurada com `CREATE POLICY` é versionada e coberta por testes automatizados.  
- **FR-002**: Lifecycle de tenant é `Pending -> Active -> Suspended -> Blocked -> Decommissioned` com transições unidirecionais; `Suspended` opera read-only (sem novas mutações, novos tokens ou writes de sessões ativas); `Blocked` nega tudo, revoga tokens e pausa jobs/filas; `Decommissioned` é acesso zero com leitura apenas de WORM para auditoria após cumprir retenções WORM/LGPD; todas as mudanças respeitam controle otimista (`ETag`/`If-Match`) e registram auditoria WORM com status, actor e motivo.  
- **FR-002.1**: Payload mínimo para criar/ativar tenant DEVE incluir nome/slug, domínios permitidos, metadados do IdP OIDC/SAML, contatos de segurança/operacionais, classificação de risco/segmento, fuso/região padrão e política de retenção WORM aplicada na criação; rejeitar ativação sem esses campos com Problem Details.  
- **FR-003**: Engine de RBAC+ABAC deve avaliar roles versionadas por tenant; matriz de autorizacao e testes de autorizacao (unitarios, contrato, object-level) devem impedir acessos excessivos e suportar rollback seguro; bindings normalizados (RoleBinding + SubjectAttribute) são fonte de verdade.  
- **FR-004**: Decisões de autorização devem considerar atributos do usuário/recurso (ex.: unidade, classificacao, sensibilidade) além de roles, retornando Problem Details padronizado em caso de negativa e refletindo o contrato OpenAPI 3.1; baseline de atributos obrigatórios definidos via JSON Schema 2020-12 parametrizável por tenant (`configs/abac/tenant-policy.schema.json`); atributos customizados por tenant só podem ser adicionados com aprovação de segurança e versionamento de esquema por tenant.  
- **FR-005**: MFA é obrigatória para qualquer sessão interativa; fator padrão é TOTP conforme blueprint, aplicado no mínimo a perfis administrativos/operacoes críticas; sem MFA, tokens de acesso/refresh não são emitidos; exceções apenas via helpdesk com códigos de recuperação auditados e validade curta.  
- **FR-006**: Refresh tokens devem ser emitidos apenas com flags `HttpOnly`, `Secure` e `SameSite=Strict`, possuir rotação e revogação em caso de reuse detectado, e serem testados automaticamente.  
- **FR-007**: Modelos e registros críticos (tenant, roles, sessoes) devem manter histórico/versionamento auditável usando `django-simple-history` conforme Blueprint §6.2 (sem stack adicional), com capacidade de rollback e verificação de integridade (hash/chain de eventos) complementando a trilha; logs imutáveis com Object Lock, retencao mínima conforme política (baseline >=365 dias), verificação de hash/assinatura pós-upload (fail-close em caso de falha) e políticas de acesso/retencao definidas; versionamento/politicas RLS nao podem ser interrompidos por migrações expand/contract.  
- **FR-008**: Todas respostas de erro devem seguir Problem Details (RFC 9457) incluindo correlação e remedio; contratos OpenAPI 3.1/Pact devem ser validados por lint/diff e falhar o pipeline em caso de divergencia.  
- **FR-009**: Operações mutáveis devem exigir `Idempotency-Key` com deduplicação primária em Redis (TTL 24h) e trilha/auditoria em Postgres sob RLS; faltas retornam 428, chaves expiradas ou reusadas retornam 409/422 com Problem Details e trilha; excessos de rate limit por tenant retornam 429 com `Retry-After` e headers `RateLimit-*`, com recomendações de backoff/jitter; ameaças modeladas (STRIDE/LINDDUN) recebem mitigações explícitas e são revisitadas em GameDays.  
- **FR-010**: LGPD e privacidade: garantir ROPA/RIPD por tenant, retenção/expurgo para dados de auditoria/sessão e direito ao esquecimento onde aplicável, sem violar integridade WORM.  
- **FR-010.1**: Logs WORM devem operar em modo compliance com retenção mínima de 365 dias, extensível por obrigação legal, com verificação de integridade pós-upload; dados de sessão/refresh devem ser expurgados em até 30 dias; direito ao esquecimento aplicado após cumprimento de retenções legais.  
- **FR-010.2**: Rate limiting por tenant: API pública 50 rps (burst 2x), API privada 200 rps (burst 2x); tenants de alto risco iniciam com 50% desses limites até revisão.  
- **FR-010.3**: `Idempotency-Key` deve ter TTL de 24h com deduplicação persistente, rejeitando reuso fora da janela e retornando Problem Details conforme ADR-011.  
- **FR-011**: Frontend/telemetria devem evitar PII em URLs e adicionar proteções (CSP com nonce/hash); Trusted Types deve ser habilitado quando suportado e, onde não houver suporte, é obrigatório documentar a exceção, reforçar sanitização nos sinks críticos e manter testes automatizados que provem a mitigação; alinhado ao adição #13, com evidencias de testes de rendering/telemetria sem PII.  
- **FR-012**: Estrategia de dados multi-tenant deve incluir índices tenant-first e unicidade por tenant nos modelos críticos, com testes que provem ausência de cross-tenant leak e regressão de performance.  
- **FR-013**: Migrações que afetem roles/RLS/políticas devem seguir expand/contract para zero-downtime: adicionar colunas nulas e índices com `CREATE INDEX CONCURRENTLY`, constraints `NOT VALID` + `VALIDATE`, backfill assistido, dual-write/dual-read ou feature flag até cutover, remoção somente após validação; testes de migração devem provar que RLS e políticas permanecem ativas e que isolamento não é reduzido durante a transição.  
- **FR-014**: PII sensível deve suportar criptografia de campo e governança de segredos com rotação e escopo por ambiente/tenant, conforme política de segurança.  
- **FR-015**: Governanca via IaC/GitOps (Art. XIV) deve versionar politicas de RLS, rate limiting, Idempotency-Key e WORM (retencao/acesso), com validacao OPA e trilha auditavel de mudancas antes de aplicar em qualquer ambiente.
- **FR-016**: Acesso headless via service accounts ou API keys long-lived é proibido; integrações devem usar delegação/impersonação de usuário com MFA ativa, avaliação ABAC e auditoria WORM; caso haja automação inevitável, deve seguir delegação com escopo mínimo e expiração curta, sem `client_credentials`.
- **FR-017**: Identidade/SSO: cada tenant deve integrar IdP externo OIDC/SAML obrigatório com MFA no IdP; SSO é mandatório, com provisionamento JIT/SCIM, mapeamento de roles/atributos para RBAC+ABAC e fluxo break-glass controlado e auditado; credenciais locais permanentes são proibidas.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Disponibilidade dos endpoints de ativação/autorização >= 99,9% e MTTR < 30 min para falhas de isolamento; rollback de roles/tenant deve ser possível em < 10 min.  
- **NFR-001.1 (Error Budgets)**: SLOs devem ter orçamentos de erro por tenant com alertas e automação de mitigação quando o consumo exceder o limite.  
- **NFR-002 (Performance)**: Decisões de autorização e verificação de MFA devem responder sem percepção de atraso (p95 < 400 ms) mesmo em carga prevista; conflitos de `If-Match` resolvidos em < 1 s com orientação clara; rate limiting por tenant calibrado para evitar latencia extra; índices tenant-first sustentam desempenho multi-tenant; performance gate automatizado deve reprovar se limiares forem excedidos.  
- **NFR-003 (Observabilidade)**: Trace Context W3C ponta-a-ponta com OpenTelemetry; spans/logs/metricas estruturados com `tenant_id`, versão de role, decisão ABAC, resultado de MFA e ID de correlação; PII mascarada em todos os sinais; métricas p95/p99, throughput e saturação monitoradas por tenant; alertas disparam em reuse de refresh token, padrão cross-tenant ou 429 recorrente; integridade e retenção das trilhas WORM não podem ser degradadas; a feature deve aderir ao stack mandatório de observabilidade definido na constituição (OpenTelemetry + structlog + django-prometheus + Sentry) sem detalhar implementação.
- **NFR-004 (Seguranca)**: Conformidade com Problem Details, OWASP ASVS e NIST SSDF/SAMM para autenticação/autorização; threat modeling documentado com mitigacoes e revisitado em GameDays; integração com auditoria WORM não pode ser desabilitada por tenants.  
- **NFR-005 (Qualidade/CI)**: Cobertura de testes >= 85%, complexidade ciclomática <= 10, SAST/DAST/SCA contínuos, SBOM gerada, Renovate ativo e testes de desempenho (k6) para fluxos de autorizacao/MFA; gates de contrato OpenAPI/Pact executados no pipeline; suites priorizam testes de integracao com factory-boy + cliente DRF para fluxos de isolamento/autorizacao/MFA/refresh.  
- **NFR-006 (FinOps)**: Custos de armazenamento WORM e execuções de decisão de acesso devem ser monitorados por tenant, com tagging consistente e showback/chargeback; orçamento definido e alerta ao exceder 80%.  
- **NFR-007 (Privacidade Frontend)**: CSP com nonce/hash e Trusted Types habilitados; quando o ambiente não suportar Trusted Types, a exceção deve ser documentada e compensada com sanitização reforçada e testes automatizados que comprovem mitigação; evitar PII em URLs, telemetria e mensagens de erro expostas ao cliente.  
- **NFR-008 (IaC/GitOps/OPA)**: Mudanças em politicas (RLS, rate limiting, WORM/retencao) devem ser aplicadas via IaC/GitOps com validacao OPA e trilha auditavel, evitando drift.
- **NFR-009 (Entrega Contínua/DORA)**: Adoção de Trunk-Based Development; DORA (lead time, frequência de deploys, change failure rate, MTTR) devem ser medidas e publicadas para a feature, com alertas e critérios de go/no-go quando metas pactuadas forem excedidas.

### Dados Sensiveis & Compliance

- Campos sensíveis: identificadores de usuário, atributos de localização/unidade, IP/dispositivo usados para MFA e refresh tokens. Devem ser mascarados em logs e acessíveis apenas via RLS.  
- Retenção: auditoria WORM com Object Lock e tempo de retenção mínimo alinhado a compliance; dados de sessão/token devem seguir política de expiração curta e direito ao esquecimento por tenant, com exceções documentadas quando bloqueio legal impedir expurgo.  
- Evidências: RIPD/ROPA atualizados por tenant, logs WORM consultáveis por auditoria, runbooks para revogação de tokens, rollback de roles e bloqueio de tenant.

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- **SC-001**: 100% das requisições `/api/v1` sem `tenant_id` válido ou com `tenant_id` divergente são bloqueadas com Problem Details e auditadas em WORM; validação por testes de contrato, dashboard de rejeições e teste automatizado de binding `SET LOCAL` que prova que overrides de header/body/path são ignorados.  
- **SC-002**: 95% dos tenants são ativados ou bloqueados com sucesso em < 5 minutos, mantendo histórico versionado e auditável; validação por monitor de rollout e consulta de trilhas WORM.  
- **SC-003**: 100% das alterações de roles geram nova versão com `If-Match` validado e testes automatizados cobrindo RBAC+ABAC (incluindo object-level) executados no pipeline; validação por suites de autorização e lint/diff de contrato.  
- **SC-004**: 100% das sessões exigem MFA antes de emissão de tokens; taxa de reuse de refresh tokens detectada e revogada em 100% dos casos com alerta registrado; validação por testes de autenticação e painéis de alertas de segurança.  
- **SC-005**: 100% dos eventos críticos (ativação/bloqueio de tenant, mudanças de roles, falhas de MFA) são registrados em WORM com Object Lock e consultáveis por auditoria sem lacunas de retenção; validação por consultas amostrais e verificação de retenção.  
- **SC-006**: 100% das operações mutáveis sem `Idempotency-Key` ou acima do rate limit retornam 428/429 com `Retry-After` correto, deduplicacao/persistencia auditavel e sem efeitos colaterais; validação por testes de idempotência/rate limit e dashboard de erros 42x/409/422.  
- **SC-007**: 100% das trilhas WORM de eventos críticos passam verificação de integridade (hash/chain) e permitem rollback seguro; validação por testes automatizados de integridade/rollback.  
- **SC-008**: Orçamentos de erro por tenant não excedem o limite pactuado em janelas definidas; consumo acima do limite dispara alerta e bloqueio de escopo conforme runbook; validação por painéis de SLO/Error Budget.  
- **SC-009**: 100% das mudancas de politicas RLS/rate limiting/WORM passam por pipeline IaC/GitOps com gate OPA e trilha auditavel; retencao WORM atende à política aprovada (baseline >=365 dias) e bloqueia deleção/edicao antecipada; validação por gates OPA/Argo e verificação de hash/assinatura pós-upload.  
- **SC-010**: 100% das releases relacionadas à feature registram métricas DORA (lead time, frequência de deploys, change failure rate, MTTR) em dashboards; alertas disparam e bloqueiam promoção quando qualquer métrica exceder o limite pactuado.

Associe cada criterio aos testes ou dashboards que validam o resultado.

## Outstanding Questions & Clarifications

*(Nenhuma pendencia no momento.)*
