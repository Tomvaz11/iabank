# Integração com Subagents - Sistema AGV v5.0

## Diagrama de Integração Completa com Subagents

```mermaid
flowchart TB
    %% INPUT LAYER
    USER[👤 USUÁRIO<br/>Solicitações]
    BP[📄 BLUEPRINT.md<br/>Especificação]
    ORDER[📋 ORDEM.md<br/>Sequência]
    
    %% INTERFACE LAYER
    CC[🎛️ Claude Code<br/>Orchestrator]
    H1[🔄 submit-hook<br/>Pre-process]
    H2[⚙️ execution-hook<br/>Mid-process]
    H3[📊 response-hook<br/>Post-process]
    
    %% SUBAGENTS LAYER
    SA1[🏗️ agv-scaffolder<br/>Alvo 0: Setup<br/>Write, Bash, Glob]
    SA2[⚡ agv-implementor<br/>Alvos 1-N<br/>Write, Edit, Read]
    SA3[🔬 agv-integrator-tester<br/>Integração T1-T8<br/>Edit, Write, Bash]
    SA4[🔧 agv-evolucionista<br/>Bugs & Refactoring<br/>Multi Tools]
    SA5[📝 agv-uat-generator<br/>UAT Scenarios<br/>Read, Write]
    SA6[🔄 agv-uat-translator<br/>UAT → Auto Tests<br/>Read, Write, Edit]
    SA7[🧠 agv-context-analyzer<br/>Context Reduction<br/>Read, Grep, Glob]
    
    %% PROCESSING ENGINE
    CTX1[📥 context_extractor.py<br/>Redução 80%]
    CTX2[🎯 inject_context.py<br/>Injeção Dinâmica]
    
    %% VALIDATION FACTORY
    VF[🏭 ValidatorGenerator v3.0<br/>Sistema Modular]
    BPI[🧩 BlueprintParser<br/>Parsing Inteligente]
    VR[📋 ValidationRule<br/>CRITICAL-LOW<br/>5 Categories]
    
    %% VALIDATORS
    VS[✅ validate_scaffold.py<br/>200+ Validações<br/>90%+ Score]
    VT1[🔐 validate_target_1.py<br/>Auth & Users]
    VT2[💰 validate_target_2.py<br/>Finance & Loans]
    VTN[🎯 validate_target_N.py<br/>Business Logic]
    VI1[🔗 validate_integration_T1.py<br/>Auth + Core]
    VI2[🔗 validate_integration_T2.py<br/>Finance + Ops]
    VE[⚡ validate_evolution.py<br/>Quality & Performance]
    
    %% REPORTS
    REP[📊 validation_results.json<br/>Resultados]
    SCORE[📈 Scores & Métricas<br/>85-100%]
    ISSUES[⚠️ Issues Categorized<br/>Severity]
    QUAL[🏆 validate_agv_quality.py<br/>Quality Check]
    
    %% COMMANDS
    SLASH1[⚡ /scaffold<br/>Scaffolding]
    SLASH2[🎯 /implement-target N<br/>Target N]
    SLASH3[✅ /validate-all<br/>All Validations]
    SLASH4[🔧 /evolve<br/>Evolve]
    
    %% MAIN FLOW CONNECTIONS
    USER --> CC
    BP --> BPI
    ORDER --> CTX1
    
    CC --> H1
    H1 --> H2
    H2 --> H3
    
    CC --> SA1
    CC --> SA2
    CC --> SA3
    CC --> SA4
    CC --> SA5
    CC --> SA6
    CC --> SA7
    
    CTX1 --> CTX2
    CTX2 --> SA2
    CTX2 --> SA3
    
    SA7 --> CTX1
    
    BPI --> VF
    VF --> VS
    VF --> VT1
    VF --> VT2
    VF --> VTN
    VF --> VI1
    VF --> VI2
    VF --> VE
    
    SA1 -.-> VS
    SA2 -.-> VTN
    SA3 -.-> VI1
    SA4 -.-> VE
    
    VS --> REP
    VTN --> REP
    VI1 --> REP
    VE --> REP
    
    REP --> SCORE
    REP --> ISSUES
    REP --> QUAL
    
    CC --> SLASH1
    CC --> SLASH2
    CC --> SLASH3
    CC --> SLASH4
    
    SLASH1 --> SA1
    SLASH2 --> SA2
    SLASH3 --> VF
    SLASH4 --> SA4
    
    %% STYLING
    classDef user fill:#E3F2FD,stroke:#1976D2,stroke-width:3px,color:#000
    classDef interface fill:#F1F8E9,stroke:#388E3C,stroke-width:2px,color:#000
    classDef subagent fill:#E8F5E8,stroke:#2E7D32,stroke-width:2px,color:#FFF
    classDef processing fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
    classDef validator fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#000
    classDef output fill:#E0F2F1,stroke:#00695C,stroke-width:2px,color:#000
    classDef command fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    
    class USER,BP,ORDER user
    class CC,H1,H2,H3 interface
    class SA1,SA2,SA3,SA4,SA5,SA6,SA7 subagent
    class CTX1,CTX2,VF,BPI,VR processing
    class VS,VT1,VT2,VTN,VI1,VI2,VE validator
    class REP,SCORE,ISSUES,QUAL output
    class SLASH1,SLASH2,SLASH3,SLASH4 command
```

## Arquitetura Simplificada - Componentes Principais

### **🎛️ Claude Code Interface**
**Orquestrador central** que coordena todos os subagents e hooks.

#### **Hooks & Middleware:**
- **submit-hook** → Pre-processamento de prompts
- **execution-hook** → Mid-processamento durante execução  
- **response-hook** → Post-processamento de respostas

---

### **🤖 Subagents Especializados**

#### **🏗️ agv-scaffolder (Alvo 0)**
- **Responsabilidade:** Setup completo do projeto
- **Tools:** Write, Bash, Glob
- **Output:** Estrutura base + configurações
- **Validação:** `validate_scaffold.py` (200+ validações)

#### **⚡ agv-implementor (Alvos 1-N)**
- **Responsabilidade:** Implementação de features específicas
- **Tools:** Write, Edit, Read, Bash
- **Context:** Reduzido 80% via `inject_context.py`
- **Validação:** `validate_target_N.py` (80+ validações)

#### **🔬 agv-integrator-tester (T1-T8)**
- **Responsabilidade:** Testes de integração robustos
- **Tools:** Edit, Write, Bash, Read
- **Foco:** Fluxos entre módulos, APIs, DB integrity
- **Validação:** `validate_integration_TN.py` (40+ validações)

#### **🔧 agv-evolucionista (F7)**
- **Responsabilidade:** Manutenção, bugs, refatoração
- **Tools:** Bash, Glob, Read, Edit, Write, MultiEdit, Grep
- **Foco:** Qualidade, performance, segurança
- **Validação:** `validate_evolution.py` (60+ validações)

#### **📝 agv-uat-generator**
- **Responsabilidade:** Cenários UAT End-to-End
- **Tools:** Read, Write
- **Foco:** Blueprint → Testes manuais
- **Output:** Cenários de teste do usuário final

#### **🔄 agv-uat-translator**
- **Responsabilidade:** UAT → Testes automatizados
- **Tools:** Read, Write, Edit
- **Foco:** Scripts de backend automatizados
- **Output:** Testes automatizados prontos

#### **🧠 agv-context-analyzer**
- **Responsabilidade:** Extração inteligente de contexto
- **Tools:** Read, Grep, Glob
- **Performance:** Redução de 80% no contexto (1500→300 linhas)
- **Output:** Contexto focado por alvo

---

### **🏭 Sistema de Validação**

#### **Validation Factory:**
- **ValidatorGenerator v3.0** → Sistema modular de geração
- **BlueprintParser** → Parsing inteligente do Blueprint
- **ValidationRule** → 5 categorias (STRUCTURE, CONTENT, MODELS, DEPENDENCIES, API)

#### **Validadores Gerados:**
- **validate_scaffold.py** → 200+ validações (Score target: 90%+)
- **validate_target_N.py** → 80+ validações por alvo
- **validate_integration_TN.py** → 40+ validações de integração
- **validate_evolution.py** → 60+ validações de qualidade

---

### **📊 Sistema de Relatórios**

- **validation_results.json** → Resultados detalhados JSON
- **Scores & Métricas** → 85-100% conformidade
- **Issues Categorized** → Por severidade (CRITICAL → LOW)
- **validate_agv_quality.py** → Check de qualidade geral

---

### **⚡ Slash Commands & Automação**

```bash
/scaffold                    # Executar scaffolding completo
/implement-target 3         # Implementar alvo específico  
/validate-all              # Executar todas validações
/evolve                    # Evoluir e refatorar código
```

---

## **🔄 Fluxo de Integração Completo**

1. **👤 Usuário** → Comando/Solicitação
2. **🎛️ Claude Code** → Análise via hooks (submit → execution → response)
3. **🧠 Context Engine** → Extração focada (80% redução)
4. **🤖 Subagent** → Execução especializada
5. **🏭 Validator Factory** → Geração automática de validador
6. **✅ Validador** → Execução de 40-200+ testes específicos
7. **📊 Relatórios** → Métricas, scores e feedback detalhado
8. **👤 Usuário** → Resultado + sugestões próximos passos

---

## **📈 Métricas de Performance**

### **Sistema:**
- **Context Reduction:** 80% (1500→300 linhas)
- **Validation Speed:** 200+ regras em ~10s
- **Subagent Selection:** <1s
- **Hook Processing:** <500ms por hook

### **Qualidade:**
- **Scaffold Score Target:** 90%+
- **Target Implementation:** 85%+ por alvo
- **Integration Tests:** 95%+ cobertura
- **Evolution Quality:** 88%+ manutenibilidade

---

## **🎯 Benefícios da Arquitetura**

1. **🎯 Especialização** → Cada subagent focado em sua responsabilidade
2. **⚡ Performance** → Context reduzido + processamento otimizado
3. **🔄 Automação** → Validação automática pós-implementação
4. **📊 Qualidade** → Métricas rigorosas + feedback detalhado
5. **🚀 Extensibilidade** → Fácil adição de novos subagents/validadores
6. **🧠 Inteligência** → Context-aware + inferência automática
7. **🔧 Manutenibilidade** → Modular + reutilizável + testável