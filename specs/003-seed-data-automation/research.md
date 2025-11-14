# Research – F-11 Automacao de Seeds e Dados de Teste

Este documento consolida decisões de pesquisa para a feature F-11 com base em `specs/003-seed-data-automation/spec.md`, na Constituição v5.2.0 e nos blueprints (`BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`).  
Cada tópico resolve itens marcados como `[NEEDS CLARIFICATION]` em `plan.md` e registra decisões com racional e alternativas.

---

## 1. Posicionamento do comando `seed_data` no monolito

**Decision**  
Implementar o comando padronizado `seed_data` como um management command Django em `backend/apps/foundation/management/commands/seed_data.py`, orquestrando seeds de todos os apps (incluindo tenants) e reutilizando o comando existente `backend/apps/tenancy/management/commands/seed_foundation_tenants.py` como sub-etapa ou serviço interno.

**Rationale**  
- `foundation` já concentra serviços transversais (idempotência, métricas), o que facilita aplicar padrões de idempotência, observabilidade e logging estruturado em todas as etapas de seeds.  
- Manter `seed_data` em `foundation` evita acoplá-lo a um domínio específico (tenancy), refletindo o papel de orquestrador de ambientes multi-tenant e não apenas de criação de tenants.  
- Reutilizar o comando `seed_foundation_tenants` reduz retrabalho e mantém compatibilidade com fluxos existentes de criação de tenants, respeitando a modularidade da arquitetura em camadas (Art. I/II).  
- Centralizar a orquestração num único comando reduz a chance de divergência entre scripts de seeds manuais e a automação padrão, além de simplificar a integração com pipelines CI/CD e GitOps.

**Alternatives considered**  
- **Colocar `seed_data` em `backend/apps/tenancy`**: facilitaria o foco em multi-tenant, mas acoplaria a orquestração de dados de negócio (clientes, contratos, transações) a um app mais técnico de tenancy, violando parcialmente o espírito de `foundation` como base transversal. Rejeitado em favor de uma visão mais geral.  
- **Criar um novo app `seeding` dedicado**: aumentaria a fragmentação do monolito e introduziria um novo módulo apenas para orquestração, o que contraria o princípio de simplicidade (Art. II) e a preferência por evoluir apps existentes. Rejeitado para evitar complexidade estrutural desnecessária.

---

## 2. Particionamento de filas Celery e limites de concorrência para seeds/datasets

**Decision**  
Definir filas dedicadas para workloads de seeds e carga, com os seguintes perfis:  
- Fila `seed_data_default`: usada para seeds assíncronas em dev/hom, com concorrência limitada (por exemplo, 1–2 workers por ambiente) e batches pequenos.  
- Fila `seed_data_perf`: usada para volumetrias grandes e ambientes de performance/DR, com concorrência configurável via setting (`SEED_DATA_MAX_CONCURRENCY`) e controles de batch para evitar saturar o PostgreSQL.  
O comando `seed_data` oferecerá modos síncrono e assíncrono; o modo assíncrono enviará tarefas idempotentes para essas filas com backoff e DLQ.

**Rationale**  
- Separar filas de seeds das filas de processamento de negócio evita que grandes cargas de seeds degradem o processamento de pedidos reais ou testes críticos, aderindo a SLOs e FinOps.  
- Filas dedicadas permitem aplicar políticas de concorrência distintas por ambiente (dev/hom vs perf/DR), alinhando volumetria Q11 e limites de custo (≈10% de budget incremental).  
- O uso de tarefas idempotentes, backoff e DLQ segue as diretrizes do §26 e reaproveita os padrões de idempotência já presentes em `backend/apps/foundation/idempotency.py`.  
- Manter ambos os modos (síncrono/assíncrono) permite que ambientes pequenos/efêmeros usem seeds rápidas inline no pipeline, enquanto ambientes de performance/DR utilizam processamento mais robusto em background.

**Alternatives considered**  
- **Reutilizar apenas a fila Celery padrão**: simplifica configuração, mas mistura workloads de seeds com tarefas de negócio, aumentando risco de saturação e violação de SLOs, especialmente durante testes de carga. Rejeitado por conflitar com metas de SRE (Art. VI, IX).  
- **Executar apenas seeds síncronas**: evitaria Celery/Redis, mas escalaria mal para volumetrias grandes, alongando demais o tempo de deploy em ambientes de performance/DR e violando o SLO de “dados prontos em ~10 minutos”. Rejeitado para não limitar a escalabilidade.

---

## 3. Formato e local dos arquivos declarativos de seeds

**Decision**  
Armazenar configurações declarativas de seeds em arquivos YAML versionados sob `backend/apps/foundation/seeds/config/`, com estrutura hierárquica por ambiente e perfil de volumetria, por exemplo:  
- `backend/apps/foundation/seeds/config/dev/small.yaml`  
- `backend/apps/foundation/seeds/config/dev/medium.yaml`  
- `backend/apps/foundation/seeds/config/dev/large.yaml`  
- `backend/apps/foundation/seeds/config/perf/small.yaml` (etc.)  
Cada arquivo definirá, por entidade e por tenant, a volumetria-alvo e flags de comportamento (por exemplo, habilitar dados adicionais para testes de carga de endpoints específicos). O comando `seed_data` aceitará parâmetros de ambiente/tenant/perfil (`--env`, `--tenant`, `--profile`) e derivará o arquivo YAML correspondente, com opção de override via variável de ambiente.

**Rationale**  
- YAML oferece boa legibilidade para humanos e suporte a estruturas aninhadas, comentários e valores ricos, o que é útil para equipes de plataforma/QA ajustarem volumetrias e flags sem alterar código Python.  
- Manter as configs dentro de `backend/apps/foundation/` mantém a proximidade com o código de orquestração de seeds, simplificando importação e empacotamento, ao mesmo tempo em que respeita o monorepo e evita espalhar configurações críticas em múltiplos diretórios.  
- A estratificação por ambiente (`dev`, `hom`, `perf`, `dr`) e perfil (`small`, `medium`, `large`) encaixa diretamente as faixas de Q11 e simplifica a integração com pipelines, que podem apenas informar `--env`/`--profile`.  
- A possibilidade de override via variável de ambiente permite cenários especiais (review apps, testes específicos) sem inflar a matriz de arquivos.

**Alternatives considered**  
- **JSON**: mais simples de parsear, mas menos amigável para edição manual e sem comentários, o que é um problema para configs complexas de seeds. Rejeitado em favor de YAML.  
- **TOML**: boa legibilidade, mas menos comum no ecossistema Django para este tipo de configuração, e não traz benefícios claros sobre YAML neste contexto. Rejeitado por evitar adicionar mais diversidade de formatos.  
- **Configs em `infra/` ou `docs/`**: manteria uma separação forte entre infra e app, mas aumentaria a distância entre seeds e código que as consome, dificultando testes locais e empacotamento. Rejeitado em favor de proximidade com o app `foundation`.

---

## 4. Ferramentas e estratégia para verificação de PII/anonimização

**Decision**  
Adotar uma combinação de scanner de PII baseado em padrões + amostragem automatizada, integrada à suíte de testes de segurança sob `tests/security/`, com pelo menos:  
- Testes automatizados (`tests/security/test_pii_scanner_seeds.py`) que percorrem amostras de registros gerados por `seed_data` e verificam ausência de padrões típicos de PII brasileira (CPF/CNPJ, e-mails, telefones, CEPs/endereço, nomes reais se houver listas de referência).  
- Funções utilitárias de mascaramento/anonimização centralizadas no app `foundation` (por exemplo, `backend/apps/foundation/services/seeds.py`), garantindo que chaves de negócio e PII sejam sempre geradas sinteticamente ou anonimizadas via regras determinísticas irreversíveis.  
- Logs estruturados contendo somente identificadores técnicos (IDs, hashes, aliases) e contagens agregadas, nunca PII em texto claro, com validação via testes de logging.  
Ferramentas externas de DLP/PII podem ser integradas futuramente via pipeline, mas não serão requisito inicial desta feature.

**Rationale**  
- A Constituição/blueprints exigem anonimização forte e irreversível, o que torna insuficiente depender apenas de processos manuais; testes automatizados em `tests/security/` reforçam continuamente esse requisito.  
- Scanners baseados em padrões (regex para CPF/CNPJ, e-mail, telefone etc.) são simples de implementar, não dependem de serviços externos e podem rodar em cada pipeline de CI.  
- Centralizar as funções de anonimização/máscara em `foundation` reduz o risco de duplicação de lógica ou tratamento inconsistente entre seeds e testes, garantindo alinhamento com ADR-010 (PII em logs) e ADR-012 (observabilidade).  
- Manter a porta aberta para DLP/PII externos via pipeline preserva a escalabilidade da solução conforme amadurecem os controles de segurança.

**Alternatives considered**  
- **Nenhum scanner automatizado (apenas amostragem manual)**: não atende aos requisitos de LGPD e às expectativas de auditoria/automação de evidências. Rejeitado.  
- **Dependência imediata de ferramentas externas complexas (ex.: suites DLP completas)**: aumentaria a superfície operacional e o acoplamento, com custo alto para o estágio inicial da feature, sem impedir que essas ferramentas sejam adicionadas depois. Rejeitado como requisito inicial.

---

## 5. Catálogo único de factories `factory-boy` em contexto multi-tenant

**Decision**  
Centralizar o catálogo de factories em `backend/apps/foundation/factories/`, com submódulos por domínio (por exemplo, `customers.py`, `accounts.py`, `loans.py`, `transactions.py`) e uma base `TenantAwareFactory` que exige explicitamente o tenant em todas as factories multi-tenant.  
Seeds e testes (unitários, integração, contrato, carga) importarão factories a partir deste catálogo, evitando duplicação de lógica de geração de dados.

**Rationale**  
- Um catálogo único facilita garantir que todos os cenários de teste usem dados consistentes e aderentes ao modelo de domínio (BLUEPRINT §3.1), reduzindo divergências entre suites e entre ambientes.  
- Uma base `TenantAwareFactory` (por exemplo, exigindo `tenant` como argumento obrigatório e aplicando filtros/validações) reforça o respeito a RLS e previne criação acidental de dados sem tenant.  
- Colocar o catálogo em `foundation/factories/` permite uso tanto pelo comando `seed_data` (código “prod”) quanto por testes, sem depender de módulos de teste internos a cada app.  
- Submódulos por domínio mantêm a modularidade sem criar um app novo, em linha com Art. II.

**Alternatives considered**  
- **Factories espalhadas por app (`app/tests/factories.py`)**: incentiva duplicação de lógica e torna difícil manter consistência de PII/anonimização entre domínios. Rejeitado em favor de um catálogo central.  
- **Factories apenas em módulos de teste**: dificultaria o uso das mesmas factories dentro do comando `seed_data`, quebrando o princípio de reuso entre seeds e testes. Rejeitado.

---

## 6. Padrões de integração de seeds/anonimização com CI/CD e GitOps

**Decision**  
Integrar a execução de `seed_data`, verificações de PII e geração de datasets de carga aos pipelines existentes de CI/CD e GitOps (Argo CD + Terraform) da seguinte forma:  
- **CI (dev/hom)**: após migrações e antes dos testes de integração/contrato, executar `python backend/manage.py seed_data --env=dev --profile=small` (ou equivalente), seguido de testes de PII (`tests/security`) e de contrato; em jobs de smoke/performance leve, rodar `profile=medium`.  
- **Pipelines de infra/Terraform + Argo CD**: ao criar/atualizar ambientes (incluindo review apps e DR), disparar um Job Kubernetes que invoque `seed_data` com o perfil apropriado (`hom`, `perf`, `dr`) e registre métricas de tempo/volume em OpenTelemetry/Sentry.  
- **Testes de carga**: em ambientes de performance, após seeds com `profile=large`, rodar cenários k6/Gatling contra `/api/v1` respeitando RateLimit por tenant/ambiente, com gates baseados em SLOs de latência/erro e limites de throughput.  
- **Gates e FinOps**: pipelines falham se seeds não completarem em tempo razoável (por exemplo, >10 minutos em dev/hom) ou se testes de PII/segurança falharem; métricas DORA e custos de execução são monitorados para garantir que seeds e cargas fiquem dentro dos budgets definidos.

**Rationale**  
- Alinha a preparação de dados ao fluxo de criação/atualização de ambientes, garantindo que ambientes recém-provisionados estejam prontos para testes sem etapas manuais.  
- Conecta diretamente seeds e datasets às métricas DORA e SLOs de preparação de ambiente, tornando visível o impacto da feature F-11 na velocidade e qualidade de entrega.  
- Reforça a governança de API e RateLimit ao incorporar testes de carga que respeitam os limites e verificam erros conforme RFC 9457.  
- Mantém o frontend intocado em termos de arquitetura, apenas beneficiando-se de dados mais previsíveis.

**Alternatives considered**  
- **Executar seeds apenas manualmente ou em scripts ad-hoc**: não atende à exigência de automação e reproducibilidade nem se integra bem a GitOps/DR. Rejeitado.  
- **Rodar seeds apenas em produção**: viola explicitamente o requisito de limitar seeds de negócio em produção e não resolve os problemas de preparação de ambientes não produtivos. Rejeitado.

---

## 7. Representação de `PiiFieldMapping` e `AnonymizationRule`

**Decision**  
Modelar `PiiFieldMapping` como configuração declarativa em YAML versionado (por exemplo, `backend/apps/foundation/seeds/pii-mapping.yaml`), carregado em memória como estrutura Python pelo módulo de seeds (`backend/apps/foundation/services/seeds.py`), enquanto `AnonymizationRule` será representada inicialmente como um conjunto de regras estáticas em código (enum/constantes e funções utilitárias). Nenhuma tabela adicional de banco de dados será criada para essas entidades na primeira iteração.

**Rationale**  
- Mantém o mapeamento de PII/PD sob controle de revisão de código (PRs), com histórico claro de alterações, sem exigir novas migrações ou dependências dinâmicas em produção.  
- Alinha-se ao princípio de simplicidade (Art. II) e evita antecipar necessidades de edição dinâmica de regras que ainda não existem.  
- Permite que seeds, anonimização e scanners de PII compartilhem a mesma fonte de verdade (`pii-mapping.yaml` + helpers de código), reduzindo risco de divergência.  
- Caso surja necessidade futura de edição via UI/painel, é possível evoluir para modelos persistidos mediante ADR específico, sem invalidar o desenho atual.

**Alternatives considered**  
- **Criar tabelas `PiiFieldMapping` e `AnonymizationRule` em PostgreSQL desde o início**: facilitaria alterações dinâmicas, mas introduz complexidade (migrações, interfaces de gestão, ACLs específicas) sem necessidade imediata, além de aumentar a área de superfície de compliance. Rejeitado para a primeira versão.  
- **Configurações espalhadas em múltiplos módulos Python**: reduziria dependência de YAML, porém dificultaria a visualização e revisão centralizada do mapa de PII/PD. Rejeitado em favor de um único arquivo declarativo.

---

## 8. Granularidade de tasks Celery e modo `--mode=auto`

**Decision**  
Adotar granularidade de tasks Celery por par `(tenant, entidade)` para seeds assíncronas: o comando `seed_data` cria um `SeedRun` e enfileira uma tarefa para cada combinação de tenant habilitado e entidade declarada no `SeedProfile`. O parâmetro `--mode` terá a seguinte semântica:  
- `sync`: executa todo o seed de forma síncrona, no próprio processo do management command.  
- `async`: registra o `SeedRun` e enfileira tasks Celery, retornando assim que as tasks forem publicadas (monitoramento feito via métricas/logs).  
- `auto`: decisão baseada em ambiente/perfil — perfis `small` em `dev/hom` usam `sync`; demais perfis/ambientes (`medium`/`large`, `perf`, `dr`) usam `async`.

**Rationale**  
- Granularidade `(tenant, entidade)` oferece equilíbrio entre controle de paralelismo (por tenant/entidade) e sobrecarga de overhead de tasks, evitando milhares de tasks muito pequenas ou poucas tasks gigantes.  
- A opção `--mode=auto` reduz fricção para uso dia a dia (especialmente em CI e dev local), mantendo ao mesmo tempo o caminho de configuração explícita (`sync`/`async`) quando necessário.  
- Permite aplicar políticas distintas de concorrência por fila (`seed_data_default`, `seed_data_perf`) e por ambiente, em linha com §26 e metas de SLO/FinOps.

**Alternatives considered**  
- **Tasks por “chunk” arbitrário de registros (ex.: 1000 por task)**: daria mais controle de volume, mas tornaria a orquestração mais complexa, especialmente na presença de FKs entre entidades. Rejeitado para a primeira versão em favor de agrupamento por entidade/tenant.  
- **Decidir sempre por `sync` em todos os ambientes**: simplificaria a implementação, porém entraria em conflito com os objetivos de volumetria elevada em performance/DR e com o SLO de preparação de ambiente. Rejeitado.

---

## 9. Políticas de ambiente e uso em produção

**Decision**  
Restringir o escopo inicial do comando `seed_data` a ambientes não produtivos (`dev`, `hom`, `perf`, `dr`, `review`). Invocações com `--env=prod` devem falhar explicitamente com mensagem clara indicando que seeds de negócio não são suportadas em produção pela feature F-11. Seeds técnicas específicas para produção continuarão a ser tratadas pelos mecanismos existentes (por exemplo, migrações, fixtures técnicas), fora do escopo desta feature.

**Rationale**  
- Garante alinhamento com a exigência de não criar seeds de dados de negócio (mesmo sintéticos) em produção, reduzindo risco operacional e de compliance.  
- Mantém o foco de F-11 em melhorar a preparação de ambientes não produtivos e de performance/DR, onde os ganhos de produtividade e qualidade são maiores.  
- Evita a necessidade de introduzir conceitos adicionais (como perfis “técnicos” específicos de produção) neste estágio, simplificando o plano.

**Alternatives considered**  
- **Permitir um subconjunto de perfis “técnicos” em produção via `seed_data`**: introduziria complexidade de governança (quem pode rodar, com quais garantias, como auditar) e risco de uso indevido; melhor tratar em feature futura com ADR dedicado. Rejeitado para F-11.  
- **Bloquear completamente qualquer comando de seed em clusters de produção (inclusive técnicos)**: poderia conflitar com necessidades operacionais legítimas; manter essa decisão para o escopo de runbooks/infra, não para F-11.

---

## 10. Fronteira com snapshots de produção e DR

**Decision**  
Considerar como pré-condição que snapshots de produção (para testes em ambientes não produtivos ou DR) sejam provisionados/restaurados pelos pipelines de infra (Terraform/DBA/runbooks). A responsabilidade de F-11 é:  
- Aplicar anonimização forte e/ou geração de dados sintéticos sobre esses dados restaurados, seguindo `PiiFieldMapping`/`AnonymizationRule`.  
- Gerar evidências automatizadas (scanners de PII, amostragens, relatórios) de que não há PII real remanescente.  
- Registrar `SeedRun`/`SeedDatasetSnapshot` vinculados à operação de DR para auditoria.  
Não faz parte do escopo de F-11 orquestrar o próprio processo de snapshot/restore de banco.

**Rationale**  
- Mantém a separação de responsabilidades entre squads de infra/DBA (snapshot/restore) e a feature de seeds/anonimização (tratamento dos dados não produtivos).  
- Evita acoplar o comando `seed_data` a detalhes de infraestrutura de backup/restore, que podem variar por ambiente ou evoluir independentemente.  
- Ainda assim, as entidades de auditoria (`SeedRun`, `SeedDatasetSnapshot`) permitem rastrear e auditar execuções relacionadas a DR.

**Alternatives considered**  
- **Incluir lógica de snapshot/restore dentro do próprio `seed_data`**: aumentaria muito o escopo da feature, duplicando responsabilidades já cobertas por runbooks e ferramentas de backup; além disso, exigiria permissões elevadas e conhecimento detalhado de infra. Rejeitado.
