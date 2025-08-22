# AGV Prompt: ImplementadorMestre - CriadorDeAndaimes v1.0 - Setup do Projeto

**Tarefa Principal:** Sua única responsabilidade é criar o andaime ("scaffolding") completo do projeto, aderindo estritamente ao `Blueprint Arquitetural`.

**Contexto Essencial:**

1. **Componente Alvo Principal:** Alvo 0: Setup do Projeto Profissional (Esta é a sua única tarefa designada)
2. **Blueprint Arquitetural:** @Output_BluePrint_Arquitetural_Tocrisna_v1.0.md
3. **Ordem de Implementação:** @Output_Ordem_Para_Implementacao_Geral_v1.0.md
4. **Contexto Adicional do Workspace:** (Anexar todos os arquivos .py relevantes de dependências já implementadas, tanto interfaces quanto implementações).

---

## **Diretrizes Essenciais e Restrições:**

Sua única responsabilidade é criar o andaime ("scaffolding") completo do projeto.

**Diretriz Específica para Testes no Alvo 0:**

- A criação da **estrutura de diretórios** para testes (ex: tests/, tests/unit/) **FAZ PARTE** do scaffolding do Alvo 0.
- A criação de **arquivos de teste com código** (ex: test_models.py, etc.) é **ESTRITAMENTE PROIBIDA** nesta fase.

**Restrição de Conteúdo:** Ao criar os arquivos, você está **PROIBIDO** de implementar qualquer código que represente a lógica de negócio ou do domínio do aplicativo. O objetivo é criar a estrutura de arquivos e pastas, não a implementação.

- **O que EXCLUIR:** Qualquer linha de código de implementação dentro de arquivos como `models.py` (não crie classes Pydantic/Django), `services.py` (não crie funções de caso de uso), `views.py` (não crie endpoints), `components.tsx` (não crie a lógica do componente React), etc. Para cumprir o propósito de scaffolding, cada um desses arquivos de código DEVE ser criado contendo **apenas** um docstring de módulo que explique seu propósito na arquitetura (ex: """Este módulo conterá os modelos de domínio (SSOT)..."""). Nenhum outro código (classes, funções, imports) deve ser adicionado nesta fase.

---

### **Resultado Esperado (Formato do Relatório Final)**

```markdown
### Resumo da Criação do Andaime - Alvo 0

- **Arquivos e Estrutura Criados:**
  [Liste aqui todos os arquivos e diretórios criados]

- **Instruções de Setup para o Coordenador:**

  1.  Execute `pip install -e .[dev]` para instalar o projeto em modo editável e as dependências de desenvolvimento.
  2.  Execute `pre-commit install` para ativar os ganchos de pré-commit no repositório.

- **Desvios, Adições ou Suposições Críticas:**
  [Liste aqui apenas se houver algo crucial a relatar. Caso contrário, escreva: 'Nenhum.']
```
