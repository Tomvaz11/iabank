---
description: "Valida conformidade da codebase atual com o Blueprint Arquitetural"
allowed_tools: ["Read", "Grep", "Glob", "Bash"]
---

# AGV Validate - Validação de Conformidade com Blueprint

Executa validação abrangente da codebase atual contra o Blueprint Arquitetural para identificar desvios arquiteturais ou violações de padrões.

## Processo de Validação

### Etapa 1: Validação Automática de Conformidade com Blueprint
Executar validação automática usando o novo validador:

```bash
python agv-system/scripts/agv-blueprint
```

Este script irá:
- Analisar o Blueprint e extrair especificações estruturadas
- Analisar a implementação atual do código
- Comparar Blueprint vs Implementação
- Gerar score de conformidade e relatório detalhado

### Etapa 2: Validação Arquitetural Manual  
Verificar aspectos que requerem validação manual:

**Estrutura de Diretórios:**
- Comparar estrutura atual com a proposta no Blueprint
- Verificar se módulos/aplicações estão organizados corretamente
- Validar estrutura do frontend (features, shared, entities)

**Separação de Camadas:**
- Apresentação: Views e Serializers
- Aplicação: Services e DTOs  
- Domínio: Models e lógica de negócio
- Infraestrutura: Repositórios e integrações

### Etapa 2: Validação de Contratos
Verificar conformidade com contratos definidos:

**Modelos de Dados:**
- Comparar models.py com especificações do Blueprint
- Verificar relacionamentos e constraints
- Validar multi-tenancy (campo tenant em todos os modelos)

**DTOs e Serializers:**
- Verificar se DTOs implementados seguem especificação
- Validar serializers do DRF
- Confirmar ViewModels do frontend

**APIs:**
- Verificar endpoints implementados vs especificados
- Validar padrão de resposta da API (formato JSON)
- Confirmar versionamento (/api/v1/)

### Etapa 3: Validação de Padrões e Qualidade
Executar verificações de qualidade:

**Padrões de Código:**
```bash
# Executar linting no backend
<lint_command> <backend_path> --output-format=text

# Verificar formatação
<format_command> --check <backend_path>

# Linting do frontend (se aplicável)
# <frontend_lint_command> <frontend_path> --format=table
```

**Testes:**
- Verificar cobertura de testes unitários
- Validar estrutura de testes conforme Blueprint
- Confirmar factories multi-tenant corretas

**Configuração:**
- Validar arquivos de configuração (pyproject.toml, package.json)
- Verificar docker-compose.yml e Dockerfiles
- Confirmar CI/CD pipeline (.github/workflows/)

### Etapa 4: Validação de Segurança
Verificar implementação de segurança:

**Multi-tenancy:**
- Confirmar isolamento de dados por tenant
- Verificar middleware de tenant
- Validar propagação de tenant em queries

**Autenticação/Autorização:**
- Verificar implementação JWT
- Confirmar classes de permissão do DRF
- Validar controle de acesso

### Etapa 5: Validação de Observabilidade
Verificar implementação dos requisitos não-funcionais:

**Logging:**
- Confirmar structlog configurado
- Verificar logs estruturados em JSON
- Validar contexto (request_id, tenant_id)

**Métricas:**
- Verificar django-prometheus configurado
- Confirmar endpoint /metrics
- Validar métricas de negócio definidas

**Health Checks:**
- Verificar endpoint /health implementado
- Confirmar verificação de DB e Redis

## Tipos de Validação

### 🏗️ **Estrutural**
- Organização de diretórios e arquivos
- Estrutura de módulos/aplicações
- Arquitetura de camadas

### 🔒 **Contratos**
- Modelos de dados
- DTOs e Serializers
- APIs e endpoints

### 📏 **Qualidade**
- Padrões de código da stack
- Cobertura de testes
- Documentação

### 🛡️ **Segurança**
- Multi-tenancy
- Autenticação/Autorização
- Validação de dados

### 📊 **Observabilidade**
- Logging estruturado
- Métricas de negócio
- Health checks

## Relatório de Validação

### ✅ **Conformidades Encontradas**
- Aspectos que estão corretos conforme Blueprint
- Padrões bem implementados
- Arquitetura respeitada

### ⚠️ **Desvios Identificados** 
- Violações arquiteturais encontradas
- Contratos não seguidos
- Padrões não implementados

### ❌ **Problemas Críticos**
- Violações graves do Blueprint
- Falhas de segurança
- Problemas que bloqueiam o projeto

### 🔧 **Recomendações de Correção**
- Ações específicas para corrigir cada problema
- Prioridade de correção
- Impacto estimado de cada correção

## Resultado
- **Score de Conformidade (0-100%)** calculado automaticamente
- **Relatório JSON detalhado** salvo em `blueprint_conformity_report.json`
- **Categorização de problemas** por severidade (CRITICAL, HIGH, MEDIUM, LOW)
- **Recomendações específicas** para cada problema identificado
- **Validação de qualidade** complementar via `validate_agv_quality.py`

### 📊 Interpretação do Score:
- **80-100%**: 🎉 EXCELENTE - Alta conformidade 
- **60-79%**: ⚠️ BOM - Conformidade aceitável
- **40-59%**: 🔧 REGULAR - Múltiplos problemas
- **0-39%**: 🚨 CRÍTICO - Revisão urgente necessária