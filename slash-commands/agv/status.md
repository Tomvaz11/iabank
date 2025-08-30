---
description: "Mostra status atual da implementação do projeto baseado na Ordem de Implementação"
allowed_tools: ["Read", "LS", "Grep", "Glob"]
---

# AGV Status - Status da Implementação do Projeto

Analisa a codebase atual e compara com a Ordem de Implementação para mostrar o progresso do projeto.

## Análise de Progresso

### Etapa 1: Leitura da Ordem de Implementação
Primeiro, analisar a ordem completa de alvos:

Vou ler a Ordem de Implementação para entender todos os alvos definidos:
- ORDEM_IMPLEMENTACAO.md

### Etapa 2: Análise da Codebase Atual  
Verificar quais componentes já foram implementados:

**Backend:**
- Estrutura de módulos/aplicações (core, users, customers, operations, finance)
- Modelos implementados em cada app
- Views, serializers e URLs
- Testes unitários e de integração

**Frontend:**
- Estrutura de diretórios (shared, features, entities)
- Componentes implementados
- Hooks e serviços de API
- Páginas e routing

**Infraestrutura:**
- Arquivos de configuração (docker, CI/CD)
- Scripts de observabilidade
- Comandos de gerenciamento

### Etapa 3: Mapeamento de Status
Para cada alvo definido na ordem, determinar status:

**✅ COMPLETO** - Alvo implementado com testes
**🔄 EM PROGRESSO** - Parcialmente implementado  
**⏳ PENDENTE** - Não iniciado
**❌ BLOQUEADO** - Dependências não atendidas

### Etapa 4: Análise de Fases de Teste
Verificar status das fases T1-T8:
- T1: Base Multi-Tenancy
- T2: Fluxo de Autenticação  
- T3: CRUD de Clientes
- T4: Criação de Empréstimos
- T5: Integração Financeira
- T6: Observabilidade
- T7: UI Components
- T8: E2E Frontend

## Relatório de Status

### Resumo Executivo
- **Total de Alvos:** X alvos definidos na ordem
- **Implementados:** Y alvos completos (Z%)
- **Em Progresso:** A alvos parciais
- **Pendentes:** B alvos não iniciados
- **Próximo Alvo Recomendado:** Alvo N

### Status Detalhado por Módulo

**iabank.core (Alvos 1-4):**
- Status de cada alvo
- Arquivos implementados
- Testes disponíveis

**iabank.users (Alvos 5-8):**
- Status de implementação
- JWT configurado
- Testes de autenticação

**iabank.customers (Alvos 9-17):**
- Modelos, views, serializers
- CRUD completo
- Multi-tenancy funcionando

**...e assim por diante para todos os módulos**

### Fases de Teste (T1-T8)
- Quais fases podem ser executadas agora
- Fases bloqueadas por dependências
- Próxima fase recomendada

### Recomendações
- Próximos alvos a implementar na sequência correta
- Dependências que precisam ser resolvidas
- Testes de integração prontos para execução

## Resultado
- Visão completa do progresso atual
- Identificação clara do próximo passo
- Status de todas as fases de teste
- Recomendações para continuidade do desenvolvimento