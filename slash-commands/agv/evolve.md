---
description: "Executa manutenção, correções e melhorias usando F7-Evolucionista respeitando rigorosamente o Blueprint"
allowed_tools: ["Task", "Read", "Edit", "Write", "Grep", "Bash"]
---

# AGV Evolve - Manutenção e Evolução com F7-Evolucionista

Executa manutenção, correção de bugs, refatorações e melhorias no projeto existente, respeitando rigorosamente o Blueprint como constituição do projeto.

## Processo de Evolução

### Etapa 1: Análise Profunda do Problema
Primeiro, realizar análise detalhada da tarefa solicitada:

**Tarefa de Evolução:** $1

Delegue para o subagent "agv-evolucionista" a análise completa da tarefa usando:
- Blueprint Arquitetural: BLUEPRINT_ARQUITETURAL.md
- Codebase atual completa para contexto
- Ordem de implementação se necessário

O evolucionista deve realizar:
- Análise da causa raiz do problema
- Identificação de impacto nos módulos existentes  
- Verificação de conformidade com Blueprint
- Planejamento da solução sem violar arquitetura

### Etapa 2: Verificação de Conformidade Arquitetural
**REGRA FUNDAMENTAL:** Se a tarefa exigir mudanças que contradigam o Blueprint:
- **PARAR** imediatamente
- Reportar "Conflito Arquitetural"  
- Explicar por que não pode ser implementado
- Sugerir atualização prévia do Blueprint se necessário

### Etapa 3: Implementação da Evolução
Se não houver conflitos arquiteturais, implementar:
- Solução da causa raiz identificada
- Manutenção da integridade dos contratos
- Preservação da separação de camadas
- Código seguindo padrões existentes

### Etapa 4: Testes Obrigatórios
**SEMPRE** implementar testes apropriados:
- **Correção de Bug:** Teste de regressão (falha antes, passa depois)
- **Nova Funcionalidade:** Testes unitários + integração se necessário
- **Refatoração:** Manter testes existentes funcionando
- **Performance:** Testes de benchmark se aplicável

## Tipos de Evolução Suportados

**Correção de Bugs:**
- Análise de causa raiz
- Implementação da correção  
- Teste de regressão obrigatório
- Validação da solução

**Refatoração:**
- Melhoria de código mantendo comportamento
- Preservação de todos os contratos públicos
- Atualização de testes se necessário
- Validação de não-regressão

**Novas Funcionalidades:**
- Implementação dentro da arquitetura existente
- Novos testes unitários e integração
- Documentação atualizada
- Conformidade total com Blueprint

**Otimizações:**
- Melhorias de performance
- Otimização de queries de banco
- Refatoração de algoritmos
- Benchmarks para validar melhorias

## Argumentos
- **$1**: Descrição da tarefa de evolução (obrigatório)
  - Exemplo: `/agv:evolve "Performance lenta nas queries de empréstimos"`
  - Exemplo: `/agv:evolve "Bug na validação de CPF duplicado"`
  - Exemplo: `/agv:evolve "Adicionar campo telefone celular no cliente"`

## Garantias de Qualidade

**Conformidade Arquitetural:**
- Blueprint como autoridade máxima
- Nenhuma violação de contratos
- Preservação da separação de camadas
- Manutenção da integridade do design

**Qualidade de Código:**
- Padrões existentes mantidos (linting, formatação, etc.)
- Docstrings atualizadas seguindo convenções da stack
- Código limpo e profissional
- Consistência com codebase existente

**Validação:**
- Testes obrigatórios para toda mudança
- Suíte de testes completa deve passar
- Análise de impacto realizada
- Documentação atualizada quando necessário

## Resultado Esperado
- Problema/melhoria implementada corretamente
- Conformidade total com Blueprint
- Testes apropriados adicionados/atualizados
- Relatório detalhado da evolução realizada
- Código pronto para produção