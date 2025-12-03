# Research: Governanca de Tenants e RBAC Zero-Trust

## 1) Binding multi-tenant e RLS
**Decision**: Usar middleware que valida `X-Tenant-Id` via HMAC-SHA256 (chave raiz em Vault/KMS, HKDF por tenant, rotacao 90d), compara com claim/session e faz `SET LOCAL iabank.tenant_id` antes de qualquer query; managers/querysets tenant-first ignoram overrides de path/body/header; RLS com `CREATE POLICY` versionada cobre leitura/escrita e nega cross-tenant.  
**Rationale**: `SET LOCAL` + RLS evita bypass por ORM bruto; HMAC + HKDF por tenant reduz blast radius; rotação 90d com auditoria atende compliance e itens do spec (FR-001).  
**Alternatives considered**: Parametro obrigatório em todas as queries (risco de esquecimento e bypass de jobs); `SET ROLE` sem RLS (não garante defesa em profundidade).

## 2) Modelo e versionamento RBAC+ABAC
**Decision**: Roles versionadas por tenant com histórico (`django-simple-history`), matriz de permissões referenciando atributos baseline (unidade, classificação, região, tipo de recurso) e atributos custom aprovados; avaliação combina RBAC + regras ABAC em serviço puro Python com policy cache por tenant e testes object-level.  
**Rationale**: Versionamento permite rollback e auditoria (FR-003/FR-004); baseline garante consistência mínima; cache reduz latência sem quebrar RLS.  
**Alternatives considered**: Engine externa (OPA) inline — rejeitado para manter monolito modular e evitar nova dependência; políticas hardcoded — pouco flexíveis e sem versionamento auditável.

## 3) Lifecycle de tenant e concorrencia
**Decision**: State machine `Pending -> Active -> Suspended -> Blocked -> Decommissioned` com transições unidirecionais; operações mutáveis exigem `ETag/If-Match`; `Suspended` read-only (bloqueia novos tokens e writes), `Blocked` revoga tokens/jobs, `Decommissioned` só leitura de WORM; auditoria WORM em cada transição.  
**Rationale**: Cumpre FR-002 e reduz efeitos de condição de corrida; `If-Match` evita sobrescrita; estados claros simplificam testes.  
**Alternatives considered**: Soft flags por coluna boolean — aumenta ambiguidade e risco de bypass; locks pessimistas — maior acoplamento e latência.

## 4) Idempotency-Key e rate limiting
**Decision**: `Idempotency-Key` obrigatória em mutações com TTL 24h e deduplicação persistente em Redis (hash + status + resposta resumida), retornando 428 sem chave, 409/422 em reuso inválido; rate limiting por tenant: público 50 rps (burst 2x), privado 200 rps (burst 2x), alto risco 50% até revisão; headers `RateLimit-*`/`Retry-After` padrão IETF.  
**Rationale**: Alinha FR-009/FR-010.2/FR-010.3 e Art. XI; Redis oferece baixa latência e expiracao automática; deduplicação auditável com WORM para eventos críticos.  
**Alternatives considered**: Idempotência apenas por chave natural — falha em retrials; rate limit global — não protege isolamento por tenant.

## 5) MFA/SSO e tokens
**Decision**: IdP externo OIDC/SAML obrigatório por tenant com MFA TOTP; refresh tokens em cookie HttpOnly/Secure/SameSite=Strict, rotação contínua e revogação em reuse detectado; exceções via helpdesk com códigos de recuperação auditados; proibir service accounts/client_credentials.  
**Rationale**: Cobre FR-005/FR-006/FR-017 e Art. XII; reduz risco de credenciais long-lived; refresh em cookie mitiga XSS/CSRF com SameSite estrito.  
**Alternatives considered**: MFA opcional — viola spec; tokens em localStorage — inseguro; service accounts — proibidas.

## 6) Auditoria WORM e integridade
**Decision**: Logs críticos enviados para S3 Object Lock em modo compliance com retenção mínima 365d, verificação de hash/assinatura pós-upload (fail-close), trilha de histórico com chain/hash para eventos de roles/tenant/MFA; consultas para auditoria não liberam PII (mascaramento).  
**Rationale**: Atende FR-007/FR-010.1 e Art. XVI; integridade verificável bloqueia tampering e dá evidência regulatória.  
**Alternatives considered**: Retenção configurável pelo tenant — arriscaria conformidade; armazenamento mutável — perde WORM.

## 7) Contratos OpenAPI/Pact e Problem Details
**Decision**: Contract-first em `/specs/004-f-01-tenant-rbac-zero-trust/contracts/` com OpenAPI 3.1; lint Spectral + diff oasdiff + Pact; erros RFC 9457 com correlação/remediação; versionamento `/api/v1` e `ETag/If-Match` em recursos versionados.  
**Rationale**: Satisfaz Art. XI/ADR-011 e spec; reduz regressões e permite governança de breaking changes.  
**Alternatives considered**: Swagger gerado de código — falha gate contract-first; ignorar Pact — perder validação de consumidores.

## 8) Observabilidade e PII
**Decision**: Instrumentação OpenTelemetry com W3C Trace Context; logs JSON via structlog com mascaramento de PII e `tenant_id`/decisão ABAC/MFA; métricas django-prometheus e alertas Sentry; dashboards por tenant para SLO/error budget, reuse de refresh, 42x/429, cross-tenant bloqueado.  
**Rationale**: Alinha Art. VII/ADR-012 e NFR-003; facilita auditoria e detecção de fraude.  
**Alternatives considered**: Logging não estruturado — inviável para correlação; spans sem `tenant_id` — quebra isolamento observável.

## 9) Frontend seguro
**Decision**: React/Vite consumindo contratos gerados, adicionando cabeçalhos de rastreamento/idempotencia/rate limit; CSP strict-dynamic com nonces, Trusted Types quando suportado, sanitização reforçada e testes automatizados onde não houver suporte; evitar PII em URLs e telemetry payloads.  
**Rationale**: Cumpre FR-011/NFR-007/Art. XII; protege contra XSS e vazamento de PII no front.  
**Alternatives considered**: CSP permissiva ou sem Trusted Types — não atende blueprint; PII em URLs — viola requisitos de privacidade.

## 10) Dados sensíveis e pgcrypto
**Decision**: Campos PII sensíveis criptografados com pgcrypto (chaves por ambiente/tenant via Vault Transit quando aplicável), índices usando hashes quando necessário; acesso mediado por managers/RLS e mascaramento em logs/traces.  
**Rationale**: Atende FR-014/Art. XII/XIII; protege PII em repouso e reduz risco de vazamento cross-tenant.  
**Alternatives considered**: Criptografia apenas na aplicação — expõe risco em dumps/replicas; sem hashing em índices — quebraria privacidade e performance.
