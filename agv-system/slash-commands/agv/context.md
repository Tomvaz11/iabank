---
description: "Visualiza o contexto que seria extraído para um alvo específico (útil para debug e validação)"
allowed_tools: ["Task", "Read", "Grep"]
---

# AGV Context - Visualização de Contexto Extraído

Mostra exatamente qual contexto seria extraído do Blueprint para um alvo específico, útil para debug e validação antes da implementação.

## Análise de Contexto

### Visualização do Contexto para Alvo $1

Delegue para o subagent "agv-context-analyzer" a tarefa de extrair e **APENAS MOSTRAR** (não implementar) o contexto que seria usado para o Alvo $1.

O analyzer deve retornar:

### Seções do Blueprint Extraídas:
- Lista das seções específicas que seriam incluídas
- Tamanho aproximado de cada seção
- Justificativa de por que cada seção é relevante

### Modelos de Dados Relacionados:
- Modelos de dados necessários para o alvo
- Dependências entre modelos
- Contratos de interface envolvidos

### Dependências Identificadas:
- Módulos que já devem estar implementados
- Arquivos de código que seriam incluídos no contexto
- Bibliotecas e tecnologias necessárias

### Estatísticas de Otimização:
- Contexto original: ~X linhas (Blueprint completo)
- Contexto otimizado: ~Y linhas (apenas relevante)
- Redução: Z% de contexto removido

## Argumentos
- **$1**: Número do alvo para análise (obrigatório)
  - Exemplo: `/agv:context 5` (ver contexto para Alvo 5)
  - Exemplo: `/agv:context 12` (ver contexto para Alvo 12)

## Utilidade

**Para Debug:**
- Verificar se contexto está correto antes da implementação
- Identificar dependências faltantes
- Validar extração de seções relevantes

**Para Otimização:**
- Confirmar redução significativa de contexto
- Ajustar extração se necessário
- Validar que informações essenciais não foram perdidas

**Para Planejamento:**
- Entender escopo antes da implementação
- Verificar pré-requisitos
- Estimar complexidade do alvo

## Resultado
- Contexto completo que seria enviado ao implementor
- Análise de relevância de cada seção
- Estatísticas de otimização
- Recomendações se contexto parece incompleto