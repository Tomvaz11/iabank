# Feature Specification: F-11 Automacao de Seeds e Dados de Teste

**Feature Branch**: `[003-seed-data-automation]`  
**Created**: 2025-11-14  
**Status**: Draft  
**Input**: User description: "F-11 Automacao de Seeds, Dados de Teste e Factories. Referencie BLUEPRINT_ARQUITETURAL.md §§3.1,6,26, adicoes_blueprint.md itens 1,3,8,11 e Constituicao Art. III/IV. Escreva especificacao contemplando comandos `seed_data`, factories `factory-boy`, mascaramento de PII, integração com CI/CD, Argo CD e testes de carga. Inclua critérios para validação automatizada das seeds, anonimização, suportes a DR, parametrização de volumetria (Q11) por ambiente/tenant e geração de datasets sintéticos sem quebrar RateLimit/API `/api/v1`."

> Referencias obrigatorias: `BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`, Constituicao v5.2.0 (Art. I-XVIII) e ADRs aplicaveis. Toda lacuna deve ser marcada com `[NEEDS CLARIFICATION]` e adicionada ao `/clarify`.

## Contexto

Hoje os ambientes do IABANK (desenvolvimento, homologacao, performance e DR) dependem de dados de teste ad-hoc ou scripts manuais, o que dificulta reproduzir bugs, validar cenarios multi-tenant e manter consistencia com o modelo de dominio descrito no `BLUEPRINT_ARQUITETURAL` (§§3.1 e 6). Esta feature define um mecanismo padronizado e automatizado de seeds (`seed_data`), factories de dados de teste (alinhadas ao uso de `factory-boy` na base atual) e geracao de datasets sinteticos para testes de carga, conectado aos pipelines de CI/CD e GitOps (Argo CD) e ao plano de DR (§26 e §27). O objetivo de negocio e reduzir o tempo para preparar ambientes, garantir conformidade com LGPD (mascaramento/anonimizacao de PII) e permitir testes de carga controlados sem violar as politicas de RateLimit da API `/api/v1` nem os SLOs definidos em `adicoes_blueprint` (itens 1, 3, 8 e 11).

## User Scenarios & Testing *(mandatorio)*

*As historias DEVEM ser fatias verticais independentes (INVEST) e testaveis de forma isolada. Mantenha o foco na jornada do usuario/persona e descreva como cada cenario prova o valor entregue.*

### User Story 1 - Seeds automatizadas por ambiente/tenant (Prioridade: P1)

- **Persona & Objetivo**: Engenheiro(a) de plataforma ou desenvolvedor(a) precisa provisionar rapidamente dados de teste consistentes para um novo ambiente ou tenant, sem scripts manuais.  
- **Valor de Negocio**: Reduz lead time de criacao de ambientes, evita divergencias de dados entre tenants e garante que todos os fluxos criticos possam ser testados de forma repetivel.  
- **Contexto Tecnico**: Ambientes multi-tenant com banco compartilhado, integrados a pipelines de CI/CD e GitOps que executam um comando padronizado de seeds (`seed_data`) logo apos o provisionamento da infraestrutura.

**Independent Test**: Executar o comando de seeds em um ambiente recem-criado em CI, verificar a volumetria por tenant e rodar a suite de testes de integracao/contrato sem necessidade de ajustes manuais de dados.

**Acceptance Scenarios (BDD)**:
1. **Dado** um ambiente de desenvolvimento ou homologacao recem-criado, com tenants configurados e banco vazio, **Quando** o pipeline de CI/CD ou o time de plataforma executa o comando padronizado de seeds (`seed_data`) informando o perfil de volumetria (por exemplo, `dev`, `staging`, `perf`) e os tenants alvo, **Entao** o ambiente fica populado com dados consistentes por tenant (clientes, emprestimos, parcelas, transacoes, usuarios), com contagens esperadas por entidade e tenant registradas em relatorio de execucao, e todos os testes automatizados de integracao e contrato relacionados a esses dominios passam sem ajustes manuais de dados.
2. **Dado** um ambiente que ja foi seedado anteriormente, **Quando** o comando de seeds e executado novamente com o mesmo perfil de volumetria, **Entao** a operacao e idempotente (nenhum registro de negocio e duplicado, chaves unicas por tenant continuam validas), o relatorio de execucao destaca reuso vs. criacao de registros, e qualquer erro de consistencia faz o comando falhar de forma clara sem deixar o ambiente em estado parcialmente populado.

### User Story 2 - Dados de teste anonimizados e seguros (Prioridade: P1)

- **Persona & Objetivo**: Responsavel por seguranca/LGPD e QA precisa garantir que dados de teste nao revelem PII real, mesmo quando derivados de snapshots de producao.  
- **Valor de Negocio**: Reduz risco de vazamento de dados pessoais em ambientes nao produtivos, mantendo a aderencia a LGPD sem prejudicar a qualidade dos testes.  
- **Contexto Tecnico**: Seeds e factories geram apenas dados sinteticos ou derivados de forma irreversivelmente anonimizados, com regras claras de mascaramento alinhadas ao mapeamento de PII nos modelos multi-tenant.

**Independent Test**: Executar seeds/anonymizacao em um snapshot de producao mascarado, aplicar ferramentas automatizadas de deteccao de PII (regex/padroes) e amostragem manual e comprovar ausencia de dados pessoais reais.

**Acceptance Scenarios (BDD)**:
1. **Dado** um conjunto de modelos de dominio que contem PII/PD (ex.: clientes, enderecos, contatos, usuarios), **Quando** o comando de seeds e/ou o processo de geracao de dados de teste e executado para um ambiente nao produtivo, **Entao** nenhum campo classificado como PII/PD guarda valores reais (todos sao sinteticos ou anonimizados de forma irreversivel), ha documentacao das regras de mascaramento por campo e as verificacoes automatizadas de PII nao encontram correspondencias com dados reais.
2. **Dado** um pedido de auditoria de dados de teste por parte do time de seguranca ou compliance, **Quando** sao analisados registros de banco, logs, metricas e trilhas de auditoria associados aos ambientes preparados via seeds, **Entao** nao sao encontrados dados pessoais reais, as politicas de RLS por tenant continuam vigentes e ha evidencias rastreaveis de que as regras de anonimização e mascaramento foram aplicadas e validadas.

### User Story 3 - Datasets sinteticos para testes de carga e DR (Prioridade: P2)

- **Persona & Objetivo**: Engenheiro(a) de SRE/performance precisa gerar datasets de alto volume para testes de carga e cenarios de DR, sem violar limites de consumo da API e sem comprometer SLOs.  
- **Valor de Negocio**: Permite planejar capacidade, validar SLOs e exercitar o plano de DR com dados realistas, evitando surpresas em producao.  
- **Contexto Tecnico**: Ambientes dedicados de performance/DR, configuracoes de volumetria (Q11) por ambiente/tenant, pipelines de performance integrados a seeds para gerar dados antes dos testes.

**Independent Test**: Em um ambiente de performance, executar seeds com perfil de alta volumetria, rodar o plano de testes de carga e verificar que as metas de throughput, taxa de erros e respeito a RateLimit/API sao atingidas.

**Acceptance Scenarios (BDD)**:
1. **Dado** um ambiente de performance com multiplos tenants configurados, **Quando** o pipeline de testes de carga executa o mecanismo de seeds/factories com um perfil de volumetria elevado (por exemplo, milhares de emprestimos e transacoes por tenant), **Entao** o sistema alcanca os objetivos de throughput definidos (ex.: operacoes por minuto por tenant), a taxa de respostas indicando limite de API excedido permanece abaixo de um limiar acordado, e e possivel ajustar a volumetria por ambiente/tenant sem alterar codigo.
2. **Dado** um cenario de ativacao do plano de Disaster Recovery com promocao de ambiente secundario, **Quando** a infraestrutura e recriada e o mecanismo de seeds e acionado no novo ambiente (aplicando as configuracoes versionadas de volumetria e tenants alvo), **Entao** os dados sinteticos necessarios para smoke tests, testes de carga iniciais e validacao de isolamento multi-tenant sao reconstruidos dentro dos RPO/RTO definidos no blueprint, permitindo comprovar que o ambiente de DR esta apto a receber trafego.

### Edge Cases & Riscos Multi-Tenant

- Seeds executadas sem `tenant_id` definido ou para tenants inexistentes DEVEM falhar de forma explicita, sem criar registros "sem dono" ou vazando dados entre tenants.  
- Execucoes concorrentes do comando de seeds para o mesmo ambiente/tenant (por exemplo, disparadas por pipelines diferentes) DEVEM ser coordenadas de forma a evitar condicoes de corrida, duplicacao em massa ou bloqueios prolongados em recursos compartilhados.  
- Seeds de alta volumetria em ambientes compartilhados (como staging) DEVEM respeitar limites de capacidade e RateLimit existentes, evitando que um tenant ou pipeline monopolize recursos e comprometa os SLOs de outros tenants.  
- Em cenarios de restauracao de backup ou DR, a reaplicacao de seeds DEVEM preservar a integridade de dados existentes e nunca reintroduzir PII real em ambientes de teste.

## Requirements *(mandatorio)*

### Constituicao & ADRs Impactados

| Artigo/ADR | Obrigacao | Evidencia nesta feature |
|------------|-----------|-------------------------|
| Art. III (TDD) | Testes antes do codigo, cobrindo trajetorias felizes/tristes | Seeds, factories e validadores de PII so podem ser introduzidos junto com testes automatizados que falham antes da implementacao (unitarios, integracao, contratos e testes de carga dirigidos pelos cenarios desta especificacao). |
| Art. IV (Teste de Integracao-Primeiro) | Priorizar testes de integracao com banco real e factories | User Stories 1–3 exigem uso consistente de factories para popular banco real em testes de integracao e contrato, inclusive para cenarios multi-tenant, anonimização de PII e RateLimit/API. |
| Art. VIII (Entrega) | Estrategia de release segura (feature flag/canary/rollback) | Execucao de seeds e geracao de datasets e controlada por configuracoes por ambiente/tenant e integrada aos pipelines, permitindo ativar/desativar perfis de volumetria e cenarios de carga sem risco para producao. |
| Art. IX (CI) | Cobertura >=85 %, complexidade <=10, SAST/DAST/SCA, SBOM, gate de performance em testes de carga | Pipelines passam a incluir estagios que executam seeds, validam anonimizacao de dados de teste e rodam testes de carga contra datasets sinteticos; qualquer falha nessas etapas quebra o build. |
| Art. XI (API) | Contratos OpenAPI 3.1 + Pact atualizados, RFC 9457 | Dados de teste e de carga sao gerados em aderencia aos contratos da API `/api/v1` e utilizados em testes de contrato, garantindo que endpoints e limites de erro padronizados sejam respeitados. |
| Art. XIII (LGPD/RLS) | Enforcar RLS, managers, retencao/direito ao esquecimento | Campos PII/PD sao mapeados, mascarados ou anonimizados antes de uso em ambientes de teste; seeds respeitam RLS por tenant e ha evidencias de que dados sensiveis nao aparecem em ambientes nao produtivos. |
| Art. XVI (FinOps) | Custos rastreados, tags e budgets atualizados | Perfis de volumetria por ambiente/tenant (Q11) sao definidos com limites de custo e sao acompanhados por relatorios de uso, evitando que testes de carga extrapolem budgets aprovados. |
| ADR-010/011/012 | Seguranca de dados, governanca de API, observabilidade | Seeds e datasets sinteticos produzem telemetria suficiente para auditar anonimização de PII, consumo de API e impactos em SLIs/SLOs, alinhados aos ADRs de seguranca e observabilidade. |
| Outros | BLUEPRINT_ARQUITETURAL §§3.1, 6, 26; adicoes_blueprint itens 1,3,8,11 | Mecanismos de seeds e factories seguem o modelo de dados canonico, estrategia de gerenciamento de dados e processamento assincrono, praticas de entrega continua, plano de performance/load testing e diretrizes de FinOps. |

Remova linhas nao aplicaveis apenas se justificar o motivo. Itens pendentes ficam com `[NEEDS CLARIFICATION]`.

### Functional Requirements

- **FR-001**: O sistema DEVE disponibilizar um comando padronizado de seeds (`seed_data` ou equivalente) capaz de popular ambientes suportados (desenvolvimento, homologacao, performance e DR) com dados consistentes por tenant a partir de configuracoes declarativas, de forma idempotente, registrando em relatorio a volumetria gerada por entidade e tenant e o perfil utilizado.  
- **FR-002**: DEVE existir um catalogo unico de factories de dados de teste, alinhado ao modelo de dominio descrito no `BLUEPRINT_ARQUITETURAL` (§3.1), de modo que para cada entidade utilizada nos cenarios desta feature exista pelo menos uma factory reutilizavel em testes unitarios, integracao, contratos e seeds.  
- **FR-003**: Todos os dados de teste gerados por seeds/factories para ambientes nao produtivos DEVEM ser totalmente sinteticos ou anonimizados de forma irreversivel; campos PII/PD (por exemplo, nome, documento, e-mail, telefone) DEVEM seguir regras explicitas de mascaramento/anonimizacao, validadas automaticamente por verificacoes de padroes e amostragens.  
- **FR-004**: A execucao de seeds e a geracao de datasets DEVE estar integrada aos pipelines de CI/CD e ao fluxo de GitOps (Argo CD ou equivalente), de forma que a criacao/atualizacao de ambientes (incluindo review apps e ambientes de DR) acione automaticamente o comando de seeds apropriado e falhe o deploy quando a validacao de dados nao for bem-sucedida.  
- **FR-005**: A volumetria de dados de teste (Q11) DEVE ser parametrizavel por ambiente e por tenant (por exemplo, perfis `small`, `medium`, `large`), com parametros versionados junto ao codigo e claramente documentados, permitindo reproduzir um mesmo cenario de carga em diferentes execucoes e ambientes.  
- **FR-006**: A geracao e o uso de datasets sinteticos para testes de carga DEVEM respeitar as politicas de consumo das APIs publicas e de RateLimit definidas na governanca de API, garantindo que a taxa de respostas de limite excedido permaneça abaixo de um limiar acordado e que seja possivel ajustar cenarios de teste para diferentes limites por ambiente/tenant.  
- **FR-007**: O mecanismo de seeds DEVE oferecer suporte explicito a cenarios de recuperacao de desastre (DR), permitindo reprovisionar rapidamente dados de teste minimos (smoke) e de carga apos restauracao ou recriacao de um ambiente, de forma compativel com os RPO/RTO definidos no plano de DR.

### Non-Functional Requirements

- **NFR-001 (SLO)**: A preparacao de dados de teste via seeds e validacoes automatizadas DEVE ocorrer em tempo previsivel; em 95% dos deploys de desenvolvimento e homologacao, ambientes recem-criados DEVEM ficar prontos para testes (dados criados e verificacoes concluidas) em ate 10 minutos a partir do acionamento do comando de seeds.  
- **NFR-002 (Performance)**: O mecanismo de seeds e o catalogo de factories DEVEM suportar os niveis de volumetria planejados para ambientes de performance, permitindo gerar datasets suficientes para atingir as metas de throughput e latencia definidas nos SLOs, sem causar timeouts excessivos ou saturacao permanente de recursos compartilhados.  
- **NFR-003 (Observabilidade)**: Todas as execucoes de seeds, geracao de datasets e validacoes de PII DEVEM produzir logs, metricas e, quando aplicavel, eventos de rastreabilidade suficientes para identificar falhas, acompanhar volumetria gerada por ambiente/tenant e comprovar que PII foi mascarada/anonimizada, sem expor dados sensiveis nos proprios logs.  
- **NFR-004 (Seguranca)**: O uso de dados de teste DEVE obedecer ao mapeamento de classificacao de dados (PII/PD) e as politicas de LGPD, garantindo que dados reais nao sejam copiados para ambientes nao produtivos e que acessos a datasets de teste sigam os mesmos principios de menor privilegio aplicados a dados de producao.  
- **NFR-005 (FinOps)**: A combinacao de execucoes de seeds, criacao de ambientes efemeros e testes de carga DEVE operar dentro dos budgets de custo por ambiente/tenant definidos em FinOps, com visibilidade clara do custo incremental associado a dados de teste em relatorios de custo da nuvem.

### Dados Sensiveis & Compliance

- Mapear explicitamente, com base no modelo de dominio, quais campos utilizados pelas seeds e factories contem PII/PD (por exemplo, nomes, documentos, contatos, identificadores de dispositivo) e quais nao contem.  
- Definir e documentar regras de mascara/anonimizacao por campo e por tipo de dado, incluindo como tratar chaves de negocio (ex.: documentos, e-mails) de forma a manter unicidade por tenant sem permitir reidentificacao, adotando anonimização forte e irreversivel resistente a reidentificacao mesmo com correlacao de multiplas bases.  
- Garantir que politicas de retencao, direito ao esquecimento e RLS permaneçam validas tambem em ambientes nao produtivos, incluindo a limpeza segura de datasets de teste quando ambientes sao desprovisionados ou quando determinados tenants deixam de existir.  
- Registrar evidencias (como relatorios de execucao, auditorias e resultados de scanners de PII) que demonstrem a aplicacao das regras acima, para uso em revisoes de LGPD e auditorias internas.

## Assumptions

- Seeds completas (dados de negocio) serao utilizadas apenas em ambientes nao produtivos (desenvolvimento, homologacao, performance e DR), enquanto producao utilizara apenas seeds tecnicas estritamente necessarias (por exemplo, configuracoes iniciais e usuarios de sistema), sem seeds de dados de negocio mesmo sinteticos, com essa politica evidenciada nas politicas de mudanca e playbooks de release.  
- Os perfis de volumetria (Q11) serao inicialmente definidos em termos de ordens de grandeza (small/medium/large) por tipo de entidade e ajustados iterativamente a partir dos resultados dos testes de carga, adotando referencia inicial: dev/homologacao com small≈50, medium≈200 e large≈500 registros por entidade/tenant; performance com small≈5.000, medium≈20.000 e large≈50.000 registros por entidade/tenant; o custo incremental mensal de seeds e testes de carga deve permanecer em ate 10% do budget aprovado de cada ambiente/tenant.  
- Testes de carga intensivos serao executados em ambientes dedicados ou janelas controladas, evitando impacto em usuarios reais e respeitando as politicas de RateLimit da plataforma.

## Success Criteria *(mandatorio)*

### Metricas Mensuraveis

- **SC-001**: Em 95% dos deploys de desenvolvimento e homologacao, ambientes recem-criados que utilizam o comando de seeds com perfil padrao ficam prontos para execucao da suite automatizada (dados criados e validacoes concluidas) em ate 10 minutos, sem intervencao manual.  
- **SC-002**: 100% das User Stories desta especificacao possuem pelo menos um teste automatizado associado (unitario, integracao, contrato ou carga) que falha quando o comportamento esperado de seeds, anonimização de PII ou respeito a RateLimit/API e quebrado.  
- **SC-003**: Em auditorias periodicas de dados de teste, nenhuma amostra analisada apresenta PII real, e as ferramentas automatizadas de deteccao de PII reportam taxa de falsos positivos/negativos dentro dos limites acordados com seguranca (por exemplo, menos de 5% de falsos negativos em amostras controladas).  
- **SC-004**: Em ambientes de performance, pelo menos um cenario de teste de carga com datasets sinteticos atinge os objetivos de throughput e latencia definidos para as APIs criticas de negocio, com taxa de respostas associadas a limite de consumo inferior a 1% durante o periodo de teste, salvo cenarios explicitamente desenhados para exercitar RateLimit.  
- **SC-005**: O custo incremental mensal de execucao de seeds, criacao de ambientes efemeros e testes de carga permanece dentro dos budgets aprovados por ambiente/tenant, conforme medicao em relatorios de custo, sem necessidade de cortes emergenciais de escopo de teste.

Associe cada criterio aos testes ou dashboards que validam o resultado.

## Outstanding Questions & Clarifications

- [Escopo/Ambientes] Limite de uso de seeds em producao: apenas seeds tecnicas estritamente necessarias (por exemplo, configuracoes iniciais e usuarios de sistema), sem seeds de dados de negocio mesmo sinteticos, com essa politica registrada nas politicas de mudanca.  
- [Privacidade/LGPD] Nivel de rigor para anonimização: adotar anonimização forte e irreversivel resistente a reidentificacao mesmo com correlacao de multiplas bases.  
- [Volumetria/FinOps] Perfis de volumetria iniciais: dev/homologacao com small≈50, medium≈200 e large≈500 registros por entidade/tenant; performance com small≈5.000, medium≈20.000 e large≈50.000 registros por entidade/tenant; custo incremental mensal de seeds e testes de carga limitado a ate 10% do budget de cada ambiente/tenant.

## Clarifications

### Session 2025-11-14

- Q: Qual o nivel de rigor esperado para os mecanismos de anonimização (por exemplo, pseudonimizacao suficiente para testes internos ou anonimização forte resistente a reidentificacao mesmo em cenarios de correlacao de dados)? → A: Adotar anonimização forte e irreversivel resistente a reidentificacao mesmo com correlacao de multiplas bases.  
- Q: Ha algum uso permitido de seeds de dados sinteticos de negocio diretamente em producao (por exemplo, para smoke tests pos-deploy), e, se sim, com quais limites e evidencias de mudanca? → A: Producao utiliza apenas seeds tecnicas estritamente necessarias, sem seeds de dados de negocio mesmo sinteticos, com essa politica evidenciada nas politicas de mudanca.  
- Q: Quais faixas numericas iniciais (por tipo de entidade) definem small/medium/large por ambiente/tenant e quais limites de custo mensais sao aceitaveis para execucoes recorrentes de testes de carga? → A: Dev/homologacao small≈50, medium≈200, large≈500 registros por entidade/tenant; performance small≈5.000, medium≈20.000, large≈50.000; custo incremental mensal limitado a ate 10% do budget de cada ambiente/tenant.
