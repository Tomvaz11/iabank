# CHANGELOG - IABANK

Todas as mudanças importantes do projeto IABANK serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Não Lançado]

### Adicionado

- **T006**: Contract test POST /api/v1/auth/login (RED phase TDD)

## [0.3.0] - 2025-09-13

### Adicionado

- **T001**: Estrutura Django backend com Apps modulares (core, customers, operations, finance, users)
- **T002**: Projeto Django inicializado com dependências (DRF, PostgreSQL, Redis, Celery, pytest)
- **T003**: Code quality tools configurados (ruff, black, mypy)
- **T004**: Estrutura React com TypeScript e Feature-Sliced Design
- **T005**: PostgreSQL com Docker e configurações multi-tenant
- Multi-tenant architecture com Row-Level Security (RLS)
- Point-in-Time Recovery (PITR) com arquivamento WAL contínuo
- Sistema de backup e retenção (FR-111)
- Management commands (`manage_backups`, `enable_rls`)
- Scripts de automação para quality checks
- Domain isolation em cada Django App

### Alterado

- Porta PostgreSQL alterada de 5432 para 5433 (conflito resolvido)
- Documentação atualizada com status real da implementação

### Removido

- Emojis dos arquivos de código fonte (substituídos por prefixos textuais)
- Arquivo temporário `SOLUCAO-POSTGRESQL.md`

### Corrigido

- Problema de conflito de porta PostgreSQL com instalação local Windows
- Inconsistências na documentação sobre status de implementação

## [0.2.0] - 2025-09-12

### Adicionado

- Feature specification com 112 requisitos funcionais
- Architecture research baseada na constitution
- Data model com 11 entidades principais
- OpenAPI 3.0 contracts completos
- Quickstart guide com 6 fluxos críticos
- Constitution v1.0.0 ratificada

### Adicionado

- Estrutura inicial do projeto
- Configurações básicas de desenvolvimento
- Documentação inicial

## Commits Relacionados

- `33777d6` - chore: remover emojis dos arquivos de código fonte
- `5d7bf9d` - chore: remover completamente arquivos **pycache** do controle de versão
- `067316a` - chore: limpar arquivos cache e adicionar componentes Django faltantes
- `e1c1954` - chore: adicionar .gitignore para arquivos Python e desenvolvimento
- `e991718` - fix: resolver problema PostgreSQL e validar T001-T005 implementações
- `57a0274` - feat: implementar T004 - Estrutura React com TypeScript e Feature-Sliced Design
- `a2165f5` - feat: implementar T003 - Formatação de código com Black
- `19ff05f` - feat: implementar T002 - Inicialização completa do Django com dependências
- `de94724` - feat: implementar estrutura inicial do backend Django
- `8e500f3` - Initial commit: IABANK project setup

---

_Mantido desde 2025-09-13_
