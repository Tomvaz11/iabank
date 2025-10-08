# CRIE O SISTEMA IABANK EXATAMENTE COMO DESCRITO NOS MEUS ARQUIVOS DE BLUEPRINT. SIGA COMPLETAMENTE TUDO O QUE É PEDIDO ABAIXO:

### Seu Papel e Tarefa
**Papel**: Analista de Produto + Facilitador Spec-Driven Development (SDD).
**Tarefa**: A partir dos anexos, extrair um índice de features (fatias verticais), auditar sua qualidade e gerar:
1. Prompts `/specify` para TODAS as features.
2. Uma lista de dúvidas para `/clarify` por feature.

### Anexos (Fonte da Verdade)
*   **[ANEXO_1]**: `./BLUEPRINT_ARQUITETURAL.md`
*   **[ANEXO_2]**: `./adicoes_blueprint.md`
*(Considere 100% do conteúdo dos anexos; ignore contexto prévio.)*

---

### Padrões e Regras Essenciais

#### Fluxo e Comandos
*   **Fluxo SDD**: `/constitution` → `/specify` → `/clarify` → `/plan` → `/tasks`.
*   **/specify**: Foco no "o quê/por quê" (requisitos). Proibido stack/arquitetura (isso pertence ao `/plan`).
*   **Incertezas**: Marcar sempre com `[NEEDS CLARIFICATION]`.

#### Quality Gates
*   **Vertical Slice**: Features devem entregar valor observável e autônomo (UI/API/Dados). Camadas (ex: "repositório") são *enablers*, não features.
*   **INVEST**: Auditar com I, N, V, E, S, T. Marcar **ATENÇÃO** se falhar em ≥2 critérios.
*   **DoR Mínima**: Cada item deve ter: persona, objetivo, valor de negócio, restrições, dependências e métrica de sucesso.
*   **Story Map**: Validar cobertura da jornada do usuário (atividades → passos → features).
*   **Critérios de Aceitação (ACs)**: Devem ser verificáveis (preferir formato BDD/Gherkin).

---

### Formato de Saída Obrigatório

**1. Índice de Features (Tabela)**
*   **Colunas**: ID, Nome da Feature, Persona, Valor de Negócio, Risco (reg/tec), Dependências, MVP/Pós-MVP, Observações.
*   **Priorização**: Valor alto + Risco alto primeiro.
*   **Incertezas**: Marcar com `[NEEDS CLARIFICATION]` na coluna Observações.

**2. Auditoria de Qualidade do Índice**
Para cada feature, avaliar:
*   **Alinhamento Spec-Kit**: OK/ATENÇÃO + justificativa (é vertical slice? cabe no spec?).
*   **INVEST**: Passe/falha por letra (I,N,V,E,S,T) + motivo.
*   **DoR**: Passe/falha para cada ponto da DoR Mínima.
*   **Story Map**: Posição na jornada; lacunas/sobreposições.

**3. Detalhamento das Features (com prompts `/specify`)**
Para cada feature:
*   **Contexto**: 1-2 frases sobre "o quê/por quê".
*   **ACs**: 5-8 bullets verificáveis (preferir BDD curta).
*   **Prompt `/specify`**: Texto pronto para o agente, exigindo:
    *   Referências explícitas aos 2 anexos.
    *   Uso do template spec-kit (escopo, histórias, ACs, métricas).
    *   Proibição de decisões de stack.
    *   Marcação `[NEEDS CLARIFICATION]` para dúvidas.

**4. Dúvidas para `/clarify` (por feature)**
*   Lista de perguntas objetivas (negócio, regulatório, edge cases) com opções propostas para trade-offs.

**5. Riscos & Dependências**
*   Mapa de dependências entre features.
*   Tabela de riscos (regulatórios/técnicos) e suas mitigações.

**6. Plano de Execução Anotado**
*   Ordem de implementação de TODAS as features, justificando por dependência e valor.
*   Anotar explicitamente o conjunto MVP e os incrementos subsequentes (v1.1, v2.0).
*   Reforçar o handshake: `/specify` → `/clarify` → `/plan` → `/tasks` por feature.

---

### Estilo e Comportamento
*   **Tom**: Objetivo, claro, conciso (usar bullets).
*   **Fidelidade**: Ater-se 100% aos anexos. Incertezas devem ser marcadas com `[NEEDS CLARIFICATION]`, nunca inventadas.

### Critérios de Aceite (Meu Pedido)
*   **Entregáveis**: Índice priorizado, Auditoria de qualidade, prompts `/specify` para todas as features, listas `/clarify` associadas, e clareza sobre o fluxo `/plan`/`/tasks`.

### Notas para a IA
*   **Enablers**: Identificar (infra/camada) e relacionar a features de valor.
*   **Splitting**: Sugerir divisão para features grandes (com nomes/critérios).
*   **Bloqueios**: Elevar dúvidas críticas que bloqueiam a especificação e propor opções.

### Formato Final
*   **Saída**: Apenas as 6 seções de saída, em Markdown.

### (Referências recentes do Spec-Kit, para você IA alinhar a análise)

* GitHub Blog — *Spec-driven development using Markdown…* (fluxo com **/specify** focado no “o quê/por quê”; integração com agentes). ([The GitHub Blog][1])
* GitHub Blog — *Get started with the open-source toolkit* (bootstrap via `uvx … specify init` e uso de **/specify** no agente). ([The GitHub Blog][3])

**FIQUE A VONTADE PARA CONSULTAR A WEB NO QUE PRECISAR**