# AGV Prompt: Geração de Cenários de Teste de Aceitação do Usuário (UAT) v1.4

**Tarefa Principal:** Com base **exclusivamente no Blueprint Arquitetural**, gerar uma lista detalhada de cenários de teste manuais (End-to-End). O objetivo é validar as funcionalidades da aplicação da perspectiva de um usuário final, cobrindo os fluxos de trabalho essenciais.

**Restrição Fundamental de Escopo:**

- Os cenários devem se ater **ESTRITAMENTE** às funcionalidades, capacidades e componentes de UI descritos no `@Blueprint_Arquitetural.md`.
- **NÃO INCLUA cenários para funcionalidades não descritas.** O objetivo é validar o que foi especificado.

**Fonte Única da Verdade (SSOT):**

- **Blueprint Arquitetural:** `@Blueprint_Arquitetural.md`
  - _(Instrução para Coordenador: Anexe o arquivo do Blueprint validado do projeto.)_

**Instruções Detalhadas para a IA:**

1. **Análise Focada do Blueprint:**

   - Estude o Blueprint para entender a arquitetura, os serviços de aplicação e, principalmente, a **decomposição da Camada de Apresentação (UI)** em Telas/Views.
   - Identifique os fluxos de usuário críticos que emergem da interação entre essas Telas/Views e os serviços de aplicação.

2. **Geração dos Cenários de Teste (Estrutura Mandatória):**

   - Para cada fluxo crítico, gere um cenário de teste seguindo a estrutura:
     - **ID do Cenário:** `UAT_[NOME_PROJETO_CURTO]_[XXX]`
     - **Título do Cenário:** Um nome claro e conciso.
     - **Fluxo Testado:** Descreva o fluxo do usuário (ex: "Configuração do Scan -> Execução -> Visualização de Resultados, etc.").
     - **Componentes do Blueprint Envolvidos:** Liste as principais Views e Serviços de Aplicação do Blueprint que são exercitados.
     - **Pré-condições:** Condições necessárias antes de iniciar o teste (ex: "Ter uma pasta com imagens duplicadas, "O usuário deve ter permissão de administrador", etc.").
     - **Passos para Execução:** Lista numerada e detalhada de ações do usuário na interface.
     - **Resultado Esperado:** O que o usuário deve observar no sistema após cada passo chave.
     - **Critério de Passagem:** Declaração concisa para determinar o sucesso do teste.

3. **Quantidade e Diversidade:**
   - Gere entre 8 e 12 cenários, cobrindo os principais fluxos de sucesso, tratamento de erros comuns (se inferíveis do design) e diferentes opções configuráveis.

**Formato do Output:**

- Apresente os cenários em Markdown, usando a estrutura detalhada.
