# 8. Ferramenta de Automação de Dependências

**Status:** Aprovado

**Contexto:** Para cumprir o Artigo sobre Gestão de Dependências da Constituição, que exige a automação da verificação e atualização de dependências para mitigar riscos de segurança, foi necessário escolher uma ferramenta.

**Decisão:** O projeto adota o **Renovate** para gerenciar as atualizações de dependências de forma contínua e automatizada.

**Consequências:** 
- Um arquivo de configuração `renovate.json` será mantido na raiz do projeto.
- As Pull Requests de atualização de dependências serão criadas automaticamente pelo Renovate.
- Essas PRs DEVEM passar por todos os gates de qualidade e segurança definidos no pipeline de CI antes de serem aprovadas para merge.
