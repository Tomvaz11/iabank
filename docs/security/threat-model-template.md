# Threat Model Template — Fundação Frontend FSD

> Utilize este modelo para documentar threat modeling recorrente seguindo STRIDE (segurança) e LINDDUN (privacidade), conforme Art. XVII da Constituição e PR-001 do spec `002-f-10-fundacao`.

## Contexto
- **Release / Sprint**: <!-- ex.: v1.0 / Sprint 25 -->
- **Data da sessão**: <!-- yyyy-mm-dd -->
- **Facilitador(a)**: <!-- nome / capítulo -->
- **Participantes**: <!-- lista com squads -->
- **Escopo**: <!-- componentes, fluxos, integrações analisadas -->
- **Referências**: <!-- links para spec, ADRs, diagramas de arquitetura -->

## Arquitetura & Fluxos de Dados
- **Diagrama atualizado**: <!-- link para Miro/Excalidraw/Structurizr -->
- **Superfícies de ataque**: <!-- entry-points, APIs, jobs, storage -->
- **Dados sensíveis**: <!-- enumere PII/PCI, chaves, tokens -->
- **Dependências externas**: <!-- provedores, serviços terceiros -->

## Inventário de Ativos
| Ativo | Descrição | Confidencialidade | Integridade | Disponibilidade | Observações |
|-------|-----------|-------------------|-------------|-----------------|-------------|
| <!-- ex.: SPA React --> | | | | | |

## STRIDE — Ameaças de Segurança
| ID | Categoria (STRIDE) | Ativo / Fluxo | Descrição da ameaça | Vetor / Pré-condição | Impacto | Probabilidade | Mitigação proposta | Dono | Status |
|----|--------------------|---------------|----------------------|----------------------|---------|---------------|---------------------|------|--------|
| STR-001 | <!-- Spoofing / Tampering / Repudiation / Info Disclosure / DoS / Elevation --> | | | | | | | | |

## LINDDUN — Ameaças de Privacidade
| ID | Categoria (LINDDUN) | Dados afetados | Descrição da ameaça | Vetor / Cenário | Impacto (LGPD) | Mitigação proposta | Dono | Status |
|----|---------------------|---------------|----------------------|-----------------|----------------|---------------------|------|--------|
| LIN-001 | <!-- Linkability / Identifiability / Non-repudiation / Detectability / Disclosure of information / Unawareness / Non-compliance --> | | | | | | | |

## Controles Existentes
- **Controles preventivos**: <!-- ex.: CSP strict-dynamic, Trusted Types -->
- **Controles detectivos**: <!-- ex.: OTEL, dashboards SC-005 -->
- **Controles corretivos**: <!-- runbooks, planos de rollback -->

## Mitigation Status
| Ação | Owner | Prazo | Referência (issue/PR) | Status |
|------|-------|-------|------------------------|--------|
| <!-- alinhar com follow-ups STRIDE/LINDDUN --> | | | | |

## Gaps & Ações Prioritárias
- **Backlog**: <!-- issues que precisam ser abertas / referenciadas -->
- **Tags SC relevantes**: `@SC-005` <!-- adicionar outras se necessário -->
- **Observações**: <!-- riscos aceitos, dependências externas, etc. -->

## Evidências e Artefatos
- <!-- anexos, provas de execução (links de dashboards, PRs, pactos de risco) -->

## Aprovação
- **Segurança**: <!-- nome / data -->
- **Frontend Foundation Guild**: <!-- nome / data -->
- **SRE**: <!-- nome / data -->
