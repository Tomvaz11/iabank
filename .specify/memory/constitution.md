<!--
Relatório de Impacto da Sincronização:
- Mudança de versão: 5.1.1 → 5.2.0
- Princípios modificados:
  - Artigo XVIII: Governança da Constituição → Governança da Constituição e Fluxo Spec-Driven
- Seções adicionadas: Nenhuma
- Seções removidas: Nenhuma
- Templates sincronizados:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
- Follow-up TODOs: Nenhum
-->
# Constituição do Projeto IABANK

## Terminologia Normativa

Os termos **DEVE**, **NÃO DEVE**, **DEVERIA**, **PODE** e variações são usados conforme as definições da [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) e [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174). Sempre que aplicados nesta constituição, indicam obrigações vinculantes ou recomendações condicionadas a esses padrões.

## Seção I: Princípios de Desenvolvimento e Arquitetura

### Artigo I: Arquitetura e Stack Tecnológico
- **Descrição**: A arquitetura do sistema é um **Monolito Modular** com **Arquitetura em Camadas (Limpa)**, mantido em um **monorepo**. O stack tecnológico mandatório é:
    - **Backend**: **Django/DRF** sobre **PostgreSQL**.
    - **Frontend**: **React/TypeScript/Vite** seguindo o padrão **Feature-Sliced Design (FSD)**.
    - **Processamento Assíncrono**: **Celery** com **Redis** como broker.
- **Justificativa**: Define a fundação técnica do projeto, garantindo consistência e alinhamento com as decisões arquiteturais primárias.

### Artigo II: Modularidade e Simplicidade
- **Descrição**: Toda funcionalidade de negócio DEVE ser encapsulada em seu próprio "app" modular Django. A lógica de negócio DEVE seguir o padrão definido: regras simples nos Models/Managers; orquestrações complexas nos Serviços da Camada de Aplicação.
- **Justificativa**: Força um design modular, combate o over-engineering e alinha o desenvolvimento com a arquitetura definida.

### Artigo III: Imperativo de Teste-Primeiro (Test-First)
- **Descrição**: Isto é **NÃO-NEGOCIÁVEL**. Toda implementação DEVE seguir estritamente o TDD. Nenhum código de implementação deve ser escrito antes que os testes (unidade, integração, contrato) sejam escritos, validados e confirmados como FALHOS.
- **Justificativa**: Garante que o código atenda a especificações verificáveis e melhora o design.

### Artigo IV: Teste de Integração-Primeiro
- **Descrição**: Testes de integração DEVEM priorizar ambientes realistas, usando `factory-boy` para popular um banco de dados real e o cliente de teste do DRF para simular requisições HTTP.
- **Justificativa**: Assegura que os componentes funcionem juntos na prática, não apenas na teoria.

### Artigo V: Documentação e Versionamento
- **Descrição**: Toda API pública e decisão de arquitetura DEVE ser documentada. Todos os componentes e a API DEVEM seguir o **Versionamento Semântico (SemVer)**. A API DEVE ser versionada via URL (`/api/v1/`).
- **Justificativa**: Garante clareza, previsibilidade e facilita a manutenção.

## Seção II: Qualidade, Confiabilidade e Entrega

### Artigo VI: Engenharia de Confiabilidade e Capacidade (SRE)
- **Descrição**: A confiabilidade do sistema DEVE ser gerenciada através de **SLIs** e **SLOs** explícitos. **Orçamentos de Erro (Error Budgets)** DEVEM ser definidos e consumidos. A monitoração DEVE incluir p95/p99 de latência, throughput e saturação. O planejamento de capacidade e o **autoscaling** DEVEM ser orientados pelos SLOs definidos.
- **Justificativa**: Transforma a confiabilidade e a escalabilidade em métricas de engenharia gerenciáveis e quantificáveis.

### Artigo VII: Observabilidade
- **Descrição**: A observabilidade DEVE seguir o padrão **OpenTelemetry** com correlação ponta-a-ponta via **W3C Trace Context**. Logs DEVEM ser estruturados em JSON e ter informações PII mascaradas conforme o **ADR-010**. A instrumentação e os stacks obrigatórios (**structlog**, **django-prometheus**, **Sentry**) DEVEM obedecer ao guia operacional descrito no **ADR-012**.
- **Justificativa**: Garante um padrão moderno e seguro para o monitoramento proativo e a garantia do nível de serviço.

### Artigo VIII: Processo de Entrega Contínua
- **Descrição**: O desenvolvimento DEVE seguir o modelo **Trunk-Based Development**. As estratégias de release DEVEM ser seguras (Feature Flags, Canary, etc.). O desempenho do processo DEVE ser medido pelas **métricas DORA**.
- **Justificativa**: Promove a integração contínua, reduz o risco de deploys e foca na melhoria do fluxo de entrega de valor.

### Artigo IX: Qualidade e Performance do Código
- **Descrição**: Um pipeline de CI DEVE garantir: cobertura de testes de no mínimo **85%**; complexidade ciclomática máxima de **10**; formatação/linting; análise de segurança **SAST/DAST/SCA**; geração de **SBOM**; e um **gate de performance** (k6).
- **Justificativa**: Automatiza e impõe um alto padrão de qualidade, segurança e performance.

### Artigo X: Migrações Zero-Downtime
- **Descrição**: Alterações em esquemas de banco de dados DEVEM seguir o padrão **Parallel Change (expand/contract)** e utilizar operações não-bloqueantes (`CREATE INDEX CONCURRENTLY`).
- **Justificativa**: Garante a evolução contínua do sistema sem impacto para o usuário final.

## Seção III: Segurança e Governança

### Artigo XI: Governança de API
- **Descrição**: O design de APIs DEVE seguir o padrão **Contrato-Primeiro (OpenAPI 3.1)**. Erros DEVEM seguir o padrão **RFC 9457**. A API DEVE implementar **Rate Limiting** (`Retry-After`), **Idempotência** (`Idempotency-Key`) e **Controle de Concorrência** (`ETag`/`If-Match`). Chaves de idempotência DEVEM ser persistidas com TTL e deduplicação auditável para garantir replays seguros. Toda alteração de contrato DEVEM passar pelos pipelines de lint/diff e pelos testes de contrato Pact definidos no **ADR-011**.
- **Justificativa**: Cria APIs robustas, previsíveis e resilientes.

### Artigo XII: Segurança por Design (Security by Design)
- **Descrição**: A segurança é uma responsabilidade de todo o time, guiada pelos frameworks **OWASP ASVS/SAMM** e **NIST SSDF**. A gestão de segredos, a criptografia de campo para PII e o mascaramento de dados sensíveis em logs/traces DEVEM seguir o processo definido no **ADR-010**. O controle de acesso DEVE ser formalizado em uma matriz **RBAC/ABAC** e validado por testes. O frontend DEVE praticar a minimização de dados, aplicar **CSP** com nonce/hash e **Trusted Types**, além de proibir PII em URLs, conforme o **ADR-010**. Nos ambientes em que **Trusted Types** não estiver disponível, a equipe DEVE documentar a exceção, reforçar sanitização em sinks críticos e executar testes automatizados que demonstrem a mitigação.
- **Justificativa**: Incorpora a segurança em todas as fases do desenvolvimento, desde o design até a operação.

### Artigo XIII: Defesa de Dados Multi-Tenant e LGPD
- **Descrição**: O acesso a dados multi-tenant DEVE ser protegido com **Row-Level Security (RLS)** e, como defesa em profundidade, a lógica de acesso a dados DEVE utilizar **query managers** que apliquem o `tenant_id` por padrão. Políticas RLS DEVEM ser definidas via `CREATE POLICY`, versionadas e cobertas por testes automatizados que falham em acessos cruzados de tenant. A conformidade com a LGPD DEVE ser evidenciada por documentos (**RIPD/ROPA**) e o sistema DEVE suportar políticas de retenção e o **direito ao esquecimento**.
- **Justificativa**: Garante o isolamento de dados e a conformidade regulatória.

### Artigo XIV: Infraestrutura como Código (IaC) e GitOps
- **Descrição**: Toda a infraestrutura DEVE ser gerenciada como código via **Terraform**, com políticas validadas por **Policy-as-Code (OPA)**. As mudanças DEVEM ser aplicadas via **GitOps**, conforme definido no **ADR-009**.
- **Justificativa**: Garante uma infraestrutura auditável, reprodutível e segura.

### Artigo XV: Gestão de Dependências
- **Descrição**: A verificação e atualização de dependências DEVEM ser contínuas e automatizadas, utilizando a ferramenta definida no **ADR-008**.
- **Justificativa**: Reduz proativamente a superfície de ataque vinda de bibliotecas de terceiros.

### Artigo XVI: Auditoria e FinOps
- **Descrição**: A trilha de auditoria de eventos críticos DEVE ser armazenada em formato **WORM**, ter sua **integridade verificada** e sua política de acesso governada. A governança de custos DEVE ser praticada através de **tagging** e **budgets/alertas**.
- **Justificativa**: Garante a integridade das trilhas de auditoria e a responsabilidade financeira.

### Artigo XVII: Operações Proativas e Resiliência
- **Descrição**: Ciclos de **Threat Modeling (STRIDE/LINDDUN)** DEVEM ser realizados para identificar ameaças proativamente. A resiliência do sistema DEVE ser testada periodicamente através de **GameDays** e os **Runbooks** de incidentes DEVEM ser mantidos atualizados.
- **Justificativa**: Move a equipe de uma postura reativa para uma proativa em relação a riscos e falhas.

## Seção IV: Aplicação e Processo de Emenda

### Artigo XVIII: Governança da Constituição e Fluxo Spec-Driven
- **Fluxo Spec-Driven Development**: Toda entrega DEVE seguir o ciclo `/constitution → /specify → /clarify → /plan → /tasks`. Nenhum desenvolvimento DEVE iniciar enquanto `spec.md` não estiver aprovado e `plan.md` e `tasks.md` não refletirem as obrigações desta constituição. Cada artefato DEVE referenciar explicitamente os artigos aplicáveis e registrar pendências em `/clarify`.
- **Processo de Emenda**: Alterações nesta constituição DEVEM ser propostas via Architectural Decision Record (ADR) com análise de impacto, plano de mitigação e atualização coordenada dos templates afetados.
- **Versionamento da Constituição**: A numeração DEVE seguir SemVer. Mudanças que introduzem novos artigos ou obrigações implicam aumento MINOR; quebras ou remoções exigem MAJOR; ajustes editoriais permanecem em PATCH.
- **Rastreabilidade**: Ferramentas e implementações específicas para cumprir os artigos DEVEM ser detalhadas em ADRs, specs e planos com links recíprocos.
- **Conformidade**: Todos os membros da equipe e sistemas automatizados DEVEM defender esta constituição; violações DEVEM bloquear merges até saneamento evidenciado por testes e checklists.
- **Auditoria Periódica**: A aderência DEVE ser revisitada a cada trimestre ou quando um ADR crítico for aprovado, com registros publicados em `docs/runbooks/`.

**Versão**: 5.2.0 | **Ratificado**: 2025-10-02 | **Última Emenda**: 2025-10-08
