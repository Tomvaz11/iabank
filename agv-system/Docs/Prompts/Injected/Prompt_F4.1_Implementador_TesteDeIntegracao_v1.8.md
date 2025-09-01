# AGV Prompt: IntegradorTester v1.8 - Geração de Testes de Integração Guiada

**Tarefa Principal:** Analisar o conjunto de módulos especificados, o Blueprint Arquitetural, e os **cenários de integração já definidos** para gerar testes de integração robustos (`pytest`) que verifiquem a correta colaboração entre esses módulos.

**Contexto Essencial (Fornecido pelo usuário):**

1. **Módulos Alvo da Integração (O Grupo Atual):**
   - `PARADA DE TESTES DE INTEGRAÇÃO T1`
   - _(Instrução para Coordenador: Anexar os arquivos .py destes módulos.)_
2. **Blueprint Arquitetural (Fonte da Verdade Arquitetural):** @Output_BluePrint_Arquitetural_Tocrisna_v1.0.md
3. **Ordem de Implementação e Plano de Testes (Fonte da Verdade dos Cenários):** @Output_Ordem_Para_Implementacao_Geral_v1.0.md
4. **Contexto Adicional do Workspace:** _(Instrução para Coordenador: Anexar outros módulos já implementados que possam ser necessários para criar stubs/fakes, ou interfaces de dependências externas ao grupo sendo testado.)_

**Instruções Detalhadas para a IA (IntegradorTester):**

1. **Identificar Escopo e Cenários Definidos:**

   - Analise a lista de "Módulos Alvo da Integração".
   - No arquivo `@Output_Ordem_Para_Implementacao_Geral_v1.0.md`, localize a seção "PARADA PARA TESTES DE INTEGRAÇÃO" correspondente ao grupo atual.
   - Extraia o "Objetivo do Teste" e os "Cenários Chave" que **já foram definidos para você**. Sua tarefa é implementar testes que cubram fielmente estes cenários.

2. **Analisar Blueprint e Código Fonte:**

   - Consulte o `@Blueprint_Arquitetural` e o código dos módulos alvo para entender as interfaces, os fluxos de dados e as dependências externas ao grupo que precisarão ser mockadas/stubbadas.

3. **Implementar Testes de Integração:**

   - Escreva o código dos testes (`pytest`) nos arquivos corretos, seguindo a estrutura e convenção definidas no `Blueprint`.
   - Crie fixtures `pytest` para setup/teardown de dados ou serviços (ex: criar tenants e usuários de teste).
   - **Garantia de Consistência de Dados Multi-tenant:**
     Para sistemas multi-tenant, **TODOS** os objetos criados em um teste devem pertencer ao mesmo tenant. Implemente factories que garantam esta consistência:
     - Use `factory.SelfAttribute('..tenant')` para propagar o tenant entre factories relacionadas
     - Use `factory.LazyAttribute` quando o tenant for derivado de outro objeto
     - **CRÍTICO:** Teste suas factories com testes específicos (`test_factories.py`) antes de usá-las em testes de integração
   - **Validação de Factories:** Antes de implementar testes de integração complexos, crie testes unitários que validem que suas factories geram dados consistentes, especialmente para relacionamentos multi-tenant.

4. **Aplicar Boas Práticas de Teste de Integração:**

   - Foque nas interações entre os módulos do grupo.
   - Use implementações reais dos módulos _dentro_ do escopo. Para dependências _fora_ do escopo, use mocks ou fakes.
   - As asserções devem verificar os resultados esperados das interações (código de status da resposta, estado final do banco de dados, chamadas a mocks).
   - Adicione docstrings claras explicando o propósito do teste e o cenário coberto.
   - **Ferramentas de Teste de API:** Para testar os endpoints da API, utilize as **ferramentas de cliente de teste fornecidas pelo framework web** (ex: o `APIClient` do Django REST Framework, o TestClient do FastAPI, etc.).

5. **Gerar Relatório Detalhado:**
   - Forneça um relatório claro, incluindo:
     1. **Introdução:** Resumo do escopo dos testes realizados.
     2. **Detalhes dos Testes Implementados:** Descreva como cada cenário foi implementado.
     3. **Lista de Arquivos de Teste Criados/Modificados (com conteúdo completo):** Apresente o código completo dos arquivos de teste gerados, seguindo o padrão de output do `ImplementadorMestre`.
