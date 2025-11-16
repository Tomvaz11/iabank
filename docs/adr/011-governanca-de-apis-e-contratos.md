# 11. Governança de APIs e Contratos

**Status:** Aprovado

**Contexto:** O Artigo XI (Governança de API) estabelece princípios contrato-primeiro, rate limiting, idempotência e controle de concorrência. As adições enterprise detalham práticas complementares (lint/diff, testes de contrato Pact, cabeçalhos RateLimit, status 428) que precisam ser institucionalizadas sem inflar a Constituição.

**Decisão:**
- **Lint e diff de OpenAPI:** Toda modificação de contrato REST deve passar por lint automático (`spectral`) e verificação de compatibilidade usando **Redocly OpenAPI CLI** (`openapi diff`) no pipeline de CI.
- **Testes de contrato:** Produtores e consumidores de APIs REST implementam testes de contrato baseados em **Pact**. A execução ocorre no CI e bloqueia merges quando há incompatibilidade.
- **Rate limiting e comunicação de limites:** Endpoints protegidos por rate limiting DEVEM retornar cabeçalhos `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` e usar `Retry-After` com `429 Too Many Requests`.
- **Idempotência e concorrência:** Mutations sensíveis DEVEM aceitar `Idempotency-Key` com backoff exponencial + jitter e aplicar `ETag/If-Match` (ou `If-None-Match`) gerando `428 Precondition Required` quando o cabeçalho condicional estiver ausente em operações que exigem controle de concorrência.

**Consequências:**
- Pull Requests que alterem contratos só podem ser aprovadas após lint/diff verde e pactos atualizados.
- Mudanças que afetem limites de rate limiting devem ajustar documentação e testes associados.
- Requisições sem cabeçalhos condicionais apropriados devem falhar explicitamente, exigindo tratamento no frontend/cliente.

**Referências Operacionais:**
- Runbook: `docs/runbooks/governanca-api.md`
- Checklist de CI: `docs/pipelines/ci-required-checks.md`
