# Pesquisa e Decisoes (Fase 0)

Nenhuma pendencia de clarificacao aberta; consolidamos decisoes e melhores praticas para dependencias/integracoes conforme spec e constituicao.

- Decision: `seed_data` sera um management command deterministico que consome manifestos YAML/JSON versionados (mode baseline/carga/DR, caps Q11, rate limit/backoff, reference_datetime UTC, janela off-peak, budgets/error budget).  
  Rationale: Mantem GitOps/Argo CD como fonte da verdade e falha em fail-closed quando schema/versao divergir, reduzindo drift multi-tenant (Art. I, XI, XVIII).  
  Alternatives considered: Flags imperativas por CLI (rejeitado por ser menos auditavel); configs dinâmicas por DB (rejeitado por quebrar GitOps e reproducibilidade).

- Decision: Concurrencia sera serializada por tenant/ambiente via advisory lock Postgres (lease curto), com teto global por ambiente/cluster e fila curta Celery; backoff+jitter em 429/erro transitório, acks tardios e DLQ para replays idempotentes.  
  Rationale: Evita duplicidade/perda (Blueprint §26), protege rate limit e SLO, permite retry seguro com checkpoints.  
  Alternatives considered: Locks Redis ou file-lock (rejeitados por menor acoplamento a RLS e risco de split-brain); retries exponenciais sem jitter (rejeitados por sincronismo e thundering herd).

- Decision: Mascaramento/anonimizacao de PII usara FPE deterministica via Vault Transit por tenant/ambiente/manifesto; PII cifrada em repouso com pgcrypto; catalogo PII explicitado em factories.  
  Rationale: Mantem formato, garante determinismo e reforca defesa em profundidade LGPD (Art. XII, XIII).  
  Alternatives considered: Randomizacao nao deterministica (rejeitada por inviabilizar replays e comparacoes); armazenar keys/salts no app (rejeitado por risco de vazamento).

- Decision: Factories factory-boy gerarão dados 100% sinteticos e deterministas (seed per tenant/ambiente/manifesto) alinhados aos contratos `/api/v1`, reutilizando validadores/serializers; nenhum snapshot de prod permitido.  
  Rationale: Reduz risco de PII real, suporta TDD/integ-primeiro e facilita dry-run CI (Art. III, IV, XI, XIII).  
  Alternatives considered: Fixtures estaticas (rejeitadas por fragilidade e drift de schema); dumps anonimizados (rejeitados por risco residual de reidentificacao).

- Decision: Contratos REST seguirao OpenAPI 3.1 contrato-primeiro com Problem Details, RateLimit-*, Idempotency-Key (TTL/dedupe) e ETag/If-Match; lint/diff Spectral, testes Pact e checagem de compatibilidade SemVer em CI.  
  Rationale: Garante governanca e evita regressao em seeds que chamam `/api/v1` (Art. XI, V).  
  Alternatives considered: Validar apenas via tests e2e (rejeitado por latencia e menor previsibilidade); desabilitar ETag/If-Match (rejeitado por risco de write skew).

- Decision: Execucoes registrarao relatorios JSON assinados (hash/assinatura) com traces/métricas/logs OTEL+Sentry; armazenamento WORM com retencao/governanca; falha se WORM indisponivel.  
  Rationale: Atende Art. VII e XVI, facilita auditoria/FinOps e rollback canary.  
  Alternatives considered: Logs aplicacionais apenas (rejeitados por falta de imutabilidade); WORM opcional (rejeitado por nao cumprir compliance).

- Decision: CI/PR executara dry-run deterministico do baseline (tenant canônico), com checagem PII/RLS/contrato/idempotencia, cobertura≥85%, complexidade≤10, SAST/DAST/SCA/SBOM e k6 perf gate; sem publicar evidencias WORM.  
  Rationale: Detecta regressao cedo e cumpre Art. III/IV/IX/XI sem custos de execucao completa.  
  Alternatives considered: Executar modos carga/DR em PR (rejeitado por custo e risco de quota); pular k6 (rejeitado por violar Art. IX e adicoes blueprint).

- Decision: Restauracao/DR ocorrera apenas em staging e perf dedicados com dados sinteticos, cumprindo RPO≤5 min/RTO≤60 min; manifestos definem checkpoints e limpeza/idempotencia antes de replays.  
  Rationale: Isola risco, permite testes de recuperacao e respeita blueprint/clarifications.  
  Alternatives considered: DR em ambientes compartilhados (rejeitado por risco cross-tenant/impacto SLO); uso de snapshots (rejeitado por LGPD e determinismo).

- Decision: Evolucao de schema relacionada a seeds seguira expand/contract com `CONCURRENTLY` e checkpoints; seeds/factories acompanharão novas colunas via manifestos versionados.  
  Rationale: Minimiza downtime (Art. X) e garante replays seguros.  
  Alternatives considered: Migrations destrutivas diretas (rejeitadas por risco de downtime); congelar schema durante seeds (rejeitado por bloquear entregas).

- Decision: Infra de seeds (Vault, WORM, filas, pipelines) sera gerenciada via Terraform + OPA e promovida por GitOps/Argo CD com flags/canary/rollback e drift detection.  
  Rationale: Cumpre Art. XIV e adicoes blueprint (itens 1/3/8/11), garante auditoria e reversibilidade.  
  Alternatives considered: Provisionamento manual ou scripts ad-hoc (rejeitados por falta de rastreabilidade e conformidade).
