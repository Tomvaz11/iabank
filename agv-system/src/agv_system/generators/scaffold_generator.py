#!/usr/bin/env python3
"""
ScaffoldGenerator - Gerador especializado para validação de scaffold (Alvo 0).
Foco em estrutura completa de projeto, configurações base e arquivos iniciais.
"""

import re
from typing import List
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.base_generator import BaseGenerator
from core.validation_rules import ValidationRule


class ScaffoldGenerator(BaseGenerator):
    """Gerador especializado para validação de scaffold completo (Alvo 0)."""
    
    def generate_rules(self) -> List[ValidationRule]:
        """Gera todas as regras específicas para scaffold."""
        self.rules = []
        
        # Validações estruturais críticas
        self._generate_structure_rules()
        
        # Validações de configuração base
        self._generate_configuration_validation_rules()
        
        # Validações de conteúdo de arquivos críticos
        self._generate_content_validation_rules()
        
        # Validações de dependências base
        self._generate_dependency_validation_rules()
        
        # Validações específicas para Django/React
        self._generate_framework_specific_rules()
        
        # Validações de modelo se multi-tenancy
        if self.specs.multi_tenancy:
            self._generate_multi_tenancy_rules()
            
        # Validações de documentação básica
        self._generate_documentation_rules()
        
        # Validações de Docker/containerização
        self._generate_docker_rules()
        
        # Validações de setup de desenvolvimento
        self._generate_development_setup_rules()
        
        return self.rules
    
    def _generate_structure_rules(self):
        """Gera regras estruturais profundas para scaffold."""
        if self.specs.directory_structure:
            rule_code = self._create_directory_validation_code(self.specs.directory_structure)
            self.rules.append(ValidationRule(
                name="validate_directory_structure",
                description="Valida estrutura completa de diretórios conforme Blueprint",
                code=rule_code,
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_configuration_validation_rules(self):
        """Gera regras para validar arquivos de configuração críticos."""
        critical_configs = [
            "pyproject.toml", "package.json", ".env.example", 
            "docker-compose.yml", ".gitignore", ".pre-commit-config.yaml"
        ]
        
        for config_file in critical_configs:
            if config_file in self.specs.configuration_files:
                rule_code = f"""
def validate_{re.sub(r'[^\w]', '_', config_file).strip('_')}():
    '''Valida existência e estrutura básica de {config_file}.'''
    issues = []
    
    config_paths = list(Path('.').rglob('**/{config_file}'))
    if not config_paths:
        issues.append(ValidationIssue(
            file_path="{config_file}",
            issue_type="missing_config_file",
            description="Arquivo de configuração crítico não encontrado: {config_file}",
            expected="Arquivo deve existir na raiz do projeto",
            actual="Arquivo não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""
                
                self.rules.append(ValidationRule(
                    name=f"validate_{re.sub(r'[^\w]', '_', config_file).strip('_')}",
                    description=f"Valida arquivo de configuração {config_file}",
                    code=rule_code.strip(),
                    severity="HIGH",
                    category="STRUCTURE"
                ))
    
    def _generate_content_validation_rules(self):
        """Gera regras para validar conteúdo específico de arquivos."""
        for file_path, validations in self.specs.file_content_validations.items():
            rule_code = self._create_content_validation_code(file_path, validations)
            clean_name = re.sub(r'[^\w]', '_', file_path).strip('_')
            
            self.rules.append(ValidationRule(
                name=f"validate_content_{clean_name}",
                description=f"Valida conteúdo específico de {file_path}",
                code=rule_code,
                severity="HIGH",
                category="CONTENT"
            ))
    
    def _generate_dependency_validation_rules(self):
        """Gera regras avançadas para validação de dependências base."""
        # Dependências críticas para scaffold
        critical_backend_deps = ['django', 'djangorestframework', 'psycopg2-binary']
        critical_frontend_deps = ['react', '@types/react']
        
        for dep_name in critical_backend_deps:
            if dep_name in self.specs.specific_dependencies:
                version = self.specs.specific_dependencies[dep_name]
                rule_code = self._create_specific_dependency_validation(dep_name, version)
                clean_name = re.sub(r'[^\w]', '_', dep_name).strip('_')
                
                self.rules.append(ValidationRule(
                    name=f"validate_dependency_{clean_name}",
                    description=f"Valida dependência crítica {dep_name}",
                    code=rule_code,
                    severity="HIGH",
                    category="DEPENDENCIES"
                ))
    
    def _generate_framework_specific_rules(self):
        """Gera regras específicas para Django e React."""
        # Django settings structure validation
        if self.specs.backend_framework == "django":
            rule_code = """
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
"""
            
            self.rules.append(ValidationRule(
                name="validate_django_settings_advanced",
                description="Valida configurações avançadas do Django",
                code=rule_code.strip(),
                severity="HIGH",
                category="CONTENT"
            ))
        
        # React package.json structure validation  
        if self.specs.frontend_framework == "react":
            rule_code = """
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
"""
            
            self.rules.append(ValidationRule(
                name="validate_react_package_structure",
                description="Valida estrutura do package.json para React",
                code=rule_code.strip(),
                severity="HIGH",
                category="DEPENDENCIES"
            ))
    
    def _generate_multi_tenancy_rules(self):
        """Gera regras específicas para multi-tenancy no scaffold."""
        if not self.specs.multi_tenancy:
            return
        
        rule_code = self._create_multi_tenancy_validation_code()
        
        self.rules.append(ValidationRule(
            name="validate_multi_tenancy_implementation",
            description="Valida implementação completa de multi-tenancy no scaffold",
            code=rule_code.strip(),
            severity="CRITICAL",
            category="MODELS"
        ))
    
    def _generate_documentation_rules(self):
        """Gera regras para documentação básica."""
        essential_docs = ["README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md"]
        
        for doc_file in essential_docs:
            if doc_file in self.specs.documentation_files or doc_file.lower() in [d.lower() for d in self.specs.documentation_files]:
                rule_code = f"""
def validate_{re.sub(r'[^\w]', '_', doc_file).strip('_').lower()}():
    '''Valida existência de {doc_file}.'''
    issues = []
    
    doc_paths = list(Path('.').rglob('**/{doc_file}'))
    if not doc_paths:
        # Tentar variações case-insensitive
        alt_paths = list(Path('.').rglob('**/{doc_file.lower()}'))
        if not alt_paths:
            issues.append(ValidationIssue(
                file_path="{doc_file}",
                issue_type="missing_documentation",
                description="Documentação essencial não encontrada: {doc_file}",
                expected="Arquivo deve existir na raiz do projeto",
                actual="Arquivo não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
                
                self.rules.append(ValidationRule(
                    name=f"validate_{re.sub(r'[^\w]', '_', doc_file).strip('_').lower()}",
                    description=f"Valida documentação essencial {doc_file}",
                    code=rule_code.strip(),
                    severity="MEDIUM",
                    category="CONTENT"
                ))
    
    def _generate_docker_rules(self):
        """Gera regras para configuração Docker."""
        docker_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
        
        for docker_file in docker_files:
            if docker_file in self.specs.docker_files:
                rule_code = f"""
def validate_{re.sub(r'[^\w]', '_', docker_file).strip('_')}():
    '''Valida arquivo Docker: {docker_file}.'''
    issues = []
    
    docker_paths = list(Path('.').rglob('**/{docker_file}'))
    if not docker_paths:
        issues.append(ValidationIssue(
            file_path="{docker_file}",
            issue_type="missing_docker_file",
            description="Arquivo Docker não encontrado: {docker_file}",
            expected="Arquivo deve existir para containerização",
            actual="Arquivo não existe",
            severity="MEDIUM"
        ))
    
    return issues if issues else None
"""
                
                self.rules.append(ValidationRule(
                    name=f"validate_{re.sub(r'[^\w]', '_', docker_file).strip('_')}",
                    description=f"Valida arquivo Docker {docker_file}",
                    code=rule_code.strip(),
                    severity="MEDIUM",
                    category="STRUCTURE"
                ))
    
    def _generate_development_setup_rules(self):
        """Gera regras para setup de desenvolvimento."""
        # Validação de ferramentas de qualidade de código
        rule_code = """
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
"""
        
        self.rules.append(ValidationRule(
            name="validate_development_quality_tools",
            description="Valida ferramentas de qualidade e setup de desenvolvimento",
            code=rule_code.strip(),
            severity="MEDIUM",
            category="STRUCTURE"
        ))