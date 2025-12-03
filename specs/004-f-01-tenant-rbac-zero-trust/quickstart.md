# Quickstart — Tenants, RBAC+ABAC e MFA

## Pré-requisitos
- PostgreSQL 15 com RLS habilitada e políticas aplicadas (`CREATE POLICY`), variável `iabank.tenant_id` setada via middleware.  
- Vault/KMS acessível para derivar chave HMAC raiz e salts HKDF por tenant; variável `TENANT_HMAC_KEY` carregada no ambiente de CI/dev.  
- Redis disponível para rate limiting e deduplicação de `Idempotency-Key` (TTL 24h).  
- WORM (S3 Object Lock) acessível; se indisponível, operações críticas devem falhar.  
- Contratos OpenAPI/Pact gerados em `/home/pizzaplanet/meus_projetos/iabank/specs/004-f-01-tenant-rbac-zero-trust/contracts/` e lintados (Spectral/oasdiff).
- Schema ABAC parametrizável por tenant em `configs/abac/tenant-policy.schema.json` (baseline obrigatória + atributos custom aprovados).

## Assinar `X-Tenant-Id` (HMAC-SHA256 + HKDF)
```bash
TENANT_ID="tenant-a"
ROOT_KEY_HEX="$(printenv TENANT_HMAC_KEY)"  # chave raiz obtida do Vault/KMS
TENANT_SALT="$(printenv TENANT_SALT_VERSION)" # ex: tenant-a-salt-v1 (registrado em TenantSecurityProfile)
SIGNATURE=$(python - <<'PY'
import os, hmac, hashlib, binascii
tenant_id = os.environ["TENANT_ID"].encode()
root_key = binascii.unhexlify(os.environ["ROOT_KEY_HEX"])
salt = os.environ["TENANT_SALT"].encode()
info = b"iabank-tenant-binding"

def hkdf_extract(salt_bytes, ikm):
    return hmac.new(salt_bytes, ikm, hashlib.sha256).digest()

def hkdf_expand(prk, info_bytes, length=32):
    t = b""
    okm = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info_bytes + bytes([counter]), hashlib.sha256).digest()
        okm += t
        counter += 1
    return okm[:length]

prk = hkdf_extract(salt, root_key)
derived = hkdf_expand(prk, info)
sig = hmac.new(derived, tenant_id, hashlib.sha256).hexdigest()
print(sig)
PY)
echo "Assinatura: $SIGNATURE"
```
Headers esperados: `X-Tenant-Id: tenant-a` e `X-Tenant-Signature: <hex>`; o middleware faz `SET LOCAL iabank.tenant_id` só a partir da sessão/claim, ignorando overrides e rejeitando ausência/divergência com Problem Details 403/404 e auditoria WORM.

## Criar tenant (estado Pending) — idempotente
```bash
curl -X POST https://api.iabank.local/api/v1/tenants \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: platform" \
  -H "X-Tenant-Signature: $SIGNATURE" \
  -H "Idempotency-Key: tenant-create-$(uuidgen)" \
  -d '{
    "slug": "tenant-a",
    "display_name": "Tenant A",
    "allowed_domains": ["tenant-a.com"],
    "risk_classification": "high",
    "region": "America/Sao_Paulo",
    "retention_policy_days": 365,
    "idp_provider": "oidc",
    "idp_metadata": {"issuer": "https://idp.tenant-a.com", "client_id": "abc", "jwks_uri": "https://idp.tenant-a.com/jwks"},
    "security_contacts": ["secops@tenant-a.com"],
    "ops_contacts": ["ops@tenant-a.com"]
  }'
```
Resposta esperada: `201` com `state=pending`, `ETag` e headers `RateLimit-*`. Replays com mesmo payload retornam 201/200; payload divergente retorna `409 idempotency_conflict`.

## Ativar/bloquear tenant com controle otimista
```bash
ETAG="<da-resposta-get>"
curl -X POST https://api.iabank.local/api/v1/tenants/tenant-a/transitions \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: platform" \
  -H "X-Tenant-Signature: $SIGNATURE" \
  -H "Idempotency-Key: tenant-activate-$(uuidgen)" \
  -H "If-Match: $ETAG" \
  -d '{"target_state": "active", "reason": "onboarding aprovado"}'
```
- `412` se `If-Match` desatualizado; `428` se `If-Match` ausente; `429` se rate limit excedido com `Retry-After`.  
- Transições inválidas (ex.: de `blocked` para `active` sem revisão) retornam Problem Details 409/422.  
- Eventos são registrados em WORM com hash/assinatura; falha de WORM retorna 503 fail-close.

## Publicar nova versão de role (RBAC+ABAC)
```bash
curl -X POST https://api.iabank.local/api/v1/roles \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-a" \
  -H "X-Tenant-Signature: $SIGNATURE" \
  -H "Idempotency-Key: role-create-$(uuidgen)" \
  -d '{
    "slug": "approver",
    "display_name": "Aprovador",
    "permissions": ["tenants:read", "roles:read"],
    "abac_rules": {"classification": ["internal"], "region": ["sa-east-1"], "resource_type": ["approval"] }
  }'

curl -X POST https://api.iabank.local/api/v1/roles/{role_id}/versions \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-a" \
  -H "X-Tenant-Signature: $SIGNATURE" \
  -H "If-Match: <role-etag>" \
  -H "Idempotency-Key: role-v2-$(uuidgen)" \
  -d '{
    "permissions": ["tenants:read", "roles:read", "tenants:block"],
    "abac_rules": {"baseline": {"classification": ["internal"], "region": ["sa-east-1"], "resource_type": ["approval"], "unit": ["sao-paulo"]}}
  }'
```
- `412` se ETag divergente; `403/404` Problem Details em tentativa cross-tenant; `422` se baseline de atributos faltar.  
- Cada versão gera histórico e evento WORM; Pact/OpenAPI devem ser atualizados/lintados.

## Fluxo de token com MFA obrigatória
```bash
curl -X POST https://api.iabank.local/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-a" \
  -H "X-Tenant-Signature: $SIGNATURE" \
  -H "Idempotency-Key: login-$(uuidgen)" \
  -d '{
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "idp_assertion": "<JWT do IdP>",
    "mfa_code": "<TOTP>",
    "device_fingerprint": "abc123"
  }'
```
- `401/403` Problem Details se MFA ausente/expirada ou assertion inválida; refresh token emitido apenas em cookie `HttpOnly; Secure; SameSite=Strict`; reuse gera revogação e alerta.  
- Headers `RateLimit-*`/`Retry-After` sempre presentes; `429` em excesso.  
- Logs são mascarados; PII não aparece em URLs ou trace attributes.

## Check rápido de contratos e RLS (CI)
```bash
pnpm exec spectral lint /home/pizzaplanet/meus_projetos/iabank/specs/004-f-01-tenant-rbac-zero-trust/contracts/tenant-rbac.openapi.yaml
pnpm exec oasdiff breaking \
  /home/pizzaplanet/meus_projetos/iabank/contracts/current.openapi.yaml \
  /home/pizzaplanet/meus_projetos/iabank/specs/004-f-01-tenant-rbac-zero-trust/contracts/tenant-rbac.openapi.yaml
pytest backend/apps/tenancy/tests/test_rls_binding.py -q
yarn jsonlint configs/abac/tenant-policy.schema.json  # ou equivalente para validar schema ABAC baseline/custom
```
- Fails se contratos divergirem, se faltar `Problem Details`, headers `RateLimit-*`/`Retry-After` em GET/POST ou se RLS/`SET LOCAL` permitir cross-tenant.  
- Valide políticas RLS no banco: `psql $DATABASE_URL -f backend/apps/tenancy/sql/rls_policies.sql --set=ON_ERROR_STOP=1` e use `\dRp+ <tabela>` para checar `USING/WITH CHECK` default deny (`tenant_id = current_setting('iabank.tenant_id')::uuid`).  
- Evidência WORM: uploads precisam de hash/assinatura verificados; falha bloqueia release.  
- k6 para p95: `k6 run observabilidade/k6/auth-abac.js` (esperado <400ms p95, p99 <600ms); exporte resultados para dashboards OTEL/Prometheus.
