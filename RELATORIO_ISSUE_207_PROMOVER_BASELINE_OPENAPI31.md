# Relatório — Issue #207: Contracts: Promover baseline OpenAPI 3.1.0 (api.previous.yaml)

Data: 2025-11-17
Issue: https://github.com/Tomvaz11/iabank/issues/207

## Objetivo
Promover o baseline utilizado nos diffs de contratos do OpenAPI de 3.0.3 para 3.1.0, garantindo que quebras reais não sejam mascaradas pelo baseline desatualizado.

## Contexto
- Após a migração do contrato para OpenAPI 3.1 + oasdiff, o arquivo `contracts/api.previous.yaml` ainda estava em `openapi: 3.0.3` (placeholder mínimo).
- Havia um baseline "sombra" (`contracts/api.baseline-3.1.yaml`) usado via label para dry‑run no CI.

## Ações Executadas
1. Criação de branch de trabalho: `chore/contracts/promote-baseline-openapi-31-207`.
2. Promoção do baseline:
   - Copiado `contracts/api.yaml` → `contracts/api.previous.yaml`.
   - Verificado que `contracts/api.previous.yaml:1` agora contém `openapi: 3.1.0`.
3. Validações locais:
   - Spectral: `pnpm openapi:lint` — sem erros.
   - oasdiff (breaking): `pnpm openapi:diff` — sem diferenças breaking (baseline == atual após promoção).
   - Geração de cliente: `pnpm openapi:generate` — concluída.
   - Pact: `pnpm pact:verify` — 3 testes passando.
   - Observação: instalado `oasdiff` localmente em `.bin/oasdiff` (v1.11.7) para viabilizar o diff local.
4. Documentação:
   - Este relatório foi adicionado para rastreabilidade e auditoria.
   - Demais documentos (runbooks e pipelines) já descrevem o procedimento de atualização do baseline e o uso do baseline alternativo via label; nenhuma atualização adicional necessária.

## Commits Relevantes
- chore(contracts): promover baseline OpenAPI 3.1.0 (api.previous.yaml)

## Arquivos Alterados/Adicionados
- M `contracts/api.previous.yaml`
- A `RELATORIO_ISSUE_207_PROMOVER_BASELINE_OPENAPI31.md`

## Decisões Tomadas
- Promover diretamente o baseline principal para 3.1.0, dada a estabilização do contrato e a existência de baseline sombra já utilizada em PRs anteriores.
- Manter o mecanismo de baseline alternativo por label como ferramenta de governança (dry‑run) para futuras mudanças.

## Pendências Identificadas e Tratadas
- Ausência do binário `oasdiff` no ambiente local: solucionado com instalação do release oficial (v1.11.7) em `.bin/`.
- Nenhum arquivo temporário/caches incluído no commit; repositório mantido limpo.

## Próximos Passos
- Monitorar 1 ciclo de PR após a promoção para confirmar ausência de regressões (gate “Contracts (Spectral, oasdiff, Pact)” deve permanecer verde).
- Caso ocorram mudanças, o changelog textual do `oasdiff` seguirá publicado como artifact de CI (`contracts-diff`).

## Evidências (execução local)
- Spectral: sem erros (severity error = 0).
- oasdiff breaking: nenhuma saída de breaking.
- Pact: 1 arquivo/3 testes passando sob `frontend`.

