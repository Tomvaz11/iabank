# Evidências LGPD — RLS e PII (Frontend Foundation)

Objetivo
- Registrar evidências de isolamento multi-tenant (RLS) e proteção de PII conforme Art. XIII e ADR-010.

Checklist de Verificação
- [ ] Políticas RLS ativas nas tabelas/view expostas ao frontend (CREATE POLICY + ENABLE RLS). 
- [ ] Managers aplicam `tenant_id` automaticamente em consultas.
- [ ] Testes automatizados de isolamento (ex.: `backend/apps/tenancy/tests/test_rls_enforcement.py`) passam.
- [ ] Campos sensíveis usam `pgcrypto` e não são retornados ao frontend (somente versões mascaradas).
- [ ] Telemetria/Logs não contêm PII (mascaramento aplicado no collector OTEL).
 - [ ] Baseline de PII validada: CPF, CNPJ, email, telefone, endereço, nome completo, data de nascimento, documento (RG/Passaporte), geolocalização precisa, quaisquer IDs de cliente.

Scripts/Procedimentos
- Executar suite de testes de RLS: `pytest backend/apps/tenancy/tests/test_rls_enforcement.py -q`.
- Validar criptografia `pgcrypto` via migrações e queries de inspeção.
- Verificar masking no collector OTEL: checar atributos de spans/logs para ausência de PII.
 - Executar scanner de PII (regex mínimas: CPF, email, telefone) sobre logs de desenvolvimento e payloads de telemetria exportados.

Evidências a Anexar
- Capturas de tela dos dashboards de alertas de RLS/OTEL.
- Logs de execução dos testes de RLS.
- Excertos de schema/migrações com `CREATE POLICY`.

Observações
- Atualizar este documento a cada mudança relevante de schema/fluxo de dados.
