# Desenvolvimento orientado a especificação (SDD)

## a inversão de energia

Por décadas, o código tem sido rei. As especificações serviram o código - eles foram os andaimes que construímos e depois descartamos quando o "trabalho real" da codificação começar. Escrevemos o PRDS para orientar o desenvolvimento, criamos documentos de design para informar a implementação, desenham diagramas para visualizar a arquitetura. Mas estes estavam sempre subordinados ao próprio código. Código era verdade. Tudo o resto era, na melhor das hipóteses, boas intenções. O código era a fonte da verdade e, à medida que avançava, as especificações raramente mantinham o ritmo. Como o ativo (código) e a implementação são um, não é fácil ter uma implementação paralela sem tentar construir a partir do código.

O desenvolvimento orientado por especificações (SDD) inverte essa estrutura de potência. Especificações não servem código - o código serve especificações. O documento de requisitos do produto (PRD) não é um guia para implementação; É a fonte que gera implementação. Planos técnicos não são documentos que informam a codificação; São definições precisas que produzem código. Esta não é uma melhoria incremental de como criamos o software. É uma repensação fundamental do que impulsiona o desenvolvimento.

A lacuna entre especificação e implementação atormentou o desenvolvimento de software desde a sua criação. Tentamos preencher com melhor documentação, requisitos mais detalhados, processos mais rígidos. Essas abordagens falham porque aceitam a lacuna como inevitáveis. Eles tentam reduzi -lo, mas nunca eliminam. O SDD elimina a lacuna fazendo especificações e seus planos de implementação concreta nascidos do executável da especificação. Quando as especificações e os planos de implementação geram código, não há lacuna - apenas a transformação.

Essa transformação agora é possível porque a IA pode entender e implementar especificações complexas e criar planos detalhados de implementação. Mas a geração de IA bruta sem estrutura produz caos. O SDD fornece essa estrutura por meio de especificações e planos de implementação subsequentes que são precisos, completos e inequívocos o suficiente para gerar sistemas de trabalho. A especificação se torna o artefato primário. O código se torna sua expressão (como uma implementação do plano de implementação) em um idioma e estrutura específicos.

Neste novo mundo, manter o software significa evolução de especificações. A intenção da equipe de desenvolvimento é expressa em linguagem natural ("** Desenvolvimento orientado a intenções **"), ativos de design, princípios fundamentais e outras diretrizes. A língua franca ** do desenvolvimento se move para um nível mais alto, e o código é a abordagem de última milha.

A depuração significa consertar especificações e seus planos de implementação que geram código incorreto. A refatoração significa reestruturação para clareza. Todo o fluxo de trabalho de desenvolvimento reorganiza as especificações como a fonte central da verdade, com planos de implementação e código como a saída continuamente regenerada. Atualizar aplicativos com novos recursos ou criar uma nova implementação paralela porque somos seres criativos, significa revisitar a especificação e criar novos planos de implementação. Este processo é, portanto, 0 -> 1, (1 ', ..), 2, 3, N.

A equipe de desenvolvimento se concentra em sua criatividade, experimentação, seu pensamento crítico.

## o fluxo de trabalho do SDD na prática

O fluxo de trabalho começa com uma idéia - geralmente vaga e incompleta. Através do diálogo iterativo com a IA, essa idéia se torna um PRD abrangente. A IA faz perguntas esclarecedoras, identifica casos de borda e ajuda a definir critérios precisos de aceitação. O que pode levar dias de reuniões e documentação no desenvolvimento tradicional acontece em horas de trabalho de especificação focada. Isso transforma o SDLC tradicional - exigências e design se tornam atividades contínuas, em vez de fases discretas. Isso apoia um processo de equipe **, onde as especificações revisadas por equipes são expressas e versionadas, criadas em ramificações e mescladas.

Quando um gerente de produto atualiza os critérios de aceitação, os planos de implementação sinalizam automaticamente as decisões técnicas afetadas. Quando um arquiteto descobre um padrão melhor, o PRD atualiza para refletir novas possibilidades.

Ao longo deste processo de especificação, os agentes de pesquisa reúnem contexto crítico. Eles investigam a compatibilidade da biblioteca, os benchmarks de desempenho e as implicações de segurança. As restrições organizacionais são descobertas e aplicadas automaticamente - seus padrões de banco de dados da empresa, requisitos de autenticação e políticas de implantação se integram perfeitamente a todas as especificações.

Do PRD, a IA gera planos de implementação que mapeiam os requisitos para decisões técnicas. Toda escolha de tecnologia documentou a lógica. Toda decisão arquitetônica remonta a requisitos específicos. Ao longo deste processo, a validação de consistência melhora continuamente a qualidade. A IA analisa as especificações de ambiguidade, contradições e lacunas-não como um portão único, mas como um refinamento em andamento.

A geração de código começa assim que as especificações e seus planos de implementação são estáveis ​​o suficiente, mas eles não precisam ser "completos". As primeiras gerações podem ser exploratórias - testando se a especificação faz sentido na prática. Os conceitos de domínio se tornam modelos de dados. As histórias de usuário se tornam terminais de API. Os cenários de aceitação se tornam testes. Isso mescla desenvolvimento e teste por meio da especificação - os cenários de teste não são gravados após o código, eles fazem parte da especificação que gera implementação e testes.

O loop de feedback se estende além do desenvolvimento inicial. As métricas e incidentes de produção não acionam apenas hotfixes - eles atualizam as especificações para a próxima regeneração. Os gargalos de desempenho se tornam novos requisitos não funcionais. As vulnerabilidades de segurança tornam -se restrições que afetam todas as gerações futuras. Essa dança iterativa entre especificação, implementação e realidade operacional é onde surge o verdadeiro entendimento e onde o SDLC tradicional se transforma em uma evolução contínua.

## por que o SDD é importante agora

Três tendências tornam o SDD não apenas possível, mas necessário:

Primeiro, os recursos de IA atingiram um limite em que as especificações de linguagem natural podem gerar com segurança o código de trabalho. Não se trata de substituir os desenvolvedores - trata -se de ampliar sua eficácia, automatizando a tradução mecânica da especificação para a implementação. Ele pode ampliar a exploração e a criatividade, apoiar "iniciar" facilmente e apoiar a adição, a subtração e o pensamento crítico.

Segundo, a complexidade do software continua a crescer exponencialmente. Os sistemas modernos integram dezenas de serviços, estruturas e dependências. Manter todas essas peças alinhadas com a intenção original através de processos manuais se torna cada vez mais difícil. O SDD fornece alinhamento sistemático por meio de geração orientada a especificação. As estruturas podem evoluir para fornecer suporte a IA, não um suporte humano primeiro ou arquiteto em torno dos componentes reutilizáveis.

Terceiro, o ritmo da mudança acelera. Os requisitos mudam muito mais rapidamente hoje do que nunca. O giratório não é mais excepcional - é esperado. O desenvolvimento moderno do produto exige iteração rápida com base no feedback do usuário, condições de mercado e pressões competitivas. O desenvolvimento tradicional trata essas mudanças como interrupções. Cada pivô requer propagação manualmente alterações por meio de documentação, design e código. O resultado são atualizações lentas e cuidadosas que limitam a velocidade ou mudanças rápidas e imprudentes que acumulam dívida técnica.

O SDD pode suportar os experimentos de What-IF/Simulação: "Se precisarmos reimplementar ou alterar o aplicativo para promover uma empresa necessária para vender mais camisetas, como implementaríamos e experimentaríamos isso?"

O SDD transforma as mudanças de requisitos dos obstáculos no fluxo de trabalho normal. Quando as especificações impulsionam a implementação, os pivôs se tornam regenerações sistemáticas, em vez de reescritas manuais. Altere um requisito principal no PRD e afetou os planos de implementação atualizados automaticamente. Modificar uma história do usuário e os financiários da API correspondentes se regeneram. Não se trata apenas de desenvolvimento inicial - trata -se de manter a velocidade de engenharia por meio de mudanças inevitáveis.

## Princípios principais

** Especificações como a língua franca **: A especificação se torna o artefato primário. O código se torna sua expressão em um idioma e estrutura específicos. Manter o software significa evolução de especificações.

** Especificações executáveis ​​**: As especificações devem ser precisas, completas e inequívocas o suficiente para gerar sistemas de trabalho. Isso elimina a lacuna entre intenção e implementação.

** Refinamento contínuo **: A validação de consistência acontece continuamente, não como um portão único. A IA analisa as especificações de ambiguidade, contradições e lacunas como um processo contínuo.

** Contexto orientado a pesquisas **: Os agentes de pesquisa reúnem contexto crítico ao longo do processo de especificação, investigando opções técnicas, implicações de desempenho e restrições organizacionais.

** Feedback bidirecional **: A realidade da produção informa a evolução da especificação. Métricas, incidentes e aprendizados operacionais tornam -se insumos para refinamento de especificações.

** Ramificação para exploração **: Gere várias abordagens de implementação a partir da mesma especificação para explorar diferentes metas de otimização - desempenho, manutenção, experiência do usuário, custo.

## abordagens de implementação

Hoje, a prática do SDD exige a montagem de ferramentas existentes e a manutenção da disciplina ao longo do processo. A metodologia pode ser praticada com:

- Assistentes de IA para desenvolvimento de especificações iterativas
- Agentes de pesquisa para reunir contexto técnico
- Ferramentas de geração de código para traduzir especificações para a implementação
- Sistemas de controle de versão adaptados para especificações Fluxos de trabalho primeiro
- Verificação de consistência através da análise de IA dos documentos de especificação

A chave é tratar as especificações como a fonte da verdade, com o código como a saída gerada que serve a especificação e não o contrário.

## simplaling sdd com comandos

A metodologia SDD é significativamente aprimorada através de três comandos poderosos que automatizam a especificação → Planejamento → Fluxo de trabalho de tarefas:

### o comando `/specify`

Este comando transforma uma descrição simples de recurso (o PROMPT) em uma especificação completa e estruturada com gerenciamento automático de repositório:

1.
2.
3. ** Geração baseada em modelo **: Copia e personaliza o modelo de especificação de recursos com seus requisitos
4.

### o comando `/plan`

Depois que existe uma especificação de recursos, este comando cria um plano de implementação abrangente:

1.
2.
3.
4. ** Documentação detalhada **: gera documentos de suporte para modelos de dados, contratos de API e cenários de teste
5.

### O comando `/tarefa`

Depois que um plano é criado, este comando analisa o plano e os documentos de design relacionados para gerar uma lista de tarefas executáveis:

1. ** Entradas **: lê `plan.md` (obrigatório) e, se presente,` data-model.md`, `contratos/` e `pesquisador.md`
2. ** Derivação de tarefas **: converte contratos, entidades e cenários em tarefas específicas
3.
4.

### Exemplo: Construindo um recurso de bate -papo

Veja como esses comandos transformam o fluxo de trabalho de desenvolvimento tradicional:

** Abordagem tradicional: **

`` `texto
1. Escreva um PRD em um documento (2-3 horas)
2. Crie documentos de design (2-3 horas)
3. Configure a estrutura do projeto manualmente (30 minutos)
4. Escreva especificações técnicas (3-4 horas)
5. Crie planos de teste (2 horas)
Total: ~ 12 horas de documentação
`` `

** SDD com comandos abordagem: **

`` `BASH
# Etapa 1: Crie a especificação do recurso (5 minutos)
/Especifique o sistema de bate-papo em tempo real com histórico de mensagens e presença do usuário

# Isso automaticamente:
#-cria ramificação "003-chat-system"
#-gera especificações/003-chat-system/spec.md
# - preenche -o com requisitos estruturados

# Etapa 2: Gere um plano de implementação (5 minutos)
/Planeje WebSocket para mensagens em tempo real, PostGresql para história, Redis para presença

# Etapa 3: Gere tarefas executáveis ​​(5 minutos)
/tarefas

# Isso cria automaticamente:
#-Specs/003-chat-system/plan.md
#-Specs/003-chat-system/pesquisa.md (Comparações da biblioteca da WebSocket)
#-Specs/003-chat-system/data-model.md (esquemas de mensagens e usuários)
#-Specs/003-Chat-System/Contracts/(WebSocket Events, Rest termina
#-Specs/003-chat-system/Quickstart.md (Cenários de validação-chave)
#-Specs/003-chat-system/tasks.md (lista de tarefas derivadas do plano)
`` `

Em 15 minutos, você tem:

- Uma especificação completa do recurso com histórias de usuários e critérios de aceitação
- Um plano de implementação detalhado com opções de tecnologia e lógica
- Contratos de API e modelos de dados prontos para geração de código
- Cenários de teste abrangentes para testes automatizados e manuais
- Todos os documentos corretamente versionados em uma filial de recursos

### O poder da automação estruturada

Esses comandos não economizam apenas tempo - eles aplicam consistência e integridade:

1. ** Não há detalhes esquecidos **: Os modelos garantem que todos os aspectos sejam considerados, de requisitos não funcionais ao tratamento de erros
2. ** Decisões rastreáveis ​​**: Toda escolha técnica liga para requisitos específicos
3. ** Documentação viva **: as especificações permanecem sincronizadas com o código porque elas o geram
4. ** iteração rápida **: Altere os requisitos e regenera planos em minutos, não dias

Os comandos incorporam os princípios do SDD, tratando as especificações como artefatos executáveis, em vez de documentos estáticos. Eles transformam o processo de especificação de um mal necessário para a força motriz do desenvolvimento.

### Qualidade modelo-driven: como a estrutura restringe o LLMS para obter melhores resultados

O verdadeiro poder desses comandos está não apenas na automação, mas na maneira como os modelos orientam o comportamento da LLM em direção a especificações de qualidade superior. Os modelos atuam como sofisticado solicita que restrinjam a produção do LLM de maneiras produtivas:

#### 1. ** Prevendo detalhes da implementação prematura **

O modelo de especificação de recursos instrui explicitamente:

`` `texto
- ✅ Concentre -se no que os usuários precisam e por que
- ❌ Evite como implementar (sem pilha de tecnologia, APIs, estrutura de código)
`` `

Essa restrição força o LLM a manter os níveis adequados de abstração. Quando um LLM pode pular naturalmente para "implementar o uso do React com o Redux", o modelo o mantém focado em "os usuários precisam de atualizações em tempo real de seus dados". Essa separação garante que as especificações permaneçam estáveis, mesmo quando as tecnologias de implementação mudam.

#### 2. ** Forçando marcadores explícitos de incerteza **

Ambos os modelos exigem o uso de `[precisa de esclarecimentos]` marcadores:

`` `texto
Ao criar esta especificação de um prompt de usuário:
1. ** Marque todas as ambiguidades **: Use [precisa de esclarecimento: pergunta específica]
2. ** Não adivinhe **: Se o prompt não especificar algo, marque -o
`` `

Isso impede o comportamento comum de LLM de fazer suposições plausíveis, mas potencialmente incorretas. Em vez de adivinhar que um "sistema de login" usa autenticação de email/senha, o LLM deve marcá -lo como `[precisa de esclarecimento: método de autenticação não especificado - email/senha, SSO, OAuth?]`.

#### 3. ** Pensamento estruturado através de listas de verificação **

Os modelos incluem listas de verificação abrangentes que atuam como "testes de unidade" para a especificação:

`` `Markdown
### Completive requisito
-!
- [] Os requisitos são testáveis ​​e inequívocos
- [] Os critérios de sucesso são mensuráveis
`` `

Essas listas de verificação forçam o LLM a revisar sua saída sistematicamente, capturando lacunas que poderiam passar. É como dar ao LLM uma estrutura de garantia de qualidade.

#### 4. ** Conformidade constitucional através de portões **

O modelo de plano de implementação aplica os princípios arquitetônicos por meio de portões de fase:

`` `Markdown
### Fase -1: portões de pré -implementação
#### Simplicity Gate (Artigo VII)
- [] Usando projetos ≤3?
- [] Sem prova de futuro?
#### portão anti-abstração (artigo VIII)
- [] Usando a estrutura diretamente?
- [] Representação de modelo único?
`` `

Esses portões impedem a engenharia excessiva, fazendo com que o LLM justifique explicitamente qualquer complexidade. Se um portão falhar, o LLM deve documentar por que na seção "Rastreamento de complexidade", criando responsabilidade por decisões arquitetônicas.

#### 5. ** Gerenciamento de detalhes hierárquicos **

Os modelos aplicam a arquitetura de informação adequada:

`` `texto
** IMPORTANTE **: Este plano de implementação deve permanecer de alto nível e legível.
Quaisquer amostras de código, algoritmos detalhados ou especificações técnicas extensas
Deve ser colocado no arquivo `implementação-details/` apropriado
`` `

Isso impede o problema comum das especificações que se tornam despejadas de código ilegíveis. O LLM aprende a manter os níveis de detalhe apropriados, extraindo a complexidade para separar arquivos, mantendo o documento principal navegável.

#### 6. ** Test-primeiro pensamento **

O modelo de implementação aplica o desenvolvimento de teste:

`` `texto
Pedido de criação de arquivos
1. Crie `contratos/` com especificações da API
2. Crie arquivos de teste em ordem: Contrato → Integração → E2E → Unidade
3. Crie arquivos de origem para fazer os testes passarem
`` `

Essa restrição de pedidos garante que o LLM pense em testabilidade e contratos antes da implementação, levando a especificações mais robustas e verificáveis.

#### 7. ** Prevenção de recursos especulativos **

Modelos desencorajam explicitamente a especulação:

`` `texto
- [] Não há recursos especulativos ou "podem precisar"
- [] Todas as fases têm pré -requisitos e entregas claras
`` `

Isso impede que o LLM adicione recursos "Nice Ter" que complicam a implementação. Todo recurso deve voltar a uma história de usuário concreta com critérios de aceitação claros.

### o efeito composto

Essas restrições trabalham juntas para produzir especificações que são:

- ** Completo **: Listas de verificação garantem que nada seja esquecido
- ** inequívocos **: Marcadores de esclarecimento forçados destacam as incertezas
- ** Testável **: Teste primeiro pensamento assado no processo
- ** Manterável **: Níveis de abstração adequados e hierarquia de informações
- ** implementável **: fases claras com entregas de concreto

Os modelos transformam o LLM de um escritor criativo em um engenheiro de especificações disciplinadas, canalizando suas capacidades para produzir especificações executáveis ​​consistentemente de alta qualidade que realmente impulsionam o desenvolvimento.

## A Fundação Constitucional: Exibindo a disciplina arquitetônica

No coração do SDD, encontra -se uma constituição - um conjunto de princípios imutáveis ​​que governam como as especificações se tornam código. A Constituição (`Memory/Constitution.md`) atua como o DNA arquitetônico do sistema, garantindo que toda implementação gerada mantenha consistência, simplicidade e qualidade.

### Os nove artigos de desenvolvimento

A Constituição define nove artigos que moldam todos os aspectos do processo de desenvolvimento:

#### Artigo I: Princípio da Biblioteca-First

Todo recurso deve começar como uma biblioteca independente - sem exceções. Isso força o design modular desde o início:

`` `texto
Todos os recursos do Specy devem começar sua existência como uma biblioteca independente.
Nenhum recurso deve ser implementado diretamente no código do aplicativo sem
Primeiro, sendo abstraído em um componente de biblioteca reutilizável.
`` `

Esse princípio garante que as especificações gerem código modular e reutilizável, em vez de aplicativos monolíticos. Quando o LLM gera um plano de implementação, ele deve estruturar os recursos como bibliotecas com limites claros e dependências mínimas.

#### Artigo II: Mandato da interface da CLI

Toda biblioteca deve expor sua funcionalidade através de uma interface da linha de comando:

`` `texto
Todas as interfaces da CLI devem:
- Aceite texto como entrada (via stdin, argumentos ou arquivos)
- Produza o texto como saída (via stdout)
- Apoie o formato JSON para troca de dados estruturada
`` `

Isso aplica observabilidade e testabilidade. O LLM não pode ocultar a funcionalidade nas classes opacas-tudo deve ser acessível e verificável através de interfaces baseadas em texto.

#### Artigo III: Test-First Imperativo

O artigo mais transformador - sem código antes dos testes:

`` `texto
Isso não é negociável: toda a implementação deve seguir o desenvolvimento rigoroso orientado a testes.
Nenhum código de implementação deve ser escrito antes:
1. Os testes de unidade são escritos
2. Os testes são validados e aprovados pelo usuário
3. Os testes são confirmados para falhar (fase vermelha)
`` `

Isso inverte completamente a geração de código de IA tradicional. Em vez de gerar código e esperar que funcione, o LLM deve primeiro gerar testes abrangentes que definem o comportamento, obtê -los aprovados e só então gerar implementação.

Artigos VII e VIII: Simplicidade e Anti-Abstração

Esses artigos emparelhados combatem a engenharia excessiva:

`` `texto
Seção 7.3: Estrutura mínima do projeto
- Máximo 3 projetos para implementação inicial
- Projetos adicionais exigem justificativa documentada

Seção 8.1: confiança da estrutura
- Use os recursos da estrutura diretamente em vez de envolvê -los
`` `

Quando um LLM pode naturalmente criar abstrações elaboradas, esses artigos o forçam a justificar todas as camadas de complexidade. A "Fase -1 portões" do modelo de plano de implementação aplica diretamente esses princípios.

#### Artigo IX: Teste de Integration-First

Prioriza os testes do mundo real em relação aos testes de unidade isolados:

`` `texto
Os testes devem usar ambientes realistas:
- prefira bancos de dados reais ao longo de zombares
- Use instâncias de serviço reais sobre stubs
- Testes de contrato obrigatórios antes da implementação
`` `

Isso garante que o código gerado funcione na prática, não apenas em teoria.

### A aplicação constitucional através de modelos

O modelo de plano de implementação operacionaliza esses artigos por meio de pontos de verificação de concreto:

`` `Markdown
### Fase -1: portões de pré -implementação
#### Simplicity Gate (Artigo VII)
- [] Usando projetos ≤3?
- [] Sem prova de futuro?

#### portão anti-abstração (artigo VIII)
- [] Usando a estrutura diretamente?
- [] Representação de modelo único?

#### Integration-First Gate (Artigo IX)
- [] Contratos definidos?
- [] Testes de contrato escritos?
`` `

Esses portões atuam como verificações no tempo de compilação dos princípios arquitetônicos. O LLM não pode prosseguir sem passar pelos portões ou documentar exceções justificadas na seção "Rastreamento de complexidade".

### O poder dos princípios imutáveis

O poder da Constituição está em sua imutabilidade. Embora os detalhes da implementação possam evoluir, os princípios principais permanecem constantes. Isso fornece:

1. ** Consistência ao longo do tempo **: O código gerado hoje segue os mesmos princípios que o código gerado no próximo ano
2.
3. ** Integridade arquitetônica **: Todo recurso reforça em vez de prejudicar o design do sistema
4.

### Evolução constitucional

Embora os princípios sejam imutáveis, sua aplicação pode evoluir:

`` `texto
Seção 4.2: Processo de alteração
Modificações para esta Constituição exigem:
- Documentação explícita da lógica da mudança
- Revisão e aprovação por mantenedores de projeto
- Avaliação de compatibilidade com versões anteriores
`` `

Isso permite que a metodologia aprenda e melhore, mantendo a estabilidade. A Constituição mostra sua própria evolução com emendas datadas, demonstrando como os princípios podem ser refinados com base na experiência do mundo real.

### Além das regras: uma filosofia de desenvolvimento

A Constituição não é apenas um livro de regras - é uma filosofia que molda como os LLMs pensam sobre a geração de código:

- ** Observabilidade sobre a opacidade **: Tudo deve ser inspecionável através de interfaces da CLI
- ** Simplicidade sobre a inteligência **: Comece simples, adicione complexidade somente quando comprovado
- ** Integração sobre isolamento **: teste em ambientes reais, não artificiais
- ** Modularidade sobre os monólitos **: Cada recurso é uma biblioteca com limites claros

Ao incorporar esses princípios no processo de especificação e planejamento, o SDD garante que o código gerado não seja apenas funcional - é sustentável, testável e arquitetonicamente sólido. A Constituição transforma a IA de um gerador de código em um parceiro de arquitetura que respeita e reforça os princípios de design do sistema.

## a transformação

Não se trata de substituir os desenvolvedores ou automatizar a criatividade. Trata -se de ampliar a capacidade humana, automatizando a tradução mecânica. Trata -se de criar um loop de feedback apertado, onde as especificações, a pesquisa e o código evoluem juntos, cada iteração trazendo uma compreensão mais profunda e melhor alinhamento entre intenção e implementação.

O desenvolvimento de software precisa de melhores ferramentas para manter o alinhamento entre intenção e implementação. O SDD fornece a metodologia para alcançar esse alinhamento por meio de especificações executáveis ​​que geram código, em vez de apenas orientá -lo.