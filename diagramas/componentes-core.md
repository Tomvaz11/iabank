# Componentes Core - Sistema AGV v5.0

## Diagrama Detalhado dos Componentes Core

```mermaid
graph TB
    subgraph "CORE COMPONENTS - SISTEMA AGV v5.0"
        direction TB
        
        subgraph "BLUEPRINT PARSING LAYER"
            direction TB
            BP[BLUEPRINT_ARQUITETURAL.md]
            
            subgraph "AdvancedBlueprintParser"
                direction LR
                BPP1[_extract_project_info<br/>Nome, Descrição]
                BPP2[_extract_technology_stack<br/>Django, React, PostgreSQL]
                BPP3[_extract_directory_structure<br/>Estrutura Completa]
                BPP4[_extract_models_deep<br/>Modelos + Relacionamentos]
                BPP5[_extract_dependencies<br/>Deps + Versões]
                BPP6[_extract_authentication<br/>JWT, Session, Token]
                BPP7[_extract_multi_tenancy<br/>BaseTenantModel]
                BPP8[_extract_file_content_validations<br/>Validações Específicas]
            end
            
            SPECS[ProjectSpecs<br/>Especificações Completas<br/>- project_name, backend_framework<br/>- models, relationships<br/>- dependencies, authentication<br/>- multi_tenancy, file_validations]
        end
        
        subgraph "VALIDATION RULES SYSTEM"
            direction TB
            VR[ValidationRule<br/>Dataclass:<br/>- name: str<br/>- description: str<br/>- code: str<br/>- severity: CRITICAL-HIGH-MEDIUM-LOW<br/>- category: STRUCTURE-CONTENT-MODELS-DEPENDENCIES-API]
        end
        
        subgraph "BASE GENERATOR SYSTEM"
            direction TB
            BG[BaseGenerator Abstract<br/>Classe Base para Todos Geradores]
            
            subgraph "MÉTODOS COMPARTILHADOS"
                direction LR
                BG1[_create_directory_validation_code<br/>Valida Estrutura Diretórios]
                BG2[_create_content_validation_code<br/>Valida Conteúdo Arquivos]
                BG3[_create_specific_dependency_validation<br/>Valida Dependência Específica]
                BG4[_create_models_validation_code<br/>Valida Modelos Django]
                BG5[_create_specific_model_validation<br/>Valida Modelo Específico]
                BG6[_create_multi_tenancy_validation_code<br/>Valida Multi-tenancy]
            end
        end
        
        subgraph "CONTEXT OPTIMIZATION SYSTEM"
            direction TB
            
            subgraph "AGVContextExtractor"
                direction LR
                CE1[extract_target_context<br/>Extrai Contexto Focado]
                CE2[_map_target_dependencies<br/>Mapeia Dependências Alvo]
                CE3[_extract_blueprint_sections<br/>Extrai Seções Relevantes]
                CE4[_extract_target_details<br/>Detalhes Específicos Alvo]
                CE5[Redução 80% Contexto<br/>1500+ → ~300 linhas]
            end
            
            subgraph "FocusedContextInjector"
                direction LR
                CI1[inject_context_to_prompt<br/>Injeta Contexto no Prompt]
                CI2[agv_context_target_N.md<br/>Arquivo Contexto Focado]
                CI3[TARGET Environment Variable<br/>Controle por Variável]
            end
        end
    end
    
    %% CONEXÕES
    BP --> BPP1
    BP --> BPP2
    BP --> BPP3
    BP --> BPP4
    BP --> BPP5
    BP --> BPP6
    BP --> BPP7
    BP --> BPP8
    
    BPP1 --> SPECS
    BPP2 --> SPECS
    BPP3 --> SPECS
    BPP4 --> SPECS
    BPP5 --> SPECS
    BPP6 --> SPECS
    BPP7 --> SPECS
    BPP8 --> SPECS
    
    SPECS --> BG
    BG --> BG1
    BG --> BG2
    BG --> BG3
    BG --> BG4
    BG --> BG5
    BG --> BG6
    
    SPECS --> CE1
    CE1 --> CE2
    CE1 --> CE3
    CE1 --> CE4
    CE1 --> CE5
    
    CE5 --> CI2
    CI2 --> CI1
    CI3 --> CI1
    
    %% STYLING
    classDef parser fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#000
    classDef specs fill:#F1F8E9,stroke:#388E3C,stroke-width:2px,color:#000
    classDef rules fill:#FFF8E1,stroke:#F57C00,stroke-width:2px,color:#000
    classDef generator fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    classDef context fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#000
    
    class BP,BPP1,BPP2,BPP3,BPP4,BPP5,BPP6,BPP7,BPP8 parser
    class SPECS specs
    class VR rules
    class BG,BG1,BG2,BG3,BG4,BG5,BG6 generator
    class CE1,CE2,CE3,CE4,CE5,CI1,CI2,CI3 context
```

## Detalhamento dos Componentes

### **AdvancedBlueprintParser**
O parser inteligente que extrai especificações complexas do Blueprint:

#### **Métodos de Extração:**
- **`_extract_project_info()`** - Nome e descrição do projeto
- **`_extract_technology_stack()`** - Django, React, PostgreSQL com versões
- **`_extract_directory_structure()`** - Árvore completa de diretórios
- **`_extract_models_deep()`** - Modelos Django com campos e relacionamentos
- **`_extract_dependencies()`** - Dependências backend/frontend com versões
- **`_extract_authentication()`** - JWT, Session ou Token
- **`_extract_multi_tenancy()`** - Detecta BaseTenantModel
- **`_extract_file_content_validations()`** - Validações específicas por arquivo

### **ProjectSpecs (Dataclass)**
Especificações completas extraídas do Blueprint:

```python
@dataclass
class ProjectSpecs:
    project_name: str
    backend_framework: str          # django, flask, etc
    frontend_framework: str         # react, vue, etc
    database: str                   # postgresql, mysql, etc
    architecture_type: str          # monolith, microservices
    models: Dict[str, Dict]         # modelo -> {fields: [], meta: {}}
    dependencies: Dict[str, List]   # backend/frontend
    multi_tenancy: bool
    authentication_method: str      # JWT, Token, Session
    file_content_validations: Dict  # arquivo -> validações
    # ... mais 15+ campos especializados
```

### **ValidationRule System**
Sistema de regras de validação padronizadas:

```python
@dataclass  
class ValidationRule:
    name: str                      # validate_django_models
    description: str               # "Valida modelos Django"
    code: str                      # Código Python gerado
    severity: str                  # CRITICAL-HIGH-MEDIUM-LOW
    category: str                  # STRUCTURE-CONTENT-MODELS-DEPENDENCIES-API
```

### **BaseGenerator (Abstract)**
Classe base abstrata com métodos compartilhados:

#### **Métodos Utilitários:**
- **`_create_directory_validation_code()`** - Gera código para validar estrutura
- **`_create_content_validation_code()`** - Gera código para validar conteúdo
- **`_create_specific_dependency_validation()`** - Valida dependência específica
- **`_create_models_validation_code()`** - Valida modelos Django gerais
- **`_create_specific_model_validation()`** - Valida modelo específico
- **`_create_multi_tenancy_validation_code()`** - Valida multi-tenancy

### **Context Optimization System**

#### **AGVContextExtractor**
Extrator de contexto focado que reduz em 80% o tamanho:

- **Input**: Blueprint completo (1500+ linhas)
- **Output**: Contexto focado (~300 linhas)
- **Benefício**: Performance e precisão dos subagents

#### **FocusedContextInjector**
Injetor dinâmico de contexto:

- **Controle**: Variável ambiente `TARGET`
- **Arquivo**: `agv_context_target_N.md`
- **Integração**: Automática com subagents

## **Fluxo de Processamento Core**

1. **Blueprint** → **AdvancedBlueprintParser** → **ProjectSpecs**
2. **ProjectSpecs** → **BaseGenerator** → **ValidationRules**
3. **Contexto Otimizado** → **Subagents** → **Validação Dinâmica**

## **Métricas de Performance**

- **Parsing**: ~2s para Blueprint de 1500+ linhas
- **Redução Contexto**: 80% (1500→300 linhas)
- **Geração Validador**: ~5s para 200+ regras
- **Execução Validação**: ~10s para projeto completo