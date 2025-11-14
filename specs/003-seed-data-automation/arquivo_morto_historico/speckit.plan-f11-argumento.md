PARA EXECUTAR O /SPECKIT.PLAN PRIMEIRO PRECISAMOS EXTRAIR DOS BLUEPRINTS OS ARGUMENTOS NECESSARIOS PARA GERAR O PLAN DA SPEC (FUNCIONALIDADE) ALVO. CRIEI O PROMPT QUE RESOLVEU O PROBLEMA, PEGUE O RESULTADO DELE E COLE COMO ARGUMENTO QUANDO EXECUTAR O COMANDO.

=========

```markdown
# PROMPT — Agente Extrator de Argumentos para /speckit.plan

## Identidade e Objetivo

Você é um Agente Especialista em Planejamento Técnico do Spec-Kit, criado para ler um Blueprint/PRD e a especificação funcional alvo (spec.md da feature) e produzir **um único parágrafo em linguagem natural** que servirá **exatamente** como argumento do comando `/speckit.plan`. Seu foco é destilar **direção técnica** (arquitetura, stack, persistência, APIs, integrações, implantação, restrições, etc.). Não automatize nada, não crie comandos, não formate como lista.

## Entradas (fornecerei em anexo)

- **SPEC ALVO (spec.md da feature)** entre `<<<SPEC>>>` e `<<<FIM_SPEC>>>` — Exemplo: objetivos, escopo, critérios de aceitação, etc.
- **BLUEPRINT/PRD** entre `<<<PRD>>>` e `<<<FIM_PRD>>>` — Exemplo: visão arquitetural, padrões, escolhas tecnológicas preferenciais, etc.
- **Opcional (se houver)**: Constituição/Guidelines entre `<<<CONST>>>` e `<<<FIM_CONST>>>` — Exemplo: princípios, restrições, convenções, etc.

## Regras de Extração

- **Priorize o contexto funcional da SPEC ALVO** para entender exatamente **o que** a feature demanda e **onde** o plano técnico deve incidir; use o Blueprint/PRD (e Constituição, se houver) para **fundamentar a direção técnica**. Em conflitos, preferir instruções explícitas e recentes da SPEC ALVO; quando o Blueprint/PRD trouxer diretrizes técnicas gerais (Exemplo: monólito modular, camadas, etc.), concilie com a SPEC ALVO.
- **Extraia somente direção técnica** que influencia o plano: Arquitetura (Exemplo: monólito modular em camadas, SPA/SSR/CSR, event-driven, etc.), Frontend (Exemplo: framework, bundler, SSR opcional, etc.), Backend/Runtime (Exemplo: linguagem, framework, padrão MVC/ports-and-adapters, etc.), Banco de Dados e Persistência (Exemplo: Postgres/SQLite, ORM, migrações, upload evitado ou não, etc.), APIs/Contratos/Tempo real (Exemplo: REST/GraphQL/WebSocket/SignalR, recursos centrais, etc.), Integrações externas (Exemplo: pagamentos, e-mail, etc.), Implantação/Infra (Exemplo: Docker local, cloud X, quickstart, etc.), Restrições/Preferências (Exemplo: minimizar bibliotecas, conformidade Y, etc.).
- **Não invente nada**. Se um item essencial não estiver especificado (Exemplo: SGBD), **não chute**; use formulações neutras como “banco de dados a confirmar”, “tempo real a confirmar”, “ORM a confirmar”, etc.
- **Não repita conteúdo funcional** (user stories, regras de negócio, etc.) a não ser quando necessário para qualificar uma decisão técnica (Exemplo: “exige streaming em tempo real, portanto WebSocket”, etc.).

## Formato de Saída (obrigatório)

- Produza **apenas um parágrafo**, se possível, em **linguagem natural**, sem listas, sem bullets, sem quebras extras, sem blocos de código, sem aspas desnecessárias, pronto para ser colado **logo após** `/speckit.plan `.
- O texto deve cobrir, de forma concisa e conectada, os pontos técnicos relevantes: Arquitetura, Frontend, Backend, Banco de Dados/Persistência, APIs/Protocolos, Integrações (se houver), Implantação/Infra (se aplicável), Restrições/Preferências. Use conectores simples (Exemplo: “;”, “,”, “e”, “com”, etc.) e termos como “Exemplo”, “etc.” apenas quando útil para **evitar engessamento**.
- **Não inclua** o literal “/speckit.plan”, títulos, rótulos como “ARGUMENTO:”, comentários, observações, perguntas de clarificação, placeholders entre colchetes, ou qualquer instrução operacional (Exemplo: não falar de `SPECIFY_FEATURE`).
- **Não inclua** "estrategias de implementação" ou "listas de tarefas".

## Qualidade e Consistência

- Garanta que o parágrafo final **reflete estritamente** o que está nas entradas. Em caso de lacuna crítica, prefira “a confirmar” em linguagem natural, etc.
- Mantenha concisão e completude técnica ao mesmo tempo (Exemplo: “Monólito modular em camadas com Frontend Vite+React possivelmente com SSR; Backend Node.js com Fastify; APIs REST cobrindo recursos X, Y, Z conforme a feature; persistência em Postgres com ORM a confirmar; evitar upload externo quando possível, metadados no DB; execução local com Docker e opção de implantação em cloud; preferir poucas bibliotecas, etc.”).

## Agora processe as entradas e responda somente com o parágrafo final em linguagem natural, pronto para ser colado como argumento do comando /speckit.plan, sem qualquer texto adicional.

---

RESULTADO:

A automação de seeds e dados de teste deve ser desenhada dentro do monolito modular Django/DRF sobre PostgreSQL já existente, respeitando a arquitetura em camadas e o modelo de domínio único descrito no Blueprint (incluindo multi-tenant com banco compartilhado e RLS por tenant), com um comando padronizado seed_data (management command Django) idempotente que lê configurações declarativas versionadas no monorepo para popular, por ambiente (desenvolvimento, homologação, performance e DR) e por tenant, volumetrias parametrizáveis small/medium/large alinhadas às faixas de Q11 (ordem de dezenas a centenas de registros por entidade/tenant em dev/hom e milhares a dezenas de milhares em performance), registrando relatórios de execução por entidade/tenant e permitindo reexecução segura inclusive em cenários de restauração/DR; o backend deve centralizar um catálogo único de factories de dados de teste com factory-boy, alinhado aos modelos do §3.1, usado de forma consistente em testes unitários, de integração, contrato e carga, seguindo estritamente o imperativo de TDD e o princípio de teste de integração-primeiro da Constituição (tests com banco real e cliente DRF) para validar seeds, anonimização de PII, comportamento multi-tenant e respeito a RateLimit/API; toda geração de dados de teste para ambientes não produtivos deve produzir apenas dados sintéticos ou derivados irreversivelmente anonimizados, com mapeamento explícito de campos PII/PD, regras de mascaramento/anonimização fortes (inclusive para chaves de negócio), uso combinado de pgcrypto e RLS conforme as diretrizes de segurança/LGPD, evidências automatizadas de verificação (scanners de PII, amostragem, relatórios) e logs estruturados sem vazamento de dados sensíveis, enquanto produção permanece restrita a seeds técnicas estritamente necessárias, sem seeds de negócio mesmo sintéticas; para volumetrias elevadas e geração de datasets de carga, o plano deve prever uso opcional de tarefas assíncronas com Celery/Redis conforme a estratégia do §26 (idempotência, backoff, DLQ), mantendo o banco PostgreSQL como fonte de verdade e evitando saturação de recursos, e integrar a execução de seeds/anonimização/datasets aos pipelines de CI/CD e GitOps (Argo CD + Terraform), de modo que a criação/atualização de ambientes (incluindo review apps e ambientes de DR) acione estágios de seeds, validação de dados e testes de carga (k6/Gatling ou equivalente) com gates claros de aprovação baseados em SLOs de preparação de ambiente (por exemplo, dados prontos em até 10 minutos em 95% dos deploys de dev/hom), métricas DORA, SAST/DAST/SCA, SBOM e políticas de migração zero-downtime; os datasets sintéticos devem ser usados para testes funcionais, de contrato e de performance contra a API REST `/api/v1` versionada por URL, em aderência ao contrato OpenAPI 3.1, testes Pact e governança de API (erros RFC 9457, RateLimit com 429/Retry-After e cabeçalhos RateLimit-*), garantindo que testes de carga respeitem limites de consumo por ambiente/tenant e preservem os SLOs, enquanto a observabilidade das execuções de seeds, verificações de PII e uso de APIs é instrumentada com OpenTelemetry, W3C Trace Context, métricas/traces/logs estruturados e Sentry para permitir auditoria e correlação ponta a ponta, e o consumo de recursos decorrente de seeds, ambientes efêmeros e testes de carga é controlado dentro dos budgets e práticas de FinOps definidos, sem alterar a arquitetura do frontend React/TypeScript/Vite em FSD, que continua consumindo a API `/api/v1` e apenas se beneficia de dados de teste mais consistentes e previsíveis.

---

INTERAÇÕES/PERGUNTAS DE CONFIRMAÇÃO:

Agora, quero que você audite o plano de implementação que voce gerou e os arquivos de detalhes da implementação.
Sua missão é avaliar se os documentos do plano (plan.md, data-model.md, etc.) contêm informações suficientemente claras e detalhadas para que uma sequência de tarefas de implementação possa ser gerada sem ambiguidades.
Em vez de listar as tarefas, aponte as áreas que estão vagas ou que carecem de detalhes para a criação de um plano de tarefas. Por exemplo, se uma parte da implementação não está bem detalhada, me diga qual é e por que ela precisa de mais informações antes de virar uma tarefa.

---

# Prompt Reutilizável — Auditoria do Fluxo `/speckit.plan`

> Use este texto como primeira mensagem para uma IA auditora quando estiver no diretório do projeto (mesmo ambiente desta interação). O prompt assume:
> - A **branch atual** do repositório corresponde à feature a ser auditada.
> - O comando `/speckit.plan` já foi executado para essa branch e todos os artefatos foram gerados.
> - O ambiente contém os mesmos arquivos do repositório (nenhum upload adicional é necessário).

---

Olá! Preciso que você audite o artefato gerado pela etapa `/speckit.plan` da feature que está ativa na branch atual deste repositório.

## Objetivo
Verificar se a documentação produzida por `/speckit.plan` está completa e consistente o suficiente para que, na sequência, possamos gerar `/speckit.tasks` sem ambiguidades. A auditoria deve apontar qualquer lacuna ou risco antes de seguir para a fase de tarefas/implementação.

## Contexto do Projeto (fixo)
- Projeto IABANK (monorepo com backend Django/DRF sobre PostgreSQL, frontend React/TypeScript/Vite, Celery/Redis, etc.).
- Constituição IABANK v5.2.0 (Art. I–XVIII) rege arquitetura, segurança, observabilidade, governança de API e fluxo Spec-Driven.
- Fluxo esperado: `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → implementação.

## Entradas para Análise (já disponíveis no repo)
- `specs/<feature>/spec.md`
- `specs/<feature>/plan.md`
- `specs/<feature>/research.md`
- `specs/<feature>/data-model.md`
- `specs/<feature>/contracts/` (OpenAPI/Pact gerados na etapa)
- `specs/<feature>/quickstart.md`
- `AGENTS.md` (contexto de agentes)
- Quaisquer referências citadas nos documentos (ex.: `BLUEPRINT_ARQUITETURAL.md`, `docs/design-system/tokens.md`, ADRs, voce conseguira ver exatamente tudo o que foi gerado pelo Git). Esses arquivos já estão no repositório; consulte-os conforme necessário.

> Nota: a feature corresponde ao diretório em `specs/` cujo nome combina com a branch atual (ex.: branch `002-f-10-fundacao` → `specs/002-f-10-fundacao/`).

## O que analisar
1. **Consistência**: As decisões em `plan.md`, `data-model.md`, `contracts/` e `quickstart.md` refletem corretamente os requisitos e clarificações do `spec.md`?
2. **Lacunas para `/speckit.tasks`**: Existe alguma parte vaga ou sem detalhes suficientes (testes, migrações expand/contract, mapeamentos backend/frontend, políticas de segurança, etc.) que impediria gerar tarefas claras?
3. **Conformidade Constitucional**:
   - Art. III (TDD)
   - Art. VIII (Lançamento Seguro)
   - Art. IX (Pipeline CI)
   - Art. XI (Governança de API)
   - Art. XIII (Multi-tenant & LGPD)
   - Art. XVIII (Fluxo Spec-Driven)
4. **Governança/Security/Observabilidade**: CSP, Trusted Types, OTEL, RLS, PII masking, rate limiting, tags `@SC-xxx`, etc., possuem instruções acionáveis?

## Formato esperado da resposta
```
### Findings Bloqueantes
1. arquivo:linha — descrição do problema, impacto na geração de tasks

### Findings Menores
...

### Sugestões
...

### Validação Constitucional
- Art. III (TDD): ✅/⚠️ — comentário
- Art. VIII (Lançamento Seguro): ...
- Art. IX (Pipeline CI): ...
- Art. XI (Governança de API): ...
- Art. XIII (Multi-tenant & LGPD): ...
- Art. XVIII (Fluxo Spec-Driven): ...

### Conclusão
- Plano pronto para `/speckit.tasks`? Sim/Não — justificativa
```

## Regras
- Não gerar código nem tarefas; apenas análise.
- Sempre que possível, cite `arquivo:linha` usando caminhos relativos.
- Responda em português.

---

TODAS ESSAS ESSAS VERIFICAÇÕES DEVEM SER FEITAS PARA GARANTIR O SUCESSO, MESMO TENDO O COMANDO NOVO "ANALYSE" DEPOIS DE EXECUTAR /TASKS. EU SEMPRE FAÇO AS MESMAS VERIFICAÇÕES VARIAS VEZES COM IAS E MODELOS DE IAS DIFERENTES PARA ALCANÇAR O MAXIMO DE SUCESSO.
