---
description: "Executa o Alvo 0 (Setup do Projeto Profissional) usando o AGV-Scaffolder especializado"
allowed_tools: ["Task", "Write", "LS", "Bash"]
---

# AGV Scaffold - Alvo 0: Setup Profissional do Projeto

Executa a criação completa da estrutura inicial do projeto seguindo rigorosamente o Blueprint Arquitetural.

## Processo Automatizado

### Etapa 1: Extração de Contexto de Setup
Primeiro, vou extrair do Blueprint apenas as seções relevantes para o setup inicial:
- Estrutura de Diretórios Proposta
- Arquivos de Configuração (.gitignore, README.md, LICENSE)  
- Configurações de Ambiente (pyproject.toml, package.json, docker-compose.yml)
- Estrutura de Testes (diretórios e arquivos base)

### Etapa 2: Delegação para AGV-Scaffolder
Delegando a criação completa do scaffolding para o subagent especializado:

Delegue para o subagent "agv-scaffolder" a tarefa de executar o Alvo 0 completo baseado no:
- Blueprint: BLUEPRINT_ARQUITETURAL.md

### Etapa 3: Validação da Estrutura
Após a criação, validar se todos os arquivos e diretórios foram criados corretamente conforme especificado no Blueprint.

## Resultado Esperado
- Estrutura completa de diretórios
- Todos os arquivos de configuração
- Arquivos de código com docstrings (SEM lógica de negócio)
- Estrutura de testes preparada
- Instruções de setup para o coordenador