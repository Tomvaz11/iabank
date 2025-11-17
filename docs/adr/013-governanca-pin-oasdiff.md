# ADR-013 — Governança do Pin do oasdiff (revisão trimestral)

**Status:** Aprovado

**Contexto:**
- O gate de contratos utiliza o `oasdiff` (`breaking`/`changelog`) com versão pinada no CI para reprodutibilidade. Pin atual: `v1.11.7`.
- Precisamos institucionalizar revisão periódica para aproveitar correções e evitar regressões.

**Decisão:**
- Estabelecer revisão trimestral do pin do `oasdiff`.
- Procedimento por ciclo:
  1) Analisar changelog/release notes do upstream (`oasdiff/oasdiff`).
  2) Abrir PR de teste atualizando o pin para a versão candidata (instalação por versão — nunca `latest`).
  3) Validar no CI: `oasdiff breaking` (baseline padrão/alternativos) e `oasdiff changelog` (artifact textual).
  4) Atualizar chaves de cache e diretórios vinculados à versão, quando aplicável.
  5) Documentar plano de rollback no PR.

**Rollback:**
- Reverter o commit do novo pin, restaurar cache key anterior e reexecutar CI. Registrar lições aprendidas no relatório do ciclo.

**Consequências:**
- Pin por versão mantém estabilidade e facilita auditoria.
- Requer disciplina operacional trimestral e pequena manutenção de docs/CI.

**Referências Operacionais:**
- Runbook: `docs/runbooks/governanca-oasdiff-pin.md`
- CI: `docs/pipelines/ci-required-checks.md`
- Script: `contracts/scripts/oasdiff.sh`
