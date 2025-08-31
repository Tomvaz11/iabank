#!/usr/bin/env python3
"""
Validador Automático Profissional - Blueprint Arquitetural - IABANK
Gerado automaticamente pelo ValidatorGenerator PRO v2.0

Este validador foi criado especificamente para validar:
- Projeto: Blueprint Arquitetural - IABANK
- Framework Backend: django
- Framework Frontend: react
- Database: postgresql
- Arquitetura: monolith
- Multi-tenancy: True
- Autenticação: JWT

Total de validações avançadas: 51
Categorias: STRUCTURE, CONTENT, MODELS, DEPENDENCIES, API

NÍVEL DE VALIDAÇÃO: PROFISSIONAL
- Validação de conteúdo de arquivos
- Validação específica de modelos Django
- Validação de dependências com versões
- Validação de multi-tenancy
- Validação de configurações avançadas
"""

import json
import re
import sys
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Importar sistema de configuração
try:
    from validation_config import ValidationConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Sistema de configuração não disponível. Usando configuração padrão.")

@dataclass
class ValidationIssue:
    """Representa um problema encontrado na validação."""
    file_path: str
    issue_type: str
    description: str
    expected: str
    actual: str
    severity: str


@dataclass 
class ValidationResults:
    """Representa os resultados completos da validação."""
    total_checks: int
    passed_checks: int
    failed_checks: int
    issues: List[ValidationIssue]
    score: float
    categories: Dict[str, int]  # contadores por categoria
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "score": self.score,
            "categories": self.categories,
            "issues": [
                {
                    "file_path": issue.file_path,
                    "issue_type": issue.issue_type,
                    "description": issue.description,
                    "expected": issue.expected,
                    "actual": issue.actual,
                    "severity": issue.severity
                }
                for issue in self.issues
            ]
        }


def validate_directory_structure():
    '''Valida estrutura completa de diretórios conforme Blueprint.'''
    issues = []
    
    dir_path = Path('iabank')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank",
            expected="Diretório iabank deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    dir_path = Path('iabank/workflows')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank/workflows',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank/workflows",
            expected="Diretório iabank/workflows deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/workflows/main.yml')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/workflows/main.yml',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/workflows/main.yml",
            expected="Arquivo iabank/workflows/main.yml deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    dir_path = Path('iabank/backend')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank/backend',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank/backend",
            expected="Diretório iabank/backend deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    dir_path = Path('iabank/backend/src')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank/backend/src",
            expected="Diretório iabank/backend/src deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/iabank')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/iabank',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/iabank",
            expected="Arquivo iabank/backend/src/iabank deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/backend/src/__init__.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/__init__.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/__init__.py",
            expected="Arquivo iabank/backend/src/__init__.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/asgi.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/asgi.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/asgi.py",
            expected="Arquivo iabank/backend/src/asgi.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/settings.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/settings.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/settings.py",
            expected="Arquivo iabank/backend/src/settings.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/urls.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/urls.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/urls.py",
            expected="Arquivo iabank/backend/src/urls.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/wsgi.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/wsgi.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/wsgi.py",
            expected="Arquivo iabank/backend/src/wsgi.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/core')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/core',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/core",
            expected="Arquivo iabank/backend/src/core deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    dir_path = Path('iabank/backend/src/customers')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank/backend/src/customers",
            expected="Diretório iabank/backend/src/customers deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/__init__.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/__init__.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/__init__.py",
            expected="Arquivo iabank/backend/src/customers/__init__.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/models.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/models.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/models.py",
            expected="Arquivo iabank/backend/src/customers/models.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/admin.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/admin.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/admin.py",
            expected="Arquivo iabank/backend/src/customers/admin.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/apps.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/apps.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/apps.py",
            expected="Arquivo iabank/backend/src/customers/apps.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/serializers.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/serializers.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/serializers.py",
            expected="Arquivo iabank/backend/src/customers/serializers.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/views.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/views.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/views.py",
            expected="Arquivo iabank/backend/src/customers/views.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/tests')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/tests',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/tests",
            expected="Arquivo iabank/backend/src/customers/tests deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/backend/src/customers/test_models.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/test_models.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/test_models.py",
            expected="Arquivo iabank/backend/src/customers/test_models.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/customers/test_views.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/customers/test_views.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/customers/test_views.py",
            expected="Arquivo iabank/backend/src/customers/test_views.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/src/finance')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/finance',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/finance",
            expected="Arquivo iabank/backend/src/finance deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/backend/src/operations')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/operations',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/operations",
            expected="Arquivo iabank/backend/src/operations deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/backend/src/users')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/src/users',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/src/users",
            expected="Arquivo iabank/backend/src/users deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/backend/manage.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/manage.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/manage.py",
            expected="Arquivo iabank/backend/manage.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/backend/Dockerfile')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/Dockerfile',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/Dockerfile",
            expected="Arquivo iabank/backend/Dockerfile deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/backend/pyproject.toml')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/backend/pyproject.toml',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/backend/pyproject.toml",
            expected="Arquivo iabank/backend/pyproject.toml deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    dir_path = Path('iabank/frontend')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank/frontend',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank/frontend",
            expected="Diretório iabank/frontend deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/frontend/public')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/frontend/public',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/frontend/public",
            expected="Arquivo iabank/frontend/public deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/frontend/src')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/frontend/src',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/frontend/src",
            expected="Arquivo iabank/frontend/src deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/frontend/Dockerfile')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/frontend/Dockerfile',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/frontend/Dockerfile",
            expected="Arquivo iabank/frontend/Dockerfile deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/frontend/package.json')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/frontend/package.json',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/frontend/package.json",
            expected="Arquivo iabank/frontend/package.json deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/frontend/tsconfig.json')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/frontend/tsconfig.json',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/frontend/tsconfig.json",
            expected="Arquivo iabank/frontend/tsconfig.json deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/frontend/vite.config.ts')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/frontend/vite.config.ts',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/frontend/vite.config.ts",
            expected="Arquivo iabank/frontend/vite.config.ts deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    dir_path = Path('iabank/tests')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='iabank/tests',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: iabank/tests",
            expected="Diretório iabank/tests deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/tests/integration')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/tests/integration',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/tests/integration",
            expected="Arquivo iabank/tests/integration deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/tests/__init__.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/tests/__init__.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/tests/__init__.py",
            expected="Arquivo iabank/tests/__init__.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/tests/test_full_loan_workflow.py')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/tests/test_full_loan_workflow.py',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/tests/test_full_loan_workflow.py",
            expected="Arquivo iabank/tests/test_full_loan_workflow.py deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    file_path = Path('iabank/.docker-compose.yml')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/.docker-compose.yml',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/.docker-compose.yml",
            expected="Arquivo iabank/.docker-compose.yml deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/.gitignore')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/.gitignore',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/.gitignore",
            expected="Arquivo iabank/.gitignore deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/.pre-commit-config.yaml')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/.pre-commit-config.yaml',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/.pre-commit-config.yaml",
            expected="Arquivo iabank/.pre-commit-config.yaml deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/CHANGELOG.md')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/CHANGELOG.md',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/CHANGELOG.md",
            expected="Arquivo iabank/CHANGELOG.md deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/CONTRIBUTING.md')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/CONTRIBUTING.md',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/CONTRIBUTING.md",
            expected="Arquivo iabank/CONTRIBUTING.md deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/LICENSE')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/LICENSE',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/LICENSE",
            expected="Arquivo iabank/LICENSE deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    file_path = Path('iabank/README.md')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='iabank/README.md',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: iabank/README.md",
            expected="Arquivo iabank/README.md deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    return issues if issues else None



def validate_content_settings_py():
    '''Valida conteudo especifico de settings.py.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/settings.py'))
    if not file_paths:
        return ValidationIssue(
            file_path="settings.py",
            issue_type="missing_file",
            description="Arquivo settings.py nao encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo ausente",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        file_path_str = str(file_path_obj)
        try:
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar INSTALLED_APPS
            if 'INSTALLED_APPS' in content:
                for app in ['operations', 'core', 'finance', 'customers']:
                    if app not in content:
                        issues.append(ValidationIssue(
                            file_path=file_path_str,
                            issue_type="missing_installed_app",
                            description=f"App {app} nao encontrada em INSTALLED_APPS",
                            expected=f"{app} deve estar em INSTALLED_APPS",
                            actual="App nao listada",
                            severity="HIGH"
                        ))
            # Verificar configuracao PostgreSQL
            if 'DATABASES' in content:
                if 'postgresql' not in content.lower() and 'psycopg' not in content.lower():
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="wrong_database_config",
                        description="Database nao configurado para PostgreSQL",
                        expected="ENGINE deve usar PostgreSQL (psycopg2)",
                        actual="PostgreSQL nao detectado",
                        severity="HIGH"
                    ))
            # Verificar configuracao DRF
            if 'REST_FRAMEWORK' not in content:
                issues.append(ValidationIssue(
                    file_path=file_path_str,
                    issue_type="missing_drf_config",
                    description="Configuracao REST_FRAMEWORK nao encontrada",
                    expected="REST_FRAMEWORK deve estar configurado",
                    actual="Configuracao ausente",
                    severity="MEDIUM"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=file_path_str,
                issue_type="file_read_error",
                description=f"Erro ao ler arquivo: {str(e)}",
                expected="Arquivo deve ser legivel",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    return issues if issues else None



def validate_content_models_py():
    '''Valida conteudo especifico de models.py.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/models.py'))
    if not file_paths:
        return ValidationIssue(
            file_path="models.py",
            issue_type="missing_file",
            description="Arquivo models.py nao encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo ausente",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        file_path_str = str(file_path_obj)
        try:
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=file_path_str,
                issue_type="file_read_error",
                description=f"Erro ao ler arquivo: {str(e)}",
                expected="Arquivo deve ser legivel",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    return issues if issues else None



def validate_content_pyproject_toml():
    '''Valida conteudo especifico de pyproject.toml.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/pyproject.toml'))
    if not file_paths:
        return ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_file",
            description="Arquivo pyproject.toml nao encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo ausente",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        file_path_str = str(file_path_obj)
        try:
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=file_path_str,
                issue_type="file_read_error",
                description=f"Erro ao ler arquivo: {str(e)}",
                expected="Arquivo deve ser legivel",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    return issues if issues else None



def validate_django_models():
    '''Valida modelos Django conforme Blueprint.'''
    issues = []
    expected_models = ['Tenant', 'User', 'BaseTenantModel', 'Customer', 'Consultant', 'Loan', 'Installment', 'BankAccount', 'PaymentCategory', 'CostCenter', 'Supplier', 'FinancialTransaction']
    
    # Encontrar arquivos models.py
    model_files = list(Path('.').rglob('**/models.py'))
    if not model_files:
        return ValidationIssue(
            file_path="models.py",
            issue_type="missing_models_files",
            description="Nenhum arquivo models.py encontrado",
            expected="Pelo menos um arquivo models.py deve existir",
            actual="Nenhum models.py encontrado",
            severity="CRITICAL"
        )
    
    found_models = set()
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Extrair classes de modelo
            class_matches = re.findall(r'class (\w+)\([^)]*Model[^)]*\):', content)
            found_models.update(class_matches)
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_file_error",
                description=f"Erro ao analisar arquivo: {str(e)}",
                expected="Arquivo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    # Verificar modelos obrigatórios
    missing_models = set(expected_models) - found_models
    for model in missing_models:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="missing_model",
            description=f"Modelo {model} especificado no Blueprint não encontrado",
            expected=f"Modelo {model} deve estar implementado",
            actual="Modelo não encontrado",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_tenant():
    '''Valida modelo específico Tenant.'''
    issues = []
    expected_fields = ['name']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class Tenant\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em Tenant",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"Tenant deve herdar de BaseTenantModel",
                        expected=f"class Tenant(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo Tenant não encontrado",
            expected=f"Modelo Tenant deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_user():
    '''Valida modelo específico User.'''
    issues = []
    expected_fields = ['tenant', 'on_delete', 'tenant']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class User\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em User",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"User deve herdar de BaseTenantModel",
                        expected=f"class User(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo User não encontrado",
            expected=f"Modelo User deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_basetenantmodel():
    '''Valida modelo específico BaseTenantModel.'''
    issues = []
    expected_fields = ['tenant', 'on_delete', 'created_at', 'updated_at']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class BaseTenantModel\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em BaseTenantModel",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"BaseTenantModel deve herdar de BaseTenantModel",
                        expected=f"class BaseTenantModel(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo BaseTenantModel não encontrado",
            expected=f"Modelo BaseTenantModel deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_customer():
    '''Valida modelo específico Customer.'''
    issues = []
    expected_fields = ['name', 'document_number', 'birth_date', 'email', 'phone', 'zip_code', 'street', 'number', 'complement', 'neighborhood', 'city', 'state']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class Customer\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em Customer",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"Customer deve herdar de BaseTenantModel",
                        expected=f"class Customer(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo Customer não encontrado",
            expected=f"Modelo Customer deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_consultant():
    '''Valida modelo específico Consultant.'''
    issues = []
    expected_fields = ['user', 'on_delete', 'balance']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class Consultant\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em Consultant",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"Consultant deve herdar de BaseTenantModel",
                        expected=f"class Consultant(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo Consultant não encontrado",
            expected=f"Modelo Consultant deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_loan():
    '''Valida modelo específico Loan.'''
    issues = []
    expected_fields = ['customer', 'on_delete', 'consultant', 'on_delete', 'principal_amount', 'interest_rate', 'number_of_installments', 'contract_date', 'first_installment_date', 'status', 'customer']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class Loan\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em Loan",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"Loan deve herdar de BaseTenantModel",
                        expected=f"class Loan(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo Loan não encontrado",
            expected=f"Modelo Loan deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_installment():
    '''Valida modelo específico Installment.'''
    issues = []
    expected_fields = ['loan', 'on_delete', 'installment_number', 'due_date', 'amount_due', 'amount_paid', 'payment_date', 'status', 'loan']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class Installment\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em Installment",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"Installment deve herdar de BaseTenantModel",
                        expected=f"class Installment(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo Installment não encontrado",
            expected=f"Modelo Installment deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_bankaccount():
    '''Valida modelo específico BankAccount.'''
    issues = []
    expected_fields = ['name', 'agency', 'account_number', 'initial_balance']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class BankAccount\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em BankAccount",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"BankAccount deve herdar de BaseTenantModel",
                        expected=f"class BankAccount(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo BankAccount não encontrado",
            expected=f"Modelo BankAccount deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_paymentcategory():
    '''Valida modelo específico PaymentCategory.'''
    issues = []
    expected_fields = ['name']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class PaymentCategory\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em PaymentCategory",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"PaymentCategory deve herdar de BaseTenantModel",
                        expected=f"class PaymentCategory(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo PaymentCategory não encontrado",
            expected=f"Modelo PaymentCategory deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_costcenter():
    '''Valida modelo específico CostCenter.'''
    issues = []
    expected_fields = ['name']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class CostCenter\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em CostCenter",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"CostCenter deve herdar de BaseTenantModel",
                        expected=f"class CostCenter(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo CostCenter não encontrado",
            expected=f"Modelo CostCenter deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_supplier():
    '''Valida modelo específico Supplier.'''
    issues = []
    expected_fields = ['name', 'document_number']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class Supplier\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em Supplier",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"Supplier deve herdar de BaseTenantModel",
                        expected=f"class Supplier(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo Supplier não encontrado",
            expected=f"Modelo Supplier deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_model_financialtransaction():
    '''Valida modelo específico FinancialTransaction.'''
    issues = []
    expected_fields = ['description', 'amount', 'transaction_date', 'is_paid', 'payment_date', 'type', 'bank_account', 'on_delete', 'category', 'on_delete', 'cost_center', 'on_delete', 'supplier', 'on_delete', 'installment', 'on_delete', 'installment']
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class FinancialTransaction\([^)]*\):(.*?)(?=\nclass|\Z)'
            model_match = re.search(model_pattern, content, re.DOTALL)
            
            if model_match:
                model_found = True
                model_body = model_match.group(1)
                
                # Verificar campos obrigatórios
                for field in expected_fields:
                    if field not in model_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {field} não encontrado em FinancialTransaction",
                            expected=f"Campo {field} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if true and 'BaseTenantModel' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"FinancialTransaction deve herdar de BaseTenantModel",
                        expected=f"class FinancialTransaction(BaseTenantModel):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {str(e)}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {str(e)}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo FinancialTransaction não encontrado",
            expected=f"Modelo FinancialTransaction deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None



def validate_dependency_django():
    '''Valida dependência django versão 4.2.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"django"\s*[=:]\s*"[^"]*4.2',
                rf'django\s*=\s*"[^"]*4.2',
                rf'"django"\s*:\s*"[^"]*4.2'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência django versão 4.2 não encontrada",
            expected=f"django = \"4.2\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_djangorestframework():
    '''Valida dependência djangorestframework versão 3.14.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"djangorestframework"\s*[=:]\s*"[^"]*3.14',
                rf'djangorestframework\s*=\s*"[^"]*3.14',
                rf'"djangorestframework"\s*:\s*"[^"]*3.14'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência djangorestframework versão 3.14 não encontrada",
            expected=f"djangorestframework = \"3.14\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_psycopg2_binary():
    '''Valida dependência psycopg2-binary versão 2.9.9.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"psycopg2-binary"\s*[=:]\s*"[^"]*2.9.9',
                rf'psycopg2-binary\s*=\s*"[^"]*2.9.9',
                rf'"psycopg2-binary"\s*:\s*"[^"]*2.9.9'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência psycopg2-binary versão 2.9.9 não encontrada",
            expected=f"psycopg2-binary = \"2.9.9\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_django_environ():
    '''Valida dependência django-environ versão 0.11.2.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"django-environ"\s*[=:]\s*"[^"]*0.11.2',
                rf'django-environ\s*=\s*"[^"]*0.11.2',
                rf'"django-environ"\s*:\s*"[^"]*0.11.2'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência django-environ versão 0.11.2 não encontrada",
            expected=f"django-environ = \"0.11.2\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_celery():
    '''Valida dependência celery versão 5.3.6.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"celery"\s*[=:]\s*"[^"]*5.3.6',
                rf'celery\s*=\s*"[^"]*5.3.6',
                rf'"celery"\s*:\s*"[^"]*5.3.6'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência celery versão 5.3.6 não encontrada",
            expected=f"celery = \"5.3.6\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_redis():
    '''Valida dependência redis versão 5.0.1.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"redis"\s*[=:]\s*"[^"]*5.0.1',
                rf'redis\s*=\s*"[^"]*5.0.1',
                rf'"redis"\s*:\s*"[^"]*5.0.1'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência redis versão 5.0.1 não encontrada",
            expected=f"redis = \"5.0.1\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_gunicorn():
    '''Valida dependência gunicorn versão 21.2.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"gunicorn"\s*[=:]\s*"[^"]*21.2.0',
                rf'gunicorn\s*=\s*"[^"]*21.2.0',
                rf'"gunicorn"\s*:\s*"[^"]*21.2.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência gunicorn versão 21.2.0 não encontrada",
            expected=f"gunicorn = \"21.2.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_structlog():
    '''Valida dependência structlog versão 23.2.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"structlog"\s*[=:]\s*"[^"]*23.2.0',
                rf'structlog\s*=\s*"[^"]*23.2.0',
                rf'"structlog"\s*:\s*"[^"]*23.2.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência structlog versão 23.2.0 não encontrada",
            expected=f"structlog = \"23.2.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_django_filter():
    '''Valida dependência django-filter versão 23.3.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"django-filter"\s*[=:]\s*"[^"]*23.3',
                rf'django-filter\s*=\s*"[^"]*23.3',
                rf'"django-filter"\s*:\s*"[^"]*23.3'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência django-filter versão 23.3 não encontrada",
            expected=f"django-filter = \"23.3\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_djangorestframework_simplejwt():
    '''Valida dependência djangorestframework-simplejwt versão 5.3.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"djangorestframework-simplejwt"\s*[=:]\s*"[^"]*5.3.0',
                rf'djangorestframework-simplejwt\s*=\s*"[^"]*5.3.0',
                rf'"djangorestframework-simplejwt"\s*:\s*"[^"]*5.3.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência djangorestframework-simplejwt versão 5.3.0 não encontrada",
            expected=f"djangorestframework-simplejwt = \"5.3.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_pytest():
    '''Valida dependência pytest versão 7.4.3.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"pytest"\s*[=:]\s*"[^"]*7.4.3',
                rf'pytest\s*=\s*"[^"]*7.4.3',
                rf'"pytest"\s*:\s*"[^"]*7.4.3'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência pytest versão 7.4.3 não encontrada",
            expected=f"pytest = \"7.4.3\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_pytest_django():
    '''Valida dependência pytest-django versão 4.7.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"pytest-django"\s*[=:]\s*"[^"]*4.7.0',
                rf'pytest-django\s*=\s*"[^"]*4.7.0',
                rf'"pytest-django"\s*:\s*"[^"]*4.7.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência pytest-django versão 4.7.0 não encontrada",
            expected=f"pytest-django = \"4.7.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_factory_boy():
    '''Valida dependência factory-boy versão 3.3.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"factory-boy"\s*[=:]\s*"[^"]*3.3.0',
                rf'factory-boy\s*=\s*"[^"]*3.3.0',
                rf'"factory-boy"\s*:\s*"[^"]*3.3.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência factory-boy versão 3.3.0 não encontrada",
            expected=f"factory-boy = \"3.3.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_pytest_cov():
    '''Valida dependência pytest-cov versão 4.1.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"pytest-cov"\s*[=:]\s*"[^"]*4.1.0',
                rf'pytest-cov\s*=\s*"[^"]*4.1.0',
                rf'"pytest-cov"\s*:\s*"[^"]*4.1.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência pytest-cov versão 4.1.0 não encontrada",
            expected=f"pytest-cov = \"4.1.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_black():
    '''Valida dependência black versão 23.11.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"black"\s*[=:]\s*"[^"]*23.11.0',
                rf'black\s*=\s*"[^"]*23.11.0',
                rf'"black"\s*:\s*"[^"]*23.11.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência black versão 23.11.0 não encontrada",
            expected=f"black = \"23.11.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_ruff():
    '''Valida dependência ruff versão 0.1.6.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"ruff"\s*[=:]\s*"[^"]*0.1.6',
                rf'ruff\s*=\s*"[^"]*0.1.6',
                rf'"ruff"\s*:\s*"[^"]*0.1.6'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência ruff versão 0.1.6 não encontrada",
            expected=f"ruff = \"0.1.6\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None



def validate_dependency_pre_commit():
    '''Valida dependência pre-commit versão 3.5.0.'''
    dependency_files = [
        Path('pyproject.toml'),
        Path('backend/pyproject.toml'), 
        Path('requirements.txt'),
        Path('backend/requirements.txt'),
        Path('package.json'),
        Path('frontend/package.json')
    ]
    
    found = False
    for dep_file in dependency_files:
        if dep_file.exists():
            content = dep_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar presença da dependência
            patterns = [
                rf'"pre-commit"\s*[=:]\s*"[^"]*3.5.0',
                rf'pre-commit\s*=\s*"[^"]*3.5.0',
                rf'"pre-commit"\s*:\s*"[^"]*3.5.0'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
                    
            if found:
                break
    
    if not found:
        return ValidationIssue(
            file_path="dependencies",
            issue_type="missing_specific_dependency",
            description=f"Dependência pre-commit versão 3.5.0 não encontrada",
            expected=f"pre-commit = \"3.5.0\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None


def validate_env___example():
    '''Valida arquivo de configuração .env(:.example).'''
    config_paths = [Path('.env(:.example)')]
    
    # Tentar localizações alternativas
    if '/' not in '.env(:.example)':
        config_paths.extend([
            Path('backend/.env(:.example)'),
            Path('frontend/.env(:.example)'),
            Path('./.env(:.example)')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='.env(:.example)',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: .env(:.example)",
            expected="Arquivo .env(:.example) deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_pnpm_lock_yaml():
    '''Valida arquivo de configuração pnpm-lock.yaml.'''
    config_paths = [Path('pnpm-lock.yaml')]
    
    # Tentar localizações alternativas
    if '/' not in 'pnpm-lock.yaml':
        config_paths.extend([
            Path('backend/pnpm-lock.yaml'),
            Path('frontend/pnpm-lock.yaml'),
            Path('./pnpm-lock.yaml')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='pnpm-lock.yaml',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: pnpm-lock.yaml",
            expected="Arquivo pnpm-lock.yaml deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_tsconfig_json():
    '''Valida arquivo de configuração tsconfig.json.'''
    config_paths = [Path('tsconfig.json')]
    
    # Tentar localizações alternativas
    if '/' not in 'tsconfig.json':
        config_paths.extend([
            Path('backend/tsconfig.json'),
            Path('frontend/tsconfig.json'),
            Path('./tsconfig.json')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='tsconfig.json',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: tsconfig.json",
            expected="Arquivo tsconfig.json deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_vite_config__jt_s():
    '''Valida arquivo de configuração vite.config.[jt]s.'''
    config_paths = [Path('vite.config.[jt]s')]
    
    # Tentar localizações alternativas
    if '/' not in 'vite.config.[jt]s':
        config_paths.extend([
            Path('backend/vite.config.[jt]s'),
            Path('frontend/vite.config.[jt]s'),
            Path('./vite.config.[jt]s')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='vite.config.[jt]s',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: vite.config.[jt]s",
            expected="Arquivo vite.config.[jt]s deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_wsgi_py():
    '''Valida arquivo de configuração wsgi.py.'''
    config_paths = [Path('wsgi.py')]
    
    # Tentar localizações alternativas
    if '/' not in 'wsgi.py':
        config_paths.extend([
            Path('backend/wsgi.py'),
            Path('frontend/wsgi.py'),
            Path('./wsgi.py')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='wsgi.py',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: wsgi.py",
            expected="Arquivo wsgi.py deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_asgi_py():
    '''Valida arquivo de configuração asgi.py.'''
    config_paths = [Path('asgi.py')]
    
    # Tentar localizações alternativas
    if '/' not in 'asgi.py':
        config_paths.extend([
            Path('backend/asgi.py'),
            Path('frontend/asgi.py'),
            Path('./asgi.py')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='asgi.py',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: asgi.py",
            expected="Arquivo asgi.py deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_gitignore():
    '''Valida arquivo de configuração .gitignore.'''
    config_paths = [Path('.gitignore')]
    
    # Tentar localizações alternativas
    if '/' not in '.gitignore':
        config_paths.extend([
            Path('backend/.gitignore'),
            Path('frontend/.gitignore'),
            Path('./.gitignore')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='.gitignore',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: .gitignore",
            expected="Arquivo .gitignore deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_pre_commit_config_yaml():
    '''Valida arquivo de configuração .pre-commit-config.yaml.'''
    config_paths = [Path('.pre-commit-config.yaml')]
    
    # Tentar localizações alternativas
    if '/' not in '.pre-commit-config.yaml':
        config_paths.extend([
            Path('backend/.pre-commit-config.yaml'),
            Path('frontend/.pre-commit-config.yaml'),
            Path('./.pre-commit-config.yaml')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='.pre-commit-config.yaml',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: .pre-commit-config.yaml",
            expected="Arquivo .pre-commit-config.yaml deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_docker_compose_yaml():
    '''Valida arquivo de configuração docker-compose.yaml.'''
    config_paths = [Path('docker-compose.yaml')]
    
    # Tentar localizações alternativas
    if '/' not in 'docker-compose.yaml':
        config_paths.extend([
            Path('backend/docker-compose.yaml'),
            Path('frontend/docker-compose.yaml'),
            Path('./docker-compose.yaml')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='docker-compose.yaml',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: docker-compose.yaml",
            expected="Arquivo docker-compose.yaml deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_Dockerfile():
    '''Valida arquivo de configuração Dockerfile.'''
    config_paths = [Path('Dockerfile')]
    
    # Tentar localizações alternativas
    if '/' not in 'Dockerfile':
        config_paths.extend([
            Path('backend/Dockerfile'),
            Path('frontend/Dockerfile'),
            Path('./Dockerfile')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='Dockerfile',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: Dockerfile",
            expected="Arquivo Dockerfile deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_github_workflows____yaml():
    '''Valida arquivo de configuração .github/workflows/.*.yaml.'''
    config_paths = [Path('.github/workflows/.*.yaml')]
    
    # Tentar localizações alternativas
    if '/' not in '.github/workflows/.*.yaml':
        config_paths.extend([
            Path('backend/.github/workflows/.*.yaml'),
            Path('frontend/.github/workflows/.*.yaml'),
            Path('./.github/workflows/.*.yaml')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='.github/workflows/.*.yaml',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: .github/workflows/.*.yaml",
            expected="Arquivo .github/workflows/.*.yaml deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None

def validate_django_settings_advanced():
    '''Valida configurações Django avançadas.'''
    issues = []
    settings_files = list(Path('.').rglob('**/settings.py'))
    
    if not settings_files:
        return ValidationIssue(
            file_path="settings.py",
            issue_type="missing_django_settings",
            description="Arquivo settings.py do Django não encontrado",
            expected="settings.py deve existir",
            actual="Arquivo não existe",
            severity="CRITICAL"
        )
    
    for settings_file in settings_files:
        content = settings_file.read_text(encoding='utf-8', errors='ignore')
        file_path_str = str(settings_file)
        
        # Verificar configurações obrigatórias
        required_settings = [
            ('INSTALLED_APPS', 'HIGH'),
            ('DATABASES', 'HIGH'),
            ('SECRET_KEY', 'CRITICAL'),
            ('DEBUG', 'MEDIUM')
        ]
        
        for setting, severity in required_settings:
            if setting not in content:
                issues.append(ValidationIssue(
                    file_path=file_path_str,
                    issue_type="missing_django_setting",
                    description=f"Configuração {setting} não encontrada",
                    expected=f"{setting} deve estar configurado",
                    actual="Configuração ausente",
                    severity=severity
                ))
        
        # Verificar apps do projeto
        if 'INSTALLED_APPS' in content:
            for app in ['operations', 'core', 'finance', 'customers']:
                if app not in content:
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="missing_project_app",
                        description=f"App do projeto {app} não está em INSTALLED_APPS",
                        expected=f"{app} deve estar listado",
                        actual="App não listado",
                        severity="HIGH"
                    ))
    
    return issues if issues else None

def validate_react_advanced():
    '''Valida configuração React avançada.'''
    issues = []
    package_files = list(Path('.').rglob('**/package.json'))
    
    react_found = False
    for package_file in package_files:
        content = package_file.read_text(encoding='utf-8', errors='ignore')
        file_path_str = str(package_file)
        
        if '"react"' in content:
            react_found = True
            
            # Verificar versão do React
            react_version_match = re.search(r'"react":\s*"([^"]+)"', content)
            if react_version_match:
                version = react_version_match.group(1)
                # Verificar se é versão 18+
                if not version.startswith(('18', '19', '^18', '~18', '^19', '~19')):
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="outdated_react_version",
                        description=f"Versão do React {version} pode estar desatualizada",
                        expected="React 18+ conforme Blueprint",
                        actual=f"React {version}",
                        severity="MEDIUM"
                    ))
            
            # Verificar TypeScript se especificado
            if 'react' == 'react' and 'typescript' not in content.lower():
                issues.append(ValidationIssue(
                    file_path=file_path_str,
                    issue_type="missing_typescript",
                    description="TypeScript não configurado conforme Blueprint",
                    expected="TypeScript deve estar configurado",
                    actual="TypeScript não encontrado",
                    severity="MEDIUM"
                ))
    
    if not react_found:
        issues.append(ValidationIssue(
            file_path="package.json",
            issue_type="react_not_configured",
            description="React não encontrado em package.json",
            expected="React deve estar configurado",
            actual="React não encontrado",
            severity="HIGH"
        ))
    
    return issues if issues else None

def validate_multi_tenancy_implementation():
    '''Valida implementação completa de multi-tenancy.'''
    issues = []
    
    # Verificar BaseTenantModel
    models_files = list(Path('.').rglob('**/models.py'))
    base_tenant_found = False
    
    for model_file in models_files:
        if model_file.exists():
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            if 'BaseTenantModel' in content:
                base_tenant_found = True
                
                # Verificar estrutura do BaseTenantModel
                if 'tenant = models.ForeignKey' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="missing_tenant_field",
                        description="BaseTenantModel deve ter campo tenant",
                        expected="Campo tenant = models.ForeignKey(Tenant, ...)",
                        actual="Campo tenant não encontrado",
                        severity="CRITICAL"
                    ))
                    
                if 'abstract = True' not in content and '__abstract__ = True' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="base_model_not_abstract",
                        description="BaseTenantModel deve ser abstrato",
                        expected="abstract = True na Meta class",
                        actual="Modelo não é abstrato",
                        severity="HIGH"
                    ))
    
    if not base_tenant_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="missing_base_tenant_model",
            description="BaseTenantModel não encontrado",
            expected="Classe BaseTenantModel deve estar definida",
            actual="BaseTenantModel não existe",
            severity="CRITICAL"
        ))
    
    return issues if issues else None

def validate_api_structure():
    '''Valida estrutura de API REST conforme Blueprint.'''
    issues = []
    
    # Procurar por arquivos de API
    api_files = ['views.py', 'serializers.py', 'urls.py']
    found_api_files = []
    
    for api_file in api_files:
        files = list(Path('.').rglob(f'**/{api_file}'))
        if files:
            found_api_files.append(api_file)
        else:
            issues.append(ValidationIssue(
                file_path=api_file,
                issue_type="missing_api_file",
                description=f"Arquivo de API {api_file} não encontrado",
                expected=f"{api_file} deve existir para API REST",
                actual="Arquivo não existe",
                severity="HIGH"
            ))
    
    # Verificar DRF se Django
    if len([f for f in found_api_files if f]) > 0:
        settings_files = list(Path('.').rglob('**/settings.py'))
        drf_configured = False
        
        for settings_file in settings_files:
            content = settings_file.read_text(encoding='utf-8', errors='ignore')
            if 'rest_framework' in content.lower():
                drf_configured = True
                break
        
        if not drf_configured:
            issues.append(ValidationIssue(
                file_path="settings.py",
                issue_type="drf_not_configured",
                description="Django REST Framework não configurado",
                expected="DRF deve estar em INSTALLED_APPS",
                actual="DRF não encontrado",
                severity="HIGH"
            ))
    
    return issues if issues else None

def validate_testing_structure_advanced():
    '''Valida estrutura avançada de testes.'''
    issues = []
    
    # Procurar estrutura de testes
    test_patterns = [
        '**/tests/',
        '**/test_*.py',
        '**/*_test.py',
        '**/tests.py'
    ]
    
    test_files_found = []
    for pattern in test_patterns:
        files = list(Path('.').glob(pattern))
        test_files_found.extend(files)
    
    if not test_files_found:
        issues.append(ValidationIssue(
            file_path="tests/",
            issue_type="no_test_structure",
            description="Nenhuma estrutura de testes encontrada",
            expected="Estrutura de testes deve existir",
            actual="Testes não encontrados",
            severity="HIGH"
        ))
    else:
        # Verificar configuração do framework de teste
        config_files = []
        if 'pytest' == 'pytest':
            config_files = ['pytest.ini', 'pyproject.toml', 'setup.cfg']
        
        config_found = False
        for config_file in config_files:
            if Path(config_file).exists():
                config_found = True
                break
        
        if not config_found and 'pytest' == 'pytest':
            issues.append(ValidationIssue(
                file_path="pytest.ini",
                issue_type="test_config_missing",
                description="Configuração do pytest não encontrada",
                expected="pytest.ini ou configuração em pyproject.toml",
                actual="Configuração não encontrada",
                severity="MEDIUM"
            ))
    
    return issues if issues else None

def validate_docker_configuration_advanced():
    '''Valida configuração avançada do Docker.'''
    issues = []
    expected_docker_files = ['Dockerfile', 'docker-compose.yaml']
    
    for docker_file in expected_docker_files:
        file_path = Path(docker_file)
        if not file_path.exists():
            issues.append(ValidationIssue(
                file_path=docker_file,
                issue_type="missing_docker_file",
                description=f"Arquivo Docker {docker_file} não encontrado",
                expected=f"{docker_file} deve existir",
                actual="Arquivo não existe",
                severity="HIGH"
            ))
        else:
            # Validar conteúdo básico do Dockerfile
            if docker_file == 'Dockerfile':
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                required_commands = ['FROM', 'COPY', 'RUN']
                for command in required_commands:
                    if command not in content:
                        issues.append(ValidationIssue(
                            file_path=docker_file,
                            issue_type="invalid_dockerfile",
                            description=f"Comando {command} não encontrado no Dockerfile",
                            expected=f"{command} deve estar presente",
                            actual="Comando ausente",
                            severity="MEDIUM"
                        ))
            
            # Validar docker-compose
            elif 'docker-compose' in docker_file:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                if 'services:' not in content:
                    issues.append(ValidationIssue(
                        file_path=docker_file,
                        issue_type="invalid_compose_file",
                        description="Seção services não encontrada no docker-compose",
                        expected="services: deve estar presente",
                        actual="Seção services ausente",
                        severity="MEDIUM"
                    ))
    
    return issues if issues else None

class BlueprintArquiteturalIabankProScaffoldValidator:
    """Validador profissional customizado para Blueprint Arquitetural - IABANK."""
    
    # Configurações padrão (serão sobrescritas se config disponível)
    DEFAULT_SEVERITY_WEIGHTS = {
        "CRITICAL": 20,
        "HIGH": 10,
        "MEDIUM": 3,
        "LOW": 1
    }
    
    DEFAULT_CATEGORY_WEIGHTS = {
        "STRUCTURE": 1.0,
        "CONTENT": 1.5,
        "MODELS": 2.0,
        "DEPENDENCIES": 1.2,
        "API": 1.3
    }
    
    def __init__(self):
        # Carregar configuração se disponível
        if CONFIG_AVAILABLE:
            self.config = ValidationConfig()
            self.SEVERITY_WEIGHTS = self.config.get_severity_weights()
            self.CATEGORY_WEIGHTS = self.config.get_category_weights()
            self.profile = self.config.current_profile
        else:
            self.config = None
            self.SEVERITY_WEIGHTS = self.DEFAULT_SEVERITY_WEIGHTS
            self.CATEGORY_WEIGHTS = self.DEFAULT_CATEGORY_WEIGHTS
            self.profile = None
        
        all_validation_methods = [
            "validate_directory_structure", "validate_content_settings_py", "validate_content_models_py", "validate_content_pyproject_toml", "validate_django_models", "validate_model_tenant", "validate_model_user", "validate_model_basetenantmodel", "validate_model_customer", "validate_model_consultant", "validate_model_loan", "validate_model_installment", "validate_model_bankaccount", "validate_model_paymentcategory", "validate_model_costcenter", "validate_model_supplier", "validate_model_financialtransaction", "validate_dependency_django", "validate_dependency_djangorestframework", "validate_dependency_psycopg2_binary", "validate_dependency_django_environ", "validate_dependency_celery", "validate_dependency_redis", "validate_dependency_gunicorn", "validate_dependency_structlog", "validate_dependency_django_filter", "validate_dependency_djangorestframework_simplejwt", "validate_dependency_pytest", "validate_dependency_pytest_django", "validate_dependency_factory_boy", "validate_dependency_pytest_cov", "validate_dependency_black", "validate_dependency_ruff", "validate_dependency_pre_commit", "validate_env___example", "validate_pnpm_lock_yaml", "validate_tsconfig_json", "validate_vite_config__jt_s", "validate_wsgi_py", "validate_asgi_py", "validate_gitignore", "validate_pre_commit_config_yaml", "validate_docker_compose_yaml", "validate_Dockerfile", "validate_github_workflows____yaml", "validate_django_settings_advanced", "validate_react_advanced", "validate_multi_tenancy_implementation", "validate_api_structure", "validate_testing_structure_advanced", "validate_docker_configuration_advanced"
        ]
        
        # Filtrar validações baseado na configuração
        self.validation_methods = []
        for method_name in all_validation_methods:
            if self.config and self.config.should_ignore_validation(method_name):
                print(f"Ignorando validação: {method_name}")
                continue
            self.validation_methods.append(method_name)
        
        self.rule_categories = {'validate_directory_structure': 'STRUCTURE', 'validate_content_settings_py': 'CONTENT', 'validate_content_models_py': 'CONTENT', 'validate_content_pyproject_toml': 'CONTENT', 'validate_django_models': 'MODELS', 'validate_model_tenant': 'MODELS', 'validate_model_user': 'MODELS', 'validate_model_basetenantmodel': 'MODELS', 'validate_model_customer': 'MODELS', 'validate_model_consultant': 'MODELS', 'validate_model_loan': 'MODELS', 'validate_model_installment': 'MODELS', 'validate_model_bankaccount': 'MODELS', 'validate_model_paymentcategory': 'MODELS', 'validate_model_costcenter': 'MODELS', 'validate_model_supplier': 'MODELS', 'validate_model_financialtransaction': 'MODELS', 'validate_dependency_django': 'DEPENDENCIES', 'validate_dependency_djangorestframework': 'DEPENDENCIES', 'validate_dependency_psycopg2_binary': 'DEPENDENCIES', 'validate_dependency_django_environ': 'DEPENDENCIES', 'validate_dependency_celery': 'DEPENDENCIES', 'validate_dependency_redis': 'DEPENDENCIES', 'validate_dependency_gunicorn': 'DEPENDENCIES', 'validate_dependency_structlog': 'DEPENDENCIES', 'validate_dependency_django_filter': 'DEPENDENCIES', 'validate_dependency_djangorestframework_simplejwt': 'DEPENDENCIES', 'validate_dependency_pytest': 'DEPENDENCIES', 'validate_dependency_pytest_django': 'DEPENDENCIES', 'validate_dependency_factory_boy': 'DEPENDENCIES', 'validate_dependency_pytest_cov': 'DEPENDENCIES', 'validate_dependency_black': 'DEPENDENCIES', 'validate_dependency_ruff': 'DEPENDENCIES', 'validate_dependency_pre_commit': 'DEPENDENCIES', 'validate_env___example': 'STRUCTURE', 'validate_pnpm_lock_yaml': 'STRUCTURE', 'validate_tsconfig_json': 'STRUCTURE', 'validate_vite_config__jt_s': 'STRUCTURE', 'validate_wsgi_py': 'STRUCTURE', 'validate_asgi_py': 'STRUCTURE', 'validate_gitignore': 'STRUCTURE', 'validate_pre_commit_config_yaml': 'STRUCTURE', 'validate_docker_compose_yaml': 'STRUCTURE', 'validate_Dockerfile': 'STRUCTURE', 'validate_github_workflows____yaml': 'STRUCTURE', 'validate_django_settings_advanced': 'CONTENT', 'validate_react_advanced': 'CONTENT', 'validate_multi_tenancy_implementation': 'MODELS', 'validate_api_structure': 'API', 'validate_testing_structure_advanced': 'STRUCTURE', 'validate_docker_configuration_advanced': 'STRUCTURE'}
    
    def validate(self) -> ValidationResults:
        """Executa todas as validações avançadas e retorna os resultados."""
        issues = []
        total_checks = len(self.validation_methods)
        failed_validations = 0
        categories = {"STRUCTURE": 0, "CONTENT": 0, "MODELS": 0, "DEPENDENCIES": 0, "API": 0}
        
        print(f"Executando {total_checks} validações PROFISSIONAIS para Blueprint Arquitetural - IABANK...")
        print("Níveis: STRUCTURE | CONTENT | MODELS | DEPENDENCIES | API")
        print("-" * 80)
        
        for method_name in self.validation_methods:
            try:
                method = globals()[method_name]
                result = method()
                
                category = self.rule_categories.get(method_name, "STRUCTURE")
                print(f"[{category:12}] {method_name}", end="")
                
                if result:
                    failed_validations += 1  # Contar validações que falharam
                    if isinstance(result, list):
                        issues.extend(result)
                        categories[category] += len(result)
                        print(f" FALHOU: {len(result)} problemas")
                    else:
                        issues.append(result)
                        categories[category] += 1
                        print(" FALHOU: 1 problema")
                else:
                    print(" OK")
                        
            except Exception as e:
                failed_validations += 1
                issues.append(ValidationIssue(
                    file_path="validator",
                    issue_type="validation_error",
                    description=f"Erro na validação {method_name}: {str(e)}",
                    expected="Validação deve executar sem erros",
                    actual=f"Erro: {str(e)}",
                    severity="CRITICAL"
                ))
                print(f" ERRO: {str(e)}")
        
        # Correção: passed_checks baseado em validações, não em issues individuais
        passed_checks = total_checks - failed_validations
        score = self._calculate_advanced_score(total_checks, failed_validations, issues)
        
        return ValidationResults(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_validations,
            issues=issues,
            score=score,
            categories=categories
        )
    
    def _calculate_advanced_score(self, total_checks: int, failed_validations: int, issues: List[ValidationIssue]) -> float:
        """Calcula score avançado baseado na severidade e categoria dos problemas."""
        if failed_validations == 0:
            return 100.0
        
        total_penalty = 0
        for issue in issues:
            severity_weight = self.SEVERITY_WEIGHTS.get(issue.severity, 1)
            
            # Aplicar peso da categoria baseado no tipo de problema
            category_weight = 1.0
            if "model" in issue.issue_type.lower():
                category_weight = self.CATEGORY_WEIGHTS["MODELS"]
            elif "content" in issue.issue_type.lower() or "config" in issue.issue_type.lower():
                category_weight = self.CATEGORY_WEIGHTS["CONTENT"]
            elif "api" in issue.issue_type.lower():
                category_weight = self.CATEGORY_WEIGHTS["API"]
            elif "dependency" in issue.issue_type.lower():
                category_weight = self.CATEGORY_WEIGHTS["DEPENDENCIES"]
            else:
                category_weight = self.CATEGORY_WEIGHTS["STRUCTURE"]
            
            penalty = severity_weight * category_weight
            total_penalty += penalty
        
        # Score mais realístico baseado em validações falhadas vs total
        # Aplica penalidade por severidade dos issues encontrados
        base_score = ((total_checks - failed_validations) / total_checks) * 100
        
        # Reduzir score baseado na severidade dos problemas encontrados
        penalty_factor = min(total_penalty / (failed_validations * 10), 0.5)  # Max 50% de penalidade
        final_score = max(0, base_score - (base_score * penalty_factor))
        
        return round(final_score, 2)
    
    def generate_professional_report(self, results: ValidationResults) -> str:
        """Gera relatório profissional detalhado dos resultados."""
        report = []
        report.append("=" * 100)
        report.append(f"RELATÓRIO PROFISSIONAL DE VALIDAÇÃO - BLUEPRINT ARQUITETURAL - IABANK")
        report.append("=" * 100)
        report.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Validador: ValidatorGenerator PRO v2.0")
        report.append("")
        report.append("ESPECIFICAÇÕES DO PROJETO:")
        report.append(f"├─ Framework Backend: django")
        report.append(f"├─ Framework Frontend: react")
        report.append(f"├─ Database: postgresql")
        report.append(f"├─ Arquitetura: monolith")
        report.append(f"├─ Multi-tenancy: True")
        report.append(f"└─ Autenticação: JWT")
        report.append("")
        report.append("RESULTADOS DA VALIDAÇÃO:")
        report.append(f"├─ Total de Verificações: {results.total_checks}")
        report.append(f"├─ Aprovadas: {results.passed_checks}")
        report.append(f"├─ Reprovadas: {results.failed_checks}")
        report.append(f"└─ Score Final: {results.score}%")
        report.append("")
        
        # Analise por categoria
        report.append("ANALISE POR CATEGORIA:")
        for category, count in results.categories.items():
            status = "FALHOU" if count > 0 else "OK"
            report.append(f"|- {status} {category:12}: {count} problemas")
        report.append("")
        
        # Determinacao do status
        if results.score >= 90:
            report.append("STATUS: SCAFFOLD EXCELENTE")
            report.append("O scaffold atende aos mais altos padroes de qualidade profissional.")
        elif results.score >= 85:
            report.append("STATUS: SCAFFOLD APROVADO")
            report.append("O scaffold atende aos padroes de qualidade estabelecidos.")
        elif results.score >= 70:
            report.append("STATUS: SCAFFOLD NECESSITA MELHORIAS")
            report.append("O scaffold tem qualidade aceitavel mas precisa de algumas correcoes.")
        else:
            report.append("STATUS: SCAFFOLD REJEITADO") 
            report.append("O scaffold precisa de correcoes significativas antes de prosseguir.")
        
        report.append("")
        
        if results.issues:
            # Agrupar problemas por severidade
            critical_issues = [i for i in results.issues if i.severity == "CRITICAL"]
            high_issues = [i for i in results.issues if i.severity == "HIGH"]
            medium_issues = [i for i in results.issues if i.severity == "MEDIUM"]
            low_issues = [i for i in results.issues if i.severity == "LOW"]
            
            if critical_issues:
                report.append("PROBLEMAS CRITICOS:")
                report.append("-" * 60)
                for i, issue in enumerate(critical_issues, 1):
                    report.append(f"{i}. {issue.description}")
                    report.append(f"   Arquivo: {issue.file_path}")
                    report.append(f"   Esperado: {issue.expected}")
                    report.append(f"   Encontrado: {issue.actual}")
                    report.append("")
            
            if high_issues:
                report.append("PROBLEMAS DE ALTA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(high_issues, 1):
                    report.append(f"{i}. {issue.description}")
                    report.append(f"   Arquivo: {issue.file_path}")
                    report.append(f"   Esperado: {issue.expected}")
                    report.append(f"   Encontrado: {issue.actual}")
                    report.append("")
            
            if medium_issues:
                report.append("PROBLEMAS DE MEDIA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(medium_issues, 1):
                    report.append(f"{i}. {issue.description}")
                    report.append(f"   Arquivo: {issue.file_path}")
                    report.append("")
            
            if low_issues:
                report.append("PROBLEMAS DE BAIXA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(low_issues, 1):
                    report.append(f"{i}. {issue.description}")
                    report.append("")
        
        report.append("=" * 100)
        return "\n".join(report)

def main():
    """Função principal do validador profissional."""
    import locale
    import os
    
    # Forçar UTF-8 para evitar problemas de encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    validator = BlueprintArquiteturalIabankProScaffoldValidator()
    results = validator.validate()
    
    # Gerar e exibir relatório profissional com encoding seguro
    report = validator.generate_professional_report(results)
    print()
    
    try:
        # Substituir caracteres problemáticos
        clean_report = report.replace('├', '+-').replace('└', '+-').replace('─', '-').replace('│', '|')
        clean_report = clean_report.replace('ã', 'a').replace('ç', 'c').replace('é', 'e')
        clean_report = clean_report.replace('ó', 'o').replace('í', 'i').replace('á', 'a')
        print(clean_report)
    except UnicodeEncodeError:
        # Fallback final
        ascii_report = report.encode('ascii', errors='replace').decode('ascii')
        print(ascii_report)
    
    # Salvar resultados em JSON com encoding explícito
    results_file = Path("validation_results_pro.json")
    results_file.write_text(
        json.dumps(results.to_dict(), indent=2, ensure_ascii=False), 
        encoding='utf-8'
    )
    print(f"\nRelatorio detalhado salvo em: {results_file}")
    
    # Usar threshold do profile configurado
    threshold = 75  # Padrão
    if CONFIG_AVAILABLE:
        config = ValidationConfig()
        threshold = config.current_profile.min_score_threshold
    
    print(f"\nThreshold configurado: {threshold}%")
    return 0 if results.score >= threshold else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)