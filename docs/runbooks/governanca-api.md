# Runbook: Governança de API e Contratos

Aplicação operacional do **ADR-011** e do Artigo XI da Constituição.

## Checklist por Entrega
1. **Contratos OpenAPI**
   - Confirme que o arquivo em `/contracts/api.yaml` foi atualizado.
   - Execute `pnpm run openapi:lint` (Spectral) e `pnpm run openapi:diff` (openapi-diff). Ambos DEVEM falhar o pipeline se houver erro.
2. **Testes de contrato (Pact)**
   - Rode `pnpm run pact:verify` e verifique publicação do pacto no broker.
   - Garanta que consumidores atualizaram verificações (`pact-broker can-i-deploy`).
3. **Rate limiting e cabeçalhos**
   - Utilize `scripts/api/check_rate_headers.sh` para validar `RateLimit-*` e `Retry-After`.
4. **Idempotência e concorrência**
   - Assegure que novos endpoints mutáveis aceitem `Idempotency-Key` e validem `ETag/If-Match`.
   - Verifique o armazenamento das chaves de idempotência (TTL, deduplicação e limpeza periódica) e documente o backend utilizado.
   - Testes de integração devem cobrir status `428 Precondition Required`.

## Ações no Pipeline
- Workflow `ci-contracts.yml` executa Spectral, openapi-diff e Pact (com degradação controlada quando ferramentas não estiverem instaladas).
- Pull requests só podem ser mergeadas após o gate `Contracts Passed`.

## Auditoria
- Armazene relatórios do diff e resultados do Pact no bucket WORM.
- Atualize `docs/runbooks/api-governance.md` com links para cada release.
