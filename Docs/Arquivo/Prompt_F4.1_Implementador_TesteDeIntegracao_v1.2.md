# AGV Prompt: IntegradorTester v1.2 - Geração de Testes de Integração Guiada

**Tarefa Principal:** Analisar o conjunto de módulos especificados, o Blueprint Arquitetural, e os **cenários de integração já definidos** para gerar testes de integração robustos (`pytest`) que verifiquem a correta colaboração entre esses módulos.

**Contexto Essencial (Fornecido pelo Coordenador):**

1. **Módulos Alvo da Integração (O Grupo Atual):**
   - `Alvo 0`, `iabank.settings`, `iabank.domain.models (Tenant, User)`, `iabank.api (Auth, Errors)`, `iabank.infrastructure (Tenancy)`
   - _(Instrução para Coordenador: Anexar os arquivos .py destes módulos.)_
2. **Blueprint Arquitetural (Fonte da Verdade Arquitetural):** @Output_BluePrint_Arquitetural_Tocrisna_v1.0.md
3. **Ordem de Implementação e Plano de Testes (Fonte da Verdade dos Cenários):** @Output_Ordem_Para_Implementacao_Geral_v1.0.md
4. **Contexto Adicional do Workspace:** _(Instrução para Coordenador: Anexar outros módulos já implementados que possam ser necessários para criar stubs/fakes, ou interfaces de dependências externas ao grupo sendo testado.)_

**Instruções Detalhadas para a IA (IntegradorTester):**

1. **Identificar Escopo e Cenários Definidos:**

   - Analise a lista de "Módulos Alvo da Integração".
   - No arquivo `@Output_Ordem_Para_Implementacao_Geral_v1.0.md`, localize a seção "PARADA PARA TESTES DE INTEGRAÇÃO" correspondente ao grupo atual.
   - Extraia o "Objetivo do Teste" e os "Cenários Chave" que **já foram definidos para você**. Sua tarefa é implementar testes que cubram fielmente estes cenários.

2. **Analisar Blueprint, Módulos Alvo e Interfaces:**

   - Consulte o `@Output_BluePrint_Arquitetural_Tocrisna_v1.0.md` e o código dos módulos alvo para entender as interfaces, os fluxos de dados e as dependências externas ao grupo que precisarão ser mockadas/stubbadas/fakadas.

3. **Implementar Testes de Integração:**

   - Escreva o código dos testes (`pytest`) nos arquivos corretos.
   - **Estrutura de Testes Mandatória:** Os testes de integração devem ser organizados em diretórios que reflitam a **camada principal** sendo testada, conforme a estrutura do Blueprint. Por exemplo:
     - Testes que validam a `Lógica de Domínio` devem ir para `tests/test_domain/`.
     - Testes que validam a `Camada de Aplicação` devem ir para `tests/test_application/`.
     - Testes que validam a `Camada de Infraestrutura` devem ir para `tests/test_infrastructure/`.
   - Crie fixtures `pytest` para setup/teardown de dados ou serviços.
   - **Padrão Recomendado:** Para testes de integração complexos, considere criar classes "Fake" (implementações leves em memória das interfaces de infraestrutura) para um ambiente de teste mais robusto e legível do que o uso excessivo de mocks.

4. **Aplicar Boas Práticas de Teste de Integração:**

   - Foque nas interações entre os módulos do grupo.
   - Use implementações reais dos módulos _dentro_ do escopo. Para dependências _fora_ do escopo, use mocks ou fakes.
   - As asserções devem verificar os resultados esperados das interações (estado final, valores retornados, chamadas a mocks).
   - Adicione docstrings claras explicando o propósito do teste e o cenário coberto.

5. **Gerar Relatório Detalhado:**
   - Forneça um relatório claro, seguindo a estrutura abaixo:
     1. **Introdução:** Resumo do escopo dos testes realizados (quais módulos, qual objetivo).
     2. **Detalhes dos Testes Implementados:** Para cada cenário definido, descreva como ele foi implementado, quais fixtures foram criadas e qual a estratégia de mocking/faking utilizada.
     3. **Cobertura Qualitativa:** Descreva o quão bem os cenários de integração definidos foram cobertos.
     4. **Lista de Todos os Arquivos de Teste Criados/Modificados.**
