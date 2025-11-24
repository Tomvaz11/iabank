# Feature Specification: Automacao de seeds, dados de teste e factories

**Feature Branch**: `003-seed-data-automation`  
**Created**: 2025-11-23  
**Status**: Ready for plan  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md` §§3.1, 6, 26; `adicoes_blueprint.md` itens 1, 3, 8, 11; Constituicao v5.2.0 (Art. III/IV, XIII, XVI) e ADRs aplicaveis.

## Contexto

Precisamos automatizar seeds e datasets de teste para ambientes multi-tenant, com PII mascarada e determinismo por ambiente/tenant, garantindo que `seed_data` e factories (factory-boy) sejam reprodutíveis, auditáveis e integradas ao CI/CD e Argo CD. O objetivo é permitir baseline, carga e DR com dados sintéticos que respeitem rate limits (`/api/v1`), volumetria (Q11) e políticas de segurança/compliance sem expor dados reais.

## Clarifications

### Session 2025-11-23 (1)
- Q1: Serialização por tenant/ambiente → A: Advisory lock Postgres com lease curto e fail-closed para evitar concorrência.  
- Q2: Concorrência global → A: Teto de execuções simultâneas por ambiente/cluster com fila curta e expiração fail-closed para proteger SLO/FinOps.  
- Q3: PII/anonimização → A: FPE determinística via Vault Transit por ambiente/tenant, preservando formato; PII em repouso cifrada; fallback só em dev isolado.  
- Q4: Manifestos obrigatórios → A: `seed_data --profile` consome manifestos YAML/JSON versionados por ambiente/tenant com mode, volumetria/caps, rate limit/backoff, TTL, budget e janela off-peak em UTC; validar schema/versão e falhar fail-closed se divergir.  
- Q5: Execução em pipelines → A: CI/PR roda dry-run determinístico do baseline; cargas/DR completas só em staging dedicado em janela off-peak com evidência WORM.

### Session 2025-11-23 (2)
- Q6: RLS e privilégio → A: Sempre com RLS habilitado e service account de menor privilégio; preflight de RLS falha se enforcement ausente.  
- Q7: Rate limit/backoff → A: Orçamento por tenant/ambiente; em 429 usar backoff+jitter curto; se persistir ou exceder cap do manifesto, abortar e reagendar off-peak.  
- Q8: Determinismo/datas → A: IDs/valores determinísticos por tenant/ambiente/manifesto; `reference_datetime` obrigatório em ISO 8601 UTC, mudança é breaking e exige reseed coordenado.  
- Q9: DR e dados sintéticos → A: Apenas dados sintéticos (vedado snapshot de prod), com RPO/RTO do blueprint; restauração/validação em staging de carga/DR isolado.  
- Q10: Evidências WORM → A: Relatórios JSON assinados (trace/span, manifesto/tenant/ambiente, custos/volumetria/status por lote) em repositório WORM; se indisponível, falhar antes de escrever dados.

## User Scenarios & Testing *(mandatorio)*

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

### User Story 3 - Carga e DR com dados sintéticos (Prioridade: P3)

- **Persona & Objetivo**: SRE gera volumetria (Q11) configurável para carga e DR sem afetar limites de API.  
- **Valor de Negocio**: Garante previsibilidade de performance e prontidão de DR sem risco a produção.  
- **Contexto Tecnico**: Staging de carga/DR, rate limits, RPO/RTO do blueprint.

**Independent Test**: Execução de carga usa manifestos, respeita caps/rate limit e entrega evidência WORM de restauração dentro de RPO/RTO.

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
| Art. IV (Qualidade Dados) | Integridade e rastreabilidade | Relatórios assinados, manifestos versionados e checkpoints/idempotência. |
| Art. VIII (Entrega) | Release seguro (flag/canary/rollback) | `seed_data` gated por manifestos/flags e validação pós-deploy em Argo CD. |
| Art. IX (CI) | Cobertura mínima e validações | CI roda dry-run do baseline com checagens de PII/contratos/volumetria. |
| Art. XI (API) | Contratos atualizados/resilientes | Seeds/factories respeitam contratos `/api/v1` e testes de contrato. |
| Art. XIII (LGPD/RLS) | RLS e proteção de PII | Mascaramento determinístico, PII cifrada em repouso, RLS obrigatório. |
| Art. XVI (FinOps) | Budgets e custos rastreados | Caps/budget em manifestos; alertas/abortos em caso de estouro. |
| Blueprint §3.1/6/26 | Isolamento, DR, PII | Manifestos por tenant, RPO/RTO definidos, dados sintéticos e trilha WORM. |
| Adições 1/3/8/11 | Determinismo, volumetria Q11, GitOps | Manifestos versionados, Argo CD/Cron e expurgo automático por TTL. |

### Functional Requirements

- **FR-001**: `seed_data --profile` DEVE provisionar baseline determinística por ambiente/tenant com idempotência e isolamento RLS.  
- **FR-002**: Factories (factory-boy) DEVEM cobrir entidades core e gerar dados sintéticos mascarados, prontos para contratos `/api/v1`.  
- **FR-003**: PII DEVEM ser mascaradas/anonimizadas de forma determinística por ambiente/tenant via Vault; PII em repouso permanece cifrada.  
- **FR-004**: Manifestos versionados por ambiente/tenant são obrigatórios (mode, volumetria/caps, rate limit/backoff, TTL, budget, janela off-peak em UTC); divergência de schema/versão falha em fail-closed.  
- **FR-005**: Execuções DEVEM ser serializadas por tenant/ambiente; concorrência global limitada por ambiente/cluster com fila curta e fail-closed.  
- **FR-006**: CI/PR DEVE rodar dry-run determinístico do baseline (tenant canônico ou lista curta), validando PII, contratos e idempotência; sem publicar evidência WORM.  
- **FR-007**: Carga e DR DEVEM rodar em staging dedicado, na janela off-peak e com evidência WORM; restauração deve cumprir RPO/RTO do blueprint.  
- **FR-008**: Integrações externas (KYC/antifraude/pagamentos/notificações) DEVEM ser simuladas (mocks/stubs) sem chamadas reais; rate limit exercitado sem side effects.  
- **FR-009**: Eventos/outbox/CDC gerados DEVEM ir para sinks sandbox isolados, sem publicar em destinos reais.  
- **FR-010**: Execução deve falhar se RLS estiver ausente/desabilitado ou se o manifesto não cobrir o perfil/volumetria requeridos.  
- **FR-011**: Relatórios de execução DEVEM ser assinados e armazenados em WORM; indisponibilidade do WORM bloqueia execução.  
- **FR-012**: `reference_datetime` em ISO 8601 UTC é obrigatório no manifesto; mudanças exigem reseed coordenado e limpeza de checkpoints.  
- **FR-013**: Dados sintéticos são exclusivos; uso de snapshots/dumps de produção é proibido em qualquer ambiente.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Execuções devem respeitar janelas por ambiente e completar dentro de tempos-alvo definidos em manifesto; violações acionam abort/rollback auditado.  
- **NFR-002 (Performance/Rate Limit)**: Carga usa até o orçamento de rate limit/volumetria definido; ao exceder, aborta e reagenda off-peak.  
- **NFR-003 (Observabilidade)**: Logs estruturados, métricas e traces OTEL com correlação por tenant/ambiente/execução; falhas de exportação bloqueiam promoção.  
- **NFR-004 (Segurança/PII)**: Mascaramento e redaction em logs/eventos; acesso às chaves/manifestos segue menor privilégio.  
- **NFR-005 (FinOps)**: Caps e budgets por ambiente/tenant medidos em tempo real; alerta em aproximação e abort em estouro.

### Dados Sensiveis & Compliance

- Catalogar PII e aplicar mascaramento determinístico por ambiente/tenant antes de persistir; vedado uso de dados reais.  
- Chaves/salts residem no Vault (segregação por ambiente/tenant, rotação automática); proibido guardar em código/config estática.  
- Evidências imutáveis (WORM) para execuções e restaurações; direito ao esquecimento atendido por limpeza por tenant.  
- DR e carga só com dados sintéticos; RLS obrigatório em todas as execuções.

## Assumptions & Defaults

- Manifestos vivem no repositório de aplicação em paths estáveis (ex.: `configs/seed_profiles/<ambiente>/<tenant>.yaml`), versionados via PR/GitOps.  
- Baseline cobre apenas domínios core; estados “sad path” ficam restritos aos modos carga/DR conforme manifesto.  
- Off-peak é declarado em UTC no manifesto (par único start/end); execuções fora da janela falham.

## Success Criteria *(mandatorio)*

- **SC-001**: `seed_data` conclui por ambiente dentro dos tempos-alvo definidos nos manifestos, com 0 erros de validação/PII/RLS.  
- **SC-002**: Factories cobrem 100% das entidades core e passam nas checagens automáticas de PII e contratos `/api/v1`.  
- **SC-003**: CI/PR mantém taxa de sucesso ≥99% no dry-run do baseline e publica relatório de conformidade.  
- **SC-004**: Carga/DR respeitam caps de rate limit/volumetria e produzem evidência WORM; restauração cumpre RPO ≤ 5 minutos e RTO ≤ 60 minutos definidos no blueprint.  
- **SC-005**: Budgets/FinOps respeitados por ambiente/tenant, com alertas antes do teto e bloqueio em estouro auditado.
