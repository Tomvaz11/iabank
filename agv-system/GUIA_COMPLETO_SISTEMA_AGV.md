# Guia Completo do Sistema AGV v5.0

## Índice
1. [Método AGV - Conceito Central](#método-agv-conceito-central)
2. [Tecnologias do IABANK](#tecnologias-do-iabank-stack-tecnológica)
3. [Sistema de Subagents](#sistema-de-subagents---o-que-são-e-como-funcionam)
4. [Sistema de Slash Commands](#sistema-de-slash-commands---interface-simplificada)
5. [Sistema de Hooks](#sistema-de-hooks---automação-inteligente)
6. [Scripts de Automação](#scripts-de-automação---o-cérebro-do-sistema)
7. [Integração dos 4 Sistemas](#integração-como-os-4-sistemas-trabalham-juntos)
8. [Por Que Isso É Revolucionário](#por-que-isso-é-revolucionário)

---

## Método AGV (Arquitetura Guiada por Valor)

### **Conceito Central**
O AGV é uma metodologia proprietária que combina:
- **Arquitetura Limpa (Clean Architecture)** - Separação em camadas bem definidas
- **Development Orientado por Blueprint** - Documento único da verdade arquitetural  
- **Implementação Sequencial** - Alvos numerados com dependências claras
- **Testes de Integração Estratégicos** - Paradas T1-T8 para validação incremental

### **Fluxo de Trabalho AGV**
```
Blueprint → Ordem → Alvo 0 (Setup) → Alvo 1-N → Testes → Evolução
```

---

## Tecnologias do IABANK (Stack Tecnológica)

### **Backend - Django (Python)**
```python
# Arquitetura em 4 Camadas
IABANK/
├── backend/iabank/
│   ├── core/          # Domínio + Infraestrutura Base
│   ├── users/         # Autenticação JWT
│   ├── customers/     # Gestão de Clientes
│   ├── operations/    # Empréstimos e Parcelas  
│   └── finance/       # Controle Financeiro
```

**Principais Tecnologias Backend:**
- **Django 4.x** - Framework web robusto
- **Django REST Framework (DRF)** - APIs RESTful  
- **PostgreSQL** - Banco de dados principal
- **JWT (djangorestframework-simplejwt)** - Autenticação stateless
- **Celery** - Processamento assíncrono (futuro)
- **Docker** - Containerização

### **Frontend - React SPA**
```typescript
frontend/
├── src/
│   ├── components/    # Componentes reutilizáveis
│   ├── pages/         # Páginas/Views
│   ├── services/      # Clientes API
│   └── utils/         # Utilitários
```

**Principais Tecnologias Frontend:**
- **React 18** - Biblioteca de interface
- **TypeScript** - Tipagem estática
- **Vite** - Build tool moderna e rápida
- **React Router** - Roteamento SPA
- **Axios** - Cliente HTTP para APIs
- **Material-UI/TailwindCSS** - Componentes visuais

### **Multi-Tenancy (Isolamento de Dados)**
```python
# Cada modelo herda de BaseTenantModel
class Customer(BaseTenantModel):
    tenant = models.ForeignKey(Tenant)  # Automático
    name = models.CharField(max_length=255)
    # Dados isolados por tenant
```

**Como Funciona:**
1. **Tenant** = Empresa/Cliente da plataforma
2. **Middleware** intercepta requisições e identifica o tenant
3. **BaseTenantModel** garante isolamento automático
4. **Cada query** filtra automaticamente por tenant

---

## Sistema de Subagents - O Que São e Como Funcionam

### **Conceito**
Os **Subagents** são **versões especializadas do Claude** que você pode criar dentro do Claude Code. Pense neles como "Claude com superpoderes específicos" - cada um é treinado para uma tarefa muito específica.

### **Como Funciona Tecnicamente**

**No Claude Code:**
```bash
/agents:new agv-implementor  # Cria um novo subagent
```

**O que acontece:**
1. Você dá um **nome** para o subagent
2. Você define uma **descrição** (o que ele faz)
3. Você escreve um **System Prompt** (as instruções específicas)
4. Você escolhe quais **ferramentas** ele pode usar

**Exemplo Real - AGV-Implementor:**
```yaml
Nome: agv-implementor
Descrição: Desenvolvedor especializado em implementar alvos específicos do AGV
System Prompt: |
  Você é o F4-ImplementadorMestre do Método AGV v5.0.
  Implementa APENAS o alvo especificado seguindo o Blueprint...
  [instruções detalhadas de 100+ linhas]
Ferramentas: Write, Edit, Read, Bash
```

### **Por Que Usar Subagents?**

**Problema Tradicional:**
```
Você: "Implemente o sistema de autenticação JWT"
Claude: "Ok, vou fazer... mas preciso de mais contexto... 
         e não sei exatamente qual padrão seguir..."
```

**Com Subagent Especializado:**
```
Você: /agv:implement 7  # Chama AGV-Implementor para alvo 7
Subagent: "Implementando alvo 7: Autenticação JWT conforme 
           Blueprint, seguindo padrões AGV, com testes 
           obrigatórios e documentação..."
```

### **Vantagens:**
- **Foco:** Cada subagent sabe exatamente o que fazer
- **Consistência:** Sempre segue os mesmos padrões
- **Qualidade:** Tem instruções específicas para qualidade
- **Eficiência:** Não perde tempo com dúvidas de contexto

### **7 Subagents Especializados**

**1. AGV-Context-Analyzer**
- **Função:** Reduz Blueprint de 1000+ linhas para ~200 linhas focadas  
- **Quando usar:** Antes de implementar alvos específicos
- **Exemplo:** `/agv:context 5` extrai apenas contexto do Alvo 5

**2. AGV-Scaffolder**  
- **Função:** Executa APENAS Alvo 0 (Setup inicial)
- **Cria:** Estrutura de diretórios, configs, arquivos base
- **Exemplo:** `/agv:scaffold` monta projeto inteiro do zero

**3. AGV-Implementor**
- **Função:** Implementa alvos 1-N com contexto otimizado
- **Inclui:** Código + testes unitários + documentação
- **Exemplo:** `/agv:implement 5` implementa modelos de User

**4. AGV-Integrator-Tester**
- **Função:** Executa testes de integração T1-T8 nas paradas
- **Valida:** Colaboração entre módulos implementados
- **Exemplo:** `/agv:test-integration` após grupo de alvos

**5. AGV-UAT-Generator**
- **Função:** Gera cenários de teste manuais E2E
- **Base:** Exclusivamente Blueprint (perspectiva usuário final)
- **Exemplo:** `/agv:uat-generate` cria testes de aceitação

**6. AGV-UAT-Translator**  
- **Função:** Converte UAT manuais em testes automatizados
- **Diferencial:** Testa backend sem UI (direto nos services)
- **Exemplo:** `/agv:uat-automate` traduz cenários para pytest

**7. AGV-Evolucionista**
- **Função:** Manutenção, bugs, refatorações, novas features
- **Foco:** Evolução sem quebrar arquitetura existente  
- **Exemplo:** `/agv:evolve "corrigir bug no cálculo de juros"`

---

## Sistema de Slash Commands - Interface Simplificada

### **Conceito**
Os **Slash Commands** são **comandos personalizados** que você pode criar no Claude Code. Funcionam como "atalhos inteligentes" que automatizam sequências complexas de ações.

### **Como Funciona Tecnicamente**

**Estrutura de um Slash Command:**
```markdown
---
description: "Executa o Alvo 0 usando AGV-Scaffolder"
allowed_tools: ["Task", "Write", "Bash"]
---

# AGV Scaffold - Processo Automatizado

## Etapa 1: Extração de Contexto
Extrair seções do Blueprint relevantes para setup...

## Etapa 2: Delegação para Subagent
Delegar para "agv-scaffolder" a criação completa...

## Etapa 3: Validação
Validar se estrutura foi criada corretamente...
```

**Localização dos Arquivos:**
```
IABANK/
└── slash-commands/agv/
    ├── scaffold.md         # /agv:scaffold
    ├── implement.md        # /agv:implement
    ├── test-integration.md # /agv:test-integration
    └── ...
```

### **Como Usar:**
```bash
# Em vez de escrever isso:
"Crie a estrutura inicial do projeto seguindo o Blueprint, 
delegue para o subagent agv-scaffolder, valide os arquivos..."

# Você simplesmente digita:
/agv:scaffold
```

### **Comandos Disponíveis:**

```bash
# Setup e Implementação
/agv:scaffold          # Alvo 0: Estrutura completa
/agv:implement 1       # Implementa alvo específico  
/agv:status           # Mostra progresso vs Ordem

# Testes e Qualidade
/agv:test-integration # Testes T1-T8 nas paradas
/agv:uat-generate     # Cenários UAT manuais
/agv:uat-automate     # Testes automatizados backend

# Manutenção e Debug  
/agv:evolve "task"    # Evolução pós-implementação
/agv:context 5        # Ver contexto focado do alvo 5
/agv:validate         # Validar conformidade Blueprint
```

### **Exemplo Real - Implementação:**

**Comando:** `/agv:implement 5`

**O que acontece internamente:**
1. Lê o arquivo `implement.md`
2. Substitui `{alvo}` por `5`
3. Chama o `agv-context-analyzer` para extrair contexto do alvo 5
4. Chama o `agv-implementor` com o contexto focado
5. Valida se implementação seguiu o Blueprint

**Vantagens:**
- **Simplicidade:** Um comando vs. explicação longa
- **Padronização:** Sempre executa da mesma forma
- **Automação:** Encadeia múltiplas ações automaticamente
- **Reutilização:** Funciona para qualquer projeto AGV

---

## Sistema de Hooks - Automação Inteligente

### **Conceito**
Os **Hooks** são **scripts que executam automaticamente** em resposta a eventos específicos no Claude Code. Pense neles como "gatilhos" que disparam ações automáticas.

### **Como Funcionam Tecnicamente**

**Eventos Disponíveis:**
```yaml
# Configuração no Claude Code
hooks:
  user-prompt-submit:     # Antes de processar comando do usuário
  tool-call-start:        # Antes de executar uma ferramenta  
  tool-call-end:          # Depois de executar uma ferramenta
  file-write:             # Quando um arquivo é criado/modificado
  task-complete:          # Quando uma tarefa é finalizada
```

**Exemplo Real - Hook de Context Injection:**
```bash
# Hook que executa ANTES de chamar subagents
# Arquivo: hooks/pre_task_context_injection.sh

if [[ $TASK_TYPE == "agv-implementor" ]]; then
    # Extrai contexto focado automaticamente
    python agv-system/scripts/agv_context_extractor.py --alvo=$ALVO_NUMBER
    
    # Injeta contexto no prompt do subagent
    python agv-system/scripts/inject_focused_context.py --target=$TASK_ID
fi
```

### **Hooks Configurados no AGV:**

**1. Pre-Task Context Extraction:**
- **Quando:** Antes de chamar qualquer subagent
- **Função:** Extrai automaticamente contexto relevante do Blueprint
- **Resultado:** Subagent recebe apenas informações necessárias

**2. Post-File Validation:**
- **Quando:** Depois de criar/modificar arquivo
- **Função:** Valida se arquivo está conforme Blueprint
- **Resultado:** Avisa se há divergências arquiteturais

**3. Quality Gate:**
- **Quando:** Depois de implementar código
- **Função:** Executa linting, testes, verificações automáticas
- **Resultado:** Bloqueia se qualidade não atender critérios

**4. Context Cleanup:**
- **Quando:** Fim de cada tarefa
- **Função:** Remove arquivos temporários, limpa cache
- **Resultado:** Workspace sempre limpo

### **Exemplo de Fluxo com Hooks:**

```bash
Você: /agv:implement 5

# 1. PRE-TASK HOOK executa automaticamente:
Hook: "Extraindo contexto do alvo 5..."
Hook: "Blueprint: 1000 linhas → 180 linhas focadas"
Hook: "Injetando contexto no agv-implementor..."

# 2. SUBAGENT executa com contexto otimizado:
AGV-Implementor: "Implementando User model..."
AGV-Implementor: "Criando testes unitários..."
AGV-Implementor: "Gerando documentação..."

# 3. POST-FILE HOOK valida cada arquivo:
Hook: "Validando models.py → ✅ Conforme Blueprint"
Hook: "Validando test_models.py → ✅ Estrutura correta"

# 4. CLEANUP HOOK limpa ambiente:
Hook: "Removendo arquivos temporários..."
Hook: "Limpando cache de contexto..."

Result: "Alvo 5 implementado com sucesso!"
```

---

## Scripts de Automação - O Cérebro do Sistema

### **Conceito**
Os **Scripts de Automação** são **programas Python** que executam a lógica inteligente por trás dos hooks e subagents. São o "cérebro" que automatiza as tarefas complexas.

### **Scripts de Automação - Funcionalidades**

**1. validator_generator.py - O Gerador de Validação Profissional**
```python
# Função Principal: Gerar automaticamente 67+ validações profissionais categorizadas

class ValidatorGenerator:
    def generate_professional_validator(self):
        # 1. Parse do Blueprint com AdvancedBlueprintParser
        # 2. Categorização: STRUCTURE, CONTENT, MODELS, DEPENDENCIES, API
        # 3. Geração automática de 67+ regras de validação
        # 4. Sistema de scoring ponderado por categoria
        # 5. Integração com sistema de 6 profiles adaptativos
        # 6. UTF-8 encoding com fallback automático
        
        return {
            'validations': 67,                # Total de validações geradas
            'categories': 5,                  # STRUCTURE, CONTENT, MODELS, DEPENDENCIES, API
            'profiles': 6,                    # development, moderate, strict, production, ci_cd, architecture_review
            'ignored_problematic': 21,        # Validações problemáticas filtradas
            'scoring_system': 'weighted',     # Sistema de scoring ponderado
            'auto_generated': True,           # 100% automático
            'quality': 'PROFESSIONAL'         # Nível sênior
        }
```

**Exemplo Prático:**
- **Input:** Blueprint IABANK (1000+ linhas)
- **Processo:** Parse inteligente → Categorização → Geração automática
- **Output:** `validate_scaffold.py` (3885 linhas, 67 validações)

**Categorias de Validação:**
- **STRUCTURE** (peso 1.0): Diretórios, arquivos base, configurações
- **CONTENT** (peso 1.5): Conteúdo dos arquivos, imports, configurações
- **MODELS** (peso 2.0): Modelos Django, campos, herança BaseTenantModel
- **DEPENDENCIES** (peso 1.0): requirements.txt, package.json
- **API** (peso 1.3): Endpoints DRF, serializers, ViewSets

**2. agv_context_extractor.py - O Otimizador Inteligente**
```python
# Função Principal: Reduzir contexto de 1000+ linhas para ~200 linhas

class AGVContextExtractor:
    def extract_target_context(self, target_num: int):
        # 1. Mapeia alvo para dependências
        # 2. Extrai seções relevantes do Blueprint  
        # 3. Identifica arquivos de código necessários
        # 4. Calcula redução percentual (80%+)
        
        return {
            'focused_context': "...",      # Contexto otimizado
            'dependencies': [...],         # Dependências do alvo
            'reduction_pct': 85.3         # % de otimização
        }
```

**Exemplo Prático:**
- **Input:** Blueprint completo (1200 linhas) + Alvo 7 (Autenticação JWT)
- **Processo:** Analisa que Alvo 7 precisa apenas de `users`, `core.Tenant`, API patterns
- **Output:** 180 linhas focadas (85% de redução)

**3. validate_blueprint_conformity.py - O Fiscal da Qualidade**
```python
class BlueprintParser:
    def extract_specifications():
        # Extrai do Blueprint:
        return {
            'stack': ['Django', 'DRF', 'PostgreSQL'],
            'models': ['User', 'Tenant', 'Customer'],
            'structure': ['backend/', 'frontend/'],
            'apis': ['/api/v1/token/', '/api/v1/customers/']
        }

class ConformityValidator:
    def validate_implementation():
        # Compara implementação real vs. especificação
        # Gera relatório de conformidade
```

**Exemplo de Validação:**
```bash
python validate_blueprint_conformity.py --check=models

✅ User model: CONFORME (todos campos obrigatórios presentes)
❌ Customer model: NÃO CONFORME (campo 'phone' obrigatório ausente)
⚠️  Loan model: AVISO (campo extra 'notes' não especificado)
```

**4. inject_focused_context.py - O Injetor Automático**
```python
# Injeta contexto otimizado nos prompts dos subagents
def inject_context_into_prompt(subagent_id, focused_context):
    # 1. Lê prompt original do subagent
    # 2. Adiciona contexto focado automaticamente
    # 3. Atualiza prompt temporariamente
    
    prompt_enhanced = f"""
    {original_prompt}
    
    CONTEXTO FOCADO PARA ESTA TAREFA:
    {focused_context}
    """
```

**5. validate_agv_quality.py - O Guardião dos Padrões**
```python
class QualityValidator:
    def run_quality_checks():
        return {
            'linting': self.check_code_style(),      # PEP8, ESLint
            'tests': self.validate_test_coverage(),   # >80% coverage
            'docs': self.check_documentation(),       # Docstrings obrigatórias
            'architecture': self.validate_layers()    # Separação de camadas
        }
```

**6. validation_config.py - O Sistema de Profiles**
```python
# Sistema de 6 profiles de validação com thresholds adaptativos
class ValidationConfig:
    def switch_profile(self, profile_name):
        # Profiles disponíveis:
        # - development: 65% threshold (foco em STRUCTURE + MODELS)
        # - moderate: 75% threshold (+ CONTENT)
        # - strict: 90% threshold (+ DEPENDENCIES + API)
        # - production: 85% threshold (perfil balanceado)
        # - ci_cd: 75% threshold (otimizado para CI/CD)
        # - architecture_review: 95% threshold (validação máxima)
        
        return {
            'active_profile': profile_name,
            'threshold': self.profiles[profile_name]['min_score_threshold'],
            'categories': self.profiles[profile_name]['required_categories'],
            'ignored_validations': 21  # Validações problemáticas filtradas
        }
```

**7. setup_validation_profiles.py - O Configurador Otimizado**
```python
# Cria profiles otimizados para Django+React
class ProfileSetup:
    def create_optimized_profiles():
        # Configura profiles específicos para projetos Django+React
        # Remove 21 validações problemáticas que geram ruído
        # Ajusta category_weights: MODELS(2.0), CONTENT(1.5), API(1.3)
        # Configura tolerâncias para arquivos opcionais (docker, CI/CD)
        
        return {
            'profiles_created': 6,
            'validations_filtered': 21,
            'optimized_for': 'Django+React multi-tenant'
        }
```

---

## Integração: Como os 4 Sistemas Trabalham Juntos

### **Fluxo Completo - Exemplo Real:**

```bash
# Você digita:
/agv:implement 7
```

**1. SLASH COMMAND processa:**
```markdown
# O arquivo implement.md é executado
Etapa 1: Extrair contexto focado para alvo 7
Etapa 2: Chamar agv-implementor com contexto otimizado
Etapa 3: Validar implementação
```

**2. HOOK PRE-TASK executa automaticamente:**
```bash
Hook: python agv-system/scripts/agv_context_extractor.py --alvo=7
# Reduz Blueprint de 1200 → 185 linhas (84.6% redução)
```

**3. SCRIPT DE CONTEXTO trabalha:**
```python
# agv_context_extractor.py analisa:
- Alvo 7 = Autenticação JWT
- Precisa de: core.User, core.Tenant, DRF patterns
- Ignora: Customer, Loan, Finance (não relevantes)
- Gera contexto focado de 185 linhas
```

**4. HOOK INJECTION executa:**
```bash
Hook: python agv-system/scripts/inject_focused_context.py --target=agv-implementor
# Injeta contexto focado no prompt do subagent
```

**5. SUBAGENT AGV-IMPLEMENTOR executa:**
```
Subagent: "Recebido contexto focado (185 linhas)
          Implementando User model + JWT views + testes..."
```

**6. HOOK POST-FILE valida cada arquivo criado:**
```bash
Hook: python agv-system/scripts/validate_blueprint_conformity.py --file=models.py
✅ models.py: CONFORME Blueprint
```

**7. HOOK QUALITY executa:**
```bash
Hook: python agv-system/scripts/validate_agv_quality.py --check=all
✅ Linting: PEP8 ok
✅ Testes: 92% coverage
✅ Docs: Docstrings presentes
```

**8. RESULTADO:**
```
Alvo 7 implementado com sucesso!
- Arquivos: models.py, views.py, serializers.py, tests.py
- Qualidade: 92% test coverage
- Conformidade: 100% Blueprint
- Otimização: 84.6% redução de contexto
```

### **RESUMO - O Que Cada Sistema Faz**

| Sistema | Função | Exemplo |
|---------|--------|---------|
| **Subagents** | Claude especializado | AGV-Implementor implementa código |
| **Slash Commands** | Interface simplificada | `/agv:implement 7` |
| **Hooks** | Automação por eventos | Auto-valida depois de criar arquivo |
| **Scripts** | Lógica inteligente | Reduz contexto 1200→185 linhas |

---

## Por Que Isso É Revolucionário?

### **Sem o Sistema:**
- Você explica tudo manualmente cada vez
- Claude pode esquecer padrões ou contexto
- Qualidade inconsistente
- Muito tempo gasto com repetição

### **Com o Sistema:**
- `/agv:implement 7` = implementação completa e consistente
- Contexto otimizado automaticamente (80% menos texto)
- Qualidade garantida por validação automática
- Velocidade 10x maior com qualidade superior

**É como ter uma equipe de 7 desenvolvedores especializados trabalhando perfeitamente coordenados!**

---

## Como Começar o IABANK

### **1. Execute o Setup Inicial (Alvo 0) com Validação Automática:**
```bash
/agv:scaffold
```
Isso irá:
- ✅ Criar toda a estrutura base do projeto (diretórios, arquivos de configuração, estrutura de testes)
- ✅ **Executar ValidatorGenerator v2.0** (67+ validações profissionais categorizadas)
- ✅ **Aprovar/rejeitar automaticamente** baseado no score de conformidade ponderado (≥95% no profile architecture_review ativo)

### **2. Verifique o Status:**
```bash
/agv:status
```
Mostrará qual o próximo alvo a implementar.

### **3. Implemente o Primeiro Alvo:**
```bash
/agv:implement 1
```
Implementará os modelos base (`Tenant`, `BaseTenantModel`) do módulo `iabank.core`.

### **4. Continue a Sequência:**
```bash
/agv:implement 2
/agv:implement 3
# etc...
```

### **5. Testes de Integração nas Paradas:**
Quando chegar nas "PARADAS DE TESTES", use:
```bash
/agv:test-integration
```

### **6. Gerar Testes UAT (quando necessário):**
```bash
/agv:uat-generate
/agv:uat-automate
```

---

## Checklist de Setup dos Subagents

Para usar o sistema, você precisa criar os 7 subagents usando `/agents:new` e colar as configurações do arquivo `AGV_SUBAGENTS_CONFIGURACOES_COMPLETAS.md`:

- [ ] agv-context-analyzer
- [ ] agv-scaffolder  
- [ ] agv-implementor
- [ ] agv-integrator-tester
- [ ] agv-uat-generator
- [ ] agv-uat-translator
- [ ] agv-evolucionista

**Após criar todos os subagents, você pode começar com:** `/agv:scaffold`