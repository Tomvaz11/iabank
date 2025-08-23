# AGV Prompt: F4-Scaffolder v1.0 - Setup do Projeto Profissional

**Tarefa Principal:** Sua única responsabilidade é executar o **"Alvo 0: Setup do Projeto Profissional"**. Você deve criar o andaime ("scaffolding") completo do projeto, incluindo toda a estrutura de diretórios e arquivos de configuração iniciais, conforme especificado no `Blueprint Arquitetural`.

**Contexto Essencial:**

1. **Componente Alvo Principal:** Alvo 0: Setup do Projeto Profissional
2. **Blueprint Arquitetural:** @Output_BluePrint_Arquitetural_Tocrisna_v1.0.md
3. **Ordem de Implementação:** @Output_Ordem_Para_Implementacao_Geral_v1.0.md

---

## **Diretrizes Essenciais:**

1. **Fonte da Verdade:** O `@Blueprint_Arquitetural.md` é a autoridade máxima para a estrutura de diretórios e o conteúdo dos arquivos de configuração. Siga rigorosamente as seções relevantes (Estrutura de Diretórios Proposta, Arquivo .gitignore Proposto, Arquivo README.md Proposto, etc.).

2. **Foco Estrito no Setup:** Sua tarefa é criar a estrutura de arquivos e pastas e preencher os arquivos de configuração. Você está **ESTRITAMENTE PROIBIDO** de implementar qualquer código que represente a lógica de negócio ou do domínio da aplicação.

3. **Regra de Conteúdo para Arquivos de Código:**

   - Ao criar arquivos de código-fonte (ex: `models.py`, `services.py`, `views.py`, `App.tsx`), eles **DEVEM** ser criados contendo **APENAS** um docstring de módulo (para Python) ou um comentário de cabeçalho (para TypeScript/JS) que explique seu propósito na arquitetura (ex: `"""Este módulo conterá os modelos de domínio do Django para o app de operações."""`).
   - Nenhum outro código (classes, funções, imports, `export default`, etc.) deve ser adicionado a esses arquivos de código-fonte nesta fase.

4. **Diretriz para Estrutura de Testes:**

   - A criação da **estrutura de diretórios** para testes (ex: `backend/src/iabank/operations/tests/`) **FAZ PARTE** do scaffolding do Alvo 0.
   - Dentro desses diretórios, você **DEVE** criar os arquivos de teste correspondentes aos arquivos de código-fonte, aplicando a mesma regra de conteúdo: os arquivos de teste devem conter **APENAS** um docstring de módulo que explique seu propósito (ex: `"""Testes unitários para os serviços do app de operações."""`). Nenhuma classe de teste, função ou import deve ser adicionado nesta fase.

5. **Conformidade com a Stack Tecnológica:**
   - Utilize **EXCLUSIVAMENTE** os nomes de arquivos, tecnologias e configurações designados no Blueprint (ex: `pyproject.toml` para Poetry/Ruff, `package.json` para Node, `.github/workflows/main.yml` para CI/CD, etc.).

---

### **Resultado Esperado (Formato do Relatório Final)**

Seu output deve ser a lista de todos os arquivos e diretórios criados, seguida por um relatório conciso.

```markdown
### Resumo da Implementação - Alvo 0: Setup do Projeto Profissional

**Estrutura de Arquivos e Diretórios Criados:**
[Liste aqui, em formato de árvore (tree), toda a estrutura de diretórios e arquivos que você criou.]

**Conteúdo dos Arquivos Gerados:**
[Apresente aqui o conteúdo completo de cada arquivo de configuração que você gerou, como .gitignore, README.md, package.json, pyproject.toml, docker-compose.yml, etc. E o conteúdo dos arquivos de código-fonte (apenas com docstrings).]

**Instruções de Setup para o Coordenador:**
[Forneça uma lista numerada de comandos que o Coordenador deve executar para inicializar o projeto, com base nos arquivos que você criou. Exemplo:]

1.  Execute `docker-compose up --build` para construir e iniciar o ambiente.
2.  Execute `pre-commit install` para ativar os ganchos de pré-commit no repositório.
3.  (Opcional) Execute `docker-compose exec backend python src/manage.py migrate` para verificar a conexão inicial com o banco.

**Desvios, Adições ou Suposições Críticas:**
[Liste aqui apenas se houver algo crucial a relatar, como um desvio, um bloqueio técnico ou uma nova dependência adicionada. Caso contrário, escreva: 'Nenhum.']
```
