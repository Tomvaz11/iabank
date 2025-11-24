# Clarifications Archive — seeds/factories (versão pré-refatoração)

> Fonte: versão anterior do `spec.md` antes da refatoração para aderir ao `/speckit.specify`. Conteúdo mantido para consulta no `/speckit.plan` e implementação. Estrutura preservada por sessões originais.

## Session 2025-11-23 (1)
- Q: Qual TTL do lock/lease por tenant/ambiente (advisory lock Postgres) para serializar execuções do `seed_data`? → A: TTL de 60s (fail-closed); expira o lock e reencaminha a tentativa para a fila curta, evitando starvation e filas longas.
- Q: Qual combinação de teto global e TTL da fila para controlar concorrência do `seed_data`/factories por ambiente/cluster? → A: Limitar a 2 execuções concorrentes por ambiente/cluster com TTL de fila de 5 minutos (fail-closed), expirando tentativas acima do teto.
- Q: Qual cadência e política de rotação das chaves/salts de FPE no Vault por ambiente/tenant? → A: Rotação automática trimestral (ou imediata em incidente) por ambiente/tenant no Vault/KMS; `seed_data` valida `salt/key version` e falha em modo fail-closed se divergir, exigindo reseed coordenado; sem dual-decrypt fora de dev isolado.
- Q: Qual fallback usar em dev isolado se o Vault/FPE estiver indisponível? → A: Fallback determinístico local apenas em dev isolado, com chave/salt dev-only em `.env.local` não versionado, preservando formato via FPE; CI/staging/prod falham se fallback estiver ativo ou se o Vault não estiver disponível.
- Q: Onde aplicar a FPE/máscara determinística de PII nas seeds/factories? → A: Centralizar a FPE (FF3-1/FF1) no Vault Transit com chaves segregadas por ambiente/tenant; seeds/factories chamam o Vault para gerar valores preservando formato. Campos PII permanecem criptografados em repouso via pgcrypto no Postgres, sem chaves na aplicação.

## Session 2025-11-23 (2)
- Q: Seeds/factories devem incluir sad paths no baseline ou separá-los por modo? → A: Baseline fica só com caminhos felizes/determinísticos por tenant; sad paths entram apenas nos modos carga/DR com percentuais/estados configurados por entidade/tenant no manifesto (`seed_data --profile`) e auditáveis.
- Q: Baseline deve incluir estados bloqueado/inadimplente/cancelado ou só ativos? → A: Baseline fica apenas com estados “happy”/ativos; estados bloqueado/inadimplente/cancelado entram só nos modos carga/DR com percentuais por entidade/tenant definidos no manifesto.
- Q: Qual escopo de execução do `seed_data` em CI/PR vs cargas/DR completas? → A: CI/PR roda apenas dry-run do baseline determinístico (`seed_data --profile`), validando PII/contratos/idempotência; cargas/DR completas rodam em staging dedicado, agendadas em janela off-peak com manifestos versionados, caps de volumetria/budget e evidência WORM.
- Q: O que fazer quando o manifesto não cobre campos/versão nova exigida pelo schema/código? → A: Validar manifesto contra schema/versão em runtime/CI e falhar em modo fail-closed se houver campo obrigatório novo ou versão divergente; exigir atualização do manifesto/checkpoint antes de executar, sem auto-preencher ou seguir só com warning.
- Q: Comportamento do `seed_data`/factories quando Celery/Redis estiverem indisponíveis? → A: Repetir poucas vezes com backoff curto e `acks_late`; se o broker permanecer indisponível, abortar fail-closed com alerta/auditoria, sem fallback local ou fora do orquestrador (exceto dev isolado).

## Session 2025-11-23 (3)
- Q: Abordagem de execução das seeds/factories (APIs `/api/v1`, ORM/BD direto ou híbrido)? → A: Usar comando `seed_data` via ORM/BD com factory-boy como caminho principal; APIs `/api/v1` apenas para smokes/validação de contrato e rate limit, sem inserção massiva.
- Q: Abordagem para mascaramento/anonimização de PII nas seeds/factories? → A: Mascaramento/anonimização determinístico por ambiente (hash + salt) garantindo consistência entre execuções, DR e integrações multi-tenant.
- Q: Escopo mínimo obrigatório das seeds/factories? → A: Núcleo bancário: tenants/usuários, clientes/endereços, consultores, contas bancárias/categorias/fornecedores, empréstimos/parcelas, transações financeiras e limites/contratos; demais domínios ficam fora do baseline.
- Q: Onde armazenar e rotacionar sal/segredo para anonimização determinística de PII? → A: Em HashiCorp Vault (Transit ou KV com envelope via KMS), com políticas e chaves por ambiente/tenant, rotação automática e acesso só via tokens efêmeros; é proibido guardar em código/vars estáticas.
- Q: Como versionar/rotacionar o sal de anonimização determinística das seeds/factories? → A: Sal versionado por ambiente/tenant; rotação publica novo `salt_version` no Vault, `seed_data` valida versão em manifesto/checkpoint e falha (fail-closed) se divergente até limpeza/reseed coordenada; breakglass só em dev isolado.

## Session 2025-11-23 (4)
- Q: Estratégia de consistência/rollback das seeds/factories em caso de falha? (transação única vs lotes com checkpoints vs duas fases) → A: Processar em lotes por entidade/segmento com checkpoints idempotentes, reexecutando apenas o lote falho; evitar transações monolíticas longas e manter integridade multi-tenant, rate limits e SLOs.
- Q: Onde persistir o estado de checkpoint/idempotência das execuções do `seed_data`? → A: Em tabela dedicada no PostgreSQL do app, segregada por ambiente/tenant com RLS, registrando checkpoints de lote, hashes e deduplicação/TTL para retomadas seguras.
- Q: Como garantir identificadores/idempotência determinística nas seeds/factories sem expor PII? → A: Usar UUIDv5/hash determinístico namespaced por tenant+entidade (ou slug lógico) e persistir a chave para dedupe/TTL; proibir uso de PII como material de chave.
- Q: Estratégia de observabilidade/telemetria para execuções do `seed_data`/factories e cargas? → A: Instrumentar com OpenTelemetry (traces/métricas/logs JSON `structlog`), `django-prometheus` e Sentry; exportar para o collector central com correlação `traceparent`/`tracestate` e labels de tenant/ambiente/execução, validando em CI/Argo; redaction de PII obrigatória no collector.
- Q: Como tratar concorrência de execuções do `seed_data` por tenant/ambiente? → A: Serializar por tenant/ambiente com lock/lease curto (advisory lock Postgres + TTL de 60s), enfileirando/rejeitando uma segunda execução até liberação do lock.

## Session 2025-11-23 (5)
- Q: Como parametrizar e versionar volumetria (Q11) por ambiente/tenant? → A: Manifesto versionado (YAML/JSON) por ambiente/tenant com volumetria/caps por entidade, consumido por `seed_data --profile=<manifest>` e validado em CI/Argo.
- Q: Qual política de limpeza/expurgo dos datasets de carga/DR? → A: Limpeza automática pós-carga/DR guiada por TTL definido no manifesto versionado por ambiente/tenant, executada por job/cron e validada em CI/Argo.
- Q: Qual política de execução/controle de acesso do `seed_data`/factories em ambientes? → A: Execução normal apenas via pipelines CI/CD/Argo com service account de menor privilégio e trilha WORM; execuções manuais restritas a dev isolado ou fluxo de breakglass aprovado/auditado; bloquear execuções locais fora de dev.
- Q: `seed_data`/factories podem rodar sem RLS ou usando superuser para acelerar? → A: Não; `seed_data`/factories devem rodar sempre com RLS habilitado, via service account de menor privilégio segregada por tenant/ambiente, sem bypass/superuser, com auditoria e validação de RLS no CI.
- Q: Como configurar timeouts (statement/lock) para baseline vs modos de carga/DR? → A: Definir timeouts por modo: baseline com limites estritos (ex.: `statement_timeout` ~30s e `lock_timeout` ~5s) por lote; cargas/DR com teto maior porém finito (ex.: 60–90s e 10–15s) observados por lote, configuráveis via manifesto/infra e auditados para proteger SLO/FinOps.

## Session 2025-11-23 (6)
- Q: Qual comportamento quando Vault/salt de anonimização estiver indisponível ou falhar leitura? → A: Operar fail-closed: abortar antes de qualquer escrita, registrar auditoria/alerta, sem usar salt cacheado ou efêmero; exceção apenas para dev isolado explicitamente sinalizado.
- Q: Fonte de dados para carga/DR? → A: Apenas dados sintéticos gerados por factories/seeds em todos os ambientes; vedado snapshot de produção mesmo mascarado.
- Q: Modelo de catálogos referenciais nas seeds/factories (categorias, fornecedores, tipos de conta, limites)? → A: Catálogo materializado por tenant (clonado/seedado por tenant/ambiente), sem catálogo global compartilhado.
- Q: Determinismo das seeds/factories (IDs e valores)? → A: Determinismo total por tenant/ambiente/manifesto; mesma entrada produz os mesmos IDs/valores em todas as execuções (CI/Argo/dev isolado).
- Q: Estratégia para datasets de DR/carga (regenerar determinístico vs dump WORM vs réplica read-only)? → A: Regerar on-demand via `seed_data` determinístico consumindo manifestos; não manter dumps/export estáticos; DR operacional usa replicação/PITR + IaC do blueprint e o `seed_data` recompõe apenas os datasets sintéticos.

## Session 2025-11-23 (7)
- Q: Qual comportamento padrão do `seed_data --dry-run`? → A: Executar fluxo completo (factories, checagens de PII/contratos, rate limit) dentro de transação/snapshot com rollback no fim; telemetria/logs marcados como dry-run, sem alterar checkpoints nem publicar evidências WORM.
- Q: Política de reexecução dos datasets de carga/DR já existentes? → A: Reexecutar limpando o dataset existente do modo (carga/DR) e recriar tudo de forma determinística antes de validar/checkpoints, evitando inflação de volumetria e facilitando rollback/DR.
- Q: Estratégia de paralelismo dos lotes do `seed_data`/factories por modo? → A: Baseline executa sequencialmente; modos de carga/DR podem paralelizar por entidade com limite curto (2–4 workers Celery) sob rate limit/backoff centralizado e janelas/SLO, mantendo checkpoints/idempotência.
- Q: Comportamento quando a estimativa ou custo real da execução ultrapassar o budget do manifesto? → A: Fail-closed: abortar/rollback imediato ao estimar ou atingir gasto > budget; exigir ajuste do manifesto antes de prosseguir; sem breakglass.
- Q: Qual retenção dos relatórios/logs WORM do `seed_data`/factories? → A: Retenção mínima de 1 ano (prod/homolog), alinhada ao blueprint (backups mensais retidos por 1 ano) e Art. XVI; governança e integridade via política WORM.

## Session 2025-11-23 (8)
- Q: Como tratar integrações externas (KYC, antifraude, pagamentos, notificações) nas execuções de seeds/carga/DR? → A: Simular via mocks/stubs com testes de contrato (Pact), sem chamadas reais; manter determinismo, evitar custos/latência e side effects; backoff/retries só nos mocks, preservando rate limits e PII mascarada.
- Q: Comportamento do `seed_data` ao encontrar dados pré-existentes ou drift fora do manifesto? → A: Fail-closed: bloquear execução ao detectar drift/dados fora do manifesto, registrar auditoria e exigir limpeza/reseed controlado antes de prosseguir (sem mescla automática nem drop silencioso).
- Q: O que fazer se os checkpoints/hashes de idempotência divergirem ou estiverem inconsistentes? → A: Fail-closed: bloquear execução, registrar auditoria e exigir saneamento/reseed coordenado antes de retomar; sem auto-merge, reset silencioso ou avanço parcial.
- Q: Como tratar 429/rate limit excedido durante o `seed_data`/factories? → A: Aplicar backoff+jitter com orçamento curto; se 429 persistir ou o cap do manifesto for excedido, abortar fail-closed com auditoria e reagendar na janela/off-peak definida.
- Q: Em que janela executar o `seed_data`/factories e como lidar com concorrência de mutações? → A: Executar apenas na janela off-peak declarada no manifesto; colocar tenant em maintenance/bloqueio de mutações concorrentes e abortar fail-closed se a janela não estiver ativa.

## Session 2025-11-23 (9)
- Q: Formato e armazenamento das evidências/logs do `seed_data`/factories? → A: Relatórios JSON assinados (hash), com trace/span IDs, manifesto/tenant/ambiente, custos/volumetria e status por lote; armazenar em WORM (ex.: S3 Object Lock) e indexar metadados no Postgres para consulta/auditoria.
- Q: Quais metas de RPO/RTO para regenerar datasets sintéticos via `seed_data`/DR? → A: RPO ≤ 5 minutos e RTO ≤ 60 minutos, alinhados ao blueprint 6.1/27.
- Q: Com que frequência validar/restaurar seeds/datasets sintéticos para DR/carga? → A: Trimestral com evidência WORM, alinhado aos testes de restauração do blueprint 6.1.
- Q: Em que ambiente executar os ensaios de restauração de DR/carga? → A: Staging dedicado de carga/DR, isolado de prod/dev, para validar throughput, janelas e evidências WORM sem risco ao tráfego real.
- Q: Qual orquestrador usar para expurgo/TTL automático dos datasets de carga/DR? → A: Preferencialmente Argo CronJob GitOps por ambiente/tenant; se faseado como melhoria pós-go-live, manter job/cron validado em CI/Argo até migrar.

## Session 2025-11-23 (10)
- Q: Cobertura de estados nas seeds/factories (apenas feliz vs principais estados)? → A: Baseline fica só com estados ativos/happy; estados bloqueado/inadimplente/cancelado entram apenas nos perfis de carga/DR com percentuais por entidade/tenant definidos no manifesto, evitando inflar volumetria fora do perfil.
- Q: Como alinhar definitivamente a cobertura de estados entre baseline e modos carga/DR? → A: Baseline mantém apenas caminhos felizes/ativos; estados bloqueado/inadimplente/cancelado permanecem restritos aos modos carga/DR com percentuais versionados no manifesto por entidade/tenant.
- Q: Como calcular CET/IOF/parcelas nas seeds/factories? → A: Usar os serviços/domínio oficiais de cálculo (mesmos do produto) para CET/IOF e geração de parcelas, evitando valores fictícios e garantindo aderência regulatória nos datasets.
- Q: Como validar CET/IOF/parcelas gerados pelas seeds/factories? → A: Validar por igualdade determinística (arredondada a centavos) contra a rotina oficial do domínio e falhar imediatamente se houver divergência; sem tolerância percentual ou ranges amplos.
- Q: Como definir datas (contrato, vencimentos, TTL) nas seeds/factories? → A: Fixar `reference_datetime` em UTC por manifesto/tenant (clock freeze) e derivar todas as datas a partir dessa âncora, garantindo determinismo e consistência nos cálculos financeiros e SLAs.

## Session 2025-11-23 (11)
- Q: Qual formato e armazenamento do `reference_datetime` nos manifestos? → A: Campo obrigatório em ISO 8601 UTC (ex.: `2025-01-01T00:00:00Z`) dentro do manifesto por tenant/mode; todas as datas derivam diretamente dele sem conversões locais ou uso de `now()`.
- Q: Em que ordem executar `seed_data` versus migrations de banco? → A: Aplicar todas as migrations primeiro; `seed_data` deve falhar (fail-closed) se houver migrations pendentes ou drift de schema em relação ao manifesto/checkpoint.
- Q: Como o `seed_data` deve operar durante fases de expand/backfill (parallel change)? → A: Manter dual-write/dual-read validando colunas/estruturas antiga e nova durante expand/backfill; falhar (fail-closed) se houver divergência e só encerrar o dual-read após o contract finalizar.
- Q: Como o `seed_data` deve se comportar diante de feature flags/canaries desativados ou ausentes? → A: Respeitar flags/canaries e operar fail-closed quando o flag da entidade/domínio estiver off ou ausente no manifesto/ambiente; só executar quando o flag estiver explicitamente ativo.
- Q: Como o `seed_data` deve tratar o escopo canary? → A: Exigir que o manifesto declare explicitamente o escopo canary (percentual ou tenants-alvo) e falhar em fail-closed se o escopo não estiver definido ao rodar nesse modo.

## Session 2025-11-23 (12)
- Q: Como garantir que o `seed_data` não bypassará RLS multi-tenant? → A: Rodar preflight de RLS/tenant (policies ativas e service account sob RLS) e falhar em fail-closed antes de qualquer escrita se RLS estiver ausente/desabilitado.
- Q: Qual escopo de tenants para o dry-run do baseline em CI/PR? → A: Executar o dry-run do baseline apenas para um tenant canônico por ambiente (ou lista curta declarada no manifesto) para manter determinismo, RLS/PII e SLO/FinOps do pipeline, sem inflar custo/tempo.

## Session 2025-11-23 (13)
- Q: Onde versionar os manifestos de volumetria/seed (YAML/JSON) por ambiente/tenant? → A: No repositório de aplicação, em paths estáveis (ex.: `configs/seed_profiles/<ambiente>/<tenant>.yaml`), revisados via PR e consumidos por CI/Argo.
- Q: Qual esquema mínimo devemos padronizar nos manifestos `configs/seed_profiles/<ambiente>/<tenant>.yaml`? → A: Incluir `metadata` (ambiente, tenant, versão/perfil), `mode` (baseline/carga/DR), `volumetry` por entidade com caps, `rate_limit` alvo/cap com `backoff`, `ttl` por modo, `budget` de custo máximo e `window` off-peak, versionados e auditáveis via GitOps.

## Session 2025-11-23 (14)
- Q: Comportamento em falha na verificação pós-deploy das seeds/factories via Argo CD? → A: Fail-closed com rollback automático via Argo CD para o commit anterior e bloqueio de promoção até a verificação passar, registrando auditoria.
- Q: Onde e como auditar relatórios/logs de execução do `seed_data`/factories? → A: Em armazenamento WORM (ex.: bucket S3 Object Lock) com hash/assinatura e retenção governada, indexando metadados no Postgres para consulta/trilha; OTEL/Sentry complementam mas não substituem a cópia imutável.
- Q: Comportamento quando o armazenamento WORM estiver indisponível ou falhar gravação? → A: Fail-closed: abortar antes de qualquer escrita de dados, registrar alerta/auditoria e não prosseguir sem a evidência imutável.

## Session 2025-11-23 (15)
- Q: Estratégia de orquestração/concorrência do `seed_data`/factories (Celery vs processo único vs threads locais vs jobs no DB)? → A: Orquestrar via Celery/Redis com filas por tenant/mode e limites de concorrência/rate limit/backoff centralizados, usando checkpoints/idempotência e `acks_late`/retries para não saturar DB/API; sem processos locais ad hoc.

## Session 2025-11-23 (16)
- Q: Qual teto global de execuções concorrentes do `seed_data`/factories por ambiente/cluster? → A: Limitar a 2 execuções concorrentes por ambiente/cluster com lease global e fila; bloquear acima do teto para proteger SLO/FinOps e evitar saturar DB/Redis/API, mantendo serialização por tenant.
- Q: O que fazer com execuções acima do teto global enquanto aguardam vaga? → A: Enfileirar com TTL curto (5 min) sob lease global; expirar em fail-closed com auditoria se não iniciar, evitando fila longa e saturação de recursos/FinOps.
- Q: Onde implementar o lock/lease global e a fila/TTL para controlar concorrência do `seed_data`/factories? → A: No PostgreSQL, usando advisory lock para o lease global e tabela de fila/TTL auditável, mantendo consistência transacional, RLS/auditoria e evitando dependência extra além de Redis/Celery.
- Q: Como aplicar FinOps na execução do `seed_data`/factories (alerta/abort por budget)? → A: Combinar estimativa prévia pelo manifesto com medição em tempo real; alertar em 80% do budget e abortar/rollback em 100% (fail-closed), registrando auditoria e exigindo ajuste do manifesto.
- Q: Como bloquear mutações concorrentes durante a janela do `seed_data`/factories por tenant? → A: Flag de manutenção por tenant no PostgreSQL (coluna/status + policy/RLS) com middleware/API gate bloqueando writes enquanto ativo; fail-closed se desrespeitado.

## Session 2025-11-23 (17)
- Q: Como declarar e aplicar a janela off-peak (`window`) no manifesto sem ambiguidade de fuso? → A: Declarar `window.start_utc`/`window.end_utc` em HH:MM UTC por tenant/ambiente; tratar `end < start` como janela que cruza meia-noite; gating e auditoria operam apenas em UTC, sem conversões locais.
- Q: Quantas janelas off-peak podem ser declaradas por tenant/ambiente? → A: Apenas uma janela diária por tenant/ambiente (par único `start_utc`/`end_utc` em UTC, podendo cruzar meia-noite), aplicada em gating/auditoria sem listas ou cron múltiplos para preservar determinismo.
- Q: O que fazer se o `reference_datetime` do manifesto mudar? → A: Tratar como breaking change: abortar em fail-closed, exigir limpeza/reseed coordenado por tenant/ambiente e atualização de manifestos/checkpoints antes de aceitar o novo valor, evitando drift em datas/cálculos financeiros.
- Q: Qual TTL/retencao aplicar aos checkpoints de idempotência antes de limpar? → A: Manter até o próximo reseed bem-sucedido do mesmo tenant/mode, limitado a no máximo 30 dias; limpar na virada do reseed para evitar acúmulo/custo e preservar retomada/DR auditável.

## Session 2025-11-23 (18)
- Q: Anonimização determinística das seeds/factories deve preservar o formato sintático (CPF/CNPJ/telefone/email) ou pode ser hash opaco? → A: Preservar formato com FPE/máscara determinística compatível com regex/contratos `/api/v1`, garantindo consistência, testes e sem exposição de PII real.
- Q: Como tratar emissão de eventos/notificações durante execuções do `seed_data`/factories? → A: Roteamento obrigatório para tópicos/filas/webhooks sandbox isolados com mocks/stubs e auditoria; nunca enviar para destinos reais, mantendo apenas telemetria/contratos exercitados.
- Q: Como tratar outbox/CDC/replicação de eventos gerados pelo `seed_data`/factories? → A: Roteamento obrigatório do outbox/CDC para sink/sandbox isolado com mocks/stubs e auditoria, sem enviar para data lake/analytics reais; manter apenas validação de telemetria/contratos e rate limit.
- Q: Onde validar integridade/idempotência pós-execução do `seed_data`/factories (primário vs réplica)? → A: Validar sempre no primário usando transação/snapshot para evitar falsos negativos por lag, mantendo determinismo, RLS e modo fail-closed.
- Q: Como lidar com caches/índices/busca ao executar `seed_data`/factories? → A: Invalidar/limpar caches (ex.: Redis) e índices/busca em torno da execução, reconstruindo apenas em modos controlados (dry-run/staging/carga/DR) e bloqueando rebuild automático em produção para preservar determinismo/idempotência e evitar poluir tráfego real.

## Session 2025-11-23 (19)
- Q: Qual nível de isolamento transacional para os lotes do `seed_data`/factories? → A: Usar `SERIALIZABLE` por lote com os timeouts curtos já definidos, garantindo determinismo/idempotência e evitando leituras sujas/lag em ambiente multi-tenant sensível.
