---
description: "Implementa um alvo específico do AGV com contexto otimizado (reduz contexto de 1000+ para ~200 linhas)"
allowed_tools: ["Task", "Read", "Write", "Edit", "Bash"]
---

# AGV Implement - Implementação com Contexto Otimizado

Implementa o **Alvo $1** usando contexto inteligentemente otimizado, eliminando o problema de estouro de contexto.

## Processo de Implementação Inteligente

### Etapa 1: Análise e Extração de Contexto Focado
Primeiro, extrair apenas o contexto necessário para o alvo específico:

Delegue para o subagent "agv-context-analyzer" a tarefa de extrair o contexto relevante para o Alvo $1 dos arquivos:
- Blueprint: BLUEPRINT_ARQUITETURAL.md  
- Ordem: ORDEM_IMPLEMENTACAO.md

O context-analyzer deve retornar:
- Seções específicas do Blueprint para este alvo
- Modelos de dados relacionados
- Dependências e contratos de interface
- Contexto reduzido de ~150-200 linhas vs 1000+ originais

### Etapa 2: Implementação Focada com AGV-Implementor
Com o contexto otimizado, delegar a implementação:

Delegue para o subagent "agv-implementor" a implementação do Alvo $1 usando o contexto focado extraído na etapa anterior.

O implementor deve entregar:
- Código de produção profissional seguindo SOLID
- Testes unitários obrigatórios para todo código
- Documentação e docstrings completas
- Conformidade total com o Blueprint

### Etapa 3: Validação e Quality Gates
Executar validações automáticas:
- Verificar conformidade com Blueprint
- Executar testes unitários  
- Validar padrões de código (linting)
- Confirmar que apenas o alvo especificado foi implementado

## Argumentos
- **$1**: Número do alvo a ser implementado (obrigatório)
  - Exemplo: `/agv:implement 5` (para implementar Alvo 5)
  - Exemplo: `/agv:implement 12` (para implementar Alvo 12)

## Vantagens do Contexto Otimizado
- **Contexto 75% menor**: De ~1500 linhas para ~500 linhas
- **Zero alucinação**: Contexto preciso e focado
- **Qualidade mantida**: Todas as diretrizes AGV preservadas
- **Implementação completa**: Código + testes + documentação