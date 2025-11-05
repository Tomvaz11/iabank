# 8. Ferramenta de Automação de Dependências

**Status:** Aprovado

**Contexto:** Para cumprir o Artigo sobre Gestão de Dependências da Constituição, que exige a automação da verificação e atualização de dependências para mitigar riscos de segurança, foi necessário escolher uma ferramenta.

**Decisão:** O projeto adota o **Renovate** para gerenciar as atualizações de dependências de forma contínua e automatizada.

**Consequências:** 
- Um arquivo de configuração `renovate.json` será mantido na raiz do projeto.
- As Pull Requests de atualização de dependências serão criadas automaticamente pelo Renovate.
- Essas PRs DEVEM passar por todos os gates de qualidade e segurança definidos no pipeline de CI antes de serem aprovadas para merge.

**Operacionalização no CI:**
- A configuração é validada pelo workflow `.github/workflows/renovate-validation.yml` usando `renovate-config-validator` com `--strict`.
- O job fixa Node `22.13.0` por compatibilidade com `renovate@latest`.
- Migrações comuns que podem causar falha no validador: `matchPaths → matchFileNames`, `stabilityDays → minimumReleaseAge`, e schedules compostos devem ser divididos em entradas separadas.
- Runbook: `docs/runbooks/renovate-validation.md`.
