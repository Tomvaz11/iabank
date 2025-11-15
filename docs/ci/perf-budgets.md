## Notas de CI — Performance Budgets

- Ajuste no workflow `frontend-foundation.yml` para tornar o upload dos artefatos Lighthouse mais resiliente.
- Removido o uso de `hashFiles()` na condição do passo de upload, evitando falhas intermitentes em runners.
- Sem impacto funcional nos budgets; apenas maior robustez na publicação dos relatórios.

