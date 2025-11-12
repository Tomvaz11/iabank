# Runbook — CI Outage (Chromatic/Lighthouse/Axe)

Objetivo: padronizar como detectar, registrar e agir em casos de indisponibilidade (outage) de ferramentas de QA no CI, usando o Worker da Cloudflare + KV.

## Visão geral

- Em PRs/execuções, o job "CI Outage Guard" avalia o estado das ferramentas (Chromatic, Lighthouse, Axe) e toma ações:
  - Branches não‑release: fail‑open (não quebra o PR), registra evento, rotula PR (ci‑outage) e gera artefato/telemetria.
  - Branches release/main: fail‑closed (quebra o pipeline) quando houver outage.
- Eventos são enviados via HTTP para um Worker Cloudflare (binding KV `CI_OUTAGES`) e persistidos como pares chave‑valor.

Política de release branches (padrão do script): `main`, `release/*`, `hotfix/*`.

Componentes relevantes:
- Script: `scripts/ci/handle-outage.ts` (compilado em `scripts/dist/ci/handle-outage.js`).
- Workflow principal: `.github/workflows/frontend-foundation.yml` (job `ci-outage-guard`).
- Selftest manual: `.github/workflows/ci-outage-selftest.yml`.
- Secrets no GitHub: `FOUNDATION_OTEL_OUTAGE_ENDPOINT`, `FOUNDATION_OTEL_OUTAGE_TOKEN`.
- Worker Cloudflare: binding `CI_OUTAGES` (KV Namespace) + secret `CI_OUTAGE_TOKEN`.

Permissões do workflow (GITHUB_TOKEN)
- Para anotar PRs (labels/comentários) quando houver outage, o workflow principal DEVE declarar:
  - `permissions:`
    - `contents: read`
    - `pull-requests: write`
    - `issues: write`
- Evidência (2025‑11‑09): run `Frontend Foundation CI` no PR #90 exibiu no log do job `CI Outage Guard` o bloco “GITHUB_TOKEN Permissions: Contents: read; Issues: write; PullRequests: write”.

## Pré‑requisitos

- Repositório com os secrets configurados (GitHub → Settings → Secrets and variables → Actions):
  - `FOUNDATION_OTEL_OUTAGE_ENDPOINT`: URL pública do Worker (ex.: `https://<worker>.<conta>.workers.dev`).
  - `FOUNDATION_OTEL_OUTAGE_TOKEN`: token secreto que o Worker exige via cabeçalho `X-Token`.
- No Worker (Cloudflare → Workers & Pages → seu Worker → Settings → Variables and bindings):
  - KV namespace binding: `CI_OUTAGES` → aponte para a namespace correta.
  - Secret: `CI_OUTAGE_TOKEN` com o mesmo valor do GitHub.

## Executar o selftest (validação ponta a ponta)

1) Acesse o workflow manual (branch `main`):
   - GitHub Actions → "CI Outage Selftest" → `Run workflow`.
2) O workflow executa dois jobs:
  - `Post OTEL Outage Event (Cloudflare)` (fail‑open): simula falha do Chromatic e envia evento. Para garantir comportamento fail‑open estável em `main`, o step cria um arquivo `artifacts/local/selftest-input.json` e invoca o script com `--input`, forçando a `branch=selftest-failopen`.
  - `Post OTEL Outage Event (Fail‑Closed on main)`: simula falha em `main`; o script sai com código 1, mas o passo ignora o erro (marcado como esperado).
3) Artefatos: baixe `ci-outage-selftest*` e verifique `observabilidade/data/ci-outages.json` se desejar confirmar localmente.

Observações:
- O selftest injeta um log de erro sintético (padrões: `ECONNRESET`, `service unavailable`) para que o script detecte outage mesmo quando a status page não responde em JSON.
- O job fail‑open usa `--input artifacts/local/selftest-input.json` para fixar `branch=selftest-failopen`; o job fail‑closed força `GITHUB_REF_NAME=main`.

## Validar no Cloudflare (KV)

1) Workers & Pages → seu Worker → aba `Bindings`.
2) Clique no link do binding `CI_OUTAGES` (garante a namespace correta).
3) Aba `KV Pairs` → `Connect/Refresh` → devem surgir chaves novas com timestamp do run (valor é o JSON do evento `foundation_ci_outage`).

## Interpretação de resultados

- `fail‑open` (branches não‑release):
  - CI não falha por outage dessas ferramentas.
  - O PR recebe rótulo `ci-outage` e comentário explicativo (quando for evento de PR).
  - Eventos são persistidos (KV) e artefatos gerados.
- `fail‑closed` (main/release/hotfix):
  - CI falha enquanto existir outage.
  - Ação imediata: acompanhar status da ferramenta e reexecutar quando estabilizar; mantenha rastreabilidade no PR.

## Operação (PRs)

- Se um PR estiver em `fail‑open` por outage:
  - Mantenha o rótulo `ci-outage` até a normalização.
  - Evite merge sem revisão consciente do risco (principalmente se o PR impactar diretamente os gates afetados).
  - Quando os jobs passarem verde novamente, remova o rótulo e prossiga.

## Evidências complementares (2025‑11‑09)
- PR #90 aplicou as permissões no workflow de CI para permitir anotações em PRs.
- Smoke test: workflow temporário executado na `main` (run `19215914570`) criou e removeu comentário e label em PR, comprovando o caminho de escrita do `GITHUB_TOKEN`.

## Troubleshooting

- "Não gerou chave no KV":
  - Confirme que abriu a namespace **via link do Binding** `CI_OUTAGES` (evita ver a namespace errada).
  - Verifique no log do step "Executar política de outage" se há `outages: []`. Isso indica que nem status page nem log sugeriram outage. Em selftest, o log sintético deve estar presente.
  - Verifique secrets no GitHub (endpoint/token) e no Worker (secret `CI_OUTAGE_TOKEN`). Em caso de falha no POST, o script registra: `[ci-outage] OTEL endpoint respondeu <status> <statusText>`; `401/403` indicam problema de token/permissão.
- "Status page JSON inválido":
  - O script tolera esse caso lendo o log local (padrões de erro). Em produção, confie na detecção por status page **ou** por log.
- "Sem botão Run workflow":
  - Abra direto: `https://github.com/<org>/<repo>/actions/workflows/ci-outage-selftest.yml` e selecione a branch `main`.
- "KV não atualiza":
  - Use `Connect/Refresh` e recarregue a página; a UI pode cachear a listagem.

## Segurança e manutenção

- Token: mantenha `FOUNDATION_OTEL_OUTAGE_TOKEN`/`CI_OUTAGE_TOKEN` restritos e rotacione periodicamente.
- Endpoint: se desejar, limite o Worker por IP allowlist, challenge ou verificação adicional no corpo.
- Observabilidade: os eventos ficam também no artefato `observabilidade/data/ci-outages.json`; para painéis, consuma o KV periodicamente.

## Referências cruzadas

- Workflow principal: `.github/workflows/frontend-foundation.yml` (job `ci-outage-guard`).
- Selftest: `.github/workflows/ci-outage-selftest.yml`.
- Script: `scripts/ci/handle-outage.ts` (distribuído como `scripts/dist/ci/handle-outage.js`).
- Worker Cloudflare: binding `CI_OUTAGES` + secret `CI_OUTAGE_TOKEN`.
