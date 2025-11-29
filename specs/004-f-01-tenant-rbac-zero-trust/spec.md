# Feature Specification: Governanca de Tenants e RBAC Zero-Trust

**Feature Branch**: `004-f-01-tenant-rbac-zero-trust`  
**Created**: 2025-11-29  
**Status**: Draft  
**Input**: User description: "F-01 Governanca de Tenants e RBAC Zero-Trust. Use BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.2,19 e adicoes_blueprint.md itens 4,5,12,13. Produza a especificacao seguindo o template oficial (contexto, historias, requisitos, metricas, riscos) sem definir stack adicional. Garanta RLS com `CREATE POLICY` e binding de sessao, RBAC+ABAC com testes automatizados, MFA obrigatoria, auditoria WORM, controle de concorrencia com `ETag`/`If-Match`, versionamento `/api/v1`, refresh tokens seguros (`HttpOnly`/`Secure`/`SameSite=Strict`) e Problem Details (RFC 9457), alinhado aos Arts. III, V, IX, XIII. Marque duvidas criticas com [NEEDS CLARIFICATION] e inclua BDD para ativacao de tenant, bloqueio cross-tenant, versionamento de roles, MFA/refresh seguro, atributos de autorizacao e logs S3 Object Lock, referenciando OpenAPI 3.1 contract-first."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituicao v5.2.0 (Art. I-XVIII) e ADRs aplicaveis. Toda lacuna deve ser marcada com `[NEEDS CLARIFICATION]` e adicionada ao `/clarify`.

## Contexto

Instituicao multi-tenant precisa garantir isolamento zero-trust entre clientes corporativos e unidades internas, assegurando que cada requisição esteja vinculada a um `tenant_id` válido e que decisões de acesso combinem RBAC e atributos (ABAC). O objetivo é ativar e governar tenants com MFA obrigatoria, logs imutaveis (WORM) e auditoria rastreavel, mitigando riscos de vazamento lateral e fraudes. A entrega deve alinhar-se aos Arts. III, V, IX e XIII, usando contratos OpenAPI 3.1 contract-first e Problem Details (RFC 9457) para consistencia e conformidade.

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

### User Story 2 - Versionar roles com RBAC+ABAC (Prioridade: P2)

- **Persona & Objetivo**: Gestor de seguranca quer publicar versoes de roles e politicas ABAC por tenant, garantindo evolucao controlada e rastreavel.  
- **Valor de Negocio**: Evita autorizacoes excessivas e permite rollback seguro de permissoes.  
- **Contexto Tecnico**: Gestao de catalogo de roles, avaliacoes RBAC+ABAC por tenant, armazenamento versionado e testes automatizados de decisao.

**Independent Test**: Testes automatizados de autorizacao (unitarios + contrato) que avaliam RBAC+ABAC com roles versionadas e detectam regressao em simulacoes cross-tenant.

**Acceptance Scenarios (BDD)**:
1. **Dado** uma role publicada na versao N, **Quando** o gestor altera permissoes ou atributos e envia via `/api/v1/roles/{id}` com `If-Match`, **Entao** cria-se versao N+1, a anterior permanece consultavel, e requests sem `If-Match` valido sao rejeitadas com Problem Details.  
2. **Dado** um usuario com role versionada, **Quando** a avaliacao ABAC detecta que o atributo (ex.: unidade, sensibilidade do recurso) nao atende a politica do tenant, **Entao** o acesso e negado, logado em WORM e o teste automatizado cobre o caso triste.

### User Story 3 - MFA e sessoes seguras auditaveis (Prioridade: P3)

- **Persona & Objetivo**: Usuario final e auditor querem que apenas sessoes multifator e tokens seguros permitam operacoes, com trilhas imutaveis para compliance.  
- **Valor de Negocio**: Reduz fraude e facilita comprovacao regulatoria.  
- **Contexto Tecnico**: Fluxos de autenticacao com MFA obrigatoria, refresh tokens com flags seguros e auditoria em WORM (S3 Object Lock).

**Independent Test**: Testes de autenticacao e sessao cobrindo MFA obrigatoria, rotacao/expiracao de refresh tokens `HttpOnly/Secure/SameSite=Strict`, e verificacao de logs em WORM.

**Acceptance Scenarios (BDD)**:
1. **Dado** um usuario com credenciais validas mas sem MFA concluida, **Quando** tenta obter access token ou refresh em `/api/v1/auth/token`, **Entao** o fluxo exige MFA, so emite tokens com flags `HttpOnly/Secure/SameSite=Strict`, e falhas retornam Problem Details com orientacao de remedio.  
2. **Dado** uma acao sensivel (ex.: troca de role ou bloqueio de tenant), **Quando** realizada por sessao autenticada, **Entao** gera evento de auditoria em WORM com S3 Object Lock, incluindo `tenant_id`, versao de role afetada e `ETag` da mudanca, validavel por teste automatizado.

> Adicione novas historias somente se entregarem valor independente. Utilize `[NEEDS CLARIFICATION]` quando houver duvidas sobre fluxo, persona ou restricoes.

### Edge Cases & Riscos Multi-Tenant

- Requisicoes sem `tenant_id` ou com `tenant_id` divergente devem ser rejeitadas com Problem Details e logadas em WORM sem expor existencia do recurso.  
- Conflitos de versao ao atualizar tenant/roles (falta de `If-Match` ou `ETag` desatualizado) precisam de resposta 412 com orientacao de retry idempotente.  
- Tentativas de reuso de refresh token ou MFA expirado devem ser bloqueadas, registrando indicio de fraude e disparando alerta de seguranca.  
- Integracoes externas (ex.: identidade corporativa ou cofres) indisponiveis devem degradar de forma segura, mantendo bloqueio cross-tenant e auditoria.  
- Retencao e bloqueio de logs WORM devem proteger contra exclusao ou edicao antecipada, inclusive para admins do tenant.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do codigo, cobrindo trajetorias felizes/tristes | Suites cobrindo ativacao de tenant, bloqueio cross-tenant e MFA/refresh tokens. |
| Art. V (Seguranca Zero-Trust) | MFA obrigatoria, menor privilegio, avaliacao RBAC+ABAC | Requisitos de MFA obrigatoria, roles versionadas e atributos por tenant. |
| Art. VIII (Entrega) | Estrategia de release segura (feature flag/canary/rollback) | Ativacao de tenant e versoes de role controladas, com rollback por versao. |
| Art. IX (CI) | Cobertura >=85 %, complexidade <=10, SAST/DAST/SCA, SBOM, k6 | Pipeline exige cobertura de testes de autorizacao e RLS, testes de carga de decisao. |
| Art. XI (API) | Contratos OpenAPI 3.1 + Pact atualizados, RFC 9457 | APIs `/api/v1` documentadas contract-first e erros em Problem Details. |
| Art. XIII (LGPD/RLS) | Enforcar RLS, managers, retencao/direito ao esquecimento | RLS via `CREATE POLICY` + binding de sessao por tenant; auditoria WORM. |
| Art. XVI (FinOps) | Custos rastreados, tags e budgets atualizados | Monitorar custo de logs WORM e avaliacoes de autorizacao por tenant. |
| ADR-010/011/012 | Seguranca de dados, governanca de API, observabilidade | Logs estruturados, trilhas WORM e metricas de decisao de acesso. |
| Outros | Pactos de risco/sandbox por tenant | [NEEDS CLARIFICATION: Politica de isolamento adicional (airgap/regioes dedicadas) para tenants de alto risco?] |

Remova linhas nao aplicaveis apenas se justificar o motivo. Itens pendentes ficam com `[NEEDS CLARIFICATION]`.

### Functional Requirements

- **FR-001**: Toda requisição `/api/v1` deve exigir `tenant_id` vinculado à sessão; RLS configurada com `CREATE POLICY` e binding de sessão bloqueia acesso a dados de outros tenants.  
- **FR-002**: Ativação, suspensão e bloqueio de tenants devem respeitar controle otimista (`ETag`/`If-Match`) e registrar auditoria WORM com status, actor e motivo.  
- **FR-003**: Engine de RBAC+ABAC deve avaliar roles versionadas por tenant; alterações geram nova versão e mantêm histórico consultável e auditável.  
- **FR-004**: Decisões de autorização devem considerar atributos do usuário/recurso (ex.: unidade, classificacao, sensibilidade) além de roles, retornando Problem Details padronizado em caso de negativa.  
- **FR-005**: MFA é obrigatória para qualquer sessão interativa; sem MFA, tokens de acesso/refresh não são emitidos.  
- **FR-006**: Refresh tokens devem ser emitidos apenas com flags `HttpOnly`, `Secure` e `SameSite=Strict`, possuir rotação e revogação em caso de reuse detectado, e serem testados automaticamente.  
- **FR-007**: Eventos críticos (ativação/bloqueio de tenant, alterações de roles, falhas de MFA, negações ABAC) devem gerar logs imutáveis com Object Lock, contendo `tenant_id`, versao e `ETag` aplicável.  
- **FR-008**: Todas respostas de erro devem seguir Problem Details (RFC 9457) incluindo correlação e remedio; contratos OpenAPI 3.1 devem refletir estes formatos de forma contract-first.  
- **FR-009**: Bloqueios cross-tenant e caminhos felizes devem possuir testes automatizados (contrato + integração) que provem aplicação de RLS e avaliação RBAC+ABAC.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Disponibilidade dos endpoints de ativação/autorização >= 99,9% e MTTR < 30 min para falhas de isolamento; rollback de roles/tenant deve ser possível em < 10 min.  
- **NFR-002 (Performance)**: Decisões de autorização e verificação de MFA devem responder sem percepção de atraso (p95 < 400 ms) mesmo em carga prevista; conflitos de `If-Match` resolvidos em < 1 s com orientação clara.  
- **NFR-003 (Observabilidade)**: Spans/logs devem incluir `tenant_id`, versão de role, decisão ABAC e resultado de MFA; alertas disparam em tentativas de reuse de refresh token ou padrões cross-tenant.  
- **NFR-004 (Seguranca)**: Conformidade com Problem Details, OWASP ASVS para autenticação/autorização, e testes automatizados cobrindo RBAC+ABAC e RLS; integração com auditoria WORM não pode ser desabilitada por tenants.  
- **NFR-005 (FinOps)**: Custos de armazenamento WORM e execuções de decisão de acesso devem ser monitorados por tenant, com orçamento definido e alerta ao exceder 80%.

### Dados Sensiveis & Compliance

- Campos sensíveis: identificadores de usuário, atributos de localização/unidade, IP/dispositivo usados para MFA e refresh tokens. Devem ser mascarados em logs e acessíveis apenas via RLS.  
- Retenção: auditoria WORM com Object Lock e tempo de retenção mínimo alinhado a compliance ([NEEDS CLARIFICATION: prazo de retenção/regime legal por tenant]). Dados de sessão/token devem seguir política de expiração curta e direito ao esquecimento por tenant.  
- Evidências: RIPD/ROPA atualizados por tenant, logs WORM consultáveis por auditoria, runbooks para revogação de tokens, rollback de roles e bloqueio de tenant.

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- **SC-001**: 100% das requisições `/api/v1` sem `tenant_id` válido ou com `tenant_id` divergente são bloqueadas com Problem Details e auditadas em WORM.  
- **SC-002**: 95% dos tenants são ativados ou bloqueados com sucesso em < 5 minutos, mantendo histórico versionado e auditável.  
- **SC-003**: 100% das alterações de roles geram nova versão com `If-Match` validado e testes automatizados cobrindo RBAC+ABAC executados no pipeline.  
- **SC-004**: 100% das sessões exigem MFA antes de emissão de tokens; taxa de reuse de refresh tokens detectada e revogada em 100% dos casos com alerta registrado.  
- **SC-005**: 100% dos eventos críticos (ativação/bloqueio de tenant, mudanças de roles, falhas de MFA) são registrados em WORM com Object Lock e consultáveis por auditoria sem lacunas de retenção.

Associe cada criterio aos testes ou dashboards que validam o resultado.

## Outstanding Questions & Clarifications

- [Segurança/MFA] [NEEDS CLARIFICATION: Qual o fator de MFA obrigatório (TOTP, WebAuthn, push) e como tratar exceções para usuários sem dispositivo compatível?]  
- [Compliance/WORM] [NEEDS CLARIFICATION: Qual o prazo/regime de retenção de logs WORM (anos, bloqueio legal) por tenant e se há exceção para tenants de teste?]  
- [Isolamento avançado] [NEEDS CLARIFICATION: Tenants de alto risco exigem isolamento adicional (região dedicada/airgap) além de RLS, ou RLS + auditoria WORM basta?]
