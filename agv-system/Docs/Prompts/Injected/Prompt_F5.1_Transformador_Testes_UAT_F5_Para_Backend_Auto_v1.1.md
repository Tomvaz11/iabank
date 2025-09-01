# AGV Prompt: Tradução de Cenários UAT para Testes de Backend Automatizados (Pytest) v1.1

**Tarefa Principal:** Analisar os cenários de teste de aceitação do usuário (UAT) e o Blueprint Arquitetural para gerar scripts de teste `pytest` correspondentes. Estes testes devem validar a funcionalidade descrita interagindo **diretamente com os serviços da camada de aplicação e infraestrutura (backend)**, sem usar a UI.

**Fontes da Verdade (SSOT):**

1. **Cenários UAT para Tradução:** `@Output_Cenarios_UAT_Testes_Manuais_v1.0.md`
2. **Blueprint Arquitetural:** `@Output_BluePrint_Arquitetural_Tocrisna_v1.0.md`
3. **Código Fonte do Projeto:** `CONSULTAR A CODEBASE` (Acesso ao workspace para referências de implementação)

**Instruções Detalhadas para a IA:**

1. **Análise Combinada:**

   - Para cada cenário UAT, traduza os "Passos para Execução" em uma sequência de chamadas aos serviços da **Camada de Aplicação** (`ScanningService`, `ActionService`, etc.) conforme descrito no Blueprint.
   - Consulte o Blueprint para entender como instanciar esses serviços e quais dependências (interfaces) eles exigem.

2. **Geração de Scripts de Teste `pytest`:**

   - Para cada cenário Uat, crie uma ou mais funções de teste `pytest`.
   - Use fixtures `pytest` e implementações "Fake" (se disponíveis no contexto) ou "Mocks" para simular as dependências de infraestrutura (I/O de disco, etc.), permitindo um teste controlado do backend.

3. **Implementação de Cada Teste `pytest`:**

   - **a. Setup:** Configure o ambiente de teste em memória (usando Fakes/Mocks) para satisfazer as "Pré-condições" do UAT.
   - **b. Instanciação:** Instancie os serviços da camada de aplicação, injetando as dependências fake/mockadas.
   - **c. Execução:** Chame os métodos dos serviços de aplicação para executar a lógica funcional do cenário.
   - **d. Asserções:** Verifique os "Resultados Esperados" através de asserções programáticas sobre o estado dos fakes/mocks ou os valores retornados pelos serviços.

4. **Boas Práticas:**
   - Mantenha os testes independentes e use nomes descritivos.
   - Siga as convenções de estilo do Python (PEP 8).

**Formato do Output:**

- Gere o(s) arquivo(s) `.py` contendo os scripts de teste `pytest` completos e executáveis.
