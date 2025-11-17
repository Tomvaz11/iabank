# Relatório — Issue #209: Frontend/Codegen — Spike @hey-api/openapi-ts (OAS 3.1/2020-12)

Data: 2025-11-17
Responsável: Automação/Assistente (via gh CLI)

## Objetivo
Avaliar `@hey-api/openapi-ts` como alternativa ao `openapi-typescript-codegen` com foco em melhor suporte a OpenAPI 3.1 + JSON Schema 2020‑12.

## Escopo executado
- Adicionada devDependency `@hey-api/openapi-ts` (compatível com Node 20.17.0) e script de geração alternativo.
- Gerado cliente em `frontend/src/shared/api/generated-next` (sem alterar imports existentes).
- Executado `pnpm build:frontend && pnpm test && pnpm typecheck` — todos verdes.
- Documentadas diferenças de tipos/assinaturas e impactos, com plano de adoção.

## Decisões e ajustes técnicos
- Versão utilizada do `@hey-api/openapi-ts`: `0.82.0`.
  - Motivo: versões `>=0.86.x` exigem Node `>=20.19.0` e a monorepo está pinada em `20.17.0` (`.nvmrc`/`.tool-versions`).
  - Observação: ao testar `0.85.0`, houve falha silenciosa por incompatibilidade ESM/CJS ao carregar dependências (erro `ERR_REQUIRE_ESM` via `c12` quando requerido de CJS). A `0.82.0` funciona corretamente com o ambiente atual.
- Script adicionado em `package.json`:
  - `openapi:generate:next`: `pnpm exec openapi-ts --input "$(pwd)/contracts/api.yaml" --output frontend/src/shared/api/generated-next --client @hey-api/client-fetch`
  - Observação importante: para evitar que o CLI interprete o input como “Hey API shorthand”, usa-se caminho absoluto (`$(pwd)/…`). Caminhos relativos como `contracts/api.yaml` resultam em erro de parsing do shorthand.

## Artefatos gerados
- Diretório: `frontend/src/shared/api/generated-next`
  - Estrutura principal:
    - `client/` (client runtime)
    - `core/` (serializers/utilitários)
    - `types.gen.ts` (tipos de dados, rotas e responses/errors por status code)
    - `sdk.gen.ts` (funções de alto nível por operação)
    - `client.gen.ts` e `index.ts`

## Validações executadas
- `pnpm build:frontend` — OK
- `pnpm test` — OK (26 arquivos, 77 testes, todos passados)
- `pnpm typecheck` — OK

Critério de aceite atendido: diretório `generated-next` presente e toolchain (build/test/typecheck) verde.

## Diferenças principais: openapi-typescript-codegen vs openapi-ts
- Organização de arquivos
  - Atual (`openapi-typescript-codegen`): `models/`, `core/` (CancelablePromise, ApiError, OpenAPI, request), `services/` com classes e métodos estáticos.
  - Novo (`openapi-ts`): `client/`, `core/`, `types.gen.ts`, `sdk.gen.ts` com funções (estilo functional) para cada operação.
- Estilo de consumo da API
  - Atual: `TenantsService.getTenantTheme({ tenantId, xTenantId, ... }): CancelablePromise<TenantThemeResponse>`.
  - Novo: `getTenantTheme(options)` com generics de resposta/erro; recebe `options.headers`, `options.path`, `options.query`, permite injetar um `client` custom.
- Modelagem de respostas/erros
  - Atual: retorno direto do tipo de sucesso, exceções via `ApiError`.
  - Novo: tipos por status code (ex.: `GetTenantThemeResponses`, `GetTenantThemeErrors`) e controle de fluxo via generic `ThrowOnError` no client.
- Tipagem inferida de rotas e parâmetros
  - Ambos inferem `path`, `query`, `headers`, porém o `openapi-ts` gera tipos agregados `{ body, headers, path, query, url }` por operação, o que favorece composição e reutilização.
- Client runtime
  - Atual: runtime próprio baseado em `fetch` com `CancelablePromise` e `OpenAPI` config.
  - Novo: `@hey-api/client-fetch` (bundle dentro do `openapi-ts`), com utilitários de serialização, SSE e auth.

## Impactos e plano de adoção
- Impactos potenciais caso migremos definitivamente:
  - Refatoração de imports de `services/` (classes) para `sdk.gen.ts` (funções) e ajustes de chamadas.
  - Adaptação do tratamento de erros: hoje conflui via `ApiError`; no novo client, os erros são tipados por status e podem ser mapeados diretamente.
  - Remoção de `CancelablePromise` em favor de `Promise` padrão.
  - Ajustes em mocks de testes (caso façam spy em classes dos services).
- Plano sugerido em etapas:
  1) Manter `generated` como fonte atual e publicar `generated-next` (feito neste spike).
  2) Criar um wrapper fino que exponha a mesma interface dos services atuais mapeando para as funções do `sdk` novo (migração gradual sem tocar call-sites).
  3) Medir impacto em DX e tipos; se positivo, remover wrapper e migrar call-sites diretamente para as funções.
  4) Opcional: subir Node p/ `>=20.19.0` e atualizar `@hey-api/openapi-ts` para o último minor quando conveniente.

## Commits e arquivos alterados
- Alterações relevantes:
  - `package.json`: adiciona script `openapi:generate:next` e dependências `@hey-api/openapi-ts@0.82.0` e `@hey-api/client-fetch@0.13.1` (esta é retrocompatível e hoje é bundlada no pacote principal; mantida por segurança).
  - `pnpm-lock.yaml`: atualizado.
  - `frontend/src/shared/api/generated-next/**`: novo cliente gerado.
- Limpezas:
  - Removidos artefatos temporários do experimento (`contracts/test-petstore.yaml`, `frontend/src/shared/api/generated-next-test/`).

## Pendências resolvidas
- Geração com `openapi-ts` falhando silenciosamente:
  - Causa raiz 1: versão do pacote incompatível com Node 20.17.0 → resolvido fixando `0.82.0`.
  - Causa raiz 2: interpretação de caminho relativo como "Hey API shorthand" → resolvido usando caminho absoluto (`$(pwd)/contracts/api.yaml`).

## Próximos passos recomendados
- Se a decisão for migrar:
  - Implementar wrapper de transição e migrar um endpoint piloto.
  - Atualizar documentação do contrato/consumo no `README.md` e no blueprint.
  - Avaliar pin/atualização da versão do Node em `.nvmrc`/`.tool-versions` para permitir versões mais novas do `openapi-ts`.

---

Este relatório cumpre o critério de aceite da issue #209 (cliente gerado em `generated-next` e toolchain verde), e descreve as diferenças técnicas e o plano de adoção.

