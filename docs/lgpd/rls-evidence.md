# Evidências LGPD — RLS e PII (Frontend Foundation)

Este playbook garante conformidade com Art. XIII (LGPD) e ADR-010, mantendo evidências rastreáveis de isolamento multi-tenant (RLS) e proteção de dados pessoais.

## Checklist Obrigatória (release)

- [ ] Políticas RLS habilitadas (`ENABLE ROW LEVEL SECURITY`) e `CREATE POLICY` revisados para todas as tabelas/views expostas ao frontend (`backend/apps/tenancy/sql/rls_policies.sql`).
- [ ] Managers/QuerySets injetam `tenant_id` automaticamente (ex.: `backend/apps/tenancy/managers.py`) e bloqueiam uso fora do contexto.
- [ ] Suite `pytest backend/apps/tenancy/tests/test_rls_enforcement.py -q` executada com sucesso.
- [ ] Chamadas privilegiadas validam assinatura HMAC-SHA256 do `X-Tenant-Id` (chave raiz por ambiente em Vault/KMS, HKDF por tenant, rotação 90d) com evidência de auditoria por tenant.
- [ ] `TenantThemeToken` e demais colunas sensíveis protegidas por `pgcrypto` (`pgp_sym_encrypt/pgp_sym_decrypt`) e auditadas no migration diff.
- [ ] Telemetria/Logs mascaram PII (verifique `scripts/observability/check_structlog.py` e spans OTEL).
- [ ] Baseline PII verificada (CPF, CNPJ, email, telefone, endereço, nome completo, data de nascimento, documento oficial, geolocalização precisa, IDs de cliente).
- [ ] `docs/runbooks/frontend-foundation.md` atualizado com evidências anexadas no release corrente.

## Fluxo de Execução

1. **Preparar ambiente**
   ```bash
   # Node/Frontend
   pnpm install

   # Python/Backend — Poetry 1.8.3 alinhado ao CI/Docker
   python -m pip install -U pip && pip install "poetry==1.8.3"
   poetry install --with dev --sync --no-interaction --no-ansi
   ```

2. **Validar RLS programaticamente**
   ```bash
   pytest backend/apps/tenancy/tests/test_rls_enforcement.py -q
   ```
   - Persistir o log de execução em `docs/runbooks/evidences/frontend-foundation/<release>/rls-tests.txt`.

3. **Inspecionar políticas diretamente**
   ```bash
   psql $DATABASE_URL -f backend/apps/tenancy/sql/rls_policies.sql --set=ON_ERROR_STOP=1
   ```
   - Execute `\dRp+ <table>` para confirmar `policyname`, `using`, `with check`.

4. **Auditar criptografia pgcrypto**
   ```bash
   psql $DATABASE_URL -c "select column_name, data_type from information_schema.columns where table_name = 'tenant_theme_token';"
   psql $DATABASE_URL -c "select encryption_type from audit.pgcrypto_catalog where table='tenant_theme_token';"
   ```

5. **Scanner de PII**
   ```bash
   python scripts/observability/check_structlog.py logs/frontend-foundation.log \
     --patterns cpf,email,phone,document --fail-on-match
   ```
   - Combine com export OTEL (`curl -X GET $OTEL_EXPORT_URL`) para verificar ausência de atributos proibidos.

6. **Capturar evidências**
   - Exportar painel “RLS Alerts” (`observabilidade/dashboards/frontend-foundation.json`) em CSV.
   - Adicionar print do painel “SC-005 — Incidentes PII (30d)”.
   - Guardar os comandos SQL/pytest acima (arquivo `.md` ou `.txt` no diretório de evidências).

## Scripts Auxiliares

| Script | Objetivo | Observações |
|--------|----------|-------------|
| `pytest backend/apps/tenancy/tests/test_rls_enforcement.py` | Valida isolamento de leitura/escrita e cabeçalho obrigatório `X-Tenant-Id`. | Falhas bloqueiam release. |
| `scripts/observability/check_structlog.py` | Escaneia logs/JSON por padrões de PII. | Inclui regex pré-configuradas para CPF/CNPJ/email/phone. |
| `pnpm finops:report` | (FinOps) Mantém métricas de uso de pipelines, útil para correlacionar custo vs. auditorias LGPD. | Gera `observabilidade/data/foundation-costs.json`. |

## Evidências a versionar

- Arquivo `docs/runbooks/evidences/frontend-foundation/<release>/README.md` com:
  - Data/hora da verificação.
  - Responsáveis e ambiente (staging/prod).
  - Links para dashboards exportados (SC-005, RLS Alerts).
  - Resultados dos comandos acima.
- Artigos/prints adicionais (SQL, logs mascarados, OTEL trace sem PII).

## Observações e Follow-up

- Sempre que surgir novo campo com PII, ampliar o checklist e atualizar `scripts/observability/check_structlog.py`.
- Qualquer exceção ao RLS deve ser registrada em ADR dedicado (linkar Art. XIII).
- Este arquivo deve ser revisado a cada iteração relevante (migração de schema, novo tenant, alteração de contrato).
