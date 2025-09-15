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
- ✅ Complexidade ciclomática limitada (McCabe ≤10)
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

### Quality Gates (T080)
- ✅ **Complexidade ciclomática**: Máximo 10 por função (ruff C90)
- ✅ **Vulnerabilidades código**: Bandit scan para issues HIGH/MEDIUM
- ✅ **Vulnerabilidades dependências**: pip-audit para packages vulneráveis
- ✅ **Cobertura de testes**: Mínimo 85% obrigatório
- ✅ **SARIF reports**: Integração com GitHub Code Scanning
- ✅ **CI/CD enforcement**: Pipeline falha se quality gates não passarem

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

## 🔒 Análise de Segurança (T080)

### Bandit - Análise de Código
```bash
# Scan básico
bandit -r src/

# Scan rigoroso (HIGH/MEDIUM only)
bandit -r src/ -ll -i

# Gerar relatório SARIF para GitHub
bandit -r src/ -f sarif -o security-report.sarif --exit-zero
```

### pip-audit - Vulnerabilidades de Dependências
```bash
# Auditar requirements.txt
pip-audit -r requirements.txt

# Auditar ambiente completo
pip-audit

# Gerar relatório JSON
pip-audit -f json -o security-audit.json
```

### Quality Gates - Verificação Completa
```bash
# Executar todos os quality gates (como no CI)
ruff check --select=C90 src/         # Complexidade
pip-audit -r requirements.txt        # Vulnerabilidades deps
bandit -r src/ -ll -i                # Vulnerabilidades código
pytest --cov=src --cov-fail-under=85 # Coverage
```

## ⚡ Celery - Processamento Assíncrono

### Configurações Enterprise (T079)
Celery configurado com funcionalidades enterprise-grade:

- **acks_late**: True - Confirmação apenas após processamento completo
- **worker_prefetch_multiplier**: 1 - Controle de memória
- **task_reject_on_worker_lost**: True - Rejeitar tasks de workers perdidos
- **Dead Letter Queue (DLQ)**: Routing automático para tasks falhadas
- **Retry backoff**: Exponencial para tasks críticas
- **Idempotência**: Tasks críticas com cache Redis para evitar reprocessamento
- **Funções utilitárias**: Geração de IDs únicos e verificação de status

### Comandos Celery

```bash
# Iniciar Celery worker
celery -A config worker --loglevel=info

# Iniciar Celery beat (tasks periódicas)
celery -A config beat --loglevel=info

# Monitorar tasks em tempo real
celery -A config events

# Verificar configurações
python -c "from config.celery import app; print(app.conf)"

# Verificar tasks registradas
celery -A config inspect registered

# Limpar filas
celery -A config purge
```

### Tasks Periódicas Configuradas
- **update-iof-rates**: Atualização diária das taxas IOF
- **calculate-overdue-interest**: Cálculo de juros em atraso (hora em hora)
- **generate-daily-reports**: Geração de relatórios diários

### Funcionalidades de Idempotência

#### Decorator @idempotent_task
Para tasks críticas que não devem ser reprocessadas:

```python
from config.celery import idempotent_task, generate_operation_id

@idempotent_task
def critical_payment_task(operation_id: str, payment_data: dict):
    # Lógica da task crítica
    return {"status": "processed", "operation_id": operation_id}

# Uso
operation_id = generate_operation_id()
result = critical_payment_task.delay(operation_id, payment_data)
```

#### Funções Utilitárias

```python
from config.celery import generate_operation_id, is_operation_completed, is_operation_processing

# Gerar ID único para operação
operation_id = generate_operation_id()

# Verificar se operação já foi completada
if is_operation_completed(operation_id):
    print("Operação já processada")

# Verificar se operação está em processamento
if is_operation_processing(operation_id):
    print("Operação em andamento")
```

#### Comandos de Teste

```bash
# Testar funcionalidades de idempotência
python -c "
from config.celery import generate_operation_id, example_critical_task
op_id = generate_operation_id()
result1 = example_critical_task(op_id, {'test': 'data'})
result2 = example_critical_task(op_id, {'test': 'data'})
print('Idempotência:', result1 == result2)
"

# Verificar configurações T079
python -c "
from config.celery import app
print('acks_late:', app.conf.task_acks_late)
print('DLQ routes:', len(app.conf.task_routes))
"
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

Após T003 + T079 + T080 implementados:
- ✅ Ruff configurado e funcional
- ✅ Black configurado e funcional
- ✅ MyPy configurado e funcional
- ✅ Scripts de automação criados
- ✅ Configurações otimizadas para desenvolvimento
- ✅ Celery enterprise-grade configurado (T079)
- ✅ Quality Gates automatizados configurados (T080)
- ✅ Análise de segurança com Bandit + pip-audit
- ✅ Integração SARIF com GitHub Code Scanning

## 🐳 Docker & Containerização (T081)

### Dockerfiles Multi-Stage Production
Dockerfiles otimizados implementados conforme Blueprint T081:

#### Backend Dockerfile
- **Multi-stage build**: Separação build/runtime para otimização
- **Poetry**: Gerenciamento de dependências moderno (`--without=dev`)
- **Non-root user**: Segurança com usuário `app`
- **Health checks**: curl instalado para monitoramento
- **Production-ready**: gunicorn + WSGI configurado

```bash
# Build e teste local
docker build -f backend/Dockerfile backend/
docker-compose up backend -d

# Verificar saúde
curl http://localhost:8000/health/
```

#### Frontend Dockerfile
- **Multi-stage build**: Build com pnpm + serve com nginx
- **pnpm**: Package manager moderno (mais rápido que npm)
- **nginx otimizado**: Gzip, SPA routing, API proxy
- **Security headers**: X-Frame-Options, CSP, XSS protection

```bash
# Build e teste local
docker build -f frontend/Dockerfile frontend/
docker-compose up frontend -d

# Verificar proxy API
curl http://localhost:3000/api/
```

#### Stack Completa
```bash
# Iniciar stack completa
docker-compose up -d

# Verificar todos os serviços
docker-compose ps
```

## 📝 Próximos Passos

1. **T082-T085**: Blueprint gaps restantes (CI/CD paths, E2E, Secrets, ADRs, DR)
2. **T013-T019**: Integration tests com isolamento multi-tenant
3. **T020+**: Implementação dos modelos de negócio
4. **API Endpoints**: DRF ViewSets e serializers

---

**Configurado em T003 + T079 + T080 + T081** | **Versão**: 1.3.0 | **Constitution**: v1.0.0# Test backend change
