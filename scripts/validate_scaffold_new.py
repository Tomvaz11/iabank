#!/usr/bin/env python3
"""
Validador especializado para scaffold completo (Alvo 0)
Gerado automaticamente pelo ValidatorGenerator v3.0 - Sistema Modular AGV
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ValidationIssue:
    """Representa um problema encontrado na validação."""
    file_path: str
    issue_type: str
    description: str
    expected: str
    actual: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW

@dataclass
class ValidationResults:
    """Resultados completos da validação."""
    total_checks: int
    passed_checks: int
    failed_checks: int
    issues: List[ValidationIssue]
    score: float
    categories: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização JSON."""
        return {
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "issues": [asdict(issue) for issue in self.issues],
            "score": self.score,
            "categories": self.categories
        }


def validate_directory_structure():
    '''Valida estrutura completa de diretórios conforme Blueprint.'''
    from pathlib import Path
    
    issues = []
    required_paths = ["'iabank/'", "'iabank/workflows/'", "'iabank/workflows/main.yml'", "'iabank/backend/'", "'iabank/backend/src/'", "'iabank/backend/src/iabank/'", "'iabank/backend/src/__init__.py'", "'iabank/backend/src/asgi.py'", "'iabank/backend/src/settings.py'", "'iabank/backend/src/urls.py'", "'iabank/backend/src/wsgi.py'", "'iabank/backend/src/core/'", "'iabank/backend/src/customers/'", "'iabank/backend/src/customers/__init__.py'", "'iabank/backend/src/customers/models.py'", "'iabank/backend/src/customers/admin.py'", "'iabank/backend/src/customers/apps.py'", "'iabank/backend/src/customers/serializers.py'", "'iabank/backend/src/customers/views.py'", "'iabank/backend/src/customers/tests/'", "'iabank/backend/src/customers/test_models.py'", "'iabank/backend/src/customers/test_views.py'", "'iabank/backend/src/finance/'", "'iabank/backend/src/operations/'", "'iabank/backend/src/users/'", "'iabank/backend/manage.py'", "'iabank/backend/Dockerfile'", "'iabank/backend/pyproject.toml'", "'iabank/frontend/'", "'iabank/frontend/public/'", "'iabank/frontend/src/'", "'iabank/frontend/Dockerfile'", "'iabank/frontend/package.json'", "'iabank/frontend/tsconfig.json'", "'iabank/frontend/vite.config.ts'", "'iabank/tests/'", "'iabank/tests/integration/'", "'iabank/tests/__init__.py'", "'iabank/tests/test_full_loan_workflow.py'", "'iabank/.docker-compose.yml'", "'iabank/.gitignore'", "'iabank/.pre-commit-config.yaml'", "'iabank/CHANGELOG.md'", "'iabank/CONTRIBUTING.md'", "'iabank/LICENSE'", "'iabank/README.md'"]
    
    for required_path in required_paths:
        path = Path(required_path)
        
        if required_path.endswith('/'):
            # Diretório
            if not path.is_dir():
                issues.append(ValidationIssue(
                    file_path=str(path),
                    issue_type="missing_directory",
                    description=f"Diretório obrigatório não encontrado: {required_path}",
                    expected=f"Diretório {required_path} deve existir",
                    actual="Diretório não existe",
                    severity="HIGH"
                ))
        else:
            # Arquivo
            if not path.is_file():
                issues.append(ValidationIssue(
                    file_path=str(path),
                    issue_type="missing_file",
                    description=f"Arquivo obrigatório não encontrado: {required_path}",
                    expected=f"Arquivo {required_path} deve existir",
                    actual="Arquivo não existe",
                    severity="MEDIUM"
                ))
    
    return issues if issues else None


def validate_pyproject_toml():
    '''Valida existência e estrutura básica de pyproject.toml.'''
    issues = []
    
    config_paths = list(Path('.').rglob('**/pyproject.toml'))
    if not config_paths:
        issues.append(ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_config_file",
            description="Arquivo de configuração crítico não encontrado: pyproject.toml",
            expected="Arquivo deve existir na raiz do projeto",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None

def validate_package_json():
    '''Valida existência e estrutura básica de package.json.'''
    issues = []
    
    config_paths = list(Path('.').rglob('**/package.json'))
    if not config_paths:
        issues.append(ValidationIssue(
            file_path="package.json",
            issue_type="missing_config_file",
            description="Arquivo de configuração crítico não encontrado: package.json",
            expected="Arquivo deve existir na raiz do projeto",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None

def validate_gitignore():
    '''Valida existência e estrutura básica de .gitignore.'''
    issues = []
    
    config_paths = list(Path('.').rglob('**/.gitignore'))
    if not config_paths:
        issues.append(ValidationIssue(
            file_path=".gitignore",
            issue_type="missing_config_file",
            description="Arquivo de configuração crítico não encontrado: .gitignore",
            expected="Arquivo deve existir na raiz do projeto",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None

def validate_pre_commit_config_yaml():
    '''Valida existência e estrutura básica de .pre-commit-config.yaml.'''
    issues = []
    
    config_paths = list(Path('.').rglob('**/.pre-commit-config.yaml'))
    if not config_paths:
        issues.append(ValidationIssue(
            file_path=".pre-commit-config.yaml",
            issue_type="missing_config_file",
            description="Arquivo de configuração crítico não encontrado: .pre-commit-config.yaml",
            expected="Arquivo deve existir na raiz do projeto",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None


def validate_content_settings_py():
    '''Valida conteúdo específico de settings.py.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/settings.py'))
    if not file_paths:
        return ValidationIssue(
            file_path="settings.py",
            issue_type="missing_file",
            description="Arquivo settings.py não encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        if file_path_obj.exists():
            file_path_str = str(file_path_obj)
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar INSTALLED_APPS
            if 'INSTALLED_APPS' in content:
                for app in ['core', 'operations', 'finance', 'customers']:
                    if app not in content:
                        issues.append(ValidationIssue(
                            file_path=file_path_str,
                            issue_type="missing_installed_app",
                            description=f"App {app} não encontrada em INSTALLED_APPS",
                            expected=f"{app} deve estar em INSTALLED_APPS",
                            actual="App não listada",
                            severity="HIGH"
                        ))
            # Verificar configuracao PostgreSQL
            if 'DATABASES' in content:
                if 'postgresql' not in content.lower() and 'psycopg' not in content.lower():
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="wrong_database_config",
                        description="Database não configurado para PostgreSQL",
                        expected="ENGINE deve usar PostgreSQL (psycopg2)",
                        actual="PostgreSQL não detectado",
                        severity="HIGH"
                    ))
            # Verificar configuracao DRF
            if 'REST_FRAMEWORK' not in content:
                issues.append(ValidationIssue(
                    file_path=file_path_str,
                    issue_type="missing_drf_config",
                    description="Configuração REST_FRAMEWORK não encontrada",
                    expected="REST_FRAMEWORK deve estar configurado",
                    actual="Configuração ausente",
                    severity="MEDIUM"
                ))
    
    return issues if issues else None



def validate_content_models_py():
    '''Valida conteúdo específico de models.py.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/models.py'))
    if not file_paths:
        return ValidationIssue(
            file_path="models.py",
            issue_type="missing_file",
            description="Arquivo models.py não encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        if file_path_obj.exists():
            file_path_str = str(file_path_obj)
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            
    
    return issues if issues else None



def validate_content_pyproject_toml():
    '''Valida conteúdo específico de pyproject.toml.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/pyproject.toml'))
    if not file_paths:
        return ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_file",
            description="Arquivo pyproject.toml não encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        if file_path_obj.exists():
            file_path_str = str(file_path_obj)
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            
    
    return issues if issues else None



def validate_dependency_django():
    '''Valida dependência específica django.'''
    issues = []
    
    # Verificar em pyproject.toml
    pyproject_files = list(Path('.').rglob('**/pyproject.toml'))
    found = False
    
    for pyproject_file in pyproject_files:
        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8', errors='ignore')
            if 'django' in content:
                found = True
                # Verificar versão se especificada
                if '4.2' and '4.2' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(pyproject_file),
                        issue_type="wrong_dependency_version",
                        description="Versão incorreta para django",
                        expected="Versão 4.2",
                        actual="Versão diferente ou não especificada",
                        severity="MEDIUM"
                    ))
    
    if not found:
        issues.append(ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_dependency",
            description="Dependência django não encontrada",
            expected="Dependência deve estar listada",
            actual="Dependência ausente",
            severity="MEDIUM"
        ))
    
    return issues if issues else None



def validate_dependency_djangorestframework():
    '''Valida dependência específica djangorestframework.'''
    issues = []
    
    # Verificar em pyproject.toml
    pyproject_files = list(Path('.').rglob('**/pyproject.toml'))
    found = False
    
    for pyproject_file in pyproject_files:
        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8', errors='ignore')
            if 'djangorestframework' in content:
                found = True
                # Verificar versão se especificada
                if '3.14' and '3.14' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(pyproject_file),
                        issue_type="wrong_dependency_version",
                        description="Versão incorreta para djangorestframework",
                        expected="Versão 3.14",
                        actual="Versão diferente ou não especificada",
                        severity="MEDIUM"
                    ))
    
    if not found:
        issues.append(ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_dependency",
            description="Dependência djangorestframework não encontrada",
            expected="Dependência deve estar listada",
            actual="Dependência ausente",
            severity="MEDIUM"
        ))
    
    return issues if issues else None



def validate_dependency_psycopg2_binary():
    '''Valida dependência específica psycopg2-binary.'''
    issues = []
    
    # Verificar em pyproject.toml
    pyproject_files = list(Path('.').rglob('**/pyproject.toml'))
    found = False
    
    for pyproject_file in pyproject_files:
        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8', errors='ignore')
            if 'psycopg2-binary' in content:
                found = True
                # Verificar versão se especificada
                if '2.9.9' and '2.9.9' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(pyproject_file),
                        issue_type="wrong_dependency_version",
                        description="Versão incorreta para psycopg2-binary",
                        expected="Versão 2.9.9",
                        actual="Versão diferente ou não especificada",
                        severity="MEDIUM"
                    ))
    
    if not found:
        issues.append(ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_dependency",
            description="Dependência psycopg2-binary não encontrada",
            expected="Dependência deve estar listada",
            actual="Dependência ausente",
            severity="MEDIUM"
        ))
    
    return issues if issues else None


def validate_django_settings_advanced():
    '''Valida configurações avançadas do Django.'''
    issues = []
    
    settings_files = list(Path('.').rglob('**/settings.py'))
    for settings_file in settings_files:
        if settings_file.exists():
            content = settings_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificações críticas
            critical_settings = [
                'DATABASES', 'INSTALLED_APPS', 'MIDDLEWARE', 
                'ROOT_URLCONF', 'TEMPLATES'
            ]
            
            for setting in critical_settings:
                if setting not in content:
                    issues.append(ValidationIssue(
                        file_path=str(settings_file),
                        issue_type="missing_django_setting",
                        description=f"Configuração Django crítica não encontrada: {setting}",
                        expected=f"{setting} deve estar configurado",
                        actual="Configuração ausente",
                        severity="HIGH"
                    ))
    
    return issues if issues else None

def validate_react_package_structure():
    '''Valida estrutura do package.json para React.'''
    issues = []
    
    package_files = list(Path('.').rglob('**/package.json'))
    for package_file in package_files:
        if package_file.exists():
            try:
                import json
                content = json.loads(package_file.read_text(encoding='utf-8'))
                
                # Verificar dependências React críticas
                deps = content.get('dependencies', {})
                dev_deps = content.get('devDependencies', {})
                all_deps = {**deps, **dev_deps}
                
                critical_react_deps = ['react', 'react-dom']
                for dep in critical_react_deps:
                    if dep not in all_deps:
                        issues.append(ValidationIssue(
                            file_path=str(package_file),
                            issue_type="missing_react_dependency",
                            description=f"Dependência React crítica não encontrada: {dep}",
                            expected=f"{dep} deve estar nas dependências",
                            actual="Dependência ausente",
                            severity="HIGH"
                        ))
                        
            except json.JSONDecodeError:
                issues.append(ValidationIssue(
                    file_path=str(package_file),
                    issue_type="invalid_package_json",
                    description="package.json com formato inválido",
                    expected="JSON válido",
                    actual="JSON inválido",
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

def validate_readme_md():
    '''Valida existência de README.md.'''
    issues = []
    
    doc_paths = list(Path('.').rglob('**/README.md'))
    if not doc_paths:
        # Tentar variações case-insensitive
        alt_paths = list(Path('.').rglob('**/readme.md'))
        if not alt_paths:
            issues.append(ValidationIssue(
                file_path="README.md",
                issue_type="missing_documentation",
                description="Documentação essencial não encontrada: README.md",
                expected="Arquivo deve existir na raiz do projeto",
                actual="Arquivo não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None

def validate_license():
    '''Valida existência de LICENSE.'''
    issues = []
    
    doc_paths = list(Path('.').rglob('**/LICENSE'))
    if not doc_paths:
        # Tentar variações case-insensitive
        alt_paths = list(Path('.').rglob('**/license'))
        if not alt_paths:
            issues.append(ValidationIssue(
                file_path="LICENSE",
                issue_type="missing_documentation",
                description="Documentação essencial não encontrada: LICENSE",
                expected="Arquivo deve existir na raiz do projeto",
                actual="Arquivo não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None

def validate_changelog_md():
    '''Valida existência de CHANGELOG.md.'''
    issues = []
    
    doc_paths = list(Path('.').rglob('**/CHANGELOG.md'))
    if not doc_paths:
        # Tentar variações case-insensitive
        alt_paths = list(Path('.').rglob('**/changelog.md'))
        if not alt_paths:
            issues.append(ValidationIssue(
                file_path="CHANGELOG.md",
                issue_type="missing_documentation",
                description="Documentação essencial não encontrada: CHANGELOG.md",
                expected="Arquivo deve existir na raiz do projeto",
                actual="Arquivo não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None

def validate_contributing_md():
    '''Valida existência de CONTRIBUTING.md.'''
    issues = []
    
    doc_paths = list(Path('.').rglob('**/CONTRIBUTING.md'))
    if not doc_paths:
        # Tentar variações case-insensitive
        alt_paths = list(Path('.').rglob('**/contributing.md'))
        if not alt_paths:
            issues.append(ValidationIssue(
                file_path="CONTRIBUTING.md",
                issue_type="missing_documentation",
                description="Documentação essencial não encontrada: CONTRIBUTING.md",
                expected="Arquivo deve existir na raiz do projeto",
                actual="Arquivo não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None

def validate_Dockerfile():
    '''Valida arquivo Docker: Dockerfile.'''
    issues = []
    
    docker_paths = list(Path('.').rglob('**/Dockerfile'))
    if not docker_paths:
        issues.append(ValidationIssue(
            file_path="Dockerfile",
            issue_type="missing_docker_file",
            description="Arquivo Docker não encontrado: Dockerfile",
            expected="Arquivo deve existir para containerização",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    
    return issues if issues else None

def validate_development_quality_tools():
    '''Valida ferramentas de qualidade de código.'''
    issues = []
    
    # Verificar pre-commit
    precommit_paths = list(Path('.').rglob('**/.pre-commit-config.yaml'))
    if not precommit_paths:
        issues.append(ValidationIssue(
            file_path=".pre-commit-config.yaml",
            issue_type="missing_precommit_config",
            description="Configuração pre-commit não encontrada",
            expected="Arquivo .pre-commit-config.yaml deve existir",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    
    # Verificar gitignore
    gitignore_paths = list(Path('.').rglob('**/.gitignore'))
    if not gitignore_paths:
        issues.append(ValidationIssue(
            file_path=".gitignore",
            issue_type="missing_gitignore",
            description="Arquivo .gitignore não encontrado",
            expected="Arquivo .gitignore deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None

class BlueprintArquiteturalIabankScaffoldValidator:
    """Validador especializado para scaffold completo (Alvo 0)."""

    SEVERITY_WEIGHTS = {
        "CRITICAL": 15,
        "HIGH": 8,
        "MEDIUM": 2,
        "LOW": 1
    }

    CATEGORY_WEIGHTS = {
        "STRUCTURE": 1.0,
        "CONTENT": 1.5,
        "MODELS": 2.0,
        "DEPENDENCIES": 1.2,
        "API": 1.3
    }

    def __init__(self):
        self.validation_methods = [
            "validate_directory_structure",
            "validate_pyproject_toml",
            "validate_package_json",
            "validate_gitignore",
            "validate_pre_commit_config_yaml",
            "validate_content_settings_py",
            "validate_content_models_py",
            "validate_content_pyproject_toml",
            "validate_dependency_django",
            "validate_dependency_djangorestframework",
            "validate_dependency_psycopg2_binary",
            "validate_django_settings_advanced",
            "validate_react_package_structure",
            "validate_multi_tenancy_implementation",
            "validate_readme_md",
            "validate_license",
            "validate_changelog_md",
            "validate_contributing_md",
            "validate_Dockerfile",
            "validate_development_quality_tools",
        ]

        self.rule_categories = {
            "validate_directory_structure": "STRUCTURE",
            "validate_pyproject_toml": "STRUCTURE",
            "validate_package_json": "STRUCTURE",
            "validate_gitignore": "STRUCTURE",
            "validate_pre_commit_config_yaml": "STRUCTURE",
            "validate_content_settings_py": "CONTENT",
            "validate_content_models_py": "CONTENT",
            "validate_content_pyproject_toml": "CONTENT",
            "validate_dependency_django": "DEPENDENCIES",
            "validate_dependency_djangorestframework": "DEPENDENCIES",
            "validate_dependency_psycopg2_binary": "DEPENDENCIES",
            "validate_django_settings_advanced": "CONTENT",
            "validate_react_package_structure": "DEPENDENCIES",
            "validate_multi_tenancy_implementation": "MODELS",
            "validate_readme_md": "CONTENT",
            "validate_license": "CONTENT",
            "validate_changelog_md": "CONTENT",
            "validate_contributing_md": "CONTENT",
            "validate_Dockerfile": "STRUCTURE",
            "validate_development_quality_tools": "STRUCTURE",
        }

    def validate(self) -> ValidationResults:
        """Executa todas as validações e retorna os resultados."""
        issues = []
        total_checks = len(self.validation_methods)
        failed_validations = 0
        categories = {"STRUCTURE": 0, "CONTENT": 0, "MODELS": 0, "DEPENDENCIES": 0, "API": 0}

        print(f"Executando {total_checks} validações especializadas...")
        print("Níveis: STRUCTURE | CONTENT | MODELS | DEPENDENCIES | API")
        print("-" * 80)

        for method_name in self.validation_methods:
            try:
                method = globals()[method_name]
                result = method()

                category = self.rule_categories.get(method_name, "STRUCTURE")
                print(f"[{category:12}] {method_name}", end="")

                if result:
                    failed_validations += 1
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

        passed_checks = total_checks - failed_validations
        score = self._calculate_score(total_checks, failed_validations, issues)

        return ValidationResults(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_validations,
            issues=issues,
            score=score,
            categories=categories
        )

    def _calculate_score(self, total_checks: int, failed_validations: int, issues: List[ValidationIssue]) -> float:
        """Calcula score baseado na severidade e categoria dos problemas."""
        if failed_validations == 0:
            return 100.0

        total_penalty = 0
        for issue in issues:
            severity_weight = self.SEVERITY_WEIGHTS.get(issue.severity, 1)
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

        base_score = ((total_checks - failed_validations) / total_checks) * 100
        penalty_factor = min(total_penalty / (failed_validations * 10), 0.5)
        final_score = max(0, base_score - (base_score * penalty_factor))

        return round(final_score, 2)

    def generate_report(self, results: ValidationResults) -> str:
        """Gera relatório detalhado dos resultados."""
        report = []
        report.append("=" * 100)
        report.append("RELATÓRIO DE VALIDAÇÃO - VALIDADOR ESPECIALIZADO PARA SCAFFOLD COMPLETO (ALVO 0)")
        report.append("=" * 100)
        report.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("Validador: BlueprintArquiteturalIabankScaffoldValidator")
        report.append("")
        report.append("RESULTADOS:")
        report.append(f"├─ Total de Verificações: {results.total_checks}")
        report.append(f"├─ Aprovadas: {results.passed_checks}")
        report.append(f"├─ Reprovadas: {results.failed_checks}")
        report.append(f"└─ Score Final: {results.score}%")
        report.append("")

        # Análise por categoria
        report.append("ANÁLISE POR CATEGORIA:")
        for category, count in results.categories.items():
            status = "FALHOU" if count > 0 else "OK"
            report.append(f"|- {status} {category:12}: {count} problemas")
        report.append("")

        # Status
        if results.score >= 90:
            report.append("STATUS: EXCELENTE")
        elif results.score >= 85:
            report.append("STATUS: APROVADO")
        elif results.score >= 70:
            report.append("STATUS: NECESSITA MELHORIAS")
        else:
            report.append("STATUS: REJEITADO")

        report.append("")

        if results.issues:
            # Agrupar por severidade
            critical_issues = [i for i in results.issues if i.severity == "CRITICAL"]
            high_issues = [i for i in results.issues if i.severity == "HIGH"]
            medium_issues = [i for i in results.issues if i.severity == "MEDIUM"]
            low_issues = [i for i in results.issues if i.severity == "LOW"]

            if critical_issues:
                report.append("PROBLEMAS CRÍTICOS:")
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
                    report.append("")

            if medium_issues:
                report.append("PROBLEMAS DE MÉDIA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(medium_issues, 1):
                    report.append(f"{i}. {issue.description}")
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
    """Função principal do validador."""
    import os
    import sys
    
    # Configurar encoding para Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    validator = BlueprintArquiteturalIabankScaffoldValidator()
    results = validator.validate()

    # Gerar e exibir relatório
    report = validator.generate_report(results)
    print()
    
    # Exibir relatório com tratamento de encoding
    try:
        print(report)
    except UnicodeEncodeError:
        # Fallback para encoding seguro
        safe_report = report.encode('utf-8', errors='replace').decode('utf-8')
        print(safe_report)

    # Salvar resultados em JSON
    results_file = Path("validation_results.json")
    results_file.write_text(
        json.dumps(results.to_dict(), indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    print(f"\nRelatório detalhado salvo em: {results_file}")

    return 0 if results.score >= 75 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)