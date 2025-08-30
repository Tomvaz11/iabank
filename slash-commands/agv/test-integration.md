---
description: "Executa testes de integração para fases T1-T8 usando AGV-Integrator-Tester especializado"
allowed_tools: ["Task", "Read", "Write", "Edit", "Bash"]
---

# AGV Test Integration - Testes de Integração T1-T8

Implementa testes de integração robustos para a fase **T$1** seguindo os cenários definidos na Ordem de Implementação.

## Processo de Testes de Integração

### Etapa 1: Análise da Fase de Integração
Identificar módulos e cenários específicos para a fase T$1:

Delegue para o subagent "agv-context-analyzer" a tarefa de extrair informações sobre a fase T$1 dos arquivos:
- Ordem de Implementação: ORDEM_IMPLEMENTACAO.md
- Blueprint: BLUEPRINT_ARQUITETURAL.md

O analyzer deve identificar:
- Módulos no grupo de integração T$1
- Cenários chave definidos para esta fase
- Dependências entre os módulos
- Interfaces que precisam ser testadas

### Etapa 2: Implementação dos Testes de Integração
Delegar a criação dos testes:

Delegue para o subagent "agv-integrator-tester" a implementação dos testes de integração para a fase T$1.

O integrator-tester deve entregar:
- Testes automatizados para todos os cenários definidos
- Fixtures adequadas para setup/teardown
- Validação de consistência multi-tenant
- Testes de interação entre módulos do grupo
- Meta-testes para factories (se aplicável)

### Etapa 3: Execução e Validação
Executar os testes criados para validar:
- Colaboração correta entre módulos
- Isolamento de tenant funcionando
- Cenários de sucesso e falha
- Conformidade com especificações

## Fases de Teste Disponíveis

- **T1**: Validação da Base Multi-Tenancy (iabank.core)
- **T2**: Validação do Fluxo de Autenticação (iabank.users) 
- **T3**: CRUD de Clientes com Segurança Multi-Tenant (iabank.customers)
- **T4**: Fluxo Central de Criação de Empréstimo (iabank.operations)
- **T5**: Validação da Integração Financeira (iabank.finance)
- **T6**: Validação dos Requisitos Não-Funcionais (observabilidade)
- **T7**: Validação da Biblioteca de Componentes UI (frontend shared/entities)
- **T8**: Fluxo de Usuário End-to-End (frontend completo)

## Argumentos
- **$1**: Número da fase de teste (obrigatório: 1-8)
  - Exemplo: `/agv:test-integration 1` (para testes T1)
  - Exemplo: `/agv:test-integration 4` (para testes T4)

## Resultado Esperado
- Testes de integração completos para a fase especificada
- Cobertura de todos os cenários definidos na Ordem
- Validação robusta da colaboração entre módulos
- Relatório detalhado dos testes implementados