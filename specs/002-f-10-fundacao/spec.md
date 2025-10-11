# Feature Specification: F-10 Fundacao Frontend FSD e UI Compartilhada

**Feature Branch**: `002-f-10-fundacao`  
**Created**: 2025-10-11  
**Status**: Draft  
**Input**: User description: "F-10 Fundacao Frontend FSD e UI Compartilhada. Referencie BLUEPRINT_ARQUITETURAL.md §4, docs de design system internos e adicoes_blueprint.md itens 1,2,13. Produza especificacao detalhando scaffolding FSD, Storybook/Chromatic, integrações com TanStack Query/Zustand, propagacao de OTEL no cliente, pactos FE/BE e critérios de acessibilidade. Reforce o uso de Tailwind CSS como base oficial do design system (conforme blueprint), permitindo theming multi-tenant via tokens personalizados. Inclua métricas de cobertura visual, lint FSD, governança de imports, prevenção de PII em URLs/telemetria e política CSP rigorosa (nonce/hash + Trusted Types)"

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituicao v5.2.0 (Art. I-XVIII) e ADRs aplicaveis. Toda lacuna deve ser marcada com `[NEEDS CLARIFICATION]` e adicionada ao `/clarify`.

## Contexto

Sem uma fundacao FSD padronizada, cada squad frontend cria estruturas distintas, alongando lead time e ampliando risco de regressao visual e de compliance multi-tenant. Esta feature estabelece o scaffolding oficial descrito no Blueprint §4, alinha o design system interno (Tailwind CSS como base) e garante que Storybook/Chromatic, TanStack Query, Zustand e pactos FE/BE funcionem como guard rails de entrega (adicoes itens 1 e 2). Tambem reforca controles de privacidade exigidos no item 13 (PII e CSP), preservando aderencia regulatoria enquanto acelera a entrega de novas features.

## Hipoteses

- A documentacao interna do design system provê tokens base, diretrizes de acessibilidade e matriz de componentes obrigatorios por persona.
- Ambientes de CI ja executam jobs obrigatorios descritos em `docs/pipelines/ci-required-checks.md`, permitindo adicionar lint FSD, Chromatic e pactos como gates adicionais.
- Os tenants pivô (Piloto e Producao) possuem variações de branding aprovadas que podem ser convertidas em tokens Tailwind sem violar contraste WCAG 2.2 AA.

## User Scenarios & Testing *(mandatorio)*

*As historias DEVEM ser fatias verticais independentes (INVEST) e testaveis de forma isolada. Mantenha o foco na jornada do usuario/persona e descreva como cada cenario prova o valor entregue.*

### User Story 1 - Scaffolding FSD Convergente (Prioridade: P1)

- **Persona & Objetivo**: Tech Lead Frontend quer criar novas features multi-tenant rapidamente sem reescrever fundacao.
- **Valor de Negocio**: Reduz lead time (DORA) e evita divergencias arquiteturais que encarecem manutencao.
- **Contexto Tecnico**: Frontend SPA, estrutura FSD (`app/pages/features/entities/shared`), lint de imports, roteamento multi-tenant.

**Independent Test**: Fluxo validado por teste de scaffolding que gera nova feature, roda lint FSD, unit tests e valida metrica de tempo fim-a-fim.

**Acceptance Scenarios (BDD)**:
1. **Dado** tenants Alfa e Beta existentes e o repositório aderente ao Blueprint §4, **Quando** o Tech Lead executa o scaffolding padrao para `loan-tracking`, **Entao** a estrutura `app/pages/features/entities/shared` é criada com arquivos iniciais de TanStack Query e Zustand, registrando a feature no roteador multi-tenant e passando lint FSD em < 5 minutos.
2. **Dado** a politica de governanca de imports ativa, **Quando** um desenvolvedor tenta importar um componente `pages` diretamente de `shared/ui`, **Entao** o lint falha a build, gera evidencias no CI e bloqueia o merge ate que a arquitetura FSD seja respeitada.

### User Story 2 - Design System Multi-tenant Observavel (Prioridade: P2)

- **Persona & Objetivo**: Designer System Owner precisa garantir consistencia visual e acessibilidade entre tenants.
- **Valor de Negocio**: Mantem experiencia uniforme e acessivel, reduzindo retrabalho de marca e suporte.
- **Contexto Tecnico**: Storybook + Chromatic, Tailwind CSS com tokens customizados por tenant, automacoes de cobertura visual e auditoria WCAG.

**Independent Test**: Pipeline de Chromatic/Storybook executando cenarios para cada tenant, com auditoria automatizada de contraste e navegabilidade via teclado.

**Acceptance Scenarios (BDD)**:
1. **Dado** tokens de marca aprovados para tenants Alfa e Beta, **Quando** um componente `shared/ui/Button` é publicado no Storybook, **Entao** as variacoes de tema geram capturas por tenant, alcançam cobertura visual >= 95% no Chromatic e registram estados documentados no design system interno.
2. **Dado** as diretrizes WCAG 2.2 AA do design system, **Quando** um componente com falha de contraste ou sem rotulos acessiveis é submetido, **Entao** os testes de acessibilidade bloqueiam o pipeline, apontando o componente e registrando nao conformidade para acao corretiva.

### User Story 3 - Telemetria, Pactos e Controles de Privacidade (Prioridade: P3)

- **Persona & Objetivo**: Gestor de Observabilidade e Compliance precisa garantir rastreabilidade ponta a ponta sem vazamentos de PII.
- **Valor de Negocio**: Permite resposta rapida a incidentes, assegura aderencia ao item 13 das adicoes e evita sanções LGPD.
- **Contexto Tecnico**: OpenTelemetry no cliente, W3C Trace Context, Pactos FE/BE, CSP com nonce/hash e Trusted Types.

**Independent Test**: Suite de contratos e testes de telemetria que injeta trace headers, exercita fluxos felizes/tristes e valida politicas de CSP/Trusted Types via scanner automatizado.

**Acceptance Scenarios (BDD)**:
1. **Dado** uma sessao autenticada com tenant Alfa e trace-id emitido pelo backend, **Quando** o frontend inicia uma interacao que consome TanStack Query, **Entao** o trace context e propagado aos spans do cliente, correlacionado com eventos back-end e pactos FE/BE aprovam os contratos de payload sem discrepancias.
2. **Dado** as politicas de CSP com nonce/hash + Trusted Types e o bloqueio de PII em URLs ou telemetria, **Quando** o frontend tenta enviar dados com CPF ou email em consultas, **Entao** o request e barrado, o evento e mascarado nos logs OTEL e o pipeline CI registra falha obrigando correcao antes do deploy.

### Edge Cases & Riscos Multi-Tenant

- Tema de tenant ausente ou tokens inconsistentes devem cair em fallback neutro validado por acessibilidade e registro no backlog de marca.
- Requests sem `tenant_id` ou com tenant invalido no Zustand devem redirecionar para selecao segura e emitir alerta observavel.
- Picos de deploy simultaneo entre tenants nao podem degradar cobertura Chromatic nem invalidar pactos ativos (reprocessamento automatico).
- Falha nos jobs de lint FSD, Chromatic ou pactos deve bloquear merge e acionar playbook de incidentes front-end.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do codigo, cobrindo trajetorias felizes/tristes | Scaffolding gera suites iniciais (unit, accessibility, contratos) e o CI falha PR sem evidencias atualizadas. |
| Art. VIII (Entrega) | Estrategia de release segura (feature flag/canary/rollback) | Storybook/Chromatic funcionam como canary visual, releases usam feature flags por tenant e rollback desabilita temas sem tocar codigo core. |
| Art. IX (CI) | Cobertura >=85 %, complexidade <=10, SAST/DAST/SCA, SBOM, k6 | Adiciona gates para lint FSD, cobertura visual >=95%, auditoria de PII e gera SBOM do frontend junto aos checks existentes. |
| Art. XI (API) | Contratos OpenAPI 3.1 + Pact atualizados, RFC 9457 | Pactos FE/BE garantem aderencia aos schemas gerados do OpenAPI e exercitam erros padrao RFC 9457. |
| Art. XIII (LGPD/RLS) | Enforcar RLS, managers, retencao/direito ao esquecimento | UI impede troca de tenant sem reset seguro, remove PII de URLs/telemetria e expõe informativos LGPD consistentes por tenant. |
| Art. XVI (FinOps) | Custos rastreados, tags e budgets atualizados | Controla execucoes Chromatic/CI via orcamento, rastreia custo de snapshots e reporta uso nas metricas DORA/FinOps. |
| ADR-010/011/012 | Seguranca de dados, governanca de API, observabilidade | Aplicacao das mascaras PII, pactos obrigatorios e spans OTEL alinhados aos ADRs. |
| Outros | Adicoes items 1, 2 e 13; Blueprint §4; design system interno | Conecta DORA lead time, SLO de UX, regras de privacidade no front e tokens Tailwind oficiais conforme docs internos. |

### Functional Requirements

- **FR-001**: O scaffolding FSD deve criar automaticamente estrutura `app/pages/features/entities/shared`, arquivos base de Storybook, hooks de TanStack Query e store Zustand, concluindo em <= 10 minutos com relatorio de sucesso.
- **FR-002**: Politicas de lint FSD devem impedir imports cruzados fora das camadas definidas, bloquear ciclos e exigir aliases aprovados, com relatorios por PR.
- **FR-003**: Cada nova feature deve registrar cenarios em Storybook/Chromatic para todos os tenants ativos, garantindo cobertura visual >= 95% e documentando variações obrigatorias.
- **FR-004**: O design system deve usar Tailwind CSS como base, expondo tokens personalizaveis por tenant (cores, tipografia, espaco) com fallback padrao auditado.
- **FR-005**: Integracoes com TanStack Query devem incluir cache, invalidacao e estrategias de refetch definidas por tenant, enquanto Zustand centraliza estado global (tema, usuario, feature flags) com testes de concorrencia.
- **FR-006**: Pactos FE/BE devem validar contratos de leitura e mutacao prioritarios, cobrindo campos obrigatorios, erros padrao e aplicando verificacao automatica no CI.
- **FR-007**: Telemetria do cliente deve propagar trace context OTEL, mascarar atributos sensiveis e incluir tags obrigatorias (`tenant_id`, persona, feature) sem expor PII.
- **FR-008**: Auditorias de acessibilidade (WCAG 2.2 AA) devem executar em Storybook, bloqueando merges que nao atendam contraste, navegabilidade e leitura por leitores de tela.
- **FR-009**: Politicas CSP com nonce/hash e Trusted Types devem ser configuraveis por ambiente e testadas automaticamente, bloqueando recursos nao autorizados e registrando incidentes.

### Non-Functional Requirements

- **NFR-001 (SLO)**: Lead time para disponibilizar nova feature frontend deve permanecer < 30 horas uteis p95, com erro orcamentario registrado no painel DORA em caso de desvio.
- **NFR-002 (Performance)**: UX deve manter LCP p95 < 2.5 s e TTI p95 < 3 s para tenants principais com rede 4G, monitorado por testes sinteticos periodicos.
- **NFR-003 (Observabilidade)**: Spans OTEL do cliente devem cobrir >90% das interacoes criticas e estar correlacionados com logs/metricas do backend seguindo W3C Trace Context.
- **NFR-004 (Seguranca)**: Nenhuma URL, cookie ou evento de telemetria pode conter PII; CSP deve bloquear inline scripts nao autorizados; Trusted Types habilitado em navegadores suportados.
- **NFR-005 (FinOps)**: Execucoes de Chromatic, artefatos Storybook e pipelines front-end devem permanecer dentro do budget mensal aprovado, com alertas quando consumo atingir 80%.

### Dados Sensiveis & Compliance

- Catalogar campos sensiveis exibidos no frontend (CPF, email, telefone) e garantir mascaramento/obfuscacao conforme papel do usuario.
- Monitorar continuamente logs OTEL e pactos para assegurar ausencia de PII em URLs, parametros ou atributos de telemetria.
- Documentar cadencia de revisao CSP/Trusted Types e anexar evidencias de testes trimestrais aos runbooks de seguranca.
- Registrar conformidade LGPD (RIPD/ROPA) para qualquer novo componente que exponha dados pessoais, incluindo trilha de consentimento por tenant.

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- **SC-001**: Tempo medio para gerar e publicar uma nova feature FSD (scaffolding + pipelines verdes) reduzido para < 1 hora p95 em squads pilotos.
- **SC-002**: Cobertura visual documentada >= 95% para componentes criticos e regressao visual < 2% por release.
- **SC-003**: 100% dos fluxos catalogados possuem contratos frontend-backend aprovados antes de cada deploy.
- **SC-004**: Indicador de conformidade WCAG 2.2 AA >= 98% para estados UI avaliados nos tenants ativos.
- **SC-005**: Zero incidentes de vazamento de PII em URLs/telemetria e CSP violacoes por trimestre, auditado via runbooks.

Associe cada criterio aos testes ou dashboards que validam o resultado.

## Outstanding Questions & Clarifications

- Nenhuma. Especificacao preparada para `/speckit.plan`.
