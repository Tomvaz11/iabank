Você é um Arquiteto de Soluções Sênior Enterprise e especialista na metodologia Spec-Driven Development (SDD). Sua tarefa é atuar como uma segunda opinião e realizar uma auditoria de qualidade em uma especificação de feature (`spec.md`) que foi gerada por um agente de IA.

**Contexto:**

Estou usando o framework `spec-kit`, que gera artefatos de projeto a partir de prompts. O projeto possui uma "Constituição" com regras rígidas de arquitetura, qualidade e segurança. Um comando `/speckit.specify` foi executado com um prompt detalhado para gerar a especificação da feature `F-01`.

**Sua Missão:**

Com base nos três documentos que fornecerei abaixo (Constituição, Prompt Original e o `spec.md` Gerado), você deve verificar três pontos críticos:

1.  **Aderência ao Prompt:** O `spec.md` gerado atende a tudo o que foi solicitado no `PROMPT ORIGINAL`?
2.  **Conformidade com a Constituição:** O `spec.md` gerado respeita e implementa TODAS as regras aplicáveis da `CONSTITUIÇÃO DO PROJETO`?
3.  **Prontidão para a Próxima Fase:** A especificação está completa, clara, sem ambiguidades e pronta para a fase de planejamento técnico (`/speckit.plan`)?

**Estrutura da Resposta:**

Por favor, estruture sua resposta exatamente da seguinte forma:

1.  **VEREDITO:** Uma resposta direta e concisa. Ex: "Sim, a especificação está pronta e alinhada" ou "Não, a especificação precisa de ajustes nos seguintes pontos".
2.  **ANÁLISE DETALHADA:**
    *   **Pontos Fortes:** Liste os pontos onde a especificação se destaca por seu alinhamento e qualidade.
    *   **Pontos de Melhoria ou Riscos:** Liste quaisquer pontos, mesmo que pequenos, que poderiam ser melhorados, ou riscos que você identifica. Se não houver nenhum, declare "Nenhum ponto de melhoria ou risco crítico foi identificado.".
3.  **RECOMENDAÇÃO FINAL:** Sua recomendação sobre o próximo passo. Ex: "Recomendo prosseguir para a fase de /speckit.plan." ou "Recomendo ajustar a especificação antes de prosseguir". 
4.  Salve sua resposta (relatório desta auditoria) em `specs/004-f-01-tenant-rbac-zero-trust/arquivo_morto_historico/arquivados_specify`, apenas isso. Não altere nada.

---

**DOCUMENTOS PARA ANÁLISE:**

1. **CONSTITUIÇÃO DO PROJETO (`.specify/memory/constitution.md`)**

2. **PROMPT ORIGINAL (usado para gerar a especificação da F-01):**
```text
F-01 Governanca de Tenants e RBAC Zero-Trust. Use BLUEPRINT_ARQUITETURAL.md §§2,3.1,6.2,19 e adicoes_blueprint.md itens 4,5,12,13. Produza a especificacao seguindo o template oficial (contexto, historias, requisitos, metricas, riscos) sem definir stack adicional. Garanta RLS com `CREATE POLICY` e binding de sessao, RBAC+ABAC com testes automatizados, MFA obrigatoria, auditoria WORM, controle de concorrencia com `ETag`/`If-Match`, versionamento `/api/v1`, refresh tokens seguros (`HttpOnly`/`Secure`/`SameSite=Strict`) e Problem Details (RFC 9457), alinhado aos Arts. III, V, IX, XIII. Marque duvidas criticas com [NEEDS CLARIFICATION] e inclua BDD para ativacao de tenant, bloqueio cross-tenant, versionamento de roles, MFA/refresh seguro, atributos de autorizacao e logs S3 Object Lock, referenciando OpenAPI 3.1 contract-first.
```

3. **SPEC.MD GERADO (`specs/004-f-01-tenant-rbac-zero-trust/spec.md`)**