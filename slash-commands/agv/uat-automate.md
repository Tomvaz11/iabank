---
description: "Traduz cenários UAT manuais para testes automatizados de backend usando AGV-UAT-Translator"
allowed_tools: ["Task", "Read", "Write", "Edit"]
---

# AGV UAT Automate - Automação de Cenários UAT

Converte cenários de teste manuais (UAT) para testes automatizados de backend usando framework de teste apropriado da stack, interagindo diretamente com os serviços de aplicação.

## Processo de Automação de UAT

### Etapa 1: Análise dos Cenários UAT Existentes
Primeiro, analisar os cenários UAT já criados:

Delegue para o subagent "agv-context-analyzer" a tarefa de analisar:
- Cenários UAT manuais: UAT_Cenarios_Testes_Manuais_v1.0.md
- Blueprint Arquitetural: BLUEPRINT_ARQUITETURAL.md
- Codebase atual para entender serviços implementados

O analyzer deve mapear:
- Passos manuais → Chamadas de serviço
- Validações de UI → Asserções programáticas  
- Fluxos de usuário → Sequências de API calls
- Dependências de infraestrutura para mocking

### Etapa 2: Tradução para Testes Automatizados
Converter cenários para testes automatizados:

Delegue para o subagent "agv-uat-translator" a criação de testes automatizados.

O UAT-Translator deve entregar:
- Scripts de teste para cada cenário UAT
- Fixtures para setup de pré-condições
- Mocks/Fakes para dependências de infraestrutura
- Instanciação correta dos serviços de aplicação
- Asserções programáticas para validar resultados
- Testes independentes com nomes descritivos

### Etapa 3: Organização e Estruturação
Estruturar os testes automatizados:
- Arquivos separados por área funcional
- Fixtures compartilhadas em conftest.py
- Helpers para cenários comuns
- Documentação clara de cada teste

## Estratégia de Automação

**Conversão de Passos:**
- Passo Manual: "Acessar tela de login"
- Teste Automatizado: Chamada direta ao AuthService

**Validações:**
- UI Manual: "Verificar se aparece mensagem de sucesso"
- Teste Automatizado: Assert no resultado do serviço

**Dados de Teste:**
- Setup via factories (garantindo multi-tenancy)
- Cleanup automático após cada teste
- Isolamento entre testes

## Vantagens da Automação

**Eficiência:**
- Execução rápida vs testes manuais
- Integração com CI/CD
- Feedback imediato para desenvolvedores

**Cobertura:**
- Validação de lógica de backend
- Testes de regressão automáticos
- Validação contínua dos fluxos críticos

**Manutenibilidade:**
- Testes versionados com código
- Fácil atualização quando lógica muda
- Documentação executável dos fluxos

## Resultado Esperado
- Testes automatizados para todos os cenários UAT
- Cobertura automatizada dos fluxos críticos
- Validação de backend sem dependência de UI
- Integração pronta para pipeline de CI/CD
- Documentação técnica dos testes criados

## Arquivos Gerados
- `tests/uat_automated/test_auth_flows.py`
- `tests/uat_automated/test_loan_management.py` 
- `tests/uat_automated/test_customer_crud.py`
- `tests/uat_automated/conftest.py` (fixtures)
- `tests/uat_automated/README.md` (documentação)