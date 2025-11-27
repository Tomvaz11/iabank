# GameDay seed_data (carga/DR)

- **Objetivo**: validar RPO<=5m e RTO<=60m, bloqueio de outbound real e fail-close de WORM/Vault/OTEL para seeds baseline/carga/DR antes de liberar US5/US1.
- **Escopo**: ambientes staging e perf dedicados; tenants canonicamente versionados nos manifestos v1; usando cost-model `configs/finops/seed-data.cost-model.yaml`.
- **Owners**: seed platform (@seed-admins), SRE (@sre-seeds), Sec/Privacidade (@security-lgpd).

## Cenarios
1) **429 persistente na fila**: simular cap global atingido e confirmar Problem Details 429 + Retry-After, sem enfileirar seeds. Esperado: `SeedQueue` marca pendencias como expiradas em 5m; budget nao consumido.
2) **Falha WORM**: negar acesso ao bucket/role e executar `seed_data` (modo carga). Esperado: preflight retorna 503 `worm-unavailable`, nenhuma escrita em DB ou WORM, auditoria com fingerprint de manifesto.
3) **Drift de manifesto**: alterar `manifest_hash` e reprocessar; execucao deve falhar antes de enfileirar batches e exigir limpeza/checkpoint. Esperado: Problem Details `manifest_hash_mismatch`, relatorio WORM com status `failed`.
4) **OTEL/Sentry fora do ar**: desligar exporter e rodar smoke; execucao deve falhar com `telemetry_unavailable` e nao prosseguir para batches.

## Roteiro
- Preparar tenants/manifestos canones e roles (`seed-runner`, `seed-admin`). Validar `scripts/ci/check-migrations.sh` e `scripts/ci/validate-finops.sh` antes do ensaio.
- Executar cada cenario isoladamente com `Idempotency-Key` unico e registrar spans/logs. Coletar `RateLimit-*`, `Retry-After`, `error_budget_remaining`, `seed_rate_limit_remaining`.
- Registrar RPO/RTO medidos, Problem Details emitidos e evidencias WORM (quando aplicavel). Falhas devem bloquear promocao/Argo ate ajuste.

## Criterios de sucesso
- Nenhum dataset real escrito; stubs Pact/Prism usados; outbound real bloqueado.
- RPO<=5m e RTO<=60m comprovados; budgets respeitados (alerta 80%, abort 100%).
- Evidencias WORM assinadas ou erro fail-close documentado; logs/OTEL sem PII.
