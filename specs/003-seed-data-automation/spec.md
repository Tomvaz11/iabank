# Feature Specification: F-11 Automacao de Seeds, Dados de Teste e Factories

**Feature Branch**: `003-seed-data-automation`  
**Created**: 2025-11-21  
**Status**: Draft  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md secoes 3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integracao com CI/CD, Argo CD e testes de carga. Inclua criterios para validacao automatizada das seeds, anonimizacao, suportes a DR, parametrizacao de volumetria (Q11) por ambiente/tenant e geracao de datasets sinteticos sem quebrar RateLimit/API `/api/v1`."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituicao v5.2.0 (Art. I-XVIII) e ADRs aplicaveis. Toda lacuna deve ser marcada com `[NEEDS CLARIFICATION]` e adicionada ao `/clarify`.

## Contexto

Sem seeds deterministicas, o ciclo TDD/Integracao (Constituicao Art. III/IV) sofre com dados inconsistentes, flakiness e risco de vazamento de PII. Esta feature formaliza o comando `seed_data` e factories `factory-boy` alinhados ao Blueprint secoes 3.1 (SSOT multi-tenant), 6 (gerenciamento de dados) e 26 (execucoes assincronas), garantindo anonimizacao, respeito a rate limiting de `/api/v1` e preparacao de datasets sinteticos para CI/CD, Argo CD e testes de carga. O valor de negocio e acelerar entregas seguras (adicoes itens 1,3,8) com custos controlados (adicoes item 11) e suporte a DR.

## Hipoteses

- Volumetria baseline por ambiente/tenant (ajustavel via `--volume`): Dev/QA por tenant ~50 clientes, 20 consultores, 80 emprestimos e 240 parcelas; Stage/Homolog ~500/200/800/2.400; Perf/Load ~5.000/2.000/8.000/24.000. Valores podem ser sobrescritos por ambiente ou tenant mantendo limite de tempo e custo acordados.
- Hooks de CI/CD e Argo CD ja aceitam estagios adicionais pos-migracao para executar `seed_data` e validar resultados antes de liberar deploy.

## User Scenarios & Testing *(mandatorio)*

*As historias DEVEM ser fatias verticais independentes (INVEST) e testaveis de forma isolada. Mantenha o foco na jornada do usuario/persona e descreva como cada cenario prova o valor entregue.*

### User Story 1 - Seeds Deterministicas Multi-tenant (Prioridade: P1)

- **Persona & Objetivo**: QA / Engenharia de Plataforma precisa povoar ambientes com dados realistas multi-tenant via `seed_data` para habilitar TDD e integracoes estaveis.  
- **Valor de Negocio**: Reduz flakiness, acelera onboarding e garante paridade com Blueprint secoes 3.1 e 6.  
- **Contexto Tecnico**: Backend e banco compartilhado com RLS, factories `factory-boy` baseadas nos modelos SSOT, datasets anonimizados e validacao automatica pos-seed.

**Independent Test**: Execucao do `seed_data` com volumetria configurada por ambiente/tenant, validando integridade referencial, regras de negocio criticas (unicidade por tenant) e mascaramento de PII.

**Acceptance Scenarios (BDD)**:
1. **Dado** tenants ativos e o comando `seed_data` parametrizado com `--env`, `--tenant` e `--volume`, **Quando** a seed roda, **Entao** cria clientes/consultores/emprestimos/parcelas coerentes com o baseline informado, respeitando RLS, status validos e unicidade de documento por tenant, registrando relatorio de integridade por ambiente.
2. **Dado** a politica de privacidade ativa, **Quando** um conjunto de seeds usa dados sinteticos ou snapshots saneados, **Entao** nenhum campo PII e gravado em claro, os campos sensiveis sao mascarados ou anonimizados e a execucao falha em modo fail-closed caso um detector de PII encontre dados reais.

### User Story 2 - Pipelines e GitOps com Seeds (Prioridade: P2)

- **Persona & Objetivo**: DevOps/SRE quer que CI/CD e Argo CD provisionem dados coerentes apos migracoes ou DR drills sem esforco manual.  
- **Valor de Negocio**: Evita ambientes quebrados, garante DoR/DoD em branches e acelera recuperacao (RPO/RTO do Blueprint secao 6.1).  
- **Contexto Tecnico**: Jobs de pipeline, hooks do Argo CD, logs observaveis e budget de tempo/custo definidos pelo adicoes item 1 (DORA) e item 11 (FinOps).

**Independent Test**: Pipeline executa `seed_data` pos-migracao, roda suite de validacao das seeds, publica metricas (tempo, volumetria, falhas) e so prossegue se todas as verificacoes passarem.

**Acceptance Scenarios (BDD)**:
1. **Dado** um pipeline de branch ou main, **Quando** chega ao estagio de dados pos-migracao, **Entao** executa `seed_data` com volumetria do ambiente, roda validacoes (regras de negocio + PII) e bloqueia merge/deploy se houver quebra de integridade ou tempo p95 acima do alvo.
2. **Dado** um sync do Argo CD ou ensaio de DR, **Quando** o hook dispara as seeds no ambiente de destino, **Entao** ele conclui dentro das janelas acordadas, registra logs auditaveis e, em falha, reverte o estado ou reexecuta em modo idempotente conforme Blueprint secao 26.

### User Story 3 - Datasets Sinteticos para Carga Segura (Prioridade: P3)

- **Persona & Objetivo**: Engenheiro de Performance precisa rodar testes de carga usando datasets sinteticos sem derrubar a API `/api/v1` nem violar RateLimit.  
- **Valor de Negocio**: Mede capacidade de cada tenant e ambiente, evitando incidentes operacionais durante testes.  
- **Contexto Tecnico**: Rate limiting por tenant, planos de carga (adicoes item 3), volumetria Q11 por ambiente, thresholds de 429 e RPS acordados.

**Independent Test**: Plano de carga consome o dataset seedado com pacing/backoff configurado por ambiente, validando que a taxa de 429 fica abaixo do limite acordado e que os SLOs de tempo de resposta sao mantidos.

**Acceptance Scenarios (BDD)**:
1. **Dado** dataset sintetico gerado com volumetria de performance, **Quando** o teste de carga roda pela API `/api/v1` respeitando RateLimit headers, **Entao** os 429 permanecem abaixo de 2% do total, o throughput alvo e atingido e ha evidencias de que nenhum PII real foi trafegado.
2. **Dado** uma simulacao de failover (DR), **Quando** o ambiente secundario e seedado e recebe testes de carga, **Entao** a restauracao ocorre dentro de RPO<5 min e RTO<1h, mantendo isolamento de tenants e paridade de volumetria configurada.

### Edge Cases & Riscos Multi-Tenant

- Execucao sem `tenant_id` ou com tenant inexistente deve ser rejeitada e logada; seeds nunca podem cruzar dados entre tenants.
- Seeds via API precisam respeitar RateLimit (`429` + `Retry-After`); throttling/backoff obrigatorio evita quedas ou bloqueios globais.
- Reexecucoes apos falhas (rede, migracao parcial, fila assincrona secao 26) devem ser idempotentes, evitando duplicacao de registros ou violacoes de unicidade.
- Detectores de PII devem falhar seeds se encontrarem dados reais, inclusive em logs ou metricas; relatorios WORM preservam evidencias.
- Migracoes em andamento (adicoes item 8) exigem ordem segura: expand/backfill/contract antes das seeds; seeds nao podem mascarar inconsistencias de schema.
- Ensaios de DR nao podem ultrapassar budgets de custo/tempo e precisam sinalizar deriva de configuracao (GitOps/Argo CD) para correcao.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do codigo, cobrindo trajetorias felizes/tristes | Seeds e factories fornecem dados deterministicos para suites automatizadas; validacao pos-seed falha o pipeline se regras de negocio forem violadas. |
| Art. IV (Integracao) | Dados realistas para integracoes ponta a ponta | `seed_data` popula cenarios multi-tenant completos, habilitando testes de contrato e carga via `/api/v1` sem flakiness. |
| Art. VIII (Entrega) | Estrategia de release segura (feature flag/canary/rollback) | Pipelines e hooks do Argo CD rodam seeds pos-migracao com rollback/idempotencia e checkpoints antes de liberar deploy. |
| Art. IX (CI) | Cobertura >=85 %, complexidade <=10, SAST/DAST/SCA, SBOM, k6 | Estagio de seeds valida integridade e PII automaticamente; testes de carga baseados em seeds sao gates obrigatorios com thresholds definidos. |
| Art. XI (API) | Contratos OpenAPI 3.1 + Pact atualizados, RFC 9457 | Seeds respeitam versionamento `/api/v1`, RateLimit headers e Problem Details padronizados para falhas de seed via API. |
| Art. XIII (LGPD/RLS) | Enforcar RLS, managers, retencao/direito ao esquecimento | Dados de seed sao anonimizados, particionados por tenant (RLS), e logs/trilhas nao armazenam PII em claro. |
| Art. XVI (FinOps) | Custos rastreados, tags e budgets atualizados | Execucoes de seeds e testes de carga possuem budget e tracking por ambiente/tenant com alertas de consumo. |
| ADR-009 (GitOps/Argo CD) | Deploy via GitOps com drift detection | Hooks de seed pos-sync e verificacoes de drift para garantir paridade de dados seeded entre ambientes/DR. |
| ADR-010/011/012 | Seguranca de dados, governanca de API, observabilidade | Mascaramento de PII em seeds, metricas/traces de execucao e aderencia aos contratos de API. |
| Outros | adicoes itens 1,3,8,11; Blueprint secoes 3.1, 6, 26 | DORA/budgets refletidos em metricas de seeds e carga; migracoes expand/contract antes de semear; capacidade e thresholds de carga definidos. |

### Functional Requirements

- **FR-001**: Disponibilizar comando `seed_data` parametrizavel por ambiente, tenant e volumetria (Q11), permitindo rodadas completas ou parciais por dominio (clientes, consultores, operacoes financeiras) com execucao reproduzivel.
- **FR-002**: Manter biblioteca de factories `factory-boy` alinhada ao SSOT de modelos (secao 3.1), garantindo geracao multi-tenant, unicidade de identificadores por tenant e cenarios cobrindo regras criticas (status validos, valores consistentes).
- **FR-003**: Todas as seeds DEVEM usar dados sinteticos ou snapshots anonimizados; qualquer presenca de PII real (ex.: CPF/E-mail/Telefone) deve acionar bloqueio imediato, log de auditoria e instrucao clara de correcao.
- **FR-004**: Execucoes de seed DEVEM incluir suite de validacao automatica cobrindo: integridade referencial, contagens esperadas por volumetria/tenant, regras de negocio (unicidade de documento, estados validos), aderencia a RLS e relatorio consolidado por ambiente.
- **FR-005**: Pipelines CI/CD DEVEM orquestrar `seed_data` apos migracoes e antes de testes de integracao/carga, bloqueando merges/deploys se validacoes falharem ou se o tempo p95 exceder o alvo definido por ambiente.
- **FR-006**: Hooks do Argo CD DEVEM acionar seeds e validacoes em syncs e ensaios de DR, registrando sucesso/falha e permitindo reexecucao idempotente conforme estrategia assincrona (secao 26).
- **FR-007**: Volumetria (Q11) deve ser configuravel por ambiente/tenant, com defaults documentados (Dev/QA/Stage/Perf) e salvaguardas para nao exceder limites de tempo/custo ou causar throttling na API.
- **FR-008**: Geracao de datasets sinteticos para testes de carga deve respeitar RateLimit da API `/api/v1` (alvo de <=2% 429), aplicando pacing/backoff e permitindo modos sem API (semente em lote) quando necessario para proteger producao.
- **FR-009**: Seeds devem suportar cenarios de DR: reconstruir ambientes a partir de backups/snapshots anonimizados, mantendo RPO<5 min e RTO<1 h, com checagem automatica de paridade de volumetria e isolamento entre tenants.
- **FR-010**: Telemetria de seeds deve expor metricas e eventos (tempo, volumetria, falhas, tenants afetados) com mascaramento de PII e correlacao com execucoes de pipeline/git commit, permitindo rastrear custo e impacto (FinOps).

### Non-Functional Requirements

- **NFR-001 (SLO de Seeds)**: Execucao do `seed_data` deve completar em p95 < 5 minutos (Dev/QA) e < 10 minutos (Stage/Perf/DR) por tenant, com erro orcamentario registrado se excedido.
- **NFR-002 (Performance/RateLimit)**: Testes de carga baseados em seeds devem manter 429 <= 2% e sucesso >= 98% das requisicoes criticas, preservando SLOs de resposta por tenant.
- **NFR-003 (Observabilidade)**: Cada execucao de seed/carga deve gerar logs estruturados e metricas com tags de tenant/ambiente/versao, spans correlacionados e alertas automaticos em falha ou degradacao.
- **NFR-004 (Seguranca/Privacidade)**: Zero PII real em seeds; anonimizacao obrigatoria, mascaramento em logs/metricas, e evidencias de cumprimento de LGPD (RIPD/ROPA atualizados quando novos campos sensiveis entrarem).
- **NFR-005 (FinOps)**: Custo de compute/storage/redes associado a seeds e testes de carga deve permanecer dentro do budget definido por ambiente, com alertas em 80% e reporte mensal por tenant.

### Dados Sensiveis & Compliance

- Campos sensiveis (CPF/CNPJ, e-mail, telefone, endereco, dados bancarios, valores de transacao) devem ser gerados sinteticamente ou anonimizados; jamais reutilizar PII real.
- Seeds devem aplicar mascaramento consistente em respostas/logs/telemetria e registrar evidencias de anonimizacao para auditoria LGPD.
- Retencao de dados de seed em ambientes compartilhados deve seguir politica minima necessaria; rotinas de limpeza/reseed devem remover dados antigos e respeitar direito ao esquecimento sem depender de dados reais.
- Ensaios de DR e pipelines devem exportar relatorios WORM de execucao, volumetria e deteccao de PII para inspecao de compliance.

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- **SC-001**: Rodadas de `seed_data` concluem dentro do SLO (p95 < 5 min Dev/QA; < 10 min Stage/Perf/DR) em 95% das execucoes por release.
- **SC-002**: Suite de validacao pos-seed cobre >=95% das regras de negocio criticas e atinge 100% de pass rate antes de liberar merge/deploy.
- **SC-003**: Zero ocorrencias de PII real em seeds, logs ou metricas por trimestre; 100% dos campos sensiveis gerados de forma sintetica/anonimizada.
- **SC-004**: Testes de carga baseados em seeds mantem taxa de 429 <= 2% e throughput alvo definido por ambiente/tenant, sem violar rate limiting ou derrubar `/api/v1`.
- **SC-005**: Ensaios de DR com seeds entregam ambientes prontos em < 1 hora com paridade de volumetria configurada e custo dentro do budget aprovado.

Associe cada criterio aos testes ou dashboards que validam o resultado.

## Outstanding Questions & Clarifications

- Nenhuma pendencia aberta; especificacao pronta para `/speckit.plan` ou ajustes conforme novos limites de volumetria/RateLimit definidos pelos donos de produto/SRE.
