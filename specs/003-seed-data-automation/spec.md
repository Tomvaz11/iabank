# Feature Specification: Automacao de seeds, dados de teste e factories

Rodada de clarificações #15 concluída em 2025-11-23.

**Clarify #15**: Especificacao atualizada na 15a rodada de esclarecimentos (2025-11-23).  
**Feature Branch**: `003-seed-data-automation`  
**Created**: 2025-11-22  
**Status**: Draft  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md` §§3.1, 6, 26; `adicoes_blueprint.md` itens 1, 3, 8, 11; Constituicao v5.2.0 (Art. III/IV e correlatos) e ADRs aplicaveis.

## Contexto

Time precisa automatizar seeds e datasets de teste, mantendo compliance de PII e evitando saturar APIs internas (`/api/v1`). Objetivo é oferecer comando unico (`seed_data`) e factories padronizadas (factory-boy) que gerem dados sinteticos seguros por tenant/ambiente, com validacao automatizada e integracao continua (CI/CD, Argo CD) inclusive para cenarios de DR e testes de carga. Atende diretrizes do blueprint arquitetural (autonomia de ambientes, isolamento multi-tenant, governanca de dados sensiveis) e Constituicao Art. III/IV.

## Clarifications

### Session 2025-11-23
- Q: Comportamento do `seed_data`/factories quando Celery/Redis estiverem indisponíveis? → A: Repetir poucas vezes com backoff curto e `acks_late`; se o broker permanecer indisponível, abortar fail-closed com alerta/auditoria, sem fallback local ou fora do orquestrador (exceto dev isolado).
- Q: Abordagem de execução das seeds/factories (APIs `/api/v1`, ORM/BD direto ou híbrido)? → A: Usar comando `seed_data` via ORM/BD com factory-boy como caminho principal; APIs `/api/v1` apenas para smokes/validação de contrato e rate limit, sem inserção massiva.
- Q: Abordagem para mascaramento/anonimização de PII nas seeds/factories? → A: Mascaramento/anonimização determinístico por ambiente (hash + salt) garantindo consistência entre execuções, DR e integrações multi-tenant.
- Q: Escopo mínimo obrigatório das seeds/factories? → A: Núcleo bancário: tenants/usuários, clientes/endereços, consultores, contas bancárias/categorias/fornecedores, empréstimos/parcelas, transações financeiras e limites/contratos; demais domínios ficam fora do baseline.
- Q: Onde armazenar e rotacionar sal/segredo para anonimização determinística de PII? → A: Em HashiCorp Vault (Transit ou KV com envelope via KMS), com políticas e chaves por ambiente/tenant, rotação automática e acesso só via tokens efêmeros; proibido guardar em código/vars estáticas.
- Q: Como versionar/rotacionar o sal de anonimização determinística das seeds/factories? → A: Sal versionado por ambiente/tenant; rotação publica novo `salt_version` no Vault, `seed_data` valida versão em manifesto/checkpoint e falha (fail-closed) se divergente até limpeza/reseed coordenada; breakglass só em dev isolado.
- Q: Estratégia de consistência/rollback das seeds/factories em caso de falha? (transação única vs lotes com checkpoints vs duas fases) → A: Processar em lotes por entidade/segmento com checkpoints idempotentes, reexecutando apenas o lote falho; evitar transações monolíticas longas e manter integridade multi-tenant, rate limits e SLOs.
- Q: Onde persistir o estado de checkpoint/idempotência das execuções do `seed_data`? → A: Em tabela dedicada no PostgreSQL do app, segregada por ambiente/tenant com RLS, registrando checkpoints de lote, hashes e deduplicação/TTL para retomadas seguras.
- Q: Como garantir identificadores/idempotência determinística nas seeds/factories sem expor PII? → A: Usar UUIDv5/hash determinístico namespaced por tenant+entidade (ou slug lógico) e persistir a chave para dedupe/TTL; proibir uso de PII como material de chave.
- Q: Estratégia de observabilidade/telemetria para execuções do `seed_data`/factories e cargas? → A: Instrumentar com OpenTelemetry (traces/métricas/logs JSON `structlog`), `django-prometheus` e Sentry; exportar para o collector central com correlação `traceparent`/`tracestate` e labels de tenant/ambiente/execução, validando em CI/Argo; redaction de PII obrigatória no collector.
- Q: Como tratar concorrência de execuções do `seed_data` por tenant/ambiente? → A: Serializar por tenant/ambiente com lock/lease curto (ex.: advisory lock Postgres + TTL), enfileirando/rejeitando uma segunda execução até liberação do lock.
- Q: Como parametrizar e versionar volumetria (Q11) por ambiente/tenant? → A: Manifesto versionado (YAML/JSON) por ambiente/tenant com volumetria/caps por entidade, consumido por `seed_data --profile=<manifest>` e validado em CI/Argo.
- Q: Qual política de limpeza/expurgo dos datasets de carga/DR? → A: Limpeza automática pós-carga/DR guiada por TTL definido no manifesto versionado por ambiente/tenant, executada por job/cron e validada em CI/Argo.
- Q: Qual política de execução/controle de acesso do `seed_data`/factories em ambientes? → A: Execução normal apenas via pipelines CI/CD/Argo com service account de menor privilégio e trilha WORM; execuções manuais restritas a dev isolado ou fluxo de breakglass aprovado/auditado; bloquear execuções locais fora de dev.
- Q: Qual comportamento quando Vault/salt de anonimização estiver indisponível ou falhar leitura? → A: Operar fail-closed: abortar antes de qualquer escrita, registrar auditoria/alerta, sem usar salt cacheado ou efêmero; exceção apenas para dev isolado explicitamente sinalizado.
- Q: Fonte de dados para carga/DR? → A: Apenas dados sintéticos gerados por factories/seeds em todos os ambientes; vedado snapshot de produção mesmo mascarado.
- Q: Modelo de catálogos referenciais nas seeds/factories (categorias, fornecedores, tipos de conta, limites)? → A: Catálogo materializado por tenant (clonado/seedado por tenant/ambiente), sem catálogo global compartilhado.
- Q: Determinismo das seeds/factories (IDs e valores)? → A: Determinismo total por tenant/ambiente/manifesto; mesma entrada produz os mesmos IDs/valores em todas as execuções (CI/Argo/dev isolado).
- Q: Estratégia para datasets de DR/carga (regenerar determinístico vs dump WORM vs réplica read-only)? → A: Regerar on-demand via `seed_data` determinístico consumindo manifestos; não manter dumps/export estáticos; DR operacional usa replicação/PITR + IaC do blueprint e o `seed_data` recompõe apenas os datasets sintéticos.
- Q: Qual comportamento padrão do `seed_data --dry-run`? → A: Executar fluxo completo (factories, checagens de PII/contratos, rate limit) dentro de transação/snapshot com rollback no fim; telemetria/logs marcados como dry-run, sem alterar checkpoints nem publicar evidências WORM.
- Q: Política de reexecução dos datasets de carga/DR já existentes? → A: Reexecutar limpando o dataset existente do modo (carga/DR) e recriar tudo de forma determinística antes de validar/checkpoints, evitando inflação de volumetria e facilitando rollback/DR.

### Session 2025-11-24
- Q: Onde versionar os manifestos de volumetria/seed (YAML/JSON) por ambiente/tenant? → A: No repositório de aplicação, em paths estáveis (ex.: `configs/seed_profiles/<ambiente>/<tenant>.yaml`), revisados via PR e consumidos por CI/Argo.
- Q: Qual esquema mínimo devemos padronizar nos manifestos `configs/seed_profiles/<ambiente>/<tenant>.yaml`? → A: Incluir `metadata` (ambiente, tenant, versão/perfil), `mode` (baseline/carga/DR), `volumetry` por entidade com caps, `rate_limit` alvo/cap com `backoff`, `ttl` por modo, `budget` de custo máximo e `window` off-peak, versionados e auditáveis via GitOps.

### Session 2025-11-26
- Q: Comportamento em falha na verificação pós-deploy das seeds/factories via Argo CD? → A: Fail-closed com rollback automático via Argo CD para o commit anterior e bloqueio de promoção até a verificação passar, registrando auditoria.
- Q: Onde e como auditar relatórios/logs de execução do `seed_data`/factories? → A: Em armazenamento WORM (ex.: bucket S3 Object Lock) com hash/assinatura e retenção governada, indexando metadados no Postgres para consulta/trilha; OTEL/Sentry complementam mas não substituem a cópia imutável.
- Q: Comportamento quando o armazenamento WORM estiver indisponível ou falhar gravação? → A: Fail-closed: abortar antes de qualquer escrita de dados, registrar alerta/auditoria e não prosseguir sem a evidência imutável.

### Session 2025-11-28
- Q: Estratégia de orquestração/concorrência do `seed_data`/factories (Celery vs processo único vs threads locais vs jobs no DB)? → A: Orquestrar via Celery/Redis com filas por tenant/mode e limites de concorrência/rate limit/backoff centralizados, usando checkpoints/idempotência e `acks_late`/retries para não saturar DB/API; sem processos locais ad hoc.

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
- Reexecuções de modos de carga/DR devem limpar o dataset vigente daquele modo antes de recriar de forma determinística, evitando inflação de volumetria e mantendo checkpoints/coerência para rollback.  
- Gatilhos de rate limit em `/api/v1` durante geracao de carga precisam de backoff e orcamento de requisicoes por tenant/ambiente.  
- Seeds/factories nao podem bypassar regras de mascaramento/anonimizacao de PII mesmo em ambientes internos.  
- Falhas em integracoes (banco, fila, cache) devem abortar apenas o lote atual e retomar do checkpoint idempotente, marcando estado inconsistente e acionando retry seguro sem refazer lotes já validados.
- Execuções concorrentes do `seed_data` para o mesmo tenant/ambiente devem ser bloqueadas/serializadas via lock/lease (advisory lock + TTL), com fila curta ou rejeição explícita e log/auditoria da tentativa.
- Manifestos de volumetria (Q11) por ambiente/tenant são obrigatórios; execuções sem perfil versionado ou fora do cap definido devem falhar com auditoria e sugerir correção no manifesto.
- Datasets de carga/DR vencidos pelo TTL do manifesto devem ser expurgados automaticamente (job/cron); se a limpeza não rodar ou falhar, o `seed_data` deve bloquear novas execuções e registrar auditoria.
- Indisponibilidade do Vault/salt de anonimização deve abortar a execução antes de escrever dados, gerar alerta/auditoria e proibir fallback de salt cacheado ou efêmero (exceto dev isolado sinalizado).
- Datasets de carga/DR DEVEM ser apenas sintéticos; uso de snapshots de produção (mesmo mascarados) é proibido.
- Armazenamento ou uso de dumps/exports de datasets sintéticos é proibido; toda execução de DR/carga deve regenerar via `seed_data --profile` determinístico, falhando e auditando se um dump for detectado.
- Catálogos referenciais devem ser materializados por tenant/ambiente; não há catálogo global compartilhado.
- Execuções não determinísticas (IDs/valores variando para mesma entrada tenant/ambiente/manifesto) devem ser bloqueadas; variação deve falhar com auditoria para evitar flakiness.
- Indisponibilidade do Celery/Redis deve acionar retries curtos; se persistir, a execução deve abortar fail-closed com auditoria/alerta, sem fallback local ou fora do orquestrador (exceto dev isolado sinalizado).

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
- **FR-003**: Todo dado PII em seeds/factories DEVE ser anonimisado ou mascarado de forma deterministica por ambiente (hash + salt) conforme catalogo de sensibilidade antes de gravacao ou uso em APIs de teste.  
- **FR-004**: Validacao automatizada DEVE bloquear seeds que nao atendam contratos de API `/api/v1`, integridade referencial ou regras multi-tenant.  
- **FR-005**: Pipeline de CI/CD DEVE executar `seed_data` e factories em modo dry-run e gerar relatorio de conformidade (PII, contratos, volumetria, idempotencia).  
- **FR-006**: Deploys via Argo CD DEVEM acionar verificacao pos-deploy das seeds/factories e publicar resultado em canal de auditoria; falhas devem operar em modo fail-closed, acionando rollback automático para o commit anterior e bloqueando promoção até a verificação passar.  
- **FR-007**: Procedimentos de DR DEVEM conseguir restaurar ambiente alvo usando seeds/factories, mantendo mascaramento e respeitando RTO/RPO definidos no blueprint.  
- **FR-008**: Geração de datasets sinteticos para teste de carga DEVE respeitar limites de requisicoes por tempo, com configuracao de rate limit por tenant/ambiente e relatorio de uso.
- **FR-009**: Seeds/factories DEVEM executar via comando `seed_data` usando ORM/BD e factory-boy; uso de APIs `/api/v1` fica restrito a smokes de contrato/rate limit, sem inserção massiva.
- **FR-010**: Baseline e factories DEVEM cobrir apenas o núcleo bancário (tenants/usuários, clientes/endereços, consultores, contas bancárias/categorias/fornecedores, empréstimos/parcelas, transações financeiras e limites/contratos); domínios acessórios permanecem fora do escopo inicial.
- **FR-011**: Execução de `seed_data` DEVE ocorrer em lotes por entidade/segmento com checkpoints idempotentes, permitindo reexecutar apenas o lote falho (sem transações globais longas) e preservando integridade multi-tenant, idempotência e janelas de SLO/rate limit.
- **FR-012**: Estado de checkpoint/idempotência do `seed_data` DEVE ser persistido em tabela dedicada no PostgreSQL do app, segregada por ambiente/tenant e protegida por RLS, armazenando checkpoints de lote, hashes e deduplicação/TTL para reexecuções seguras.
- **FR-013**: Seeds/factories DEVEM gerar IDs determinísticos (UUIDv5 ou hash) namespaced por tenant+entidade/slug lógico, persistindo a chave para dedupe/TTL e bloqueando divergências; é proibido usar PII como material de geração ou log.
- **FR-014**: Execuções do `seed_data` DEVEM ser serializadas por tenant/ambiente via lock/lease curto (ex.: advisory lock Postgres com TTL), enfileirando ou rejeitando novas chamadas enquanto houver execução ativa para evitar corridas e duplicidades.
- **FR-015**: Parametrização de volumetria (Q11) DEVE ser feita via manifesto versionado (YAML/JSON) por ambiente/tenant com caps por entidade; os manifestos DEVEM residir no repositório de aplicação em paths estáveis (ex.: `configs/seed_profiles/<ambiente>/<tenant>.yaml`), revisados via PR e consumidos por CI/Argo; `seed_data --profile=<manifest>` é obrigatório e validado em CI/Argo para reprodutibilidade e auditoria. Cada manifesto DEVE conter `metadata` (ambiente, tenant, versão/perfil), `mode` (baseline/carga/DR), `volumetry` por entidade com caps, `rate_limit` alvo/cap com `backoff`, `ttl` por modo, `budget` máximo e `window` off-peak para execução segura/finops.
- **FR-016**: Limpeza/expurgo de datasets de carga/DR DEVE ocorrer automaticamente por ambiente/tenant seguindo o TTL definido no manifesto versionado, orquestrado por job/cron e validado em CI/Argo; execuções fora da janela/TTL devem falhar com auditoria.
- **FR-017**: Execução regular do `seed_data`/factories DEVE ocorrer apenas via pipelines CI/CD/Argo com service account de menor privilégio e trilha WORM; execuções manuais ficam restritas a dev isolado ou fluxo de breakglass aprovado/auditado, vedando execuções locais fora de dev.
- **FR-018**: Se o Vault (salt/chaves de anonimização) estiver indisponível ou a leitura falhar, o `seed_data` DEVE abortar antes de qualquer escrita, registrar auditoria/alerta e não usar salt cacheado ou efêmero; apenas dev isolado explicitamente sinalizado pode ter exceção controlada.
- **FR-019**: Datasets de carga e DR DEVEM ser gerados exclusivamente com dados sintéticos via factories/seeds em todos os ambientes; é vedado usar snapshots de produção mesmo mascarados. Não manter dumps/export estáticos: execuções de DR/carga devem regenerar os dados on-demand via `seed_data --profile=<manifest>` determinístico, alinhado à replicação/PITR + IaC do blueprint para o dado operacional.
- **FR-020**: Catálogos referenciais (categorias, fornecedores, tipos de conta, limites padrão etc.) DEVEM ser materializados por tenant/ambiente via seeds/factories; é proibido catálogo global compartilhado entre tenants.
- **FR-021**: Seeds/factories DEVEM ser determinísticas por tenant/ambiente/manifesto, gerando os mesmos IDs e valores a cada execução (CI/Argo/dev isolado) para garantir idempotência, auditoria e ausência de flakiness.
- **FR-022**: Relatórios e logs de execução do `seed_data`/factories DEVEM ser armazenados em repositório WORM (ex.: bucket S3 com Object Lock) com hash/assinatura e retenção governada; metadados indexados no Postgres para consulta/auditoria. Logs/OTEL/Sentry são complementares, não substitutos da cópia imutável.
- **FR-023**: Se o repositório WORM estiver indisponível ou falhar na gravação, a execução do `seed_data`/factories DEVE operar fail-closed: abortar antes de qualquer escrita de dados, registrar alerta/auditoria e só prosseguir quando a evidência imutável for gravada com sucesso.
- **FR-024**: Rotação de sal/segredo de anonimização DEVE ser versionada por ambiente/tenant no Vault; `seed_data` compara `salt_version` do manifesto/checkpoint com a versão ativa, falha (fail-closed) se houver divergência e exige limpeza/reseed coordenada ou expurgo conforme TTL antes de aceitar a nova versão; exceções apenas para dev isolado sinalizado.
- **FR-025**: Orquestração do `seed_data`/factories DEVE usar Celery/Redis com filas por tenant/mode e limites de concorrência/rate limit/backoff centralizados; tarefas executam em lotes com checkpoints/idempotência, `acks_late` e retries, evitando saturar DB/API e alinhando-se aos SLOs e gates de CI/Argo.
- **FR-026**: O modo `seed_data --dry-run` DEVE executar o fluxo completo (factories, checagens de PII/contratos, rate limit/backoff) em transação/snapshot com rollback no final, marcando telemetria/logs como dry-run, sem atualizar checkpoints/idempotência nem publicar evidências WORM; medir SLOs e falhar se qualquer gate bloquear.
- **FR-027**: Se o broker Celery/Redis estiver indisponível, o `seed_data`/factories DEVE aplicar poucas tentativas com backoff curto (`acks_late` ativos) e, persistindo a falha, abortar em modo fail-closed com alerta/auditoria, sem fallback para execução local ou fora do orquestrador (exceto dev isolado sinalizado).
- **FR-028**: Reexecuções do `seed_data` em modos de carga ou DR DEVEM apagar o dataset existente daquele modo antes de recriar tudo de forma determinística, preservando idempotência, caps de volumetria e facilitando rollback/DR sem inflação de dados.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Execucoes de `seed_data` devem completar dentro de janelas definidas por ambiente (dev <5 min, homolog <10 min, producao controlada <20 min); exceder +20% aciona abort/rollback auditado.  
- **NFR-002 (Performance)**: Testes de carga com datasets sinteticos nao devem acionar mais de 80% do limite configurado de requisicoes por minuto; variacao de tempo de resposta deve permanecer dentro do orcamento de SLO do blueprint.  
- **NFR-003 (Observabilidade)**: Seeds/factories e cargas devem emitir logs JSON via `structlog`, métricas via `django-prometheus` e traces OpenTelemetry exportados ao collector central, propagando `traceparent`/`tracestate` e labels de tenant/ambiente/execução; Sentry gera alertas e o collector aplica redaction de PII; pipelines (CI/Argo) validam exportação/correlação e bloqueiam em caso de falha.  
- **NFR-004 (Seguranca)**: Dados sensiveis devem permanecer mascarados em logs, dumps e exportacoes; acesso a configuracoes de seeds/factories deve seguir principio do menor privilegio.  
- **NFR-005 (FinOps)**: Volume de dados gerados e custo estimado por execucao deve ser registrado; execucoes de carga devem respeitar budgets definidos por ambiente/tenant.

### Dados Sensiveis & Compliance

- Catalogo PII deve mapear campos sensiveis usados em seeds/factories (ex.: documentos, email, telefone, endereco) e aplicar mascaramento/anonimizacao deterministica por ambiente (hash + salt) antes de persistir para manter integridade referencial e idempotencia.  
- Salts/segredos de anonimização devem residir no HashiCorp Vault (Transit ou KV com envelope via KMS), com políticas e chaves segregadas por ambiente/tenant, rotação automática no pipeline `ci-vault-rotate` e acesso apenas via tokens efêmeros; é proibido persistir esses valores em código, configs ou variáveis estáticas.  
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
