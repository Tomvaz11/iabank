#!/usr/bin/env python3
"""
BaseGenerator - Classe base compartilhada para todos os geradores de validação AGV.
Contém funcionalidades comuns e métodos utilitários reutilizáveis.
"""

import re
from typing import Dict, List, Any
from abc import ABC, abstractmethod

from .blueprint_parser import ProjectSpecs
from .validation_rules import ValidationRule
from .logging_config import get_logger
from .metrics import get_metrics_collector
from .exceptions import GeneratorException


class BaseGenerator(ABC):
    """Classe base abstrata para todos os geradores de validação."""
    
    def __init__(self, specs: ProjectSpecs):
        self.specs = specs
        self.rules: List[ValidationRule] = []
        self.logger = get_logger(f"generator.{self.__class__.__name__.lower()}")
        self.metrics = get_metrics_collector()
        
        self.logger.info(f"Initialized {self.__class__.__name__} for project: {specs.project_name}")
    
    @abstractmethod
    def generate_rules(self) -> List[ValidationRule]:
        """Método abstrato que cada gerador deve implementar."""
        pass
    
    def _create_directory_validation_code(self, directory_structure: Dict[str, Any], prefix: str = "") -> str:
        """Cria código para validação da estrutura de diretórios."""
        validations = []
        
        def collect_validations(struct, current_path=""):
            for name, content in struct.items():
                full_path = f"{current_path}/{name}" if current_path else name
                
                if content is None:  # Arquivo
                    validations.append(full_path)
                elif isinstance(content, dict):  # Diretório
                    validations.append(full_path + "/")
                    collect_validations(content, full_path)
        
        collect_validations(directory_structure)
        
        return f"""
def validate_directory_structure():
    '''Valida estrutura completa de diretórios conforme Blueprint.'''
    import os
    from pathlib import Path
    
    issues = []
    required_paths = {validations}
    
    for required_path in required_paths:
        path = Path(required_path)
        
        if required_path.endswith('/'):
            # Diretório
            if not path.is_dir():
                issues.append(ValidationIssue(
                    file_path=str(path),
                    issue_type="missing_directory",
                    description=f"Diretório obrigatório não encontrado: " + required_path,
                    expected=f"Diretório " + required_path + " deve existir",
                    actual="Diretório não existe",
                    severity="HIGH"
                ))
        else:
            # Arquivo
            if not path.is_file():
                issues.append(ValidationIssue(
                    file_path=str(path),
                    issue_type="missing_file",
                    description=f"Arquivo obrigatório não encontrado: " + required_path,
                    expected=f"Arquivo " + required_path + " deve existir",
                    actual="Arquivo não existe",
                    severity="MEDIUM"
                ))
    
    return issues if issues else None
"""

    def _create_content_validation_code(self, file_path: str, validations: List[str]) -> str:
        """Cria código para validação de conteúdo específico."""
        validation_checks = []
        
        for validation in validations:
            if "INSTALLED_APPS" in validation:
                validation_checks.append(f"""
            # Verificar INSTALLED_APPS
            if 'INSTALLED_APPS' in content:
                for app in {self.specs.django_apps}:
                    if app not in content:
                        issues.append(ValidationIssue(
                            file_path=file_path_str,
                            issue_type="missing_installed_app",
                            description=f"App " + app + " não encontrada em INSTALLED_APPS",
                            expected=f"" + app + " deve estar em INSTALLED_APPS",
                            actual="App não listada",
                            severity="HIGH"
                        ))""")
            
            elif "DATABASE" in validation and "PostgreSQL" in validation:
                # Validação específica para scaffold: verificar estrutura de configuração
                validation_checks.append("""
            # Verificar configuracao PostgreSQL - SCAFFOLD: estrutura apenas
            if 'DATABASES' in content:
                # Para scaffold, verificar se usa django-environ ou tem estrutura PostgreSQL
                if ('env.db()' not in content and 
                    'postgresql' not in content.lower() and 
                    'psycopg' not in content.lower()):
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="wrong_database_config",
                        description="Database não configurado para PostgreSQL",
                        expected="ENGINE deve usar PostgreSQL (psycopg2) ou env.db()",
                        actual="PostgreSQL não detectado",
                        severity="HIGH"
                    ))""")
            
            elif "REST_FRAMEWORK" in validation:
                validation_checks.append("""
            # Verificar configuracao DRF
            if 'REST_FRAMEWORK' not in content:
                issues.append(ValidationIssue(
                    file_path=file_path_str,
                    issue_type="missing_drf_config",
                    description="Configuração REST_FRAMEWORK não encontrada",
                    expected="REST_FRAMEWORK deve estar configurado",
                    actual="Configuração ausente",
                    severity="MEDIUM"
                ))""")
        
        return f"""
def validate_content_{re.sub(r'[^\w]', '_', file_path).strip('_')}():
    '''Valida conteúdo específico de {file_path}.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/{file_path}'))
    if not file_paths:
        return ValidationIssue(
            file_path="{file_path}",
            issue_type="missing_file",
            description="Arquivo {file_path} não encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo não existe",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        if file_path_obj.exists():
            file_path_str = str(file_path_obj)
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            {''.join(validation_checks)}
    
    return issues if issues else None
"""

    def _create_specific_dependency_validation(self, dep_name: str, version: str) -> str:
        """Cria validação para dependência específica."""
        return f"""
def validate_dependency_{re.sub(r'[^\w]', '_', dep_name).strip('_')}():
    '''Valida dependência específica {dep_name}.'''
    issues = []
    
    # Verificar em pyproject.toml (excluindo agv-system próprio)
    pyproject_files = list(Path('.').rglob('**/pyproject.toml'))
    # Filtrar arquivos do agv-system para evitar validar as próprias dependências  
    project_files = [f for f in pyproject_files if 'agv-system' not in str(f)]
    found = False
    
    for pyproject_file in project_files:
        if pyproject_file.exists():
            content = pyproject_file.read_text(encoding='utf-8', errors='ignore')
            if '{dep_name}' in content:
                found = True
                # Verificar versão se especificada
                if '{version}' and '{version}' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(pyproject_file),
                        issue_type="wrong_dependency_version",
                        description="Versão incorreta para {dep_name}",
                        expected="Versão {version}",
                        actual="Versão diferente ou não especificada",
                        severity="MEDIUM"
                    ))
    
    if not found:
        issues.append(ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_dependency",
            description="Dependência {dep_name} não encontrada",
            expected="Dependência deve estar listada",
            actual="Dependência ausente",
            severity="MEDIUM"
        ))
    
    return issues if issues else None
"""

    def _create_models_validation_code(self) -> str:
        """Cria código para validação geral de modelos."""
        expected_models = list(self.specs.models.keys())
        
        return f"""
def validate_django_models():
    '''Valida modelos Django conforme especificação.'''
    issues = []
    expected_models = {expected_models}
    
    models_files = list(Path('.').rglob('**/models.py'))
    found_models = set()
    
    for model_file in models_files:
        if model_file.exists():
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Encontrar definições de classe
            class_matches = re.findall(r'class (\\w+)\\([^)]*\\):', content)
            for class_name in class_matches:
                if class_name in expected_models:
                    found_models.add(class_name)
    
    # Verificar modelos não encontrados
    missing_models = set(expected_models) - found_models
    for missing_model in missing_models:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="missing_model",
            description=f"Modelo " + missing_model + " não encontrado",
            expected=f"Classe " + missing_model + " deve estar definida",
            actual="Modelo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""

    def _create_specific_model_validation(self, model_name: str, model_info: Dict[str, Any]) -> str:
        """Cria validação para modelo específico."""
        expected_fields = model_info.get('fields', [])
        
        return f"""
def validate_model_{model_name.lower()}():
    '''Valida modelo específico {model_name}.'''
    issues = []
    expected_fields = {expected_fields}
    
    models_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in models_files:
        if model_file.exists():
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Buscar definição da classe
            class_pattern = rf'class {model_name}\\([^)]*\\):(.*?)(?=^class |^def |\\Z)'
            class_match = re.search(class_pattern, content, re.MULTILINE | re.DOTALL)
            
            if class_match:
                model_found = True
                class_body = class_match.group(1)
                
                # Verificar campos obrigatórios
                for expected_field in expected_fields:
                    if f'{{expected_field}} =' not in class_body:
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_field",
                            description=f"Campo {{expected_field}} não encontrado em {model_name}",
                            expected="Campo {{expected_field}} deve estar definido",
                            actual="Campo não existe",
                            severity="HIGH"
                        ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="missing_model_class",
            description="Modelo {model_name} não encontrado",
            expected="Classe {model_name} deve estar definida",
            actual="Modelo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""

    def _create_multi_tenancy_validation_code(self) -> str:
        """Cria código para validação de multi-tenancy."""
        if not self.specs.multi_tenancy:
            return ""
        
        return f"""
def validate_multi_tenancy_implementation():
    '''Valida implementação completa de multi-tenancy.'''
    issues = []
    
    # Verificar BaseTenantModel especificamente no core/models.py
    core_models_files = list(Path('.').rglob('**/core/models.py'))
    base_tenant_found = False
    
    for model_file in core_models_files:
        if model_file.exists():
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            if '{self.specs.base_model_class}' in content:
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
                    
                # Verificação mais flexível para abstract = True
                import re
                abstract_pattern = r'abstract\s*=\s*True'
                if not re.search(abstract_pattern, content, re.IGNORECASE):
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
"""