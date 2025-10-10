# Relatório de Auditoria – Índice de Features (IABANK)

Escopo: análise do arquivo `specs/001-indice-features-template/spec.md` à luz de `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituição v5.2.0 e ADRs 008–012.

Referência base: specs/001-indice-features-template/spec.md:1

## 1) Análise de Cobertura e Conformidade

- Cobertura geral: O conjunto F-01 a F-11 cobre de forma coerente as frentes essenciais previstas no blueprint e nas adições enterprise: multi-tenant e RBAC (F-01), KYC/PII (F-02), originação regulatória (CET/IOF) (F-03), recebimentos e conciliação (F-04), payables (F-05), cobrança/renegociação (F-06), painéis executivos com SLO/DORA/FinOps (F-07), LGPD + trilhas WORM (F-08), SRE/observabilidade/CI-CD (F-09), fundação frontend FSD (F-10) e seeds/factories para TDD/integração (F-11). Alinha-se às camadas, DTOs e entidades descritas no blueprint (ex.: `LoanCreateDTO`, `BaseTenantModel`).
- Constituição: Estão refletidos os princípios mandatórios: TDD (Art. III) e integração-primeiro (Art. IV) via F-11; documentação e versionamento da API via `/api/v1` (Art. V) em múltiplos prompts; SLOs, error budgets e métricas p95/p99 (Art. VI/VII) em F-07/F-09; Trunk-Based/DORA (Art. VIII) em F-09; gates de CI com cobertura e SAST/DAST/SCA/SBOM (Art. IX) em F-08/F-09; migrações expand/contract e índices `CONCURRENTLY` (Art. X) em F-04/F-05/F-06.
- ADRs: 
  - ADR-011 (Governança de API): prompts exigem RateLimit headers, `Idempotency-Key`, `ETag/If-Match` e Pact/openapi-diff.
  - ADR-010 (Proteção de Dados): pgcrypto, Vault/KMS, mascaramento de PII, direito ao esquecimento (F-02/F-08/F-11).
  - ADR-012 (Observabilidade): OTEL, logs JSON, Sentry/django-prometheus e dashboards SLO (F-07/F-09/F-10).
  - ADR-008 (Renovate) e ADR-009 (Argo CD): previstos em F-09 e integração com DR (F-11).

Lacunas e recomendações (com fontes):
- [G-01] Threat Modeling formal (STRIDE/LINDDUN) não aparece como entregável regular. Recomendado incluir em F-09 (planejamento recorrente e backlog mitigável) e/ou F-08 (privacidade), com critérios de aceite e artefatos. Base: adicoes_blueprint.md (item 9).
- [G-02] OpenAPI 3.1 não é explicitado nos prompts (apenas “OpenAPI”). Padronizar a menção “OpenAPI 3.1 contract-first (lint/diff)” em todos os prompts que tocam contrato. Base: ADR-011; adicoes_blueprint.md (item 7).
- [G-03] Idempotência em F-05: o prompt não cita `Idempotency-Key` para criação de despesas e webhooks/eventos bancários. Incluir para evitar duplicidades. Base: ADR-011.
- [G-04] Autenticação/refresh: reforçar no escopo de F-01 os detalhes de armazenamento seguro de `refresh_token` (cookie `HttpOnly`/`Secure`/`SameSite=Strict`) e política de expiração/rotação. Base: BLUEPRINT_ARQUITETURAL.md §19 (Segurança por Design).
- [G-05] ABAC: F-01 foca em RBAC, mas as adições pedem RBAC/ABAC e testes automatizados de autorização. Incluir matriz de atributos, cenários de object-level permissions e testes. Base: adicoes_blueprint.md (item 12).
- [G-06] Gates de complexidade: a meta de complexidade ciclomática ≤ 10 (Art. IX) não está explicitamente referenciada em prompts/ACs. Sugerir incorporar em F-09 (pipeline CI) como gate formal.
- [G-07] RLS operacional: F-01 fala em RLS ativo, mas faltam detalhes operacionais (políticas `CREATE POLICY`, binding do `tenant_id` em sessão e testes negativos). Tornar explícito nos ACs. Base: adicoes_blueprint.md (item 4) e BLUEPRINT_ARQUITETURAL.md §6.3.
- [G-08] Privacidade no frontend: F-10 não reforça “nada de PII em URLs” e CSP estrita com nonce/hash/Trusted Types. Incluir como requisito de fundação. Base: adicoes_blueprint.md (item 13).
- [G-09] Supply chain: assinatura/proveniência (cosign/SLSA) é recomendação enterprise nas adições, mas não aparece. Sugerir como incremento em F-09. Base: adicoes_blueprint.md (evidências, “assinatura/proveniência”).

Conclusão (1): A cobertura é sólida e majoritariamente conforme os artefatos. As lacunas acima são incrementais e elevam o “nível enterprise sênior” sem alterar o escopo funcional.

## 2) Análise de Risco e Dependência

- Dependências: A cadeia proposta (F-01 → F-02 → F-03 → F-04 → F-05 → F-06; F-10/F-11 como fundação; F-07 após dados consolidados; F-08 em paralelo para compliance; F-09 pós-MVP) é lógica e consistente com o plano anotado.
- Ajuste pontual: Na tabela, F-11 depende de F-09; no plano, F-11 é “Passo 0”. Para evitar bloqueio artificial, recomendo ajustar a dependência para “integra com F-09, mas não depende” (Seeds podem anteceder observabilidade avançada). Base: specs/001-indice-features-template/spec.md:435-441.

Riscos adequadamente cobertos no índice:
- Vazamento cross-tenant por RLS (mitigado por testes e WORM); PII em serializers; falha de conciliação; segregação de funções em payables; limites LGPD em cobrança; quebras de contrato sem Pact; migrações expand/contract; ausência de gates de segurança (todos mapeados com mitigação). Base: specs/001-indice-features-template/spec.md:385-414.

Riscos subestimados/omitidos (novos) e ações:
- [R-01] Modelagem de ameaças ausente como processo cíclico (STRIDE/LINDDUN) com backlog acionável e critérios de saída. Ação: incluir em F-09 e como check no `/speckit.plan`. Base: adicoes_blueprint.md (item 9).
- [R-02] Gestão de segredos/Vault/KMS: risco de indisponibilidade/rotação quebrada afetando trilhas e integrações. Ação: health checks, feature flags de fallback e runbooks de rotação com janelas seguras. Base: ADR-010; BLUEPRINT_ARQUITETURAL.md §19/§27.
- [R-03] Supply chain/proveniência: imagens/artefatos sem assinatura. Ação: cosign/SLSA no pipeline, validação em CD. Base: adicoes_blueprint.md (evidências).
- [R-04] PII em URLs/traces do frontend: risco de vazamento via router/telemetria. Ação: lint de rotas, testes e processadores OTEL para redaction. Base: adicoes_blueprint.md (item 13); ADR-012.
- [R-05] Reexecução de webhooks bancários (replay) em payables: F-05 não explicita idempotência. Ação: `Idempotency-Key` e tabelas de deduplicação. Base: ADR-011.
- [R-06] Concurrency avançada: TOCTOU além de `ETag` (ex.: lot sizing em cobranças). Ação: locks transacionais e testes de contenção. Base: BLUEPRINT_ARQUITETURAL.md §3.1/§6.
- [R-07] Conflito LGPD “direito ao esquecimento” vs. compliance contábil: precisa política clara de anonimização seletiva com pseudonimização e retenção mínima. Ação: detalhar nos ACs de F-08 (já iniciado). Base: ADR-010; BLUEPRINT_ARQUITETURAL.md §6.2.

Conclusão (2): Os riscos e dependências estão bem estruturados; ajustes recomendados aumentam a robustez operacional e de segurança sem alterar o roadmap.

## 3) Análise de Clareza dos Prompts (/speckit.specify)

Veredito geral: Prompts são claros, específicos, citam as fontes corretas e aplicam restrições (“proiba decisões de stack”) de acordo com o fluxo Spec-Kit. Ajustes recomendados por feature:

- F-01 (Governança de Tenants e RBAC Zero-Trust): Claro. Acrescentar: ABAC e testes de autorização; detalhes de `refresh_token` seguro conforme segurança do blueprint. Fontes: adicoes_blueprint.md (item 12); BLUEPRINT_ARQUITETURAL.md §19; Constituição Art. V.
- F-02 (Cadastro e KYC): Claro. Acrescentar: explicitar “OpenAPI 3.1” e checklist de minimização de dados nos DTOs. Fontes: ADR-011; ADR-010; Constituição Art. V.
- F-03 (Originação CET/IOF): Claro. Já inclui backoff e fallback. Manter Q1; explicitar “OpenAPI 3.1”. Fontes: BLUEPRINT_ARQUITETURAL.md §3.1.1/§3.2; adicoes_blueprint.md (itens 1,7).
- F-04 (Parcelas/Recebimentos): Claro. Cobertura forte de idempotência/concorrência/RateLimit. Apenas reforçar “OpenAPI 3.1” e Problem Details (RFC 9457) já citado. Fontes: ADR-011; BLUEPRINT_ARQUITETURAL.md §26.
- F-05 (Payables/Despesas): Claro, porém incluir `Idempotency-Key` para criação/integrações e reforçar webhooks idempotentes. Fontes: ADR-011; BLUEPRINT_ARQUITETURAL.md §6.1/§6.3.
- F-06 (Cobrança/Renegociação): Claro. Já contempla DLQ, backoff e RateLimit. Reforçar política de consentimento por canal e “OpenAPI 3.1”. Fontes: adicoes_blueprint.md (itens 2,10); ADR-011.
- F-07 (Painel Executivo): Claro. Manter bloqueio por Q3. Acrescentar validação de integridade/late-binding das métricas (evitar métricas desnormalizadas). Fontes: Constituição Art. VI/VII; adicoes_blueprint.md (itens 1,2,11).
- F-08 (LGPD/Auditoria Imutável): Claro. Reforçar pseudonimização vs. anonimização e política de retenção por ato jurídico. Fontes: ADR-010; BLUEPRINT_ARQUITETURAL.md §6.2/§27.
- F-09 (Observabilidade/SRE/CI-CD): Claro e abrangente. Acrescentar assinatura/proveniência (cosign/SLSA) e gate de complexidade (≤ 10). Fontes: Constituição Art. IX; adicoes_blueprint.md (evidências).
- F-10 (Fundação FSD/UI): Claro. Acrescentar restrição de PII em URLs e CSP estrita (nonce/hash/Trusted Types). Fontes: adicoes_blueprint.md (item 13); ADR-012.
- F-11 (Seeds/Factories): Claro. Reforçar cenários de DR e volumetria variável (Q11) com geração paralela controlada por tenant. Fontes: Constituição Art. III/IV; BLUEPRINT_ARQUITETURAL.md §6/§26.

Conclusão (3): Prompts viáveis para `/speckit.specify`. Pequenos acréscimos padronizam OpenAPI 3.1, idempotência em payables, ABAC e privacidade no frontend.

## Referências Citadas

- Constituição: .specify/memory/constitution.md:1 (Arts. I–IX). 
- Blueprint: BLUEPRINT_ARQUITETURAL.md:1 (camadas, DTOs, segurança, Celery, DR, índices multi-tenant).
- Adições: adicoes_blueprint.md:1 (DORA/SRE, RLS, segurança/compliance, governança de API, threat modeling, FinOps, privacidade frontend, IaC/GitOps).
- ADRs: docs/adr/008-ferramenta-de-automacao-de-dependencias.md:1; docs/adr/009-plataforma-de-gitops.md:1; docs/adr/010-protecao-dados-sensiveis-e-segredos.md:1; docs/adr/011-governanca-de-apis-e-contratos.md:1; docs/adr/012-observabilidade-e-telemetria.md:1.

## 4) Consolidação das Recomendações do Relatório “Gemini”

Fonte analisada: RELATORIO_AUDITORIA_INDICE_FEATURES_Gemini.md:1. Após revisão, incorporamos os seguintes pontos adicionais ao presente relatório, a serem refletidos na etapa de incorporação das recomendações:

- [R-08] Complexidade de Configuração (Vault/Argo CD/Terraform/KMS): risco operacional/segurança por má configuração. Mitigações: Policy-as-Code (OPA/Gatekeeper) para validar planos Terraform; peer-review obrigatório de políticas do Vault/Argo CD; testes de configuração em staging antes de produção. Fontes: adicoes_blueprint.md:1 (item 14); docs/adr/009-plataforma-de-gitops.md:1; docs/adr/010-protecao-dados-sensiveis-e-segredos.md:1.
- [R-09] “Drift” de Conformidade: risco de novas features violarem padrões (PII sem pgcrypto; endpoints sem testes de isolamento). Mitigações: gates no CI que falham ao detectar modelos com PII sem criptografia/campos mascarados e endpoints sem testes de isolamento multi-tenant. Fontes: Constituição Art. IX (gates), docs/adr/010-protecao-dados-sensiveis-e-segredos.md:1.
- [R-10] Performance em Larga Escala: risco de degradação com crescimento de dados. Mitigações: revisão periódica de `EXPLAIN ANALYZE` das queries críticas; criação de índices com `CREATE INDEX CONCURRENTLY`; observabilidade de slow queries. Fontes: BLUEPRINT_ARQUITETURAL.md:1 (§6.3); Constituição Art. X.
- [R-11] Governança de Custos (FinOps): risco de custo descontrolado por logging/queries/autoscaling. Mitigações: dashboards de FinOps cruzando custo por `tenant` e `feature`; revisões trimestrais de otimização. Fontes: adicoes_blueprint.md:1 (item 11); F-07 (FinOps) como veículo de entrega.

Observação: o relatório Gemini não apontou lacunas de cobertura; mantemos as lacunas [G-01..G-09] deste relatório por entendermos que elevam o nível enterprise (OpenAPI 3.1, ABAC, idempotência em F-05, privacidade no frontend, assinatura/proveniência etc.).
