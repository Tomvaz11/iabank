# IABANK Backend - Code Quality Automation
# Makefile para automação de linting, formatação e testes

.PHONY: help install lint format typecheck test quality full-check clean setup-dev

# Configurações
PYTHON = python
PIP = pip
SOURCE_DIR = src
TEST_DIR = tests

# Cores para output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
NC = \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "$(BLUE)IABANK Backend - Code Quality Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup:$(NC)"
	@echo "  install      Instala dependências do requirements.txt"
	@echo "  setup-dev    Setup completo do ambiente de desenvolvimento"
	@echo ""
	@echo "$(YELLOW)Code Quality:$(NC)"
	@echo "  lint         Executa ruff para linting"
	@echo "  format       Executa black para formatação"
	@echo "  typecheck    Executa mypy para verificação de tipos"
	@echo "  quality      Executa lint + format + typecheck"
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@echo "  test         Executa todos os testes com pytest"
	@echo "  test-cov     Executa testes com relatório de cobertura"
	@echo "  test-unit    Executa apenas testes unitários"
	@echo "  test-int     Executa apenas testes de integração"
	@echo "  test-contract Executa apenas testes de contrato"
	@echo ""
	@echo "$(YELLOW)All-in-one:$(NC)"
	@echo "  full-check   Executa quality + test (validação completa)"
	@echo "  clean        Remove arquivos temporários e cache"

install: ## Instala dependências
	@echo "$(BLUE)📦 Instalando dependências...$(NC)"
	$(PIP) install -r requirements.txt

setup-dev: install ## Setup completo do ambiente de desenvolvimento
	@echo "$(BLUE)🛠️  Configurando ambiente de desenvolvimento...$(NC)"
	@echo "$(GREEN)✅ Dependências instaladas$(NC)"
	@echo "$(GREEN)✅ Configurações de linting criadas$(NC)"
	@echo "$(YELLOW)💡 Execute 'make quality' para validar o código$(NC)"

lint: ## Executa linting com ruff
	@echo "$(BLUE)🔍 Executando ruff linting...$(NC)"
	ruff check $(SOURCE_DIR) $(TEST_DIR) --fix
	@echo "$(GREEN)✅ Linting concluído$(NC)"

lint-check: ## Executa linting sem correção automática
	@echo "$(BLUE)🔍 Verificando linting com ruff...$(NC)"
	ruff check $(SOURCE_DIR) $(TEST_DIR)

format: ## Executa formatação com black
	@echo "$(BLUE)🎨 Executando formatação com black...$(NC)"
	black $(SOURCE_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Formatação concluída$(NC)"

format-check: ## Verifica formatação sem aplicar mudanças
	@echo "$(BLUE)🎨 Verificando formatação com black...$(NC)"
	black --check $(SOURCE_DIR) $(TEST_DIR)

typecheck: ## Executa verificação de tipos com mypy
	@echo "$(BLUE)📝 Executando verificação de tipos com mypy...$(NC)"
	mypy $(SOURCE_DIR)
	@echo "$(GREEN)✅ Verificação de tipos concluída$(NC)"

quality: lint format typecheck ## Executa todas as verificações de qualidade
	@echo "$(GREEN)✅ Todas as verificações de qualidade concluídas com sucesso!$(NC)"

quality-check: lint-check format-check typecheck ## Verifica qualidade sem correções automáticas
	@echo "$(GREEN)✅ Verificações de qualidade concluídas!$(NC)"

test: ## Executa todos os testes
	@echo "$(BLUE)🧪 Executando testes com pytest...$(NC)"
	pytest
	@echo "$(GREEN)✅ Testes concluídos$(NC)"

test-cov: ## Executa testes com relatório de cobertura detalhado
	@echo "$(BLUE)🧪 Executando testes com cobertura...$(NC)"
	pytest --cov=$(SOURCE_DIR) --cov-report=term-missing --cov-report=html
	@echo "$(YELLOW)📊 Relatório HTML disponível em: coverage_html/index.html$(NC)"

test-unit: ## Executa apenas testes unitários
	@echo "$(BLUE)🧪 Executando testes unitários...$(NC)"
	pytest -m unit
	@echo "$(GREEN)✅ Testes unitários concluídos$(NC)"

test-int: ## Executa apenas testes de integração
	@echo "$(BLUE)🧪 Executando testes de integração...$(NC)"
	pytest -m integration
	@echo "$(GREEN)✅ Testes de integração concluídos$(NC)"

test-contract: ## Executa apenas testes de contrato
	@echo "$(BLUE)🧪 Executando testes de contrato...$(NC)"
	pytest -m contract
	@echo "$(GREEN)✅ Testes de contrato concluídos$(NC)"

test-tenant: ## Executa testes de isolamento de tenant
	@echo "$(BLUE)🧪 Executando testes de isolamento de tenant...$(NC)"
	pytest -m tenant_isolation
	@echo "$(GREEN)✅ Testes de isolamento de tenant concluídos$(NC)"

test-fast: ## Executa testes rápidos (exclui testes marcados como slow)
	@echo "$(BLUE)🧪 Executando testes rápidos...$(NC)"
	pytest -m "not slow"
	@echo "$(GREEN)✅ Testes rápidos concluídos$(NC)"

full-check: quality test ## Executa verificação completa: quality + testes
	@echo "$(GREEN)🎉 VERIFICAÇÃO COMPLETA CONCLUÍDA COM SUCESSO!$(NC)"
	@echo "$(YELLOW)📋 Resumo:$(NC)"
	@echo "  ✅ Linting (ruff)"
	@echo "  ✅ Formatação (black)"
	@echo "  ✅ Verificação de tipos (mypy)"
	@echo "  ✅ Testes (pytest)"

clean: ## Remove arquivos temporários e cache
	@echo "$(BLUE)🧹 Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf coverage_html
	rm -rf .coverage
	rm -rf htmlcov
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

# Comandos específicos para desenvolvimento
dev-check: quality-check test-fast ## Verificação rápida para desenvolvimento

pre-commit: full-check ## Comando para executar antes de commit
	@echo "$(GREEN)🚀 Código pronto para commit!$(NC)"

# Comandos para CI/CD
ci-check: quality-check test-cov ## Verificação completa para CI/CD
	@echo "$(GREEN)✅ Verificação CI/CD concluída$(NC)"

# Default target
.DEFAULT_GOAL := help