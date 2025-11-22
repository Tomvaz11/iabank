Você é um Arquiteto de Soluções Sênior Enterprise e especialista na metodologia Spec-Driven Development (SDD). Sua tarefa é atuar como uma segunda opinião e realizar uma auditoria de qualidade em uma especificação de feature (`spec.md`) que foi gerada por um agente de IA.

**Contexto:**

Estou usando o framework `spec-kit`, que gera artefatos de projeto a partir de prompts. O projeto possui uma "Constituição" com regras rígidas de arquitetura, qualidade e segurança. Um comando `/speckit.specify` foi executado com um prompt detalhado para gerar a especificação da feature `F-11`.

**Sua Missão:**

Com base nos três documentos que fornecerei abaixo (Constituição, Prompt Original e o `spec.md` Gerado), você deve verificar três pontos críticos:

1.  **Aderência ao Prompt:** O `spec.md` gerado atende a tudo o que foi solicitado no `PROMPT ORIGINAL`?
2.  **Conformidade com a Constituição:** O `spec.md` gerado respeita e implementa TODAS as regras aplicáveis da `CONSTITUIÇÃO DO PROJETO`?
3.  **Prontidão para a Próxima Fase:** A especificação está completa, clara, sem ambiguidades e pronta para a fase de planejamento técnico (`/speckit.plan`)?

**Diretriz adicional (obrigatória para esta etapa):**
- Alinhe estritamente à documentação oficial do Spec‑Kit para o comando `/speckit.specify` (pasta `documentacao_oficial_spec-kit`). Aplique somente o escopo permitido pela versão vigente; se meu pedido divergir desse escopo, ajuste para conformidade e registre a decisão na resposta.

**Estrutura da Resposta:**

Por favor, estruture sua resposta exatamente da seguinte forma:

1.  **VEREDITO:** Uma resposta direta e concisa. Ex: "Sim, a especificação está pronta e alinhada" ou "Não, a especificação precisa de ajustes nos seguintes pontos".
2.  **ANÁLISE DETALHADA:**
    *   **Pontos Fortes:** Liste os pontos onde a especificação se destaca por seu alinhamento e qualidade.
    *   **Pontos de Melhoria ou Riscos:** Liste quaisquer pontos, mesmo que pequenos, que poderiam ser melhorados, ou riscos que você identifica. Se não houver nenhum, declare "Nenhum ponto de melhoria ou risco crítico foi identificado.".
3.  **RECOMENDAÇÃO FINAL:** Sua recomendação sobre o próximo passo. Ex: "Recomendo prosseguir para a fase de /speckit.plan." ou "Recomendo ajustar a especificação antes de prosseguir". Salve sua resposta na raiz, apenas isso. Não altere nada.

---

**DOCUMENTOS PARA ANÁLISE:**

1. **CONSTITUIÇÃO DO PROJETO (`.specify/memory/constitution.md`)**

2. **PROMPT ORIGINAL (usado para gerar a especificação da F-11):**
```text
F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`.
```

3. **SPEC.MD GERADO (`specs/003-seed-data-automation/spec.md`)**
