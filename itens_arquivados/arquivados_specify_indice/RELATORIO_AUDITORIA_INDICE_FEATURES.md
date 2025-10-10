# Relatório de Auditoria — Índice de Features (specs/001-indice-features-template/spec.md)

Data: 2025-10-10
Autor: Arquiteto de Software Sênior (auditoria de alto nível)
Escopo: Análise de cobertura/conformidade, riscos/dependências e clareza dos prompts para F-01 a F-09, com base em BLUEPRINT_ARQUITETURAL.md, adicoes_blueprint.md, Constituição do Projeto (v5.2.0) e ADRs 008–012.

Referências consultadas:
- BLUEPRINT_ARQUITETURAL.md (seções 2, 3.1, 3.1.1, 3.2, 6.1, 6.2, 6.3, 16, 17, 18, 19, 21, 26, 27)
- adicoes_blueprint.md (itens 1 a 14)
- .specify/memory/constitution.md (Art. I–X; notadamente Art. III, V, VI, VII, VIII, IX, X)
- docs/adr/008-ferramenta-de-automacao-de-dependencias.md (Renovate)
- docs/adr/009-plataforma-de-gitops.md (Argo CD)
- docs/adr/010-protecao-dados-sensiveis-e-segredos.md (pgcrypto, Vault, KMS, WORM)
- docs/adr/011-governanca-de-apis-e-contratos.md (OpenAPI lint/diff, Pact, RateLimit headers, RFC 9457, Idempotency-Key, ETag/If-Match)
- docs/adr/012-observabilidade-e-telemetria.md (structlog JSON, django-prometheus, Sentry, OTEL)

Arquivo avaliado: specs/001-indice-features-template/spec.md:1


**1) Cobertura e Conformidade**

Conclusão: A cobertura de F-01 a F-09 atende de forma ampla ao blueprint, à Constituição e aos ADRs estratégicos, com foco correto nas fatias de negócio essenciais (tenancy/RBAC, KYC, originação com CET/IOF, parcelas/conciliação, contas a pagar, cobrança/renegociação, painéis executivos SLO/DORA, LGPD/auditoria imutável, SRE/observabilidade). Há, entretanto, lacunas pontuais que devem ser sanadas para plena conformidade “enterprise”.

Pontos fortes (aderências claras):
- Multi-tenant e RBAC: F-01 cobre isolamento e auditoria, alinhado ao blueprint (camadas, BaseTenantModel, §6.2 histórico) e adições (RLS em Postgres). Constituição Art. II e Art. XIII (citada no índice) reforçam modularidade e LGPD/RLS.
- KYC/PII/LGPD: F-02 e F-08 tratam consentimento, export, direito ao esquecimento, WORM e pgcrypto/Vault (ADR-010). Constituição Art. V (documentação/versionamento), Art. VII (observabilidade com PII mascarado) e adições (itens 4,5,6,12) contemplados.
- Originação com CET/IOF: F-03 coaduna com blueprint §3.1/3.1.1 (campos regulatórios CET/IOF), cenários de arrependimento e idempotência; adições item 7 (governança de API) em parte endereçada.
- Parcelas, recebimentos e Celery: F-04 aborda idempotência, backoff, DLQ e tratamento 429/Retry-After; conversa com blueprint §26 (Celery) e ADR-011 (idempotência/retries).
- Finance (AP/Despesas): F-05 se alinha ao blueprint (finance models) e adições 11 (FinOps), incluindo aprovação multinível e evidências auditáveis.
- Cobrança e renegociação: F-06 inclui runbooks, limites de contato LGPD e expand/contract (zero-downtime) conforme Constituição Art. X (migrações) e adições 8.
- Painéis SLO/DORA/FinOps: F-07 está alinhado a Constituição Art. VI e VII, adições 1,2 e 11, e ADR-012 (telemetria padronizada) — dependência de Data Mart reconhecida.
- Observabilidade/SRE/CI-CD: F-09 abrange gates de CI (SAST/DAST/SCA, SBOM, k6), error budgets, GameDays, feature flags; alinhado a Constituição Art. VIII/IX e ADR-012.

Lacunas e não conformidades identificadas:
- Versionamento de API (Constituição Art. V; Blueprint §17): Não há menção explícita ao prefixo de versão (/api/v1) nos prompts/AC. Sugestão: incluir critério de aceitação para versionamento e política de compatibilidade.
- Rate limiting — headers IETF (ADR-011): F-04 cobre 429 + Retry-After, mas não exige `RateLimit-Limit/Remaining/Reset`. Sugestão: adicionar AC para envio e validação destes headers.
- Controle de concorrência (ADR-011): Ausentes ACs sobre ETag/If-Match (ou If-None-Match) e uso de 428 Precondition Required para updates. Relevante em F-02 (edição KYC), F-05 (despesas), F-06 (renegociação) e F-04 (baixas/conciliação). Lacuna importante.
- Testes de contrato Pact (ADR-011): A tabela “Constituição & ADRs Impactados” declara testes de contrato para F-01..F-06, mas os ACs por feature não exigem “Pact published/verified” como gate. Incluir AC explícito.
- GitOps e Renovate (ADR-009, ADR-008): Não referenciados no índice. Devem constar como obrigações transversais (p.ex., em F-09) ou em seção de requisitos globais.
- Zero-downtime (Constituição Art. X): Embora F-06 cite expand/contract, faltam ACs genéricos de “parallel change” em fluxos que alterem schema (ex.: F-04/F-05). Incluir referência a índices `CONCURRENTLY` quando aplicável.
- Indexação multi-tenant (Blueprint §6.3): Não há AC para garantir índices compostos com `tenant_id` na frente (desempenho). Incluir NFR/AC de verificação de índices críticos (loans/status, loans/customer, transactions/tenant).
- Segurança por design (Blueprint §19): MFA aparece como dúvida (Q4) mas sem AC para MFA obrigatório em perfis críticos (admin/financeiro). Sugerir AC mínimo para MFA TOTP/SSO em F-01.
- Celery acks_late (Blueprint §26): Idempotência e backoff cobertos; contudo `acks_late=True` (ou equivalente) não aparece nos ACs. Sugerir inserir em F-04/F-06 como requisito operacional.
- RFC 9457 vs. padrão de erro do blueprint (§18): O índice adota RFC 9457 (positivo; ADR-011), mas faltam ACs de “exception handler” padronizando Problem Details e cobertura de erros 4xx/5xx.


**2) Risco e Dependências**

Conclusão: Dependências listadas são coerentes entre as fatias, mas algumas dependências técnicas e de governança ficaram implícitas. A análise de riscos cobre grande parte de segurança/compliance/performance, porém há riscos adicionais subestimados.

Observações sobre dependências:
- F-07 (painéis) depende de Data Mart e catálogo SLO, mas também depende de padronização de tracing/logs (ADR-012) e versionamento de contratos (para extrair métricas por versão). Explicitá-las melhora previsibilidade.
- F-04 (recebimentos) depende de políticas de idempotência end-to-end (servidor, gateway e webhooks), além de rate limits do provedor e chaves KMS para criptografia de payloads sensíveis — tangencia ADR-010.
- F-08 (LGPD/auditoria) depende de trilha WORM e políticas de retenção; depende também de processos de alteração controlada de schema para manter trilhas válidas em DR (Blueprint §27), o que convém explicitar.
- F-09 (SRE) depende de ADR-008 (Renovate) e ADR-009 (Argo CD) para garantir “drift detection”/proveniência e atualização contínua de dependências — não listadas.

Riscos adicionais identificados:
- Conciliação vs. direito ao esquecimento (LGPD): Como garantir anonimização sem quebrar reconciliação contábil? Exigir pseudonimização/anonimização preservando chaves técnicas (hash salted) em F-08.
- Vieses e disponibilidade de bureaus (F-03): Dependência regulatória e de SLA de terceiros. Incluir AC para “graceful degradation” (circuit breaker + fila de reprocesso) e “fallback manual auditável”. Parte já citada, mas formalizar SLO e timeouts.
- RLS incompleto (ADO + ORM): Se RLS Postgres falhar por política ausente/bug, o ORM ainda poderia vazar dados. Exigir testes de isolamento multi-tenant (com e sem RLS) e managers tenant-aware por padrão (adições item 4).
- Rate limiting assimétrico entre tenants: Sem políticas por-tenant, “noisy neighbor” pode degradar experiência. Requer “quotas/limites por tenant” e headers RateLimit em todos endpoints sensíveis (ADR-011).
- Concurrency/lost update: Sem ETag/If-Match, updates concorrentes podem gerar perdas silenciosas. Adicionar ACs em F-02/F-05/F-06 conforme ADR-011.
- Custos de gateway e conciliação (FinOps): Necessidade de ACs para “cost tagging” por tenant/feature e alarmes de 80/100% (adições item 11) — parte está em F-07/F-09, mas reforçar em F-04/F-05.
- Segurança operacional de segredos: Rotação automática (Vault/KMS) prevista, porém sem ACs de “key rotation test” e “secret lease TTL” por ambiente. Sugerir ACs em F-08/F-09.
- Migrações e índices: Falta AC para `CREATE INDEX CONCURRENTLY` e “expand/contract” em alterações de alto impacto (Constituição Art. X). Incluir em F-04/F-05/F-06.


**3) Clareza dos Prompts (/speckit.specify por feature)**

Conclusão: Os prompts são, em geral, claros, objetivos e bem referenciados. Entretanto, há referências de seção imprecisas e oportunidades de reforçar vínculos com ADRs e Constituição para garantir geração de especificações sem ambiguidade.

Avaliação por feature (observações principais):
- F-01: Bom escopo e referências corretas (RBAC, RLS, WORM, Art. III/IX/XIII). Ajustar citação “BLUEPRINT §§2.A” para “§2.2 (Containers) ou §2 (C4)”. Incluir AC explícito para MFA (Blueprint §19) e testes de isolamento multi-tenant (adições item 4).
- F-02: Objetivo e restrições bem definidas. Referência “§§2.A,3.1,3.2” — substituir “2.A” por “§2” (C4) e manter 3.1/3.2. Acrescentar ETag/If-Match (ADR-011) e Pact como gate de aceite.
- F-03: Alinha CET/IOF e bureau; manter Q1. Reforçar: headers RateLimit (ADR-011), pactos de contrato e versionamento API (/api/v1). “§2.A” deve ser “§2”.
- F-04: Excelente em idempotência/429/DLQ. Adicionar: RateLimit headers (ADR-011), `acks_late=True` (Blueprint §26), pactos de contrato para webhooks e versionamento (/api/v1). “§2.A” → “§2”.
- F-05: Coeso com fiscal/FinOps. Incluir ETag/If-Match (ADR-011) para updates de despesas; NFR para índices por `tenant_id` (Blueprint §6.3); canário/rollback para mudanças sensíveis (Art. VIII).
- F-06: Adequado; incluir ETag/If-Match, pactos para endpoints de renegociação e critérios de “parallel change” mais formais (Art. X, adições 8).
- F-07: Correto quanto a SLO/DORA/FinOps, mas “§§2.3” não existe no blueprint; usar “§2 (C4)” e “§6.3” (indexação) apenas quando aplicável. Manter Q3 para metas SLO.
- F-08: Referências sólidas (6.2, 27 e adições 4,5,6,12). Reforçar AC de “key rotation” (Vault/KMS) e de conflito “direito ao esquecimento vs. WORM” por meio de anonimização reversible-safe.
- F-09: Completo e bem ancorado em §6, §26, §27 e adições 1,2,3,8,9,10. Incluir GitOps (ADR-009) e Renovate (ADR-008), além de AC para canary/blue-green e OpenAPI diff gate (ADR-011) explicitamente.

Observação transversal: Consistência de citações
- Corrigir todas as menções “§§2.A” e “§§2.3” para seções válidas do blueprint (ex.: §2, §2.1/§2.2 conforme aplicável).
- Tornar explícito em todos os prompts a exigência de versionamento de API (/api/v1) e “Problem Details” (RFC 9457) como padrão de erro.
- Onde aplicável, acrescentar “Pact (producer/consumer) published/verified” como critério objetivo de aceite.


**Recomendações objetivas (resumo acionável):**
- Adicionar AC de versionamento de API (/api/v1) e compatibilidade retroativa aos prompts F-01..F-06. (Constituição Art. V; Blueprint §17)
- Incluir RateLimit headers (ADR-011) e ETag/If-Match + 428 (ADR-011) nos ACs de F-02, F-04, F-05 e F-06.
- Tornar “Pact tests passed” parte dos critérios de aceite das features que expõem/consomem APIs (F-01..F-06).
- Sanitizar referências “§§2.A/2.3” para seções reais do blueprint (§2, §2.1/2.2; §3.1/3.1.1/3.2; §6.x; §26; §27).
- Incluir GitOps (ADR-009) e Renovate (ADR-008) como requisitos transversais em F-09 (ou seção global de requisitos) com ACs claros.
- Reforçar zero-downtime (Art. X) e indexação multi-tenant (Blueprint §6.3) com ACs verificáveis.
- Acrescentar ACs de MFA obrigatório para perfis de alto privilégio (Blueprint §19) em F-01.
- Declarar `acks_late=True` (ou equivalente) nos ACs de tarefas críticas (F-04/F-06) — Blueprint §26.


Estado: Relatório informativo; nenhuma alteração de especificações efetuada neste commit. As correções podem ser aplicadas nos prompts/ACs conforme orientações acima.


---

**Addenda de Consolidação (auditoria_indice_features.md:1)**

Após revisar o conteúdo de auditoria_indice_features.md, consolidei os pontos adicionais que fazem sentido e que complementam este relatório. Abaixo, os acréscimos incorporados:

- Cobertura e Conformidade — Acrescentado
  - Frontend FSD (Blueprint §4): Incluir como lacuna explícita a ausência de uma feature/tarefa dedicada ao scaffolding do frontend em Feature-Sliced Design (estrutura `features/`, `entities/`, `shared/ui`, estado e dados via TanStack Query/Zustand). Essa fundação deve constar no índice como pré-requisito técnico transversal das features de UI.
  - Seed e Dados de Teste (Constituição Art. III/IV; Blueprint §6): Incluir como lacuna a ausência de uma feature/tarefa para manutenção de dados de teste realistas e seeds via `factory-boy`/comandos de gestão (ex.: `seed_data`). Essencial para TDD e integração-primeiro.

- Risco e Dependências — Acrescentado
  - Vazamento de PII via Serialização/DTO (ADR-010; Blueprint §19; adicoes item 13): Risco de exposição de PII em respostas de API por erro de mapeamento/serializer. Mitigações: política de minimização de dados no DTO, checagens automatizadas no CI para campos marcados como PII e mascaramento consistente nas camadas de log/telemetria.
  - Quebra de Contrato FE/BE (ADR-011): Risco de incompatibilidade entre produtor (API) e consumidor (SPA) no monorepo. Mitigações: Pact producer/consumer como gate obrigatório no CI, além de OpenAPI lint/diff.
  - Complexidade Operacional de Parallel Change (Constituição Art. X): Risco de inconsistência durante etapas de expand/backfill/contract. Mitigações: planos de migração detalhados, verificação de backfill e reversibilidade ensaiada (GameDays focados em migração).

- Clareza dos Prompts — Acrescentado
  - Controle de Concorrência (ADR-011): Tornar explícito nos prompts das features com mutação (F-02, F-04, F-05, F-06) a exigência de `ETag` + `If-Match`/`If-None-Match` e uso de `428 Precondition Required`.
  - Diretrizes de Frontend (Blueprint §4): Incluir, nos prompts que impactam UI (ex.: F-03 `NewLoanWizard`), instrução para detalhar a estrutura FSD (composição de `features`, `entities`, `shared/ui`) e estratégia de estado/dados, mantendo neutralidade de stack onde já definida.
  - Testes de Contrato Externos (ADR-011): Em F-03, explicitar Pact para a integração com bureaus de crédito (produtor/consumidor ou contrato de fornecedor simulado), com timeouts, circuit breaker e políticas de retry definidas.

Estes itens foram incorporados ao corpo do relatório como recomendações adicionais de lacunas, riscos e melhorias de prompts, sem alterar as conclusões principais.
