# Feature Specification: Automacao de seeds, dados de teste e factories

**Feature Branch**: `003-seed-data-automation`  
**Created**: 2025-11-22  
**Status**: Draft  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md` §§3.1, 6, 26; `adicoes_blueprint.md` itens 1, 3, 8, 11; Constituicao v5.2.0 (Art. III/IV e correlatos) e ADRs aplicaveis.

## Contexto

Time precisa automatizar seeds e datasets de teste, mantendo compliance de PII e evitando saturar APIs internas (`/api/v1`). Objetivo é oferecer comando unico (`seed_data`) e factories padronizadas (factory-boy) que gerem dados sinteticos seguros por tenant/ambiente, com validacao automatizada e integracao continua (CI/CD, Argo CD) inclusive para cenarios de DR e testes de carga. Atende diretrizes do blueprint arquitetural (autonomia de ambientes, isolamento multi-tenant, governanca de dados sensiveis) e Constituicao Art. III/IV.

## User Scenarios & Testing *(mandatorio)*

*As historias DEVEM ser fatias verticais independentes (INVEST) e testaveis de forma isolada. Mantenha o foco na jornada do usuario/persona e descreva como cada cenario prova o valor entregue.*

### User Story 1 - Seeds automatizadas multi-tenant (Prioridade: P1)

- **Persona & Objetivo**: Engenheira de QA precisa provisionar dados de teste consistentes por tenant/ambiente com um unico comando.  
- **Valor de Negocio**: Reduz tempo de preparacao de ambientes e falhas causadas por datasets incompletos ou desatualizados.  
- **Contexto Tecnico**: Dominios de dados core, pipeline CI, triggers em deploy via Argo CD, tenants de homolog/producao controlados.

**Independent Test**: Execucao de `seed_data` em ambiente limpo cria baseline completa por tenant sem erros de validacao.

**Acceptance Scenarios (BDD)**:
1. **Dado** um ambiente novo com `tenant_id` definido, **Quando** executo `seed_data --tenant=<id> --env=<ambiente>`, **Entao** dados basicos e relacionamentos obrigatorios sao criados e validados automaticamente.  
2. **Dado** regras de acesso multi-tenant, **Quando** `seed_data` tenta cruzar dados entre tenants, **Entao** a operacao e bloqueada, logada e auditada sem expor PII.

### User Story 2 - Factories reutilizaveis com PII mascarada (Prioridade: P2)

- **Persona & Objetivo**: Desenvolvedora backend quer gerar cenarios especificos via factories (factory-boy) com anonimização garantida em campos PII.  
- **Valor de Negocio**: Facilita testes deterministas e seguros, evitando vazamento de dados reais.  
- **Contexto Tecnico**: Suites de unidade/integracao, contratos de API `/api/v1`, catalogo de PII do blueprint.

**Independent Test**: Factories geram registros com PII mascarada e schemas compatíveis com contratos de API validados por testes automatizados.

**Acceptance Scenarios (BDD)**:
1. **Dado** uma factory de cliente com campos PII marcados, **Quando** gero 100 registros, **Entao** todos os campos sensiveis estao mascarados/anonimizados e passam pela checagem automatizada de PII.  
2. **Dado** uma chamada de API `/api/v1/...` usando dados vindos da factory, **Quando** submeto a requisicao em ambiente de teste, **Entao** o contrato e respeitado sem violar limites de rate limit.

### User Story 3 - Datasets sinteticos para carga e DR (Prioridade: P3)

- **Persona & Objetivo**: Engenheira de SRE precisa gerar volumetria (Q11) configuravel para testes de carga e cenarios de recuperacao de desastre sem afetar limites de API.  
- **Valor de Negocio**: Garante previsibilidade de performance e prontidao de DR sem risco de degradar servicos.  
- **Contexto Tecnico**: Testes de carga orquestrados, limitadores de taxa, politicas de DR e retencao de dados.

**Independent Test**: Execucao de carga configurada cria e limpa datasets sinteticos dentro do orcamento de rate limit e valida restauracao conforme RTO/RPO definidos.

**Acceptance Scenarios (BDD)**:
1. **Dado** parametros de volumetria por ambiente/tenant, **Quando** gero dataset sintetico em modo carga, **Entao** o processo respeita rate limits, completa dentro do tempo-alvo e exporta relatorio de volumetria.  
2. **Dado** um cenário de DR simulado, **Quando** disparo restauracao a partir das seeds e factories, **Entao** o ambiente retorna ao estado consistente dentro do RTO/RPO definidos e logs comprovam anonimização.

### Edge Cases & Riscos Multi-Tenant

- Execucao de `seed_data` sem `tenant_id` ou com tenant inexistente deve falhar com mensagem auditavel e sem criar dados parciais.  
- Reexecucao de seeds deve ser idempotente e resolver conflitos de versao para evitar duplicidades ou violacao de unicidade.  
- Gatilhos de rate limit em `/api/v1` durante geracao de carga precisam de backoff e orcamento de requisicoes por tenant/ambiente.  
- Seeds/factories nao podem bypassar regras de mascaramento/anonimizacao de PII mesmo em ambientes internos.  
- Falhas em integracoes (banco, fila, cache) devem abortar seeds de forma transacional ou marcar estado inconsistente com mecanismo de retry seguro.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do codigo, cobrindo trajetorias felizes/tristes | Seeds e factories so sao aprovadas com testes automatizados de criacao/validacao por tenant. |
| Art. IV (Qualidade Dados) | Integridade e rastreabilidade de dados gerados | Relatorios de validacao e auditoria de seeds com hash/assinaturas por execucao. |
| Art. VIII (Entrega) | Estrategia de release segura (feature flag/canary/rollback) | Habilitacao gradual do comando `seed_data` por ambiente com rollback documentado. |
| Art. IX (CI) | Cobertura >=85 %, SAST/DAST/SCA, SBOM, carga | Pipeline valida seeds/factories, rodas basicas de carga com volumetria Q11 e reporta cobertura. |
| Art. XI (API) | Contratos atualizados e resiliencia | Seeds/factories respeitam contratos `/api/v1` e validacao de contratos roda na pipeline. |
| Art. XIII (LGPD/RLS) | Enforcar RLS, mascaramento PII, direito ao esquecimento | Catalogo PII aplicado a seeds/factories, mascaramento automatico e limpeza por tenant. |
| Art. XVI (FinOps) | Custos rastreados, budgets | Volumetria por ambiente monitorada; execucoes de carga reportam consumo previsto. |
| ADR-010/011/012 | Seguranca de dados, governanca de API, observabilidade | Telemetria de seeds com traceabilidade e alertas de falha/PII. |
| Outros | Blueprint §§3.1, 6, 26 e adicoes 1,3,8,11 referenciam isolamento, DR e testes | Regras aplicadas em configuracao de volumetria, DR e mascaramento. |

### Functional Requirements

- **FR-001**: Comando `seed_data` DEVE provisionar baseline completa por ambiente/tenant, parametrizando volumetria (Q11) e garantindo idempotencia.  
- **FR-002**: Catalogo de factories baseado em factory-boy DEVE cobrir entidades principais e permitir sobreposicao de cenarios (happy/sad paths) com mascaramento automatico de PII.  
- **FR-003**: Todo dado PII em seeds/factories DEVE ser anonimisado ou mascarado conforme catalogo de sensibilidade antes de gravacao ou uso em APIs de teste.  
- **FR-004**: Validacao automatizada DEVE bloquear seeds que nao atendam contratos de API `/api/v1`, integridade referencial ou regras multi-tenant.  
- **FR-005**: Pipeline de CI/CD DEVE executar `seed_data` e factories em modo dry-run e gerar relatorio de conformidade (PII, contratos, volumetria, idempotencia).  
- **FR-006**: Deploys via Argo CD DEVEM acionar verificacao pos-deploy das seeds/factories e publicar resultado em canal de auditoria.  
- **FR-007**: Procedimentos de DR DEVEM conseguir restaurar ambiente alvo usando seeds/factories, mantendo mascaramento e respeitando RTO/RPO definidos no blueprint.  
- **FR-008**: Geração de datasets sinteticos para teste de carga DEVE respeitar limites de requisicoes por tempo, com configuracao de rate limit por tenant/ambiente e relatorio de uso.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Execucoes de `seed_data` devem completar dentro de janelas definidas por ambiente (dev <5 min, homolog <10 min, producao controlada <20 min); exceder +20% aciona abort/rollback auditado.  
- **NFR-002 (Performance)**: Testes de carga com datasets sinteticos nao devem acionar mais de 80% do limite configurado de requisicoes por minuto; variacao de tempo de resposta deve permanecer dentro do orcamento de SLO do blueprint.  
- **NFR-003 (Observabilidade)**: Seeds/factories devem emitir logs e metricas de execucao, incluindo contagem de registros gerados por entidade, deteccao de PII mascarada e alertas de falha.  
- **NFR-004 (Seguranca)**: Dados sensiveis devem permanecer mascarados em logs, dumps e exportacoes; acesso a configuracoes de seeds/factories deve seguir principio do menor privilegio.  
- **NFR-005 (FinOps)**: Volume de dados gerados e custo estimado por execucao deve ser registrado; execucoes de carga devem respeitar budgets definidos por ambiente/tenant.

### Dados Sensiveis & Compliance

- Catalogo PII deve mapear campos sensiveis usados em seeds/factories (ex.: documentos, email, telefone, endereco) e aplicar mascaramento/anonimizacao antes de persistir.  
- Retencao: datasets sinteticos devem seguir politicas do ambiente (limpeza automatica em ambientes de teste, expurgo em DR apos validacao).  
- Direito ao esquecimento: comandos de limpeza por tenant devem remover dados sinteticos vinculados ao tenant sob solicitacao.  
- Evidencias: relatórios de execucao com hash/assinatura, trilha de auditoria de quem disparou seeds, provas de mascaramento e conformidade com LGPD/RLS.

## Assumptions & Defaults

- Volumetria (Q11) por ambiente/tenant: dev 1x baseline, homolog 3x, staging de carga 5x, producao controlada 1x (apenas minimo); hard cap configuravel por entidade/tenant (ex.: clientes 50k, contratos 200k, transacoes 1M).  
- Rate limit para geracao via `/api/v1`: usar ate 80% do limite por ambiente com throttling sugerido (dev 300 rpm, homolog 600 rpm, staging carga 1.200 rpm, producao controlada 300 rpm) e backoff com jitter.  
- Janela de carga: execucoes preferenciais em horarios de baixo uso (ex.: 22h–06h local do datacenter) para evitar competicao com usuarios.  
- DR: manter RPO <5 min e RTO <1h do blueprint; seeds/factories devem completar restauracao e validacao em ate 40 min para preservar margem.  
- FinOps: budget por execucao de carga (dev/homolog <US$5, staging carga <US$25, producao controlada <US$50); alertar e bloquear acima de 80% do budget.  
- PII: mascaramento obrigatorio em 100% dos campos sensiveis; checagem automatizada bloqueia execucoes em caso de falha.

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- **SC-001**: `seed_data` conclui em cada ambiente dentro dos tempos-alvo (dev <5 min, homolog <10 min, producao controlada <20 min) com 0 erros de validacao; execucoes que excedem +20% sao abortadas e auditadas.  
- **SC-002**: Factories cobrem 100% das entidades criticas e passam por checagem automatizada de PII, com 0 campos sensiveis sem mascaramento detectados.  
- **SC-003**: Pipelines de CI/CD executam seeds/factories em dry-run com taxa de sucesso >=99% por PR/release e publicam relatorio de conformidade.  
- **SC-004**: Testes de carga com datasets sinteticos consomem <=80% do limite de requisicoes previsto (ex.: 300/600/1.200/300 rpm por ambiente) e completam na janela off-peak sem incidentes de degradacao.  
- **SC-005**: DR simulado restaura estado consistente por tenant em <40 min para respeitar RTO <1h e perda de dados <=RPO de 5 min, comprovado por relatorios de verificacao.  
- **SC-006**: Custos estimados de volumetria mantidos dentro do budget por ambiente/tenant, com alertas ao atingir 80% e bloqueio acima do teto.

## Outstanding Questions & Clarifications

Nenhuma aberta; decisoes assumidas seguem blueprint e constituicao para seeds, PII e DR.
