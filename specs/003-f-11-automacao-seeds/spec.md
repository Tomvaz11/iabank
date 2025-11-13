# Feature Specification: F-11 Automação de Seeds, Dados de Teste e Factories

**Feature Branch**: `003-f-11-automacao-seeds`  
**Created**: 2025-11-13  
**Status**: Draft  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`."

> Referências obrigatórias: `BLUEPRINT_ARQUITETURAL.md` §§3.1, 6, 26; `adicoes_blueprint.md` itens 1, 3, 8, 11; Constituição (Art. III/IV) e ADRs aplicáveis. Esta especificação foca no QUE e POR QUÊ, sem detalhar como implementar.

## Contexto

Hoje a criação de dados de base e de teste é manual e inconsistente entre ambientes/tenants, o que atrasa validações, gera risco de exposição de PII e dificulta DR e testes de carga. A feature padroniza e automatiza seeds e factories com mascaramento/anonimização, parametrização de volumetria (Q11) por ambiente/tenant e integração aos fluxos de entrega para garantir reprodutibilidade, segurança e governança. Respeita limites de taxa dos serviços expostos, evitando degradação operacional.

## Clarifications

### Session 2025-11-13

- Q: Qual a chave única canônica para dados gerados que garanta idempotência por tenant sem expor PII? → A: UUIDv5 determinístico namespaced por tenant+entidade.
- Q: Por onde as seeds devem operar em ambientes não‑produtivos para preservar invariantes e respeitar limites de taxa? → A: APIs de domínio com throttling.
- Q: Como orquestrar a execução das seeds por ambiente? → A: Híbrido: CI valida; Argo aplica nos ambientes.
- Q: Qual o formato padrão para export/restore de datasets (DR/seeds)? → A: NDJSON por entidade + manifest + checksums.
- Q: Qual a estratégia canônica de anonimização de PII? → A: Substituição sintética determinística (faker+segredo Vault).
- Q: Qual mecanismo padrão para escopo de tenant nas chamadas às APIs de domínio? → A: Cabeçalho X-Tenant-ID obrigatório em todas as requisições.
- Q: Qual estratégia de rate limiting e retries deve ser adotada nas seeds/chamadas às APIs? → A: Backoff exponencial com jitter + token bucket por tenant.
- Q: Como as seeds devem se autenticar nas APIs de domínio? → A: Service Account + OAuth2 Client Credentials (escopos mínimos).
- Q: Qual o padrão mínimo de observabilidade para seeds/factories? → A: OTel tracing + logs estruturados + métricas (cardinalidade controlada).
- Q: Como criptografar os artefatos NDJSON/DR exportados? → A: Vault Transit por ambiente; envelope AES‑256‑GCM; manifest inclui KID/algoritmo.
- Q: Qual deve ser a granularidade canônica de restore (DR/seeds)? → A: Por tenant como padrão; ambiente inteiro só via playbook DR aprovado.
- Q: Como parametrizar Q11 (volumetria) por entidade/tenant? → A: Manifesto por ambiente com contagens absolutas por entidade (versionado) + multiplicador opcional por tenant.
- Q: Qual política de concorrência para execução de seeds no mesmo tenant? → A: Exclusão mútua por tenant via lock distribuído com TTL e renovação.
- Q: Onde armazenar os artefatos NDJSON (export/restore) de forma segura e auditável? → A: Bucket de objetos por ambiente (versioning + WORM/immutability), com prefixos por tenant.
- Q: Em produção, qual caminho de execução é permitido para seeds não sensíveis? → A: Somente via APIs de domínio com throttling e auditoria.
- Q: Qual política de reconciliação para seeds ao alinhar contagens por entidade/tenant? → A: Reconciliação por origem: upsert determinístico e deletar apenas registros criados pela seed que excedam a meta.
- Q: Como identificar a origem “seed” para rastreabilidade e reconciliação sem alterar contratos de API? → A: Auditoria do domínio (created_by=service account “seed-data” + run_id/correlação).
- Q: Qual a granularidade canônica de rollback/limpeza das seeds? → A: Rollback por run_id: desfaz somente registros seed daquela execução.
- Q: Como tratar compatibilidade de schema ao importar artefatos NDJSON? → A: Fail-fast se versão do manifest != esperada; migrar dataset no CI.
- Q: Qual política de retenção WORM para artefatos NDJSON por ambiente? → A: Dev 7d, Homolog 30d, Perf 90d (WORM).
- Q: Qual backend de lock distribuído para exclusão mútua por tenant? → A: Redis 7 (SET NX + TTL com renovação, Redlock-safe).
- Q: Qual a ordem de import/restore entre entidades? → A: Manifesto com ordem topológica por dependências (ex.: Cliente→Conta→Cartão→Transação→Identificador de Pagamento).
- Q: Qual a fonte do rate limit efetivo? → A: Auto-descoberta via cabeçalhos HTTP (X-RateLimit-*, Retry-After) com fallback para manifesto por ambiente/tenant.
- Q: Qual limite de paralelismo global por ambiente? → A: Dev=3, Homolog=5, Perf=10; Produção sem seeds sensíveis.
- Q: Qual a granularidade das Service Accounts? → A: Service Account por tenant (escopos mínimos por domínio).

- Q: As APIs de domínio devem aceitar `external_id` estável por entidade/tenant para upsert idempotente via API, sem leitura prévia? → A: Sim — padronizar `external_id` por entidade/tenant para upsert idempotente.

## Hipóteses

- Existem políticas e um catálogo de PII/PD por domínio atualizados e acessíveis para orientar anonimização/mascaramento.
- Os pipelines de CI/CD possuem permissões e recursos para executar gates de validação de seeds/factories, varreduras de PII e publicação de evidências.
- A orquestração de entrega via Argo CD está habilitada para aplicar seeds em ambientes pré‑aprovados, respeitando janelas operacionais e RBAC.
- Os limites de taxa das APIs (incluindo a superfície `/api/v1`) estão documentados por ambiente/tenant; a execução manterá uso ≤ 80% do teto efetivo.
- A política de volumetria Q11 por ambiente/tenant é vigente (Dev=baixo, Homolog=médio, Perf=alto); sobrescritas exigem aprovação do ambiente.
- Ambientes não‑produtivos isolam dados por tenant (RLS) e suportam reexecução idempotente; produção não recebe seeds com PII.
- Metas de DR acordadas: RTO 60 minutos (p95) e RPO 15 minutos, com snapshots/datasets disponíveis para restauração controlada.

## User Scenarios & Testing (mandatório)

As histórias abaixo são independentes (INVEST) e validáveis de forma isolada.

### User Story 1 - Popular ambiente com dados seguros (Prioridade: P1)

- Persona & Objetivo: QA/Engenharia precisa popular um ambiente não-produtivo com dados realistas, porém anonimizados, para validar regressões e jornadas críticas.
- Valor de Negócio: Reduz tempo de preparação de testes e elimina risco de PII vazada; acelera feedback de qualidade.
- Contexto Técnico: Multi-tenant; parametrização de volumetria (Q11) por ambiente/tenant; execução controlada para não exceder limites de taxa.

Independent Test: Execução do comando de produto "seed_data" valida criação idempotente e segura; checagens automáticas de consistência e anonimização aprovadas.

Acceptance Scenarios (BDD):
1. Dado um ambiente não-produtivo vazio e um tenant válido, Quando executo "seed_data" com Q11=medium, Então o ambiente contém entidades mínimas e relacionamentos íntegros, com PII mascarada e evidências registradas.
2. Dado um conjunto de regras de anonimização, Quando o dataset contém PII em campos textuais e estruturados, Então todos os campos classificados como PII permanecem não reversíveis e auditáveis.

### User Story 2 - Gate de CI/CD para seeds (Prioridade: P1)

- Persona & Objetivo: Plataforma/Dev quer validar automaticamente que seeds e factories permanecem válidas a cada mudança.
- Valor de Negócio: Evita que quebras em seeds cheguem a ambientes; garante previsibilidade de testes e releases.
- Contexto Técnico: Execução em pipeline; relatórios e artefatos de evidência; integração com orquestração declarativa de deploy (GitOps) para ambientes alvo.

Independent Test: Pipeline executa estágio de seeds, coleta métricas/relatórios e reprova a mudança ao encontrar violações.

Acceptance Scenarios (BDD):
1. Dado uma PR que altera factories, Quando o estágio de validação roda, Então falha se a contagem/distribuição esperada não for atingida ou se houver PII não mascarada.
2. Dado um ambiente de destino, Quando a orquestração de entrega aplica a rotina de seed, Então a execução respeita janelas/limites definidos e registra sucesso com auditoria.

### User Story 3 - Datasets sintéticos e testes de carga (Prioridade: P2)

- Persona & Objetivo: SRE/Perf quer gerar datasets sintéticos com volumetria variável para testes de carga, sem afetar limites de taxa dos serviços.
- Valor de Negócio: Permite medir capacidade e planejar escala com segurança.
- Contexto Técnico: Geração progressiva, throttling e janelas por ambiente/tenant; não exceder limites de taxa acordados.

Independent Test: Execução de carga com Q11 alto produz volume configurado dentro do tempo alvo e sem ultrapassar limites de taxa.

Acceptance Scenarios (BDD):
1. Dado um ambiente de performance e três tenants, Quando solicito Q11=alto por tenant, Então o sistema entrega o volume em janela controlada, com taxa efetiva ≤ 80% do limite alocado e sem erros por rate limiting.
2. Dado políticas de DR, Quando aciono a restauração baseada em seeds e snapshots, Então o ambiente é reconstituído dentro do RTO/RPO definidos, com dados anonimizados.

### Edge Cases & Riscos Multi-Tenant

- Tenant inexistente ou sem associação a ambiente: a execução deve abortar com erro claro e sem efeitos colaterais.
- Falhas intermitentes de dependências: aplicar repetição com backoff e idempotência para evitar duplicidade.
- Q11 inválido ou fora da faixa: rejeitar parâmetros e informar opções válidas por ambiente.
- PII em campos livres (observações, descrições): garantir mascaramento consistente e irreversível.
- Reexecução de seeds: múltiplas execuções levam ao mesmo estado final (idempotência) e registram difs.
- Limites de taxa: nunca exceder 80% do limite contratado por ambiente/tenant; aplicar limitação e janelas.
- Cabeçalho X-Tenant-ID ausente ou inválido: rejeitar com erro claro (HTTP 400/401) sem efeitos colaterais.
- Erros 429/503: aplicar retries com backoff exponencial com jitter e limitação por token bucket por tenant; abortar após limiar configurado.
- Manifest sem KID/algoritmo ou falha de decriptação: abortar restore com erro claro e registrar evidências; nunca armazenar PII em claro.
- Autenticação expirada ou escopo insuficiente (401/403): renovar token via OAuth2 CC; falhar com erro claro se o escopo mínimo não estiver disponível.
 - Logs/traces contendo PII: reprovar pipeline; aplicar redaction e reprocessar; registrar evidências.
 - Explosão de cardinalidade em métricas: aplicar limites/normalização de labels e reduzir cardinalidade; falhar validação se exceder política.

## Integrações e Restrições

- Orquestração de entrega: abordagem híbrida — CI valida (gates, relatórios, evidências) e Argo CD aplica nos ambientes (GitOps), com janelas, aprovações, rollback e detecção de drift; execução disparada por artefatos versionados; execução registrada e auditável por ambiente/tenant.
- Factories padronizadas: uso de factories compatíveis com o padrão corporativo (ex.: factory-boy) para garantir dados previsíveis, repetíveis e auditáveis.
- Caminho de execução: seeds e validações DEVEM operar via APIs de domínio com throttling; acesso direto ao banco É PROIBIDO em todos os ambientes. Em produção, apenas seeds não sensíveis são permitidas e OBRIGATORIAMENTE via APIs com auditoria.
- Escopo multi-tenant: todas as requisições DEVEM incluir o cabeçalho obrigatório `X-Tenant-ID`; alternativas (path param, subdomínio, somente claim JWT) NÃO SÃO ACEITAS para seeds/factories.
- Idempotência via API: as rotinas de seed DEVEM enviar `Idempotency-Key` em mutações com TTL e deduplicação auditável; e todas as APIs de domínio DEVEM aceitar `external_id` estável por entidade/tenant para permitir upsert idempotente sem leitura prévia pelas rotinas de seed.
- Export/Restore de datasets: adotar NDJSON por entidade, com manifest (schemaVersion, checksums SHA‑256, contagens esperadas, metadados de catálogo de PII). Criptografia obrigatória via Vault Transit por ambiente (envelope AES‑256‑GCM); manifest deve incluir `kid` e `algoritmo`. Formato stream‑friendly, agnóstico de engine e validável no CI/Argo. Granularidade canônica: por tenant como padrão; restauração do ambiente inteiro apenas via playbook de DR aprovado. Armazenamento: bucket de objetos por ambiente com versionamento e WORM/imutabilidade, organizado por prefixos de tenant, com políticas de retenção e IAM restritivas.
- Respeito a limites de taxa: geração e validações NÃO DEVEM exceder 80% do rate limit efetivo das APIs do domínio, incluindo a superfície `/api/v1`, por ambiente e por tenant.
- Controle de taxa e retries: DEVEM implementar limitação por tenant (ex.: token bucket) combinada a backoff exponencial com jitter e concorrência adaptativa para manter uso ≤ 80% do limite.
 - Concorrência: aplicar exclusão mútua por tenant por meio de lock distribuído com TTL e renovação; proibir execuções paralelas no mesmo tenant para evitar conflitos e pressão nos rate limits.
- Autenticação: DEVEM usar Service Account com OAuth2 Client Credentials com escopos mínimos por domínio; tokens de curta duração (≤ 15 min), segredos/creds geridos no Vault; mTLS opcional como camada adicional. SÃO VEDADOS tokens de usuário delegados e JWT estático de longa duração.
 - Observabilidade: DEVEM instrumentar seeds/factories/validações com OpenTelemetry (tracing), logs JSON estruturados e métricas (Prometheus), sem PII; adotar amostragem e limites de cardinalidade; correlação por `run_id`, `tenant_id`, `env` e `q11`.
- Governança de API: erros devem seguir RFC 9457 (Problem Details) e, quando aplicável, mutações devem aplicar controle de concorrência condicional (`ETag`/`If-Match`) para evitar lost‑update.
- Escopo de execução por ambiente:
  - Desenvolvimento: Q11 baixo por padrão; reexecuções livres, focadas em rapidez.
  - Homologação: Q11 médio; prioriza representatividade e anonimização estrita.
  - Performance: Q11 alto; foco em volumetria e janela controlada sem estourar limites de taxa.
  - Produção: execução restrita às rotinas sem PII (ex.: catálogos/configurações); seeds com dados sensíveis não devem ser aplicadas em produção; somente via APIs de domínio com throttling e auditoria; vedado acesso direto ao banco.
  - Observação: valores de Q11 podem ser sobrescritos por política do ambiente/tenant, respeitando limites máximos aprovados.

## Interfaces & Comandos (o que/por quê)

- Comando de gerenciamento: a feature DEVE expor um comando de gerenciamento do Django para seeds ("seed_data") responsável por criar/atualizar dados base e de teste por ambiente/tenant, com idempotência comprovada e validações pós‑execução.
- Parâmetros funcionais obrigatórios: seleção de tenant(s); ambiente de destino; nível de volumetria (Q11: baixo/médio/alto); seleção de entidades/escopos; modos de execução (dry‑run, validate‑only); identificador de execução (run_id); limites configuráveis de concorrência, taxa e tempo; padronização de códigos de saída. Não prescrever sintaxe/flags aqui — detalhar no /speckit.plan.
- Resultados observáveis: publicar relatórios de validação (contagens/distribuições, integridade referencial, anonimização/PII=0), métricas de execução e artefatos/evidências no pipeline; respeitar rate limit efetivo (≤ 80%) por ambiente/tenant.

## Requirements (mandatório)

### Constituição & ADRs Impactados

| Artigo/ADR           | Obrigação                                                           | Evidência nesta feature                                                                 |
|----------------------|---------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| Art. III (TDD)       | Testes antes do código, felizes/tristes                            | Testes automatizados para validação de seeds, factories e anonimização por tenant       |
| Art. IV (Integração) | Validações integradas e evidências nos fluxos de entrega            | Gate dedicado nas rotinas de entrega, com auditoria e rollback documentado              |
| Art. VIII (Entrega)  | Estratégia de release segura (feature flag/canary/rollback)        | Execução controlada por ambiente com rollback seguro de dados sem efeito em produção    |
| Art. IX (CI)         | Cobertura, qualidade e gates em CI                                 | Estágio dedicado que bloqueia merge/deploy ao detectar violações nas validações         |
| Art. XI (API)        | Contratos e erros padronizados                                     | Aceitar `external_id` para upsert idempotente; exigir `Idempotency-Key` com TTL/deduplicação auditável; erros no padrão RFC 9457; quando aplicável, `ETag`/`If-Match` para evitar lost‑update; consumo respeita limites de taxa e SLO |
| Art. XII (Security)  | RBAC/ABAC, proteção de dados                                        | Matriz de permissões para executar seeds/rollback/export/restore por ambiente/tenant; testes automatizados de autorização |
| Art. XIII (LGPD/RLS) | RLS, mascaramento PII, retenção/direito ao esquecimento            | Catálogo de PII, regras de anonimização e evidências de auditoria por ambiente/tenant   |
| Art. XVI (FinOps)    | Custos rastreados e otimizados                                     | Execuções janeladas, limites por ambiente/tenant e relatórios para evitar picos de custo|
| ADR-009 (GitOps)     | Entrega declarativa e detecção de drift                            | Seeds integradas ao fluxo GitOps e compatíveis com rollback e auditoria                  |
| ADR-010/011/012      | Segurança de dados, governança de API, observabilidade             | Logs e métricas sobre seeds/anonimização, sem exposição de PII                          |

## Entidades‑Chave

- Cliente: pessoa com dados de identificação e contato que deve ser sempre anonimizada fora de produção.
- Conta: relacionamento do cliente com saldos, limites e configurações; base para volumetria por tenant.
- Transação: movimentos financeiros associados a contas; usados para testes de carga e integridade.
- Cartão: meio de pagamento associado à conta/cliente; incluir somente dados sintéticos e mascarados.
- Identificador de Pagamento: chaves/tokens usadas em operações; sempre geradas de forma sintética e não reidentificável.
- Identidade & idempotência: usar chave técnica determinística (UUIDv5 namespaced por tenant+entidade) nas seeds/factories; nunca derivar de PII; este valor será enviado às APIs como `external_id` para permitir upsert idempotente sem leitura prévia.

### Functional Requirements

- FR-001: Disponibilizar comando de gerenciamento do Django "seed_data" para criar/atualizar dados base e de teste por ambiente e tenant, com idempotência comprovada.
- FR-002: Disponibilizar factories padronizadas para geração determinística de entidades e relacionamentos, com perfis de dados (mínimo, médio, alto) alinhados ao Q11.
- FR-003: Aplicar anonimização/mascaramento irreversível para todos os campos classificados como PII/PD antes de qualquer uso fora de produção.
- FR-004: Implementar validações automáticas pós-seed (contagem mínima por entidade, distribuição por tenant, integridade referencial, inexistência de PII não mascarada). Execução falha ao violar qualquer regra.
- FR-005: Integrar a rotina de seeds aos fluxos de entrega, como um gate obrigatório: mudança só avança se as validações passarem e as evidências forem publicadas.
- FR-006: Permitir parametrização de volumetria (Q11) por ambiente/tenant via manifesto versionado por ambiente com contagens absolutas por entidade e multiplicador opcional por tenant, respeitando valores padrão e limites máximos por ambiente.
- FR-007: Gerar datasets sintéticos para testes de carga com limitação de taxa e controle de concorrência para não exceder 80% do limite por ambiente/tenant.
- FR-008: Suportar DR por meio de reconstituição do estado via seeds e snapshots/datasets exportáveis, assegurando consistência entre tenants.
- FR-009: Fornecer observabilidade e auditoria: trilhas de execução, métricas de progresso/erros, e relatórios de anonimização sem vazar PII.
- FR-010: Prever rotina de limpeza/rollback canônica por run_id em ambientes não‑produtivos, desfazendo apenas registros de origem seed daquela execução; vedado alterar/deletar dados fora da origem seed.
- FR-011: Restringir execução a perfis autorizados e registrar quem, quando e onde executou, por compliance.
- FR-012: Adotar UUIDv5 determinístico namespaced por tenant+entidade como chave técnica canônica nas seeds/factories para garantir idempotência e reexecuções seguras sem expor PII.
- FR-013: Executar seeds via APIs de domínio com throttling e controles de concorrência; vedado acesso direto ao banco em todos os ambientes. Em produção, apenas seeds não sensíveis e obrigatoriamente via APIs com auditoria.
- FR-014: Orquestração híbrida: validação obrigatória no CI (gates/evidências) e aplicação declarativa via Argo CD nos ambientes aprovados.
 - FR-015: Padronizar export/import (DR e seeds) como NDJSON por entidade com manifest (versionamento de schema, ordem topológica por dependências e checksums); restore por tenant como padrão deve validar checksums e contagens esperadas antes de aplicar; restauração de ambiente inteiro somente via playbook de DR aprovado; falhar imediatamente se a versão de schema do manifest divergir da esperada e exigir migração do dataset no CI.
- FR-016: Anonimização por substituição sintética determinística (faker) parametrizada por tenant, usando segredo armazenado no Vault; preservar formatos/validações de domínio e proibir tokenização reversível.
- FR-017: Escopo multi-tenant padronizado via cabeçalho obrigatório `X-Tenant-ID` em todas as chamadas realizadas por seeds/factories/validações.
 - FR-018: Implementar retries com backoff exponencial com jitter e limitação por token bucket por tenant, com controle de concorrência para respeitar o teto de 80% do rate limit; descobrir dinamicamente o rate limit via cabeçalhos HTTP (X-RateLimit-*, Retry-After), com fallback para manifesto por ambiente/tenant quando os cabeçalhos não estiverem disponíveis.
 - FR-019: Seeds/factories/validações devem autenticar via Service Account por tenant usando OAuth2 Client Credentials com escopos mínimos por domínio; tokens com TTL curto e rotação automática; proibir chaves/tokens estáticos de longa duração.
- FR-020: Criptografar artefatos de export/restore (NDJSON) usando Vault Transit por ambiente com envelope AES‑256‑GCM; manifest deve conter KID/algoritmo; chaves segregadas por ambiente; proibir armazenamento de PII em claro.
 - FR-021: Instrumentar com OpenTelemetry (tracing), logs estruturados e métricas com cardinalidade controlada; correlação por run_id/tenant_id/env/q11; proibir PII nos sinais.
 - FR-022: Aplicar exclusão mútua por tenant com lock distribuído com expiração e renovação para impedir execuções concorrentes no mesmo tenant; registrar contenda e fila de espera quando aplicável.
 - FR-023: Armazenar artefatos NDJSON (export/restore) em bucket de objetos por ambiente com versionamento habilitado e WORM/imutabilidade, usando prefixos por tenant; acesso via IAM mínimo necessário; retenção: Desenvolvimento 7 dias, Homologação 30 dias, Performance 90 dias; ajustes de retenção exigem aprovação do ambiente.
 - FR-024: Reconciliação por origem: realizar upsert determinístico e deletar apenas registros criados pela seed que excedam a meta por entidade/tenant; nunca alterar/deletar dados fora da origem seed; sempre via APIs de domínio.
- FR-025: Marcação de origem “seed”: todo registro criado via seeds deve ser identificável pela auditoria do domínio (created_by=service account “seed-data” e run_id/correlação persistidos) para permitir reconciliação e auditoria sem mudanças de contrato.

- FR-026: Todas as APIs de domínio devem aceitar campo `external_id` estável por entidade/tenant e realizar upsert idempotente com base nele, sem necessidade de leitura prévia; chamadas de seed sem `external_id` devem ser rejeitadas.

- FR-027: As rotinas de seed DEVEM enviar `Idempotency-Key` em todas as mutações e as APIs DEVEM aplicar deduplicação com TTL auditável conforme a governança de API (Art. XI); chamadas que violem a política devem ser rejeitadas.

- FR-028: O pipeline de CI/CD DEVE incluir um gate de performance com thresholds mensuráveis por ambiente; mudanças que violem os thresholds devem ser reprovadas e os relatórios publicados como evidência.

- FR-029: DEVE existir matriz RBAC/ABAC que define quem pode executar seeds/rollback/export/restore por ambiente/tenant, acompanhada de testes automatizados de autorização.


### Parametrização de Volumetria (Q11)

| Ambiente       | Padrão Q11 | Faixa Permitida     | Notas                                                        |
|----------------|------------|---------------------|--------------------------------------------------------------|
| Desenvolvimento| baixo      | baixo–médio         | Foco em rapidez; reexecuções livres                          |
| Homologação    | médio      | baixo–médio         | Representatividade; anonimização estrita                     |
| Performance    | alto       | médio–alto          | Janela controlada; uso ≤ 80% do limite de taxa               |
| Produção       | N/A        | somente não sensível| Sem PII; apenas catálogos/configurações; Q11 não aplicável   |

Observação: valores podem ser sobrescritos por tenant mediante política/aprovação do ambiente, respeitando limites máximos.
\
Modelo de parametrização: manifesto versionado por ambiente define contagens absolutas por entidade; cada tenant pode aplicar um multiplicador opcional aprovado (ex.: 1x, 2x, 5x) sobre os mínimos por entidade, respeitando limites do ambiente.

### Non-Functional Requirements

- NFR-001 (Confiabilidade): Reexecuções são idempotentes; falhas parciais recuperam de forma automática sem duplicidades.
- NFR-002 (Desempenho): População Q11=médio por tenant conclui em até 15 minutos no p95; Q11=alto em até 45 minutos, conforme ambiente.
- NFR-003 (Observabilidade): OpenTelemetry tracing + logs JSON estruturados + métricas (Prometheus) com cardinalidade controlada e correlação por run_id/tenant_id/env/q11; sem expor PII.
- NFR-004 (Segurança/Compliance): Controles de acesso, classificação de dados e anonimização verificada por varreduras automáticas.
- NFR-005 (Operabilidade/FinOps): Execuções em janelas, limitação de taxa e paralelismo global configuráveis por ambiente para evitar impactos em custos e SLOs. Limites padrão de execuções simultâneas: Desenvolvimento=3, Homologação=5, Performance=10; Produção: sem seeds sensíveis (somente via APIs com auditoria).
- NFR-006 (Segurança): Tokens de acesso com TTL ≤ 15 minutos, escopos mínimos por domínio e rotação periódica de credenciais/segredos pelo Vault.
 - NFR-007 (Proteção de dados): Artefatos NDJSON/DR sempre criptografados (AES‑256‑GCM via Vault Transit), com rotação de chaves por ambiente e comprovação de integridade (checksums) antes do restore; restore deve falhar imediatamente em divergência de versão de schema.
 - NFR-008 (Observabilidade): Sampling configurável e limites de cardinalidade em métricas/traces; reprovar execuções que excedam políticas definidas no CI.

### Dados Sensíveis & Compliance

- Classificar campos sensíveis por domínio (ex.: identificação pessoal, contato, documentos, dados financeiros) e manter catálogo versionado.
- Regras de anonimização devem ser irreversíveis e consistentes entre ambientes; amostragens devem comprovar 0 ocorrência de PII não mascarada.
- Estratégia canônica: substituição sintética determinística (faker) com segredo por ambiente/tenant no Vault (KV/Transit), garantindo reprodutibilidade sem reversibilidade; preservar formatos (ex.: CPF/CNPJ com dígitos válidos) sem apontar para pessoas reais.
- Gestão de credenciais: contas de serviço e client credentials armazenados/rotacionados no Vault; proibir compartilhamento; auditoria de uso por ambiente/tenant.
- Criptografia de artefatos: usar Vault Transit (AES‑256‑GCM) por ambiente; manifest inclui KID/algoritmo; proibir export/armazenamento em claro; evidenciar processo no pipeline.
- Evidências requeridas: relatório de varredura de PII, relatório de validação de seeds, trilha de auditoria por tenant e por execução.
 - Logs/Traces: aplicar redaction e denylist de PII antes da emissão; validações automáticas em CI para prevenir vazamento.

## Success Criteria (mandatório)

### Métricas Mensuráveis

- SC-001: 100% das execuções de "seed_data" em ambientes-alvo concluem com todas as validações automáticas aprovadas.
- SC-002: 0 ocorrências de PII não mascarada nas varreduras automáticas sobre os dados gerados (por ambiente/tenant) por 30 dias após a entrada em vigor.
- SC-003: Geração de datasets sintéticos atinge os alvos de volumetria Q11 por tenant em janela acordada (p95: médio ≤ 15 min; alto ≤ 45 min), sem exceder 80% do limite de taxa.
- SC-004: Gate de entrega reprova 100% das mudanças que causam quebra de seeds/factories/anonimização, com evidências publicadas.
- SC-005: Procedimento de DR reconstitui ambiente de teste dentro do RTO de 60 minutos (p95) e RPO de 15 minutos, com dados anonimizados.

- SC-006: Gate de performance no CI/CD reprova mudanças que violem thresholds definidos por ambiente; relatórios e métricas de execução publicados como evidência.

Associe cada critério aos testes automatizados e relatórios do pipeline para verificação objetiva.

## Outstanding Questions & Clarifications

Sem pendências críticas no momento; dúvidas operacionais menores podem ser tratadas em planejamento.
