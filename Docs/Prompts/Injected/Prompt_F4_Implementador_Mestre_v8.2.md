# AGV Prompt: ImplementadorMestre v8.2 - Implementação de Módulo Funcional

**Tarefa Principal:** Implementar o componente de software alvo, aderindo estritamente ao `Blueprint Arquitetural` e às diretrizes abaixo.

**Contexto Essencial:**

1. **Componente Alvo Principal:** Alvo 4
2. **Blueprint Arquitetural:** @Output_BluePrint_Arquitetural_Tocrisna_v1.0.md
3. **Ordem de Implementação:** @Output_Ordem_Para_Implementacao_Geral_v1.0
4. **Contexto Adicional do Workspace:** (Anexar todos os arquivos .py/.ts relevantes de dependências já implementadas).

---

## **Diretrizes Essenciais:**

1. **Fonte da Verdade:** O `@Blueprint_Arquitetural` é a autoridade máxima para responsabilidades, dependências, tecnologias e estrutura de diretórios. Siga-o rigorosamente.

2. **Foco Estrito no Escopo:** Sua tarefa é implementar **APENAS** o "Componente Alvo Principal". Não implemente funcionalidades de alvos futuros.

3. **Qualidade do Código:** Escreva código limpo, profissional e de fácil manutenção, aderindo aos princípios SOLID e aos padrões de estilo definidos no `Blueprint` (PEP 8, etc.).

4. **Testes Unitários (OBRIGATÓRIO):**

   - Gere testes unitários (`pytest` para backend, `@testing-library/react` para frontend) para **TODO** o código de produção novo ou modificado.
   - Atingir **alta cobertura da lógica de implementação** é a meta.
   - Siga a estrutura de diretórios de testes definida no `Blueprint`.
   - **Para sistemas multi-tenant:** Se implementando factories de teste, garanta propagação explícita de tenant usando `factory.SelfAttribute('..tenant')` em sub-factories.
   - **Meta-testes obrigatórios:** Se criar factories complexas, implemente `test_factories.py` para validar consistência dos dados gerados.

5. **Documentação e Clareza (Docstrings/Comentários - OBRIGATÓRIO):**

   - **Docstring de Módulo:** Todo arquivo de produção (`.py`, `.ts`, `.tsx`) criado ou modificado DEVE começar com um comentário de cabeçalho que explique sucintamente o propósito do módulo.
   - **Docstrings/JSDoc:** Todas as classes, funções e componentes públicos devem ter documentação clara explicando o que fazem, seus parâmetros/props e o que retornam.

6. **Conformidade com a Stack e o Contexto (Protocolo de Bloqueio):**

   - Utilize **EXCLUSIVAMENTE** as bibliotecas, tecnologias e componentes definidos no contexto fornecido (`Blueprint`, arquivos de código). É **PROIBIDO** inventar ou supor a implementação de um componente que não foi fornecido.
   - Se a sua tarefa exigir a utilização de um componente ou módulo que está referenciado no `Blueprint` mas cuja definição detalhada não foi incluída no seu contexto, **considere isso um bloqueio técnico.**
   - Nesse caso, **PARE a implementação e comunique o bloqueio claramente** no seu relatório final, especificando qual informação de contexto está faltando.

7. **Diretriz de Foco no Contrato (Interface-First para Dependências):**

   - Ao interagir com uma dependência que possui uma interface ou tipo definido (seja uma interface Python, um tipo TypeScript ou um ViewModel no `Blueprint`), sua implementação **DEVE** aderir a esse contrato.
   - Ao criar testes unitários, seus mocks devem replicar a **interface/contrato**, não os detalhes internos da implementação concreta. Isso resulta em testes mais robustos e desacoplados.

8. **Gerenciamento do Ambiente (Lifecycle-Aware):**
   - Se a implementação do seu alvo exigir uma **nova biblioteca/dependência externa**, você **DEVE**:
     - Adicionar a nova dependência ao arquivo de gerenciamento de pacotes apropriado (`pyproject.toml`, `package.json`).
     - Mencionar explicitamente essa adição no seu relatório final para que o Coordenador possa executar `pip install` ou `npm install`.

---

### **Resultado Esperado (Formato do Relatório Final)**

````markdown
### Resumo da Implementação

**Arquivos Criados/Modificados:**
[Liste aqui os caminhos completos de todos os arquivos de produção e de teste que você criou ou modificou.]

**Conteúdo dos Arquivos:**
[Apresente aqui o conteúdo completo e final de cada arquivo, um após o outro, dentro de blocos de código Markdown. Comece cada bloco com o caminho completo do arquivo.]

--- START OF FILE backend/src/iabank/operations/services.py ---

```python
# Conteúdo completo e final do arquivo
```
````

--- END OF FILE backend/src/iabank/operations/services.py ---

--- START OF FILE backend/tests/unit/iabank/operations/tests/test_services.py ---

```python
# Conteúdo completo e final do arquivo de teste
```

--- END OF FILE backend/tests/unit/iabank/operations/tests/test_services.py ---

**Confirmação de Testes:**
Testes unitários foram criados para todo o código de produção, seguindo a estrutura definida e visando alta cobertura da lógica de implementação.

**Confirmação de Documentação:**
Todo o código de produção foi documentado com comentários de módulo e de função/classe, conforme as diretrizes.

**Desvios, Adições ou Suposições Críticas:**
[Liste aqui apenas se houver algo crucial a relatar, como um desvio, um bloqueio técnico ou uma nova dependência adicionada. Caso contrário, escreva: 'Nenhum.']
