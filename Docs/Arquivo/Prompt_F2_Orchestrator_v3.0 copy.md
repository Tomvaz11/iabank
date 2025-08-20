# AGV Prompt: OrchestratorHelper v3.0 (Lean e Granular)

**Tarefa Principal:** Analisar o `@Blueprint_Arquitetural.md`, que é a fonte única da verdade sobre a arquitetura. Suas responsabilidades são: (1) Derivar uma ordem de implementação lógica e (2) Gerar cenários chave para os Testes de Integração.

**Input Principal (Blueprint Arquitetural):**

## --- Conteúdo do Blueprint Arquitetural ---

[ADICIONE AQUI O CONTEÚDO DO BLUEPRINT]

**Diretrizes Essenciais:**

1. **Análise de Dependências em Duas Camadas:** A ordem deve ser determinada por duas análises sequenciais:

   a. **Primeiro, Módulos de Suporte Transversal (Cross-Cutting Concerns):** Analise o Blueprint e identifique os módulos que fornecem funcionalidades transversais, das quais outros módulos dependem para funcionar corretamente em tempo de execução, mesmo que não haja uma dependência de `import` direta. Exemplos incluem:

   - Configuração central (`core/settings`)
   - Autenticação e Autorização (`core/auth`)
   - Logging
   - Gerenciamento de Features (Feature Flags) \* Isolamento de Dados (Multi-tenancy)

   **Estes módulos de suporte transversal DEVEM ser implementados primeiro.**

   b. **Segundo, Dependências Diretas de Código:** Após ordenar os módulos de suporte, analise as dependências de `import` diretas entre os "Módulos Principais" restantes para definir a sequência final. Um módulo não pode ser implementado antes de suas dependências diretas.

2. **Criação do "Alvo 0":** Sua primeira tarefa é SEMPRE gerar um item inicial na ordem de implementação chamado **"Alvo 0: Setup do Projeto Profissional"**. Os detalhes do que este alvo implica estão definidos no prompt do Implementador (`F4`).

3. **Geração da Ordem Sequencial Única:** Após o "Alvo 0", crie uma lista numerada contendo os nomes completos dos "Módulos Principais". A sequência deve seguir a análise de dependências em duas camadas (suporte transversal primeiro, depois o resto). **O resultado final DEVE ser uma única lista numerada contendo todos os alvos, começando com o "Alvo 0".**

4. **Decomposição de Componentes Complexos (UI):** Ao analisar a Camada de Apresentação (UI), você **DEVE** usar a decomposição em Telas/Views/Componentes fornecida no Blueprint para criar alvos de implementação individuais e sequenciais (ex: `'fotix.ui.views.ScanSetupView'`, `'fotix.ui.views.ResultsView'`), em vez de um único alvo genérico `'fotix.ui'`.

5. **Identificação de Pontos de Teste de Integração (TI):**

   - Identifique grupos de módulos recém-listados que completam um "subsistema coerente" ou um "fluxo funcional significativo".
   - **Um grupo de módulos de suporte transversal (ex: auth, core) DEVE ser considerado um "subsistema coerente" e ter sua própria parada de testes de integração imediatamente após sua implementação.**
   - Após o último módulo de um desses grupos, insira um ponto de verificação no formato exato:
     `>>> PARADA PARA TESTES DE INTEGRAÇÃO (Nome do Subsistema em maiúsculas) <<<`

6. **Geração de Cenários de Teste de Integração:**

   - Para cada `>>> PARADA ... <<<` criada, você **DEVE** gerar uma seção detalhada logo abaixo dela.
   - Esta seção deve conter:
     - **Módulos no Grupo:** Liste os módulos principais implementados desde a última parada.
     - **Objetivo do Teste:** Descreva em uma frase clara o que se espera validar com a integração deste grupo, baseando-se nas responsabilidades combinadas dos módulos conforme o Blueprint.
     - **Cenários Chave:** Liste de 2 a 4 cenários de teste específicos e acionáveis que verifiquem as interações mais críticas entre os módulos do grupo.

7. **Simplicidade do Output:** O resultado final deve ser um documento Markdown contendo apenas as instruções para o Coordenador, a lista de Módulos Base, e a lista numerada da ordem de implementação com as paradas de teste detalhadas. **Não inclua descrições de módulos ou justificativas de ordem.** Essa informação reside exclusivamente no Blueprint.

**Resultado Esperado:**

Um documento Markdown (`Output_Ordem_e_Testes.md`) contendo a ordem de implementação e, para cada ponto de TI, os detalhes (Módulos, Objetivo, Cenários) para guiar a próxima fase de testes.
