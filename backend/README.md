# IABANK Backend - Ferramentas de Qualidade de Código

Este diretório contém as configurações e scripts para manter a qualidade do código do backend IABANK.

## 📦 Instalação das Dependências

```bash
pip install -r requirements.txt
```

## 🛠️ Ferramentas Disponíveis

### Linting com Ruff
Ruff é um linter moderno e extremamente rápido para Python.

```bash
# Verificar problemas
python -m ruff check src/

# Corrigir problemas automaticamente
python -m ruff check src/ --fix

# Verificar testes também
python -m ruff check src/ tests/
```

### Formatação com Black
Black formata automaticamente o código Python seguindo padrões consistentes.

```bash
# Verificar formatação
python -m black --check src/

# Aplicar formatação
python -m black src/

# Incluir testes
python -m black src/ tests/
```

### Verificação de Tipos com MyPy
MyPy verifica tipagem estática no código Python.

```bash
# Verificar tipos
python -m mypy src/

# Verificar tipos com relatório detalhado
python -m mypy src/ --show-error-codes
```

## 🚀 Scripts de Automação

### Script Python (Multiplataforma)

```bash
# Executar todas as verificações de qualidade
python scripts/lint.py --quality

# Executar com correção automática
python scripts/lint.py --quality --fix

# Apenas verificar (sem correções)
python scripts/lint.py --quality --check-only

# Executar apenas linting
python scripts/lint.py --lint

# Executar apenas formatação
python scripts/lint.py --format

# Executar apenas verificação de tipos
python scripts/lint.py --typecheck

# Executar verificação completa (qualidade + testes)
python scripts/lint.py --full

# Ajuda
python scripts/lint.py --help
```

### Script Batch (Windows)

```batch
# Verificações de qualidade
scripts\quality.bat quality

# Testes com cobertura
scripts\quality.bat test-cov

# Verificação completa
scripts\quality.bat full

# Ajuda
scripts\quality.bat help
```

### Makefile (Linux/Mac)

```bash
# Verificações de qualidade
make quality

# Testes com cobertura
make test-cov

# Verificação completa
make full-check

# Ajuda
make help
```

## ⚙️ Configurações

### pyproject.toml
Arquivo principal de configuração para todas as ferramentas:

- **Ruff**: Configurações de linting, imports, complexidade
- **Black**: Configurações de formatação
- **MyPy**: Configurações básicas de verificação de tipos
- **Pytest**: Configurações de testes

### mypy.ini
Configurações específicas e detalhadas do MyPy, incluindo:
- Configurações para módulos externos
- Diferentes níveis de rigor para diferentes partes do código
- Configurações específicas para Django

## 📋 Padrões de Qualidade

### Ruff (Linting)
- ✅ Seguir PEP 8
- ✅ Imports organizados (isort)
- ✅ Complexidade limitada (McCabe)
- ✅ Segurança básica (Bandit rules)
- ✅ Boas práticas Django
- ⚠️ Alguns avisos são ignorados durante desenvolvimento

### Black (Formatação)
- ✅ Linha máxima: 88 caracteres
- ✅ Aspas duplas
- ✅ Espaços em vez de tabs

### MyPy (Tipos)
- ✅ Verificação básica habilitada
- ⚠️ Modo não-rigoroso durante desenvolvimento
- ✅ Ignorar imports de bibliotecas externas

## 🧪 Integração com Testes

```bash
# Executar testes
pytest

# Testes com cobertura
pytest --cov=src --cov-report=term-missing --cov-report=html

# Testes por tipo
pytest -m unit        # Apenas testes unitários
pytest -m integration # Apenas testes de integração
pytest -m contract    # Apenas testes de contrato
```

## 🔧 Comandos de Desenvolvimento Rápido

### Verificação Pré-Commit
```bash
# Verificação rápida antes de commit
python scripts/lint.py --quality --fix
pytest --no-cov -x
```

### Limpeza
```bash
# Limpar arquivos de cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache .mypy_cache .ruff_cache
```

## 📊 Relatórios de Cobertura

Após executar testes com cobertura, os relatórios ficam disponíveis em:
- **Terminal**: Relatório resumido
- **HTML**: `coverage_html/index.html` - Relatório interativo detalhado

## 🏗️ CI/CD Integration

Para integração contínua, use:

```bash
# Verificação completa para CI
python scripts/lint.py --quality --check-only
pytest --cov=src --cov-fail-under=85
```

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Comando não encontrado**: Instale as dependências com `pip install -r requirements.txt`
2. **Avisos sobre rules removidos**: Normal, são rules deprecados do ruff
3. **Erros de MyPy com bibliotecas**: Configurado para ignorar, será resolvido gradualmente
4. **Encoding issues no Windows**: Use `chcp 65001` ou scripts em UTF-8

### Status dos Checks

Após T003 implementado:
- ✅ Ruff configurado e funcional
- ✅ Black configurado e funcional
- ✅ MyPy configurado e funcional
- ✅ Scripts de automação criados
- ✅ Configurações otimizadas para desenvolvimento

## 📝 Próximos Passos

1. **T004**: Configurar estrutura React com TypeScript
2. **T005**: Setup PostgreSQL com Docker
3. **T006-T019**: Implementar testes TDD
4. **T020+**: Implementação dos modelos e lógica de negócio

---

**Configurado em T003** | **Versão**: 1.0.0 | **Constitution**: v1.0.0