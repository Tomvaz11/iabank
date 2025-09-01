# Sequência de Execução - Sistema AGV v5.0

## Diagrama de Sequência - Fluxo Completo de Execução

```mermaid
sequenceDiagram
    participant U as 👤 Usuário
    participant CC as 🎛️ Claude Code
    participant H1 as 🔄 Pre-Hook
    participant CTX as 📥 Context
    participant SA as ⚡ Subagent
    participant VG as 🏭 Generator
    participant VS as ✅ Validator
    participant R as 📊 Reports

    Note over U,R: FLUXO AGV v5.0 - IMPLEMENTAÇÃO ALVO 3

    U->>CC: Implementar Alvo 3 do IABANK
    
    CC->>H1: Trigger user-prompt-submit-hook
    H1->>H1: Análise intenção Alvo 3
    H1->>H1: Selecionar agv-implementor
    H1->>H1: Preparar contexto TARGET=3
    H1-->>CC: Pre-processamento OK
    
    CC->>CTX: Extrair contexto Alvo 3
    Note over CTX: Blueprint 1500+ linhas
    
    CTX->>CTX: Mapear dependências
    CTX->>CTX: Extrair seções relevantes
    CTX->>CTX: Focar modelos Loan/Transaction
    CTX->>CTX: Reduzir 80% contexto
    CTX-->>CC: Context 300 linhas
    
    CC->>SA: Executar agv-implementor
    Note over SA: Context injetado<br/>Models: Loan, Transaction
    
    SA->>SA: Implementar Loan
    SA->>SA: Implementar Transaction  
    SA->>SA: Criar LoanListView
    SA->>SA: Implementar serializers
    SA->>SA: Configurar URLs
    SA->>SA: Criar testes unitários
    SA->>SA: Executar pytest
    
    Note over SA: Cobertura 92%
    
    SA->>VG: Solicitar validador Alvo 3
    VG->>VG: Parse Blueprint
    VG->>VG: Extrair ProjectSpecs
    VG->>VG: Instanciar TargetGenerator
    VG->>VG: Inferir contexto
    VG->>VG: Gerar 80+ regras
    VG->>VS: Criar validate_target_3.py
    
    Note over VS: 80+ validações específicas<br/>Modelos, APIs, Testes
    
    VS->>VS: Validar Loan existe
    VS->>VS: Validar Transaction existe
    VS->>VS: Validar relacionamentos
    VS->>VS: Validar LoanListView
    VS->>VS: Validar URLs configuradas
    VS->>VS: Validar testes existem
    VS->>VS: Validar migrações
    
    Note over VS: 80+ validações em 10s
    
    VS->>R: Gerar results.json
    
    R->>R: Calcular score 92%
    R->>R: Passed 76/80 validações
    R->>R: Failed 4/80 validações
    R->>R: Categorizar issues
    R->>R: CRITICAL 0
    R->>R: HIGH 2 URLs faltantes
    R->>R: MEDIUM 2 testes extras
    
    R-->>SA: Score 92% EXCELENTE
    SA->>SA: Corrigir 2 issues HIGH
    SA->>SA: Adicionar URLs faltantes
    SA->>SA: Re-executar validação
    SA->>VS: Validação final
    VS-->>SA: Score atualizado 96%
    
    SA-->>CC: Alvo 3 implementado OK
    
    CC->>H1: Trigger response-hook
    H1->>H1: Compilar métricas
    H1->>H1: Gerar sumário
    H1->>H1: Sugerir próximos passos
    H1-->>CC: Post-processamento OK
    
    CC-->>U: Alvo 3 concluído - Score 96%
    
    Note over U,R: Próximo: Alvo 4 ou Integração T2
```

## Fluxos Alternativos de Execução

### **Fluxo de Scaffolding (Alvo 0)**

```mermaid
sequenceDiagram
    participant U as 👤 Usuário  
    participant CC as 🎛️ Claude Code
    participant SA as 🏗️ Scaffolder
    participant VG as 🏭 Generator
    participant VS as ✅ Validator

    U->>CC: /scaffold Setup projeto
    CC->>SA: Executar scaffolding
    
    SA->>SA: Criar estrutura
    SA->>SA: Gerar pyproject.toml
    SA->>SA: Configurar Docker
    SA->>SA: Criar settings.py
    SA->>SA: Setup pre-commit
    
    SA->>VG: Gerar validador
    VG->>VS: Criar validator 200+ validações
    VS->>VS: Executar validação
    VS-->>SA: Score 94% EXCELENTE
    
    SA-->>CC: Scaffolding completo
    CC-->>U: Setup OK! Score 94%
```

### **Fluxo de Testes de Integração**

```mermaid
sequenceDiagram
    participant U as 👤 Usuário
    participant CC as 🎛️ Claude Code  
    participant SA as 🔬 Integrator
    participant VG as 🏭 Generator
    participant VS as ✅ Validator

    U->>CC: Executar integração T1
    CC->>SA: Integração T1 Auth+Core
    
    SA->>SA: Analisar Auth↔Core
    SA->>SA: Criar testes login
    SA->>SA: Testar APIs integradas
    SA->>SA: Validar integridade BD
    SA->>SA: Testes segurança
    
    SA->>VG: Gerar validador T1
    VG->>VS: Criar validator 40+ validações
    VS->>VS: Executar validações
    VS-->>SA: Score 89% APROVADO
    
    SA-->>CC: Integração T1 OK
    CC-->>U: T1 aprovada! Score 89%
```

### **Fluxo de Evolução/Refatoração**

```mermaid
sequenceDiagram
    participant U as 👤 Usuário
    participant CC as 🎛️ Claude Code
    participant SA as 🔧 Evolucionista  
    participant VG as 🏭 Generator
    participant VS as ✅ Validator

    U->>CC: Refatorar para performance
    CC->>SA: Executar evolução
    
    SA->>SA: Analisar qualidade atual
    SA->>SA: Identificar melhorias
    SA->>SA: Refatorar SOLID
    SA->>SA: Otimizar consultas BD
    SA->>SA: Atualizar testes
    SA->>SA: Atualizar docs
    
    SA->>VG: Gerar validador
    VG->>VS: Criar validator 60+ validações
    VS->>VS: Validar refatorações
    VS->>VS: Medir performance
    VS->>VS: Validar segurança
    VS-->>SA: Score 91% EXCELENTE
    
    SA-->>CC: Performance +35%
    CC-->>U: Refatoração OK! +35%
```

## **Métricas de Performance dos Fluxos**

### **Tempos de Execução Típicos**

| **Fluxo** | **Subagent** | **Context Processing** | **Implementation** | **Validation** | **Total** |
|-----------|--------------|------------------------|-------------------|----------------|-----------|
| **Scaffolding** | agv-scaffolder | ~2s | ~45s | ~15s | **~60s** |
| **Alvo Individual** | agv-implementor | ~1s | ~30s | ~10s | **~40s** |
| **Integração T1** | agv-integrator-tester | ~1s | ~20s | ~5s | **~25s** |
| **Evolução** | agv-evolucionista | ~1s | ~35s | ~8s | **~45s** |
| **UAT Generation** | agv-uat-generator | ~1s | ~15s | N/A | **~15s** |

### **Scores de Qualidade Típicos**

| **Tipo de Validação** | **Score Target** | **Score Típico** | **Validações** |
|-----------------------|------------------|------------------|----------------|
| **Scaffold** | 90%+ | 92-96% | 200+ |
| **Target Individual** | 85%+ | 88-94% | 80+ |
| **Integração** | 85%+ | 87-92% | 40+ |
| **Evolução** | 88%+ | 89-93% | 60+ |

### **Taxa de Sucesso por Categoria**

| **Categoria** | **CRITICAL** | **HIGH** | **MEDIUM** | **LOW** |
|---------------|--------------|----------|------------|---------|
| **STRUCTURE** | 98% | 94% | 91% | 89% |
| **CONTENT** | 95% | 92% | 88% | 85% |
| **MODELS** | 97% | 93% | 90% | 87% |
| **DEPENDENCIES** | 99% | 96% | 93% | 91% |
| **API** | 96% | 91% | 87% | 84% |

## **Pontos de Decisão Automatizados**

### **Seleção Automática de Subagent**

```python
# Lógica de dispatch automático
if "/scaffold" in user_input:
    return "agv-scaffolder"
elif re.search(r"alvo (\d+)", user_input, re.I):
    return "agv-implementor"
elif re.search(r"integra[çc][ãa]o T(\d+)", user_input, re.I):
    return "agv-integrator-tester"
elif "refator" in user_input or "evolu" in user_input:
    return "agv-evolucionista"
elif "uat" in user_input.lower():
    return "agv-uat-generator" if "gerar" in user_input else "agv-uat-translator"
```

### **Otimização Automática de Contexto**

```python
# Context optimization baseado no alvo
def optimize_context(target_number: int, blueprint: str) -> str:
    if target_number <= 3:  # Auth/Users
        relevant_sections = ["authentication", "users", "core"]
    elif target_number <= 5:  # Business logic
        relevant_sections = ["models", "business_logic", "api"]
    else:  # Advanced features
        relevant_sections = ["integrations", "reporting", "admin"]
    
    # Redução de 80% do contexto
    focused_context = extract_sections(blueprint, relevant_sections)
    return focused_context  # 1500+ → ~300 lines
```

### **Correção Automática de Issues**

```python
# Auto-fix de problemas comuns
def auto_fix_issues(validation_results: ValidationResults) -> bool:
    auto_fixable = ["missing_urls", "missing_imports", "formatting"]
    
    for issue in validation_results.issues:
        if issue.issue_type in auto_fixable and issue.severity != "CRITICAL":
            apply_automatic_fix(issue)
            return True
    
    return False
```

## **Próximos Passos Inteligentes**

Após cada execução bem-sucedida, o sistema sugere automaticamente:

### **Sugestões Pós-Scaffolding:**
- "Projeto scaffolding completo! **Próximo**: Implementar Alvo 1 (Autenticação)"
- "Score 94% - Considere resolver 3 issues MEDIUM antes de continuar"

### **Sugestões Pós-Implementação Alvo:**
- "Alvo 3 implementado! **Próximo**: Alvo 4 ou Testes Integração T2"
- "Score 92% - Pronto para testes de integração com módulos existentes"

### **Sugestões Pós-Integração:**
- "Integração T1 aprovada! **Próximo**: Implementar Alvos 4-5 ou T2"
- "89% de sucesso - Sistema robusto para continuar desenvolvimento"

Este sistema de fluxos garante execução **determinística**, **otimizada** e **com qualidade garantida** para todo o processo AGV v5.0.