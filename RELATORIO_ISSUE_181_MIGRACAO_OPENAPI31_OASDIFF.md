# Relatório — Issue #181: OpenAPI 3.1 + oasdiff (gate)

Data: 2025-11-17
Responsável: Automação/Assistente (via gh CLI)

## Contexto
- Situação inicial:
  - Contratos em OpenAPI 3.0.3 (`contracts/api.yaml`).
  - Gate de compatibilidade usando `openapi-diff` (Node/Java), sem suporte a 3.1.
- Objetivo da Issue #181: migrar os contratos para OpenAPI 3.1.0 e trocar o diff semântico para `oasdiff` (gate de breaking).

Links de referência:
- Issue: https://github.com/Tomvaz11/iabank/issues/181
- PR 1 (pipeline + backend + docs): https://github.com/Tomvaz11/iabank/pull/202
- PR 2 (contratos 3.1): https://github.com/Tomvaz11/iabank/pull/203

## Decisão
- Adotar `oasdiff` como ferramenta de diff semântico (subcomando `breaking`), com versão pinada no CI (v1.11.7, binário linux_amd64).
- Migrar `contracts/api.yaml` para OpenAPI 3.1.0 e declarar `jsonSchemaDialect` (2020‑12). Substituir `nullable: true` por union types (`type: [T, 'null']`).
- Manter Spectral para lint e o codegen atual; avaliar futuramente `@hey-api/openapi-ts`.

## Execução (em 2 PRs)
### PR 1 — Preparar pipeline (Refs #181)
- Troca do gate para `oasdiff`:
  - Instalação por binário pinado no job dedicado de contratos:
    - `.github/workflows/ci-contracts.yml:43`
    - `.github/workflows/ci-contracts.yml:71`
  - Atualização do job "Contracts" no workflow principal para instalar o binário (suporte ao `pnpm openapi:diff`):
    - `.github/workflows/frontend-foundation.yml:516`
  - Scripts/PNPM:
    - `package.json:24` — `openapi:diff` usa `oasdiff breaking contracts/api.previous.yaml contracts/api.yaml`.
    - `contracts/scripts/openapi-diff.sh:1` — wrapper atualizado para `oasdiff breaking`.
- Backend (aceitar nova ferramenta):
  - `backend/apps/contracts/models.py:32` — adiciona `Tool.OASDIFF`.
  - `backend/apps/contracts/migrations/0002_alter_contractdiffreport_tool_add_oasdiff.py:1` — migração de choices.
  - `backend/apps/contracts/tests/test_contracts_signals.py:52` — teste atualizado para `'oasdiff'`.
- Documentação:
  - ADR e runbooks atualizados para `oasdiff` e versão pinada v1.11.7.

Resultado: CI verde no job dedicado de contratos; workflow principal passou a instalar `oasdiff` também no job "Contracts".

### PR 2 — Migrar contratos para OpenAPI 3.1 (Closes #181)
- Contratos:
  - `contracts/api.yaml:1` — `openapi: 3.1.0`.
  - `contracts/api.yaml:2` — `jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema`.
  - `contracts/api.yaml` — `nullable: true` substituído por union types (ex.: `tenantId`).
  - Espelho: `specs/002-f-10-fundacao/contracts/frontend-foundation.yaml:1,2`.
- Validações locais: Spectral OK, `oasdiff breaking` OK, build/test frontend OK.
- Merge: após PR 1, conflitos mínimos resolvidos em `docs/runbooks/governanca-api.md` mantendo a menção da versão do `oasdiff` no CI.

## Logs e Validações (resumo)
- CI (PR 1):
  - CI Contracts — SUCCESS com `oasdiff` v1.11.7 binário pinado.
  - Frontend Foundation CI — SUCCESS após corrigir título do PR e instalar `oasdiff` no job "Contracts".
- CI (PR 2):
  - CI Contracts — SUCCESS (Spectral + `oasdiff breaking`).
- main: último run do workflow principal — SUCCESS.

Observações relevantes de execução:
- Falhas iniciais ao tentar `go install` por caminhos de módulo incorretos e versionamento do Go; substituído por download do binário oficial pinado (determinístico e simples).
- O job "Contracts" do workflow principal falhou inicialmente por ausência do binário; corrigido adicionando o step de instalação também nesse workflow.
- Validação de título do PR usava payload antigo do evento; commit trivial gerou novo evento e a checagem passou.

## Mudanças por arquivo (principais)
- `.github/workflows/ci-contracts.yml:43,71` — instalar binário `oasdiff` v1.11.7 e rodar `oasdiff breaking …`.
- `.github/workflows/frontend-foundation.yml:516` — instalar binário `oasdiff` v1.11.7 no job Contracts.
- `package.json:24` — `openapi:diff` com `oasdiff breaking`.
- `contracts/scripts/openapi-diff.sh:1` — wrapper atualizado para `oasdiff breaking`.
- `backend/apps/contracts/models.py:32` — adiciona choice `oasdiff`.
- `backend/apps/contracts/migrations/0002_alter_contractdiffreport_tool_add_oasdiff.py:1` — migração de choices.
- `backend/apps/contracts/tests/test_contracts_signals.py:52` — teste ajustado para `'oasdiff'`.
- `contracts/api.yaml:1,2` — OpenAPI 3.1 + jsonSchemaDialect; union types.
- `specs/002-f-10-fundacao/contracts/frontend-foundation.yaml:1,2` — espelho atualizado.
- `docs/adr/011-governanca-de-apis-e-contratos.md:8` — dif atualizado para `oasdiff`.
- `docs/runbooks/governanca-api.md` — menciona `oasdiff v1.11.7` no CI.
- `docs/pipelines/ci-required-checks.md:8` — gate lista `oasdiff`.

## Pendências (para executar depois)
1) Promover baseline para 3.1.0
- O que fazer: atualizar `contracts/api.previous.yaml` para refletir o contrato estável 3.1.0.
- Quando: após confirmação de estabilidade do 3.1 (ex.: junto do próximo release).
- Como validar: `pnpm openapi` e checar CI (Spectral + `oasdiff breaking`).
- Risco: promover cedo demais mascara o comparativo; prefira após consenso de estabilidade.

2) Avaliar migração do codegen para `@hey-api/openapi-ts` (opcional)
- Benefício: melhor suporte a OpenAPI 3.1/JSON Schema 2020‑12 e qualidade de tipos.
- Passos sugeridos (spike):
  - `pnpm add -D @hey-api/openapi-ts`.
  - Ajustar script de geração e regenerar cliente.
  - Rodar `pnpm build:frontend && pnpm test`.
  - Abrir PR com impactos de tipos e plano de adoção.

## Rollback
- Reverter `openapi: 3.1.0` para `3.0.3` em `contracts/api.yaml`.
- Restabelecer o step de diff anterior (se necessário) — não recomendado; `oasdiff` cobre 3.0.x e 3.1.
- Reverter migração de enum (`ContractDiffReport.Tool`) se requerido.

## Como validar localmente
- `pnpm install`
- `pnpm openapi:lint`
- `pnpm openapi:diff`
- `pnpm openapi:generate`
- `pnpm build:frontend && pnpm test`

---

Este relatório documenta as decisões, mudanças e validações da migração para OpenAPI 3.1 e adoção do `oasdiff` como gate no CI, além de listar pendências planejadas para execução futura.

## Recomendações adicionais e operações

3) Nome do job do Required Check (merge)
- Manter o nome exatamente como protegido hoje: "Contracts (Spectral, OpenAPI Diff, Pact)" (Branch Protection exige este contexto).
- Se optarmos por renomear no futuro (ex.: citar explicitamente "oasdiff"), primeiro atualize os Required Checks da branch `main` para evitar bloqueio de merge.

4) Versão do oasdiff (pin) e revisão periódica
- Permanecer com o pin v1.11.7 nos workflows para previsibilidade.
- Revisitar trimestralmente para avaliar atualização do oasdiff; ao atualizar, manter a instalação por versão (não `latest`).

5) Publicar artefatos de diff/changelog no CI (opcional)
- Vantagem: auditoria e troubleshooting rápidos pós-PR.
- Exemplo de passo adicional (após o `oasdiff breaking`):
  ```yaml
  - name: OpenAPI changelog (texto)
    if: ${{ always() }}
    run: |
      mkdir -p artifacts/contracts
      oasdiff changelog contracts/api.previous.yaml contracts/api.yaml -f text > artifacts/contracts/changelog.txt || true
  - name: Upload artifacts (contracts)
    if: ${{ always() }}
    uses: actions/upload-artifact@v4
    with:
      name: contracts-diff
      path: artifacts/contracts
      if-no-files-found: ignore
  ```

6) Cache do binário do oasdiff por versão (opcional)
- Reduz tempo de setup. Exemplo (chaveado pela versão):
  ```yaml
  - name: Cache oasdiff
    uses: actions/cache@v4
    with:
      path: ${{ runner.temp }}/oasdiff-bin
      key: oasdiff-${{ runner.os }}-v1.11.7
  - name: Install oasdiff (v1.11.7, linux_amd64)
    if: ${{ steps.cache.outputs.cache-hit != 'true' }}
    run: |
      OASDIFF_VERSION="1.11.7"
      OASDIFF_URL="https://github.com/oasdiff/oasdiff/releases/download/v${OASDIFF_VERSION}/oasdiff_${OASDIFF_VERSION}_linux_amd64.tar.gz"
      INSTALL_DIR="$RUNNER_TEMP/oasdiff-bin"
      mkdir -p "$INSTALL_DIR"
      curl -sSL "$OASDIFF_URL" -o "$INSTALL_DIR/oasdiff.tar.gz"
      tar -xzf "$INSTALL_DIR/oasdiff.tar.gz" -C "$INSTALL_DIR"
      chmod +x "$INSTALL_DIR/oasdiff"
      echo "$INSTALL_DIR" >> $GITHUB_PATH
  ```

7) Verificação de menções legadas a `openapi-diff` em documentação
- Já atualizamos ADR/Runbooks/Required Checks; ainda assim, revisar periodicamente:
  - Comando sugerido local: `rg -n "openapi-diff" docs .github scripts contracts backend`
- Caso surja nova menção, alinhar para `oasdiff` quando adequado.
