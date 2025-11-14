# Quickstart — F-11 Automacao de Seeds e Dados de Teste

## 1. Pré-requisitos
- Python 3.11 instalado (alinhado ao backend atual).
- Docker/Docker Compose para executar PostgreSQL, Redis, backend Django/DRF e stack de observabilidade.
- Acesso local às chaves necessárias para `pgcrypto`/Vault (por exemplo, `PGCRYPTO_KEY`) conforme runbooks de segurança.
- Ferramentas de teste:
  - `pytest` + `pytest-django` para testes de unidade/integração.
  - k6 (ou Gatling equivalente) para testes de carga.
  - Ferramentas CLI do monorepo (`pnpm`, scripts em `scripts/`).

## 2. Inicializar monorepo e stack local
```bash
git checkout 003-seed-data-automation
pnpm install
poetry install --with dev
```

```bash
./scripts/dev/foundation-stack.sh up
```
- Sobe PostgreSQL, Redis, backend Django e componentes de observabilidade (OTEL collector, Sentry/dev, etc.).
- Aplica migrações, habilita RLS multi-tenant e prepara tenants de demo (ex.: `tenant-default`, `tenant-alfa`, `tenant-beta`) conforme especificações existentes.

## 3. Executar `seed_data` localmente
```bash
cd backend
python manage.py seed_data \
  --env dev \
  --profile small \
  --tenants tenant-default,tenant-alfa \
  --mode sync
```
- Usa o perfil declarativo `SeedProfile` (`dev-small`) configurado em `backend/apps/foundation/seeds/config/dev/small.yaml`.
- Gera dados sintéticos multi-tenant (clientes, contratos, transações, usuários) com volumetria pequena adequada para desenvolvimento.
- Registra um `SeedRun` e múltiplos `SeedRunEntityMetric`, permitindo verificar contagens por entidade/tenant e tempo de execução.

Parâmetros principais:
- `--env` controla o ambiente lógico (`dev`, `hom`, `perf`, `dr`, `review`).  
- `--profile` combina com `--env` para selecionar o perfil declarativo (`dev-small`, `dev-medium`, etc.).  
- `--tenants` aceita uma lista de slugs separados por vírgula; se omitido, todos os tenants ativos são considerados.  
- `--mode` pode ser `sync`, `async` ou `auto` (recomendado em pipelines), onde `auto` usa `sync` para perfis `small` em `dev/hom` e `async` para volumetrias maiores.  

Para reexecução idempotente (incluindo cenários de restauração/DR):
```bash
python manage.py seed_data \
  --env dev \
  --profile small \
  --tenants tenant-default,tenant-alfa \
  --mode sync \
  --allow-reuse
```
- Não duplica registros de negócio; consolida métricas de reuso/criação em `SeedRunEntityMetric`.

## 4. Validar anonimização e PII
Após executar `seed_data`, rode os testes de segurança:
```bash
cd /home/pizzaplanet/meus_projetos/iabank
pytest tests/security/test_pii_scanner_seeds.py
```
- Garante que datasets gerados não contenham PII real (CPF/CNPJ, e-mails, telefones, endereços) e que regras de anonimização/máscara definidas em `PiiFieldMapping`/`AnonymizationRule` estejam ativas.
- Falhas nesses testes devem bloquear merges e deploys em ambientes não produtivos.

## 5. Exercitar API `/api/v1` com datasets de seeds
Com o backend e seeds aplicados:
```bash
cd /home/pizzaplanet/meus_projetos/iabank
pytest backend/apps/foundation/tests/test_seed_data_command_integration.py
pytest backend/apps/tenancy/tests/test_seed_data_multi_tenant.py
pytest tests/contracts/test_seed_data_openapi_usage.py
```
- Usa o catálogo de factories central em `backend/apps/foundation/factories/` para compor cenários de teste.
- Valida que chamadas à API `/api/v1` (conforme `contracts/api.yaml` e `specs/003-seed-data-automation/contracts/seed-data-openapi.yaml`) respeitam RateLimit, retornam erros RFC 9457 (`429`/`Retry-After`/`RateLimit-*`) e mantêm SLOs definidos.

## 6. Rodar testes de carga com perfis de volumetria
Para testar volumetria alinhada a Q11:
```bash
cd /home/pizzaplanet/meus_projetos/iabank
python backend/manage.py seed_data --env perf --profile large --mode async
pnpm k6 run tests/performance/test_seed_data_load_profiles.js
```
- O perfil `perf-large` gera milhares/dezenas de milhares de registros por entidade/tenant, conforme `seed-data-openapi.yaml` (`x-seedProfiles`).
- O teste k6 deve respeitar limites de consumo da API por ambiente/tenant e validar que SLOs de latência/erro permanecem dentro dos budgets.

## 7. Integração com CI/CD e GitOps (visão rápida)
- **CI (dev/hom)**:
  - Etapa “Apply Seeds”: `python backend/manage.py seed_data --env dev --profile small --mode auto`.
  - Etapa “PII Scan”: `pytest tests/security/test_pii_scanner_seeds.py`.
  - Etapa “Contracts & Load”: Pact/OpenAPI + testes de carga leve.
- **GitOps/Argo CD + Terraform**:
  - Após provisionamento de ambiente, Job Kubernetes executa `seed_data` com perfil adequado (`hom-medium`, `perf-large`).
  - Métricas de `SeedRun`/`SeedRunEntityMetric` alimentam dashboards de preparação de ambiente e FinOps.

> Importante: `seed_data` não deve ser executado com `--env=prod` na feature F-11; seeds de negócio em produção permanecem proibidas, e seeds técnicas continuam sendo tratadas por mecanismos existentes (migrações/fixtures técnicas).

## 8. Checklist antes do PR
- [ ] `seed_data` executado localmente com sucesso em `dev-small`, sem duplicar registros por tenant.  
- [ ] Testes de integração/contrato relacionados a seeds/anonimização verdes (`pytest backend/apps/foundation/tests/test_seed_data_command_integration.py`, `pytest tests/security/test_pii_scanner_seeds.py`).  
- [ ] Testes de carga básicos contra `/api/v1` em dev/hom com perfis `small`/`medium` executados sem violar RateLimit/SLOs.  
- [ ] `specs/003-seed-data-automation/plan.md`, `research.md`, `data-model.md` e `contracts/seed-data-openapi.yaml` revisados e consistentes com `contracts/api.yaml`.  
- [ ] Evidências de anonimização forte e ausência de PII real em datasets e logs anexadas (relatórios de scanner em `artifacts/`).  
- [ ] Impacto em FinOps avaliado (tempo de execução de seeds, custo dos testes de carga) e documentado em dashboards/reportes apropriados.  

## 9. Mapa de evidências para SC-001..SC-005

- **SC-001** — Evidenciado pela duração das execuções `SeedRun` (campo `duration_ms` em `specs/003-seed-data-automation/data-model.md:52`) e pela execução bem-sucedida dos testes de integração `backend/apps/foundation/tests/test_seed_data_command_integration.py` e `backend/apps/tenancy/tests/test_seed_data_multi_tenant.py` em pipelines de desenvolvimento/homologação, garantindo ambientes prontos em até 10 minutos.  
- **SC-002** — Evidenciado pela existência de pelo menos um teste automatizado por user story entre os testes de integração mencionados acima, os testes de contrato de seeds (`tests/contracts/test_seed_data_openapi_usage.py`) e os testes de carga (`tests/performance/test_seed_data_load_profiles.js`), cobrindo comportamento de seeds, anonimização de PII e respeito a RateLimit/API.  
- **SC-003** — Evidenciado pelos resultados de `pytest tests/security/test_pii_scanner_seeds.py` (ausência de PII real em datasets de teste) e pelo status `pii_scan_status` de `SeedDatasetSnapshot` em `specs/003-seed-data-automation/data-model.md:112-121`, que deve estar em `pass` para datasets utilizados em ambientes não produtivos.  
- **SC-004** — Evidenciado pela execução de cenários de carga com `pnpm k6 run tests/performance/test_seed_data_load_profiles.js`, verificando que os objetivos de throughput/latência para APIs críticas são atingidos e que a taxa de respostas associadas a limite de consumo (HTTP 429) permanece abaixo de 1% durante o período de teste, salvo cenários desenhados especificamente para exercitar RateLimit.  
- **SC-005** — Evidenciado por relatórios de custo que isolam o impacto de execuções de `seed_data`, criação de ambientes efêmeros e testes de carga, garantindo que o custo incremental mensal permaneça dentro de 10% do budget por ambiente/tenant, conforme métricas de FinOps descritas em `adicoes_blueprint.md` e nos scripts de validação de tags de custo em `docs/pipelines/ci-required-checks.md`.  
