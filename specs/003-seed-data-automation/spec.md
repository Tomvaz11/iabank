# Feature Specification: Automacao de seeds, dados de teste e factories

**Feature Branch**: `003-seed-data-automation`  
**Created**: 2025-11-23  
**Status**: Ready for plan  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md` §§3.1, 6, 26; `adicoes_blueprint.md` itens 1, 3, 8, 11; Constituicao v5.2.0 (Art. III/IV, XIII, XVI) e ADRs aplicaveis.

## Contexto

Precisamos automatizar seeds e datasets de teste para ambientes multi-tenant, com PII mascarada e determinismo por ambiente/tenant, garantindo que `seed_data` e factories (factory-boy) sejam reprodutíveis, auditáveis e integradas ao CI/CD e Argo CD. O objetivo é permitir baseline, canary, carga e DR com dados sintéticos que respeitem rate limits (`/api/v1`), volumetria (Q11) e políticas de segurança/compliance sem expor dados reais.

## Clarifications

### Session 2025-11-23 (1)
- Q1: Serialização por tenant/ambiente → A: Advisory lock Postgres com lease curto e fail-closed para evitar concorrência.  
- Q2: Concorrência global → A: Teto de execuções simultâneas por ambiente/cluster com fila curta e expiração fail-closed para proteger SLO/FinOps.  
- Q3: PII/anonimização → A: FPE determinística via Vault Transit por ambiente/tenant, preservando formato; PII em repouso cifrada; fallback só em dev isolado.  
- Q4: Manifestos obrigatórios → A: `seed_data --profile` consome manifestos YAML/JSON versionados por ambiente/tenant com mode, volumetria/caps, rate limit/backoff, TTL, budget e janela off-peak em UTC; validar schema/versão e falhar fail-closed se divergir.  
- Q5: Execução em pipelines → A: CI/PR roda dry-run determinístico do baseline; cargas/DR completas só em staging e perf dedicados, em janela off-peak, com evidência WORM.

### Session 2025-11-23 (2)
- Q6: RLS e privilégio → A: Sempre com RLS habilitado e service account de menor privilégio; preflight de RLS falha se enforcement ausente.  
- Q7: Rate limit/backoff → A: Orçamento por tenant/ambiente; em 429 usar backoff+jitter curto; se persistir ou exceder cap do manifesto, abortar e reagendar off-peak.  
- Q8: Determinismo/datas → A: IDs/valores determinísticos por tenant/ambiente/manifesto; `reference_datetime` obrigatório em ISO 8601 UTC, mudança é breaking e exige reseed coordenado.  
- Q9: DR e dados sintéticos → A: Apenas dados sintéticos (vedado snapshot de prod), com RPO/RTO do blueprint; restauração/validação em staging/perf dedicados e isolados para carga/DR.  
- Q10: Evidências WORM → A: Relatórios JSON assinados (trace/span, manifesto/tenant/ambiente, custos/volumetria/status por lote) em repositório WORM; se indisponível, falhar antes de escrever dados.

> Decisões adicionais detalhadas permanecem registradas em `clarifications-archive.md` e valem como referência normativa para o plano/implementação.

### Clarifications Coverage Summary

| Categoria                           | Status      | Notas                                                     |
|-------------------------------------|-------------|-----------------------------------------------------------|
| Escopo funcional & comportamento    | Resolved    | Seeds baseline/carga/DR/canary, manifestos obrigatórios   |
| Domínio & dados                     | Resolved    | Tenants, manifestos, datasets, checkpoints, PII/keys      |
| UX/fluxos                           | Clear       | Fluxos de seed_data e uso de factories cobertos nas US    |
| NFR (perf/observabilidade/segurança)| Resolved    | Rate limit/backoff, OTEL/Sentry, PII/vault, WORM          |
| Integrações externas                | Resolved    | Mocks/stubs Pact, sem chamadas reais                      |
| Edge cases & falhas                 | Resolved    | Fail-closed, 429, drift, indisponibilidade de vault/WORM  |
| FinOps                              | Resolved    | Budgets/caps por manifesto, abort em estouro              |
| DR/RPO/RTO                          | Resolved    | RPO ≤5 min, RTO ≤60 min, staging/perf dedicados           |
| Cobertura clarify                   | Clear       | 10 Qs no spec + archive referenciado; sem pendências      |

## User Scenarios & Testing *(mandatorio)*

### User Story 5 - Validar manifestos via API (Prioridade: P1)

- **Persona & Objetivo**: QA/SRE valida manifestos v1 via API antes de qualquer execução, garantindo schema/versão e governança de headers.  
- **Valor de Negocio**: Evita drift ou schema inválido chegar à execução, reduzindo falhas e retrabalho.  
- **Contexto Tecnico**: `/api/v1/seed-profiles/validate`, JSON Schema 2020-12, RateLimit-*, Idempotency-Key, Problem Details.

**Independent Test**: `POST /api/v1/seed-profiles/validate` retorna 200 para manifesto v1 válido e 422/429 com Problem Details, mantendo RateLimit-* e Idempotency-Key.

**Acceptance Scenarios (BDD)**:
1. **Dado** um manifesto v1 válido com headers `Idempotency-Key`, `X-Tenant-ID`, `X-Environment`, **Quando** chamo `POST /api/v1/seed-profiles/validate`, **Entao** recebo `200` com `valid=true`, `issues=[]`, `RateLimit-*`, `Retry-After` e versão normalizada.  
2. **Dado** um manifesto com schema/versão divergente ou campos obrigatórios ausentes, **Quando** chamo o endpoint, **Entao** recebo `422` Problem Details com lista de issues e RateLimit-* preservado.  
3. **Dado** um cenário de limite excedido ou retry/backoff ativo, **Quando** chamo o endpoint, **Entao** recebo `429` com `Retry-After` e não inicia execução.

### User Story 1 - Seeds baseline multi-tenant (Prioridade: P1)

- **Persona & Objetivo**: Engenheira de QA provisiona baseline consistente por tenant/ambiente com um comando.  
- **Valor de Negocio**: Reduz preparação de ambientes e falhas por dados desatualizados.  
- **Contexto Tecnico**: CI/PR, tenants segregados, gatilhos em deploy (Argo CD).

**Independent Test**: `seed_data --profile` cria baseline completa por tenant sem violar RLS ou PII.

**Acceptance Scenarios (BDD)**:
1. **Dado** um manifesto válido por tenant/ambiente, **Quando** executo `seed_data --profile=<manifest>`, **Entao** cria baseline determinística e auditável sem erros de validação.  
2. **Dado** isolamento multi-tenant, **Quando** `seed_data` tenta cruzar dados entre tenants, **Entao** a operação é bloqueada e auditada.

### User Story 2 - Factories com PII mascarada (Prioridade: P2)

- **Persona & Objetivo**: Dev backend gera cenários específicos via factory-boy com PII mascarada determinística.  
- **Valor de Negocio**: Testes seguros/determinísticos e aderentes a contratos `/api/v1`.  
- **Contexto Tecnico**: Suites unit/integration, catálogo PII, manifestos por tenant.

**Independent Test**: Factories geram registros com PII mascarada e passam em checagem automática de PII/contratos.

**Acceptance Scenarios (BDD)**:
1. **Dado** uma factory com campos PII, **Quando** gero registros em série, **Entao** todos os campos sensíveis são mascarados e validados.  
2. **Dado** uma chamada `/api/v1/...` usando dados da factory, **Quando** submeto no ambiente de teste, **Entao** o contrato é respeitado e o rate limit não é violado.

### User Story 4 - Orquestrar seed runs via API/CLI (Prioridade: P2)

- **Persona & Objetivo**: SRE/QA agenda, consulta ou cancela execuções via API/CLI com governança de RateLimit/Idempotency/ETag.  
- **Valor de Negocio**: Automação segura e auditável do ciclo de seeds/carga/DR.  
- **Contexto Tecnico**: `/api/v1/seed-runs*`, Argo CD/GitOps, headers obrigatórios e Problem Details.

**Independent Test**: POST/GET/POST cancel em `/api/v1/seed-runs*` retornam cabeçalhos RateLimit-*, Idempotency-Key e ETag/If-Match corretos, com Problem Details previsíveis em 4xx/5xx.

**Acceptance Scenarios (BDD)**:
1. **Dado** manifesto válido e headers `Idempotency-Key`, `X-Tenant-ID`, `X-Environment`, **Quando** chamo `POST /api/v1/seed-runs`, **Entao** recebo `201` com `seed_run_id`, `ETag` e `RateLimit-*`, e a execução inicia com estado `queued/running`.  
2. **Dado** um `seed_run` ativo, **Quando** chamo `POST /api/v1/seed-runs/{id}/cancel` com `If-Match`, **Entao** recebo `202` e o run é finalizado como `aborted` após dreno dos batches.  
3. **Dado** limite de rate/budget excedido ou lock ativo, **Quando** chamo `POST /api/v1/seed-runs`, **Entao** recebo `429` ou `409` com Problem Details e `Retry-After`, sem criar novo run.

### User Story 3 - Carga e DR com dados sintéticos (Prioridade: P3)

- **Persona & Objetivo**: SRE gera volumetria (Q11) configurável para carga e DR sem afetar limites de API.  
- **Valor de Negocio**: Garante previsibilidade de performance e prontidão de DR sem risco a produção.  
- **Contexto Tecnico**: Staging/perf dedicados para carga/DR, rate limits, RPO/RTO do blueprint.

**Independent Test**: Execução de carga usa manifestos, respeita caps/rate limit e entrega evidência WORM de restauração dentro de RPO/RTO em staging/perf dedicados.

**Acceptance Scenarios (BDD)**:
1. **Dado** volumetria por ambiente/tenant no manifesto, **Quando** gero dataset sintético em modo carga, **Entao** respeito rate limits e concluo na janela off-peak com relatório de volumetria.  
2. **Dado** um cenário de DR simulado, **Quando** restauro a partir das seeds/factories, **Entao** o ambiente volta ao estado consistente dentro de RPO/RTO definidos, com logs que comprovam anonimização.

### Edge Cases & Riscos Multi-Tenant

- Execução sem `tenant_id` ou com tenant inexistente falha em modo fail-closed, sem dados parciais.  
- Detectar drift/dados fora do manifesto ou checkpoints divergentes falha e exige limpeza/reseed controlado.  
- Reexecução em modos carga/DR limpa dataset do modo antes de recriar determinístico, evitando inflação.  
- 429/rate limit persistente aborta e reagenda; proibir seguir acima do orçamento do manifesto.  
- Indisponibilidade de Vault/salt ou WORM bloqueia execução antes de gravar dados.  
- Execuções sem RLS ou fora da janela off-peak definida falham e são auditadas.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do código, trajetórias felizes/tristes | Seeds/factories só aprovam com testes automatizados e dry-run em CI/PR. |
| Art. IV (Teste de Integração-Primeiro) | Fluxo integração-primeiro com factories | Dry-run/integração falham antes de código; factories alimentam testes de integração. |
| Art. VI (SLO/Error Budget) | SLOs explícitos (p95/p99, throughput, saturação) e orçamento de erro | Manifestos trazem metas por ambiente/tenant; execuções que rompem metas abortam. |
| Art. VII (Observabilidade) | OTEL + W3C Trace Context, Sentry, logs estruturados com redaction | Traces/métricas/logs por tenant/execução; bloqueia promoção se export falhar ou PII não mascarada. |
| Art. VIII (Entrega) | Release seguro (flags; canary só quando modo=canary) | `seed_data` gated por manifestos/flags e validação pós-deploy em Argo CD. |
| Art. IX (CI) | Cobertura mínima e validações | CI roda dry-run do baseline com checagens de PII/contratos/volumetria. |
| Art. V (Documentação/Versão) | Contrato-primeiro OpenAPI 3.1, SemVer e governança de diffs | Seeds/factories que tocam `/api/v1` obedecem contrato versionado e checagens de compatibilidade. |
| Art. XI (API) | Contratos e resiliência (RateLimit, Idempotency-Key, ETag) | Seeds/factories respeitam contratos `/api/v1`, idempotência, RateLimit headers e Problem Details. |
| Art. XII (Security by Design) | Privilégio mínimo, testes de autorização, proteção de segredos/PII | Execução de seeds exige contas/roles mínimas por ambiente/tenant e testes automatizados de permissão. |
| Art. XIII (LGPD/RLS) | RLS e proteção de PII | Mascaramento determinístico, PII cifrada em repouso, RLS obrigatório. |
| Art. XIV (IaC + GitOps + OPA) | Infra como código com validação policy-as-code | Recursos de seeds (WORM, Vault, filas, pipelines) versionados em Terraform, validados por OPA e promovidos via GitOps/Argo. |
| Art. XV (Dependências) | Gestão contínua de dependências (ADR-008) | Seeds/factories/perf libs entram no ciclo de verificação/atualização automática e bloqueiam CI se desatualizadas/risco alto. |
| Art. XVII (Resiliência/Threat Modeling) | Threat modeling recorrente, runbooks e GameDays | Seeds/carga/DR têm threat modeling dedicado e runbooks testados para falhas/rate limit/PII. |
| Art. XVI (Auditoria/FinOps) | WORM íntegro e FinOps | Caps/budget em manifestos; trilha WORM com integridade verificada e acesso governado; alertas/abortos em caso de estouro. |
| Blueprint §3.1/6/26 | Isolamento, DR, PII, filas idempotentes | Manifestos por tenant, RPO/RTO definidos, seeds/factories idempotentes e auditáveis. |
| Adições 1/3/8/11 | DORA/flags, carga/gate perf, expand/contract, FinOps | Manifestos versionados via GitOps/Argo; gate de performance, expand/contract e caps/alertas. |

### Functional Requirements

- **FR-001**: `seed_data --profile` DEVE provisionar baseline determinística por ambiente/tenant com idempotência e isolamento RLS.  
- **FR-002**: Factories (factory-boy) DEVEM cobrir entidades core e gerar dados sintéticos mascarados, prontos para contratos `/api/v1`.  
- **FR-003**: PII DEVEM ser mascaradas/anonimizadas de forma determinística por ambiente/tenant via Vault; PII em repouso permanece cifrada.  
- **FR-004**: Manifestos versionados por ambiente/tenant são obrigatórios e DEVEM seguir schema explícito (ex.: v1) com campos mínimos: `metadata` (`tenant`, `environment`, `profile`, `version` SemVer, `schema_version`, `salt_version`), `reference_datetime` (ISO 8601 UTC), `mode` (`baseline|carga|dr|canary`), `window.start_utc/end_utc` (off-peak UTC), `volumetry` (caps Q11), `rate_limit`, `backoff` com jitter, `budget`, `ttl`, `slo` e `integrity.manifest_hash` (sha256). Ausência ou versão incompatível falha em fail-closed. Campo `canary` é opcional e só é exigido quando `mode=canary`, devendo estar ausente nos demais modos.  
- **FR-005**: Execuções DEVEM ser serializadas por tenant/ambiente; concorrência global limitada por ambiente/cluster (teto de 2 execuções simultâneas) com fila curta (TTL 5 min) e lock por tenant/ambiente com lease de 60s, sempre fail-closed.  
- **FR-006**: CI/PR DEVE rodar dry-run determinístico do baseline (tenant canônico ou lista curta), validando PII, contratos e idempotência; sem publicar evidência WORM.  
- **FR-007**: Carga e DR DEVEM rodar em staging e perf dedicados, na janela off-peak e com evidência WORM; restauração deve cumprir RPO/RTO do blueprint.  
- **FR-008**: Integrações externas (KYC/antifraude/pagamentos/notificações) DEVEM ser simuladas (mocks/stubs) sem chamadas reais; rate limit exercitado sem side effects.  
- **FR-009**: Eventos/outbox/CDC gerados DEVEM ir para sinks sandbox isolados, sem publicar em destinos reais.  
- **FR-010**: Execução deve falhar se RLS estiver ausente/desabilitado ou se o manifesto não cobrir o perfil/volumetria requeridos.  
- **FR-011**: Relatórios de execução DEVEM ser assinados, ter integridade verificada pós-upload e ser armazenados em WORM com retenção/lock e governança; falha em qualquer etapa (assinatura, verificação, WORM indisponível) bloqueia a execução/promoção (Art. XVI).  
- **FR-012**: `reference_datetime` em ISO 8601 UTC é obrigatório no manifesto; mudanças exigem reseed coordenado e limpeza de checkpoints.  
- **FR-013**: Dados sintéticos são exclusivos; uso de snapshots/dumps de produção é proibido em qualquer ambiente.
- **FR-014**: Seeds/factories DEVEM suportar coordenação assíncrona/idempotente (fila curta, acks tardios, backoff/DLQ) alinhada à estratégia de tarefas do blueprint para evitar perda/duplicidade.  
- **FR-015**: Manifestos e execuções DEVEM seguir fluxo GitOps/Argo CD (promoção/rollback auditados, janelas off-peak, evidência anexada) e falhar sem aprovação ou drift detectado.  
- **FR-016**: Execuções DEVEM expor validação automatizada e mensurável (checklist PII/RLS/contrato/idempotência/rate limit), produzindo relatório WORM com percentuais e itens reprovados.  
- **FR-017**: Modo carga/DR DEVE exercitar testes de performance/capacidade com orçamentos de volumetria/rate limit definidos em manifesto e gate de aprovação antes da promoção.  
- **FR-018**: Operações que acionam `/api/v1` DEVEM respeitar governança de API (Idempotency-Key persistida com TTL/deduplicação auditável, Problem Details RFC 9457, RateLimit-* e ETag/If-Match); descumprimento bloqueia a execução.  
- **FR-019**: Evoluções de schema ligadas às seeds DEVEM seguir padrão expand/contract e índices `CONCURRENTLY`, com checkpoints e rollback seguros.
- **FR-020**: Qualquer uso de `/api/v1` por seeds/factories DEVE estar coberto por contrato OpenAPI 3.1 versionado (SemVer) e checagens de compatibilidade (lint/diff/contrato) antes da execução/promoção.  
- **FR-021**: Execução de `seed_data` DEVE exigir autorização explícita por ambiente/tenant (RBAC/ABAC com privilégio mínimo) e testes automatizados que neguem execuções fora do perfil autorizado.  
- **FR-022**: A automação de seeds/carga/DR DEVE passar por threat modeling dedicado (STRIDE/LINDDUN) e manter runbooks/GameDays para falhas de rate limit, PII/anonimização e DR.
- **FR-023**: Pipeline de CI/CD DEVE aplicar gates de qualidade: cobertura mínima de 85%, complexidade máxima 10, SAST/DAST/SCA e geração de SBOM obrigatórias, além de testes de carga/performance como bloqueadores de promoção; qualquer falha impede promoção de seeds/factories.  
- **FR-024**: Promoções e execuções de `seed_data` DEVEM seguir Trunk-Based (histórico linear, branches curtas, squash-only) + feature flags (canary apenas quando `mode=canary`) com rollback ensaiado e rastreio de métricas DORA; pipeline/Argo DEVEM falhar se o fluxo não cumprir essas condições.  
- **FR-025**: Seeds/factories DEVEM evitar poluição da trilha de auditoria (incluindo WORM) com rotulagem por execução/tenant e preservação de RLS/índices multi-tenant; execuções que gerem drift ou falsos positivos de auditoria devem falhar.  
- **FR-026**: Infraestrutura e artefatos necessários para seeds/factories (WORM, Vault, filas/assíncrono, pipelines CI/CD) DEVEM ser gerenciados como código (Terraform) com validação OPA/policy-as-code e fluxo GitOps/Argo CD; ausência de validação bloqueia promoção.  
- **FR-027**: A gestão de dependências para bibliotecas de seeds/factories/performance e para o cliente de Vault Transit DEVE seguir automação contínua (ADR-008), com checagem/atualização em CI e bloqueio por CVEs críticos ou versões defasadas.  
- **FR-028 (alias de FR-011)**: Alias histórico de FR-011 (WORM/assinatura); não gera checklist próprio nem gate adicional. Rastreabilidade e verificação permanecem apenas em FR-011.  
- **FR-029**: A API/CLI de seed runs (`/api/v1/seed-runs*`) DEVE suportar criar/consultar/cancelar execuções com RateLimit-*, `Idempotency-Key`, `ETag/If-Match` e Problem Details RFC 9457; ausência de headers ou conflito de lock/rate/budget deve retornar 4xx previsível sem criar execuções.
- **FR-030**: O endpoint `/api/v1/seed-profiles/validate` DEVE validar manifestos v1 (JSON Schema 2020-12), aplicar RateLimit-* e `Retry-After`, exigir `Idempotency-Key`, retornar Problem Details previsível em 4xx (incluindo 422 para schema/versão incompatível, 429 para rate-limit/backoff) e nunca iniciar execução em caso de falha.

### Volumetria Q11 (canônica e ambientes)

- Carga/DR somente em staging e perf dedicados; vedado executar carga/DR em produção/controlada.  
- Caps base por entidade (antes de multiplicadores de ambiente): tenant_users 5; customers 100; addresses 150; consultants 10; bank_accounts 120; account_categories 20; suppliers 30; loans 200; installments 2.000; financial_transactions 4.000; limits 100; contracts 150.  
- Caps para carga/DR: tenant_users 10; customers 500; addresses 750; consultants 30; bank_accounts 600; account_categories 60; suppliers 150; loans 1.000; installments 10.000; financial_transactions 20.000; limits 500; contracts 750.  
- Multiplicadores por ambiente: dev = 1x, homolog = 3x, staging/carga = 5x (staging dedicado) e perf = 5x (perf dedicado). Manifestos devem versionar esses caps; divergência falha em lint/diff/schema.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Execuções devem respeitar janelas por ambiente e metas de SLO (p95/p99 de duração/throughput/saturação) definidas em manifesto; violações consomem orçamento de erro e acionam abort/rollback auditado.  
- **NFR-002 (Performance/Rate Limit)**: Carga usa até o orçamento de rate limit/volumetria definido; ao exceder, aborta e reagenda off-peak; gate de performance impede promoção se thresholds não forem atingidos.  
- **NFR-003 (Observabilidade)**: Logs estruturados (redação de PII), métricas e traces OTEL com W3C Trace Context por tenant/ambiente/execução; falhas de exportação ou redaction bloqueiam promoção.  
- **NFR-004 (Segurança/PII)**: Mascaramento e redaction em logs/eventos; acesso às chaves/manifestos segue menor privilégio e audita usos.  
- **NFR-005 (FinOps)**: Caps e budgets por ambiente/tenant medidos em tempo real; alerta em aproximação e abort em estouro, com evidência no relatório.

### Dados Sensiveis & Compliance

- Catalogar PII e aplicar mascaramento determinístico por ambiente/tenant antes de persistir; vedado uso de dados reais.  
- Chaves/salts residem no Vault (segregação por ambiente/tenant, rotação automática); proibido guardar em código/config estática.  
- Evidências imutáveis (WORM) para execuções e restaurações; direito ao esquecimento atendido por limpeza por tenant.  
- DR e carga só com dados sintéticos; RLS obrigatório em todas as execuções.

## Key Entities & Relationships

- **Tenant**: identificador e políticas de RLS; relaciona com manifestos, datasets e evidências.  
- **Manifesto (seed_profile)**: por ambiente/tenant; contém metadata completa, mode (`baseline|carga|dr|canary`), `canary` (somente quando `mode=canary`), volumetria/caps, rate limit/backoff, TTL, budget, `reference_datetime`, janela off-peak, SLOs e versão/schema + `integrity.manifest_hash`.  
- **Mode/Profile**: baseline vs carga vs DR vs canary, definindo escopo de entidades/estados e caps; `canary` exige bloco dedicado e é vedado nos demais modos.  
- **Dataset sintético**: conjunto de registros gerados por mode/tenant; vinculado ao manifesto e ao checkpoint.  
- **Checkpoint/Idempotência**: estado de execução por lote/tenant/mode; guarda hashes/versão para retomada/limpeza.  
- **PII/Keys**: catálogo de campos sensíveis e chaves/salts de anonimização por ambiente/tenant.  
- **Budget/RateLimit**: limites financeiros e de throughput do manifesto, aplicados por tenant/mode.  
- **Evidência WORM**: relatórios assinados com trace/span, manifesto/tenant/ambiente, custos/volumetria/status por lote; armazenados imutavelmente e indexados.
- **Entidades bancárias (Blueprint §3.1)**: Customer/Address/Consultant/BankAccount/AccountCategory/Supplier/Loan/Installment/FinancialTransaction/CreditLimit/Contract com `tenant_id`, estados enumerados (ex.: Loan `IN_PROGRESS/PAID_OFF/IN_COLLECTION/CANCELED`, Installment `PENDING/PAID/OVERDUE/PARTIALLY_PAID`, BankAccount `ACTIVE/BLOCKED`, CreditLimit `ACTIVE/FROZEN/CANCELED`), campos PII (document_number/email/phone/address/account_number/agency) protegidos por FPE+pgcrypto e unicidades por tenant. Factories e serializers DEVEM respeitar esses estados e contratos `/api/v1`.

## Assumptions & Defaults

- Manifestos vivem no repositório de aplicação em paths estáveis (ex.: `configs/seed_profiles/<ambiente>/<tenant>.yaml`), versionados via PR/GitOps.  
- **Q11 (Volumetria/caps)**: catálogo obrigatório de caps por entidade (contagem de registros por modo baseline/carga/DR/canary e por ambiente/tenant), declarado no manifesto e usado como fonte única para throughput/FinOps/performance; ausência ou cap fora do catálogo falha em fail-closed.  
- Schema de manifesto presume versão explícita (ex.: v1) com campos obrigatórios (`metadata` completo, mode `baseline|carga|dr|canary`, `canary` só quando `mode=canary`), volumetria/caps, rate limit/backoff+jitter, budgets/error budget, janela off-peak UTC, `reference_datetime`, SLO/performance e `integrity.manifest_hash`; defaults declarados no próprio manifesto; lacunas ou versões não suportadas devem falhar em fail-closed.  
- Baseline cobre apenas domínios core; estados “sad path” ficam restritos aos modos carga/DR conforme manifesto.  
- Off-peak é declarado em UTC no manifesto (par único start/end); execuções fora da janela falham.
- Promoção/rollback das execuções ocorre via Argo CD/GitOps, vinculando cada execução a um commit e impedindo drift.

## Success Criteria *(mandatorio)*

- **SC-001**: `seed_data` conclui por ambiente dentro dos tempos-alvo de manifesto, p95/p99 dentro das metas e 0 erros de validação/PII/RLS.  
- **SC-002**: Factories cobrem 100% das entidades core e passam nas checagens automáticas de PII, contratos `/api/v1`, RateLimit e idempotência.  
- **SC-003**: CI/PR mantém taxa de sucesso ≥99% no dry-run do baseline, com cobertura ≥85%, complexidade ≤10, SAST/DAST/SCA/SBOM verdes, gate de carga/performance aprovado e falha antecipada se qualquer checagem ou teste de integração cair.  
- **SC-004**: Carga/DR respeitam caps de rate limit/volumetria, passam no gate de performance/capacidade e produzem evidência WORM; restauração cumpre RPO ≤ 5 minutos e RTO ≤ 60 minutos definidos no blueprint.  
- **SC-005**: Budgets/FinOps respeitados por ambiente/tenant, com alertas antes do teto e bloqueio em estouro auditado.  
- **SC-006**: Observabilidade ativa (traces/logs/métricas OTEL+W3C) sem PII exposta e sem falhas de export/redaction; violações bloqueiam promoção.  
- **SC-007**: Fluxo GitOps/Argo CD promove apenas com manifesto válido, sem drift detectado e com rollback testado; relatórios WORM vinculam commit/tenant/ambiente.  
- **SC-008**: Orçamento de erro (SLO) não estourado durante campanhas de seeds/carga; exceder orçamento implica abort e reagendamento off-peak com evidência.
- **SC-009**: Governança de API e autorização validadas: contratos `/api/v1` aprovados sem diffs incompatíveis e execuções `seed_data` bloqueiam identidades não autorizadas, com evidências nos relatórios. 
- **SC-010**: Promoções/execuções de `seed_data` ocorrem via flags (canary apenas quando `mode=canary`) com rollback ensaiado e métricas DORA visíveis; ausência dessas evidências bloqueia promoção.
