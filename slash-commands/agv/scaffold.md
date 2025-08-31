---
description: "Executa Alvo 0 com validação automática profunda integrada"
allowed_tools: ["Task", "Write", "LS", "Bash"]
---

# AGV Scaffold + Validação Automática

Executa o Alvo 0 (Setup Profissional) seguido de **validação automática profunda** linha por linha vs Blueprint.

## Fluxo Automatizado com Validação

### Etapa 1: Extração de Contexto de Setup

Primeiro, vou extrair do Blueprint apenas as seções relevantes para o setup inicial:

- Estrutura de Diretórios Proposta
- Arquivos de Configuração (.gitignore, README.md, LICENSE)
- Configurações de Ambiente (pyproject.toml, package.json, docker-compose.yml)
- Estrutura de Testes (diretórios e arquivos base)

### Etapa 1.2: Geração Automática do Validador PROFISSIONAL

Primeiro, gero automaticamente um validador PROFISSIONAL específico para este Blueprint:

```bash
python scripts/validator_generator.py BLUEPRINT_ARQUITETURAL.md
```

Este comando irá:

- Analisar o Blueprint arquitetural com parser avançado e inteligente
- Extrair especificações complexas (modelos Django, multi-tenancy, dependências com versões)
- Gerar validações profundas de conteúdo (não só existência de arquivos)
- Criar validações específicas para modelos, configurações e dependências
- Gerar um `scripts/validate_scaffold.py` de NÍVEL PROFISSIONAL (67+ validações)
- Incluir validações por categoria: STRUCTURE, CONTENT, MODELS, DEPENDENCIES, API

### Etapa 1.3: Delegação para AGV-Scaffolder

Após gerar o validador customizado, delego a criação completa do scaffolding:

Delegue para o subagent "agv-scaffolder" a tarefa de executar o Alvo 0 completo baseado no:

- Blueprint: BLUEPRINT_ARQUITETURAL.md

### Etapa 2: Validação Automática Profunda

Após o scaffold, executo automaticamente o validador profundo que:

- ✅ Analisa **100+ verificações** linha por linha
- ✅ Valida conteúdo real vs especificações Blueprint
- ✅ Verifica JSON/YAML válidos
- ✅ Confirma dependências exatas
- ✅ Sistema de pontuação ponderado por severidade

### Etapa 3: Aprovação/Rejeição

Primeiro, obtenho o threshold atual dinamicamente:

```bash
CURRENT_THRESHOLD=$(python scripts/validation_config.py threshold)
echo "Threshold ativo: $CURRENT_THRESHOLD"
```

- **Score ≥ Threshold Ativo:** Scaffold aprovado, pode prosseguir
- **Score < Threshold Ativo:** Scaffold rejeitado, corrigir antes de prosseguir

## Processo de Execução

### Executar Geração do Validador PROFISSIONAL

Primeiro, execute o ValidatorGenerator PRO para criar validador de nível profissional:

```bash
python scripts/validator_generator.py BLUEPRINT_ARQUITETURAL.md
```

### Executar Scaffold

Após gerar o validador customizado, delegue para o subagent "agv-scaffolder" a tarefa de executar o Alvo 0 completo baseado no Blueprint Arquitetural.

## Resultado Esperado do Scaffold

- Estrutura completa de diretórios
- Todos os arquivos de configuração
- Arquivos de código com docstrings (SEM lógica de negócio)
- Estrutura de testes preparada
- Instruções de setup para o coordenador

### Executar Validação Profunda

Após o scaffold, execute automaticamente:

```bash
python scripts/post_scaffold_validation.py
```

Este script irá:

1. Executar validação profunda (`validate_scaffold.py`)
2. Analisar 100+ verificações
3. Gerar relatório detalhado
4. Aprovar/rejeitar baseado no score

## Resultado Esperado

**Verificação Dinâmica do Threshold:**

```bash
CURRENT_THRESHOLD=$(python scripts/validation_config.py threshold)
echo "Usando threshold: $CURRENT_THRESHOLD"
```

**Se Score ≥ Threshold Ativo:**

- ✅ Scaffold aprovado
- ✅ Relatório de conformidade
- ✅ Pronto para Alvo 1

**Se Score < Threshold Ativo:**

- ❌ Scaffold rejeitado
- 📋 Lista detalhada de problemas
- 🔧 Recomendações de correção
- ⚠️ Bloqueio para próximos alvos

**Gerenciamento de Profiles:**
```bash
python scripts/validation_config.py list        # Ver profiles disponíveis
python scripts/validation_config.py threshold   # Ver threshold atual
python scripts/validation_config.py switch development  # Trocar para development (65%)
```
