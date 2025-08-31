# Como Contribuir para o IABANK

Agradecemos o seu interesse em contribuir! Para garantir a qualidade e a consistência do projeto, pedimos que siga estas diretrizes.

## Processo de Desenvolvimento

1.  **Siga o Blueprint:** Todas as contribuições devem estar alinhadas com o [Blueprint Arquitetural](BluePrint_Arquitetural.md). Mudanças na arquitetura devem ser discutidas e aprovadas antes da implementação.
2.  **Crie uma Issue:** Antes de começar a trabalhar, abra uma issue descrevendo o bug ou a feature.
3.  **Crie um Branch:** Crie um branch a partir do `main` com um nome descritivo (ex: `feature/add-loan-export` ou `fix/login-bug`).
4.  **Desenvolva com Testes:** Todo novo código de negócio deve ser acompanhado de testes unitários e/ou de integração.
5.  **Abra um Pull Request:** Ao concluir, abra um Pull Request para o branch `main`. Descreva as suas alterações e vincule a issue correspondente.

## Qualidade de Código

Utilizamos ferramentas para garantir um padrão de código consistente.

*   **Backend (Python):**
    *   **Formatador:** [Black](https://github.com/psf/black)
    *   **Linter:** [Ruff](https://github.com/astral-sh/ruff)
*   **Frontend (TypeScript):**
    *   **Formatador:** [Prettier](https://prettier.io/)
    *   **Linter:** [ESLint](https://eslint.org/)

### Ganchos de Pre-commit

Configuramos ganchos de pre-commit usando a ferramenta `pre-commit` para executar essas checagens automaticamente antes de cada commit. Para instalar, execute:

```bash
pip install pre-commit
pre-commit install
```

Qualquer código que não passe nas verificações do linter/formatador será bloqueado.

## Padrão de Documentação

- **Python:** Todas as funções públicas, classes e métodos devem ter docstrings no estilo [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- **React:** Componentes complexos devem ter comentários explicando seu propósito, props e estado.