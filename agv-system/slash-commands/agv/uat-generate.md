---
description: "Gera cenários de teste manuais E2E (UAT) baseados exclusivamente no Blueprint usando AGV-UAT-Generator"
allowed_tools: ["Task", "Read", "Write"]
---

# AGV UAT Generate - Geração de Cenários de Teste Manuais

Gera cenários de teste de aceitação do usuário (UAT) manuais baseados **exclusivamente** no Blueprint Arquitetural.

## Processo de Geração de UAT

### Etapa 1: Análise do Blueprint para UAT
Extrair informações relevantes para testes de usuário final:

Delegue para o subagent "agv-context-analyzer" a tarefa de identificar no Blueprint:
- Telas/Views descritas na Camada de Apresentação
- Fluxos de usuário críticos
- Componentes de UI e suas interações
- Serviços de aplicação que serão exercitados
- ViewModels e contratos de dados

### Etapa 2: Geração dos Cenários UAT
Criar cenários de teste manuais:

Delegue para o subagent "agv-uat-generator" a criação de 8-12 cenários de teste UAT baseados no Blueprint.

O UAT-Generator deve entregar cenários com:
- ID padronizado: UAT_[NOME_PROJETO]_[XXX]
- Título claro e conciso  
- Fluxo testado (ex: "Login → Dashboard → Novo Empréstimo")
- Componentes do Blueprint envolvidos
- Pré-condições necessárias
- Passos detalhados de execução manual
- Resultado esperado para cada passo
- Critério claro de passagem/falha

### Etapa 3: Organização e Documentação
Organizar os cenários gerados em:
- Fluxos de sucesso principais
- Cenários de tratamento de erro
- Validações de diferentes permissões de usuário
- Testes de funcionalidades configuráveis

## Tipos de Cenários Cobertos

**Fluxos Principais:**
- Login e Autenticação
- Gestão de Clientes (CRUD)
- Criação e Gestão de Empréstimos  
- Operações Financeiras
- Relatórios e Dashboards

**Validações de Segurança:**
- Isolamento multi-tenant
- Controle de acesso por perfil
- Validação de permissões

**Cenários de Erro:**
- Dados inválidos
- Tentativas de acesso não autorizado
- Falhas de rede/sistema

## Resultado Esperado
- 8-12 cenários UAT bem estruturados
- Cobertura dos fluxos críticos do sistema
- Baseado 100% no Blueprint (sem invenções)
- Formato padronizado para execução manual
- Critérios claros de validação

## Arquivos Gerados
- `UAT_Cenarios_Testes_Manuais_v1.0.md` - Cenários completos
- Estrutura organizada por área funcional
- Documentação clara para execução pela equipe de QA