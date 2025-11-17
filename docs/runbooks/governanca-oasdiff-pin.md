# Runbook: Revisão Trimestral do Pin do oasdiff

Implementa o **ADR-013** (Governança do pin do oasdiff).

## Objetivo
Padronizar a revisão trimestral do `oasdiff` (pin atual `v1.11.7`), garantindo estabilidade do gate e evolução controlada.

## Quando Rodar
- Periodicidade: trimestral. Há um lembrete automatizado via workflow agendado.

## Pré‑requisitos
- Permissão para abrir PRs; `gh` autenticado para consultar releases.

## Passo a Passo
1. Levantar versões candidatas
   - Releases upstream: `gh release list -R oasdiff/oasdiff` e `gh release view <tag> -R oasdiff/oasdiff`.
   - Selecionar a mais recente estável.
2. Abrir PR de teste atualizando o pin
   - Atualizar referências de versão (instalação, cache keys, diretórios) quando necessário.
   - Incluir no PR: “Closes #<issue do ciclo>” e referência ao ADR-013.
3. Validar no CI
   - `breaking`: `contracts/scripts/oasdiff.sh` (baseline padrão ou via `--baseline`/`OPENAPI_BASELINE`).
   - `changelog`: publicar artifact textual `oasdiff changelog <baseline> <atual> -f text`.
4. Plano de rollback (obrigatório no PR)
   - Reverter commit do pin, restaurar cache key anterior, reexecutar CI.
5. Merge e registro
   - Merge (squash/auto‑merge) e atualização do relatório do ciclo.

## Notas
- Instalação por versão (NÃO usar `latest`).
- Se diretório de instalação mudar, atualizar PATH e documentação.

## Referências
- ADR: `docs/adr/013-governanca-pin-oasdiff.md`
- CI: `docs/pipelines/ci-required-checks.md`
- Script: `contracts/scripts/oasdiff.sh`
