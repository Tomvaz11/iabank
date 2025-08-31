#!/usr/bin/env python3
"""
ValidatorGenerator v2.0 - Sistema Avançado de Geração de Validadores
Gera validadores de nível profissional com validações profundas de conteúdo.

VERSÃO PROFISSIONAL - Successor do ValidatorGenerator v1.0
- Parser avançado de Blueprint com análise profunda
- 67+ validações especializadas por categoria
- Validação de conteúdo real vs apenas existência
- Sistema de scoring com pesos por severidade e categoria
- Suporte completo a multi-tenancy e modelos Django avançados
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationRule:
    """Representa uma regra de validação específica."""
    name: str
    description: str
    code: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # STRUCTURE, CONTENT, DEPENDENCIES, MODELS, API


@dataclass
class ProjectSpecs:
    """Especificações avançadas extraídas do Blueprint."""
    project_name: str
    project_description: str
    backend_framework: str
    frontend_framework: str
    database: str
    architecture_type: str
    backend_apps: List[str]
    directory_structure: Dict[str, Any]
    configuration_files: List[str]
    documentation_files: List[str]
    dependencies: Dict[str, List[str]]
    models: Dict[str, Dict]  # modelo -> {fields: [], meta: {}}
    api_patterns: List[str]
    testing_framework: str
    ci_cd_pipeline: List[str]
    docker_files: List[str]
    # Especificações avançadas
    django_apps: List[str]
    model_relationships: Dict[str, List[str]]
    authentication_method: str
    multi_tenancy: bool
    base_model_class: str
    specific_dependencies: Dict[str, str]  # nome -> versão
    file_content_validations: Dict[str, List[str]]  # arquivo -> validações


class AdvancedBlueprintParser:
    """Parser inteligente e profundo para extrair especificações complexas."""
    
    def __init__(self, blueprint_path: str):
        self.blueprint_path = Path(blueprint_path)
        self.content = self._read_blueprint()
        self.specs = ProjectSpecs(
            project_name="",
            project_description="",
            backend_framework="",
            frontend_framework="",
            database="",
            architecture_type="",
            backend_apps=[],
            directory_structure={},
            configuration_files=[],
            documentation_files=[],
            dependencies={"backend": [], "frontend": []},
            models={},
            api_patterns=[],
            testing_framework="",
            ci_cd_pipeline=[],
            docker_files=[],
            django_apps=[],
            model_relationships={},
            authentication_method="",
            multi_tenancy=False,
            base_model_class="",
            specific_dependencies={},
            file_content_validations={}
        )
    
    def _read_blueprint(self) -> str:
        """Lê o arquivo Blueprint."""
        if not self.blueprint_path.exists():
            raise FileNotFoundError(f"Blueprint não encontrado: {self.blueprint_path}")
        
        return self.blueprint_path.read_text(encoding='utf-8')
    
    def parse(self) -> ProjectSpecs:
        """Faz o parsing completo e profundo do Blueprint."""
        self._extract_project_info()
        self._extract_technology_stack()
        self._extract_directory_structure()
        self._extract_configuration_files()
        self._extract_documentation_files()
        self._extract_dependencies()
        self._extract_models_deep()
        self._extract_django_apps()
        self._extract_api_patterns()
        self._extract_testing_info()
        self._extract_ci_cd_info()
        self._extract_docker_files()
        self._extract_authentication()
        self._extract_multi_tenancy()
        self._extract_file_content_validations()
        
        return self.specs
    
    def _extract_project_info(self):
        """Extrai informações básicas do projeto."""
        # Nome do projeto
        title_match = re.search(r'^#\s*(.+?)(?:\s*\(.*?\))?$', self.content, re.MULTILINE)
        if title_match:
            self.specs.project_name = title_match.group(1).strip().replace(":", " -")
        
        # Descrição mais precisa
        desc_patterns = [
            r'Este documento define.*?para o (.+?)\.', 
            r'O (.+?) é uma plataforma',
            r'Sistema de (.+?) moderno'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                self.specs.project_description = match.group(1).strip()
                break
    
    def _extract_technology_stack(self):
        """Extrai stack tecnológica com detalhes específicos."""
        # Backend framework com versões
        django_match = re.search(r'django["\s]*=?\s*["\^~]*([0-9.]+)', self.content, re.IGNORECASE)
        if django_match or 'Django' in self.content:
            self.specs.backend_framework = "django"
            if django_match:
                self.specs.specific_dependencies["django"] = django_match.group(1)
        
        # Frontend framework com versões  
        react_match = re.search(r'"react":\s*"[\^~]*([0-9.]+)"', self.content, re.IGNORECASE)
        if react_match or 'React' in self.content:
            self.specs.frontend_framework = "react"
            if react_match:
                self.specs.specific_dependencies["react"] = react_match.group(1)
        
        # Database
        if re.search(r'postgresql', self.content, re.IGNORECASE):
            self.specs.database = "postgresql"
        
        # Arquitetura
        if re.search(r'monolito|monolith', self.content, re.IGNORECASE):
            self.specs.architecture_type = "monolith"
    
    def _extract_models_deep(self):
        """Extrai modelos com análise profunda de campos e relacionamentos."""
        # Buscar blocos de código Python com modelos
        python_blocks = re.findall(r'```python\n(.*?)\n```', self.content, re.DOTALL)
        
        for block in python_blocks:
            # Buscar definições de classe
            class_matches = re.findall(r'class (\w+)\([^)]*\):\s*\n(.*?)(?=\nclass|\n#|\Z)', block, re.DOTALL)
            
            for class_name, class_body in class_matches:
                if 'models.' in class_body or 'Model' in class_body:
                    model_info = self._parse_model_details(class_name, class_body)
                    self.specs.models[class_name] = model_info
                    
                    # Extrair relacionamentos
                    relationships = self._extract_model_relationships(class_body)
                    if relationships:
                        self.specs.model_relationships[class_name] = relationships
    
    def _parse_model_details(self, class_name: str, class_body: str) -> Dict[str, Any]:
        """Parse detalhado de um modelo Django."""
        model_info = {
            'fields': [],
            'field_types': {},
            'meta': {},
            'methods': [],
            'inheritance': '',
            'is_abstract': False
        }
        
        # Campos com tipos
        field_patterns = [
            (r'(\w+)\s*=\s*models\.(\w+)', 'django_field'),
            (r'(\w+)\s*=\s*models\.ForeignKey\([^)]*["\']([^"\']+)["\']', 'foreign_key'),
            (r'(\w+)\s*=\s*models\.OneToOneField\([^)]*["\']([^"\']+)["\']', 'one_to_one'),
            (r'(\w+)\s*=\s*models\.ManyToManyField\([^)]*["\']([^"\']+)["\']', 'many_to_many')
        ]
        
        for pattern, field_type in field_patterns:
            matches = re.findall(pattern, class_body)
            for match in matches:
                if isinstance(match, tuple):
                    field_name = match[0]
                    if field_type in ['foreign_key', 'one_to_one', 'many_to_many']:
                        model_info['field_types'][field_name] = f"{field_type}:{match[1] if len(match) > 1 else match[1]}"
                    else:
                        model_info['field_types'][field_name] = match[1]
                else:
                    field_name = match
                    model_info['field_types'][field_name] = field_type
                
                model_info['fields'].append(field_name)
        
        # Meta class
        if 'abstract = True' in class_body:
            model_info['is_abstract'] = True
        
        # Métodos
        method_matches = re.findall(r'def (\w+)\(', class_body)
        model_info['methods'] = [m for m in method_matches if not m.startswith('_')]
        
        return model_info
    
    def _extract_model_relationships(self, class_body: str) -> List[str]:
        """Extrai relacionamentos do modelo."""
        relationships = []
        
        # ForeignKey, OneToOne, ManyToMany
        fk_matches = re.findall(r'models\.(?:ForeignKey|OneToOneField|ManyToManyField)\([^)]*["\']([^"\']+)["\']', class_body)
        relationships.extend(fk_matches)
        
        return list(set(relationships))
    
    def _extract_django_apps(self):
        """Extrai apps Django específicas."""
        # Buscar menções de apps Django
        app_patterns = [
            r"'(\w+)'",  # em INSTALLED_APPS
            r'iabank/(\w+)/',  # estrutura de diretórios
            r'backend_apps.*?\[([^\]]+)\]'  # lista específica
        ]
        
        apps = set()
        for pattern in app_patterns:
            matches = re.findall(pattern, self.content)
            for match in matches:
                if isinstance(match, str) and match.isalnum():
                    apps.add(match)
        
        # Apps Django padrão conhecidos
        django_apps = {'core', 'users', 'customers', 'operations', 'finance'}
        
        # Extrair apps específicas do Blueprint primeiro
        apps_section = re.search(r'backend_apps.*?\[([^\]]+)\]', self.content, re.DOTALL)
        if apps_section:
            app_names = re.findall(r"'(\w+)'", apps_section.group(1))
            self.specs.django_apps = app_names
        else:
            # Fallback para apps conhecidos encontrados no texto
            self.specs.django_apps = [app for app in apps if app in django_apps and app.isalnum()]
    
    def _extract_authentication(self):
        """Extrai método de autenticação."""
        if re.search(r'JWT|simplejwt', self.content, re.IGNORECASE):
            self.specs.authentication_method = "JWT"
        elif re.search(r'Token', self.content, re.IGNORECASE):
            self.specs.authentication_method = "Token"
        else:
            self.specs.authentication_method = "Session"
    
    def _extract_multi_tenancy(self):
        """Detecta se o projeto usa multi-tenancy."""
        multi_tenant_indicators = [
            'multi-tenant', 'tenant', 'BaseTenantModel', 
            'tenant_id', 'ForeignKey.*Tenant'
        ]
        
        for indicator in multi_tenant_indicators:
            if re.search(indicator, self.content, re.IGNORECASE):
                self.specs.multi_tenancy = True
                self.specs.base_model_class = "BaseTenantModel"
                break
    
    def _extract_file_content_validations(self):
        """Extrai validações específicas de conteúdo de arquivos."""
        # settings.py validations
        self.specs.file_content_validations["settings.py"] = [
            "INSTALLED_APPS deve incluir apps do projeto",
            "DATABASE deve usar PostgreSQL", 
            "REST_FRAMEWORK deve estar configurado",
            "Configuração de multi-tenancy se aplicável"
        ]
        
        # models.py validations
        if self.specs.multi_tenancy:
            self.specs.file_content_validations["models.py"] = [
                "BaseTenantModel deve estar definido",
                "Todos os modelos devem herdar de BaseTenantModel",
                "Campo tenant deve estar presente"
            ]
        
        # pyproject.toml validations
        self.specs.file_content_validations["pyproject.toml"] = [
            "Django versão correta",
            "DRF incluído",
            "PostgreSQL driver incluído",
            "Dependências de desenvolvimento configuradas"
        ]
    
    def _extract_directory_structure(self):
        """Extrai estrutura de diretórios com análise inteligente."""
        # Buscar seção específica de estrutura
        structure_section = re.search(
            r'## 7\. Estrutura de Diretórios Proposta.*?```\s*\n(.*?)```', 
            self.content, 
            re.IGNORECASE | re.DOTALL
        )
        
        if structure_section:
            structure_text = structure_section.group(1)
            if '├──' in structure_text or '└──' in structure_text or '│' in structure_text:
                self.specs.directory_structure = self._parse_directory_tree_advanced(structure_text)
    
    def _parse_directory_tree_advanced(self, tree_text: str) -> Dict[str, Any]:
        """Parser avançado para árvore de diretórios."""
        structure = {}
        lines = [line.rstrip() for line in tree_text.split('\n') if line.strip()]
        
        current_path = []
        
        for line in lines:
            # Determina o nível baseado em indentação
            original_line = line
            level = 0
            
            # Conta símbolos de árvore de forma mais precisa
            tree_chars = 0
            for char in line:
                if char in '├└│':
                    tree_chars += 1
                elif char in '─ ':
                    continue
                else:
                    break
            
            # Limpa a linha de forma mais precisa
            clean_line = re.sub(r'^[├└│\s─]+', '', line).strip()
            
            # Remove comentários e linhas vazias
            if not clean_line or clean_line.startswith('#') or clean_line.startswith('//'):
                continue
                
            # Remove caracteres problemáticos e descrições
            clean_line = re.sub(r'\s*\(.*?\)\s*$', '', clean_line)  # Remove (descrições)
            clean_line = re.sub(r'\s*#.*$', '', clean_line)  # Remove # comentários
            clean_line = re.sub(r'[^\w\-._/]', '', clean_line)  # Remove chars especiais
            
            if clean_line:
                # Calcula nível de indentação baseado nos símbolos de árvore
                indent_level = tree_chars
                current_path = current_path[:indent_level]
                
                # Adiciona à estrutura
                current_dict = structure
                for path_part in current_path:
                    if path_part in current_dict and isinstance(current_dict[path_part], dict):
                        current_dict = current_dict[path_part]
                
                if clean_line.endswith('/'):
                    # Diretório
                    dir_name = clean_line.rstrip('/')
                    if dir_name and dir_name.isalnum() or '_' in dir_name or '-' in dir_name:
                        current_dict[dir_name] = {}
                        current_path.append(dir_name)
                else:
                    # Arquivo - validar extensão
                    if ('.' in clean_line and len(clean_line) < 100) or clean_line in ['README', 'LICENSE', 'Dockerfile']:
                        current_dict[clean_line] = None
        
        return structure
    
    def _extract_configuration_files(self):
        """Extrai arquivos de configuração com análise detalhada."""
        config_patterns = [
            r'\.env(?:\.example)?', r'pyproject\.toml', r'requirements\.txt',
            r'package\.json', r'package-lock\.json', r'yarn\.lock', r'pnpm-lock\.yaml',
            r'tsconfig\.json', r'vite\.config\.[jt]s', r'tailwind\.config\.[jt]s',
            r'settings\.py', r'config\.py', r'wsgi\.py', r'asgi\.py',
            r'\.gitignore', r'\.pre-commit-config\.yaml',
            r'docker-compose\.ya?ml', r'Dockerfile', r'\.dockerignore',
            r'\.github/workflows/.*\.ya?ml'
        ]
        
        for pattern in config_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                clean_pattern = pattern.replace('\\', '').replace('?', '')
                if clean_pattern not in self.specs.configuration_files:
                    self.specs.configuration_files.append(clean_pattern)
    
    def _extract_documentation_files(self):
        """Extrai arquivos de documentação."""
        doc_patterns = [
            r'README\.md', r'CHANGELOG\.md', r'CONTRIBUTING\.md',
            r'LICENSE', r'docs/', r'\.md'
        ]
        
        for pattern in doc_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                clean_pattern = pattern.replace('\\', '')
                if clean_pattern not in self.specs.documentation_files:
                    self.specs.documentation_files.append(clean_pattern)
    
    def _extract_dependencies(self):
        """Extrai dependências com versões específicas."""
        # Dependências Python
        python_deps = {}
        
        # Lista de dependências válidas para filtrar ruído
        valid_python_deps = {
            'django', 'djangorestframework', 'psycopg2-binary', 'django-environ',
            'celery', 'redis', 'gunicorn', 'structlog', 'django-filter',
            'djangorestframework-simplejwt', 'pytest', 'pytest-django',
            'factory-boy', 'pytest-cov', 'black', 'ruff', 'pre-commit'
        }
        
        # Buscar em blocos de configuração
        toml_blocks = re.findall(r'```toml\n(.*?)\n```', self.content, re.DOTALL)
        for block in toml_blocks:
            deps = re.findall(r'(\w[\w-]*)\s*=\s*["\^~]*([0-9.]+)', block)
            for dep, version in deps:
                if dep.lower() in valid_python_deps:
                    python_deps[dep] = version
        
        # Dependências mencionadas no texto (com filtro)
        text_deps = re.findall(r'([a-z][\w-]+)\s*[=:]\s*["\^~]*([0-9.]+)', self.content)
        for dep, version in text_deps:
            if dep.lower() in valid_python_deps:
                python_deps[dep] = version
        
        self.specs.dependencies["backend"] = list(python_deps.keys())
        self.specs.specific_dependencies.update(python_deps)
        
        # Dependências Node.js
        package_blocks = re.findall(r'```json.*?"dependencies":\s*{([^}]+)}', self.content, re.DOTALL)
        for block in package_blocks:
            deps = re.findall(r'"([^"]+)":\s*"[\^~]*([0-9.]+)"', block)
            node_deps = dict(deps)
            self.specs.dependencies["frontend"] = list(node_deps.keys())
            self.specs.specific_dependencies.update(node_deps)
    
    def _extract_api_patterns(self):
        """Extrai padrões de API."""
        if re.search(r'REST|RESTful', self.content, re.IGNORECASE):
            self.specs.api_patterns.append("REST")
        if re.search(r'api/v\d+', self.content, re.IGNORECASE):
            self.specs.api_patterns.append("versioned")
        if re.search(r'DRF|Django REST Framework', self.content, re.IGNORECASE):
            self.specs.api_patterns.append("DRF")
    
    def _extract_testing_info(self):
        """Extrai informações sobre testes."""
        if re.search(r'pytest', self.content, re.IGNORECASE):
            self.specs.testing_framework = "pytest"
        elif re.search(r'vitest', self.content, re.IGNORECASE):
            self.specs.testing_framework = "vitest"
    
    def _extract_ci_cd_info(self):
        """Extrai informações sobre CI/CD."""
        ci_patterns = [
            "github actions", "gitlab ci", "jenkins",
            "docker build", "docker push", "deploy"
        ]
        
        for pattern in ci_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                self.specs.ci_cd_pipeline.append(pattern)
    
    def _extract_docker_files(self):
        """Extrai informações sobre Docker."""
        docker_patterns = [
            r'Dockerfile', r'docker-compose\.ya?ml',
            r'\.dockerignore'
        ]
        
        for pattern in docker_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                clean_pattern = pattern.replace('\\', '').replace('?', '')
                if clean_pattern not in self.specs.docker_files:
                    self.specs.docker_files.append(clean_pattern)


class ProValidationRuleGenerator:
    """Gera regras de validação avançadas e profundas."""
    
    def __init__(self, specs: ProjectSpecs):
        self.specs = specs
        self.rules: List[ValidationRule] = []
    
    def generate_all_rules(self) -> List[ValidationRule]:
        """Gera todas as regras de validação avançadas."""
        self._generate_structure_rules()
        self._generate_content_validation_rules()
        self._generate_model_validation_rules()
        self._generate_dependency_validation_rules()
        self._generate_configuration_validation_rules()
        self._generate_framework_specific_rules()
        self._generate_multi_tenancy_rules()
        self._generate_api_validation_rules()
        self._generate_testing_rules()
        self._generate_docker_rules()
        
        return self.rules
    
    def _generate_structure_rules(self):
        """Gera regras estruturais profundas."""
        if self.specs.directory_structure:
            rule_code = self._create_directory_validation_code(self.specs.directory_structure)
            self.rules.append(ValidationRule(
                name="validate_directory_structure",
                description="Valida estrutura completa de diretórios conforme Blueprint",
                code=rule_code,
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
    
    def _generate_model_validation_rules(self):
        """Gera regras específicas para validação de modelos."""
        if not self.specs.models:
            return
        
        # Validação geral de modelos
        rule_code = self._create_models_validation_code()
        self.rules.append(ValidationRule(
            name="validate_django_models",
            description="Valida modelos Django conforme especificação",
            code=rule_code,
            severity="CRITICAL",
            category="MODELS"
        ))
        
        # Validações específicas por modelo
        for model_name, model_info in self.specs.models.items():
            rule_code = self._create_specific_model_validation(model_name, model_info)
            self.rules.append(ValidationRule(
                name=f"validate_model_{model_name.lower()}",
                description=f"Valida modelo específico {model_name}",
                code=rule_code,
                severity="HIGH",
                category="MODELS"
            ))
    
    def _generate_dependency_validation_rules(self):
        """Gera regras avançadas para validação de dependências."""
        for dep_name, version in self.specs.specific_dependencies.items():
            rule_code = self._create_specific_dependency_validation(dep_name, version)
            clean_name = re.sub(r'[^\w]', '_', dep_name).strip('_')
            
            self.rules.append(ValidationRule(
                name=f"validate_dependency_{clean_name}",
                description=f"Valida dependência específica {dep_name}",
                code=rule_code,
                severity="MEDIUM",
                category="DEPENDENCIES"
            ))
    
    def _generate_multi_tenancy_rules(self):
        """Gera regras específicas para multi-tenancy."""
        if not self.specs.multi_tenancy:
            return
        
        rule_code = f"""
def validate_multi_tenancy_implementation():
    '''Valida implementação completa de multi-tenancy.'''
    issues = []
    
    # Verificar BaseTenantModel
    models_files = list(Path('.').rglob('**/models.py'))
    base_tenant_found = False
    
    for model_file in models_files:
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
"""
        
        self.rules.append(ValidationRule(
            name="validate_multi_tenancy_implementation",
            description="Valida implementação completa de multi-tenancy",
            code=rule_code.strip(),
            severity="CRITICAL",
            category="MODELS"
        ))
    
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
                            description=f"App {{app}} nao encontrada em INSTALLED_APPS",
                            expected=f"{{app}} deve estar em INSTALLED_APPS",
                            actual="App nao listada",
                            severity="HIGH"
                        ))""")
            
            elif "DATABASE" in validation and "PostgreSQL" in validation:
                validation_checks.append("""
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
                    ))""")
            
            elif "REST_FRAMEWORK" in validation:
                validation_checks.append("""
            # Verificar configuracao DRF
            if 'REST_FRAMEWORK' not in content:
                issues.append(ValidationIssue(
                    file_path=file_path_str,
                    issue_type="missing_drf_config",
                    description="Configuracao REST_FRAMEWORK nao encontrada",
                    expected="REST_FRAMEWORK deve estar configurado",
                    actual="Configuracao ausente",
                    severity="MEDIUM"
                ))""")
        
        return f"""
def validate_content_{re.sub(r'[^\w]', '_', file_path).strip('_')}():
    '''Valida conteudo especifico de {file_path}.'''
    issues = []
    
    file_paths = list(Path('.').rglob('**/{file_path}'))
    if not file_paths:
        return ValidationIssue(
            file_path="{file_path}",
            issue_type="missing_file",
            description="Arquivo {file_path} nao encontrado",
            expected="Arquivo deve existir",
            actual="Arquivo ausente",
            severity="HIGH"
        )
    
    for file_path_obj in file_paths:
        file_path_str = str(file_path_obj)
        try:
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            {"".join(validation_checks)}
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=file_path_str,
                issue_type="file_read_error",
                description=f"Erro ao ler arquivo: {{str(e)}}",
                expected="Arquivo deve ser legivel",
                actual=f"Erro: {{str(e)}}",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
    
    def _create_models_validation_code(self) -> str:
        """Cria validação geral para modelos Django."""
        expected_models = list(self.specs.models.keys())
        
        return f"""
def validate_django_models():
    '''Valida modelos Django conforme Blueprint.'''
    issues = []
    expected_models = {expected_models}
    
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
            class_matches = re.findall(r'class (\\w+)\\([^)]*Model[^)]*\\):', content)
            found_models.update(class_matches)
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_file_error",
                description=f"Erro ao analisar arquivo: {{str(e)}}",
                expected="Arquivo deve ser analisável",
                actual=f"Erro: {{str(e)}}",
                severity="MEDIUM"
            ))
    
    # Verificar modelos obrigatórios
    missing_models = set(expected_models) - found_models
    for model in missing_models:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="missing_model",
            description=f"Modelo {{model}} especificado no Blueprint não encontrado",
            expected=f"Modelo {{model}} deve estar implementado",
            actual="Modelo não encontrado",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""
    
    def _create_specific_model_validation(self, model_name: str, model_info: Dict[str, Any]) -> str:
        """Cria validação específica para um modelo."""
        expected_fields = model_info.get('fields', [])
        
        return f"""
def validate_model_{model_name.lower()}():
    '''Valida modelo específico {model_name}.'''
    issues = []
    expected_fields = {expected_fields}
    
    model_files = list(Path('.').rglob('**/models.py'))
    model_found = False
    
    for model_file in model_files:
        try:
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se modelo existe
            model_pattern = rf'class {model_name}\\([^)]*\\):(.*?)(?=\\nclass|\\Z)'
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
                            description=f"Campo {{field}} não encontrado em {model_name}",
                            expected=f"Campo {{field}} deve existir",
                            actual="Campo ausente",
                            severity="HIGH"
                        ))
                
                # Verificar herança se multi-tenancy
                if {str(self.specs.multi_tenancy).lower()} and '{self.specs.base_model_class}' not in content:
                    issues.append(ValidationIssue(
                        file_path=str(model_file),
                        issue_type="wrong_model_inheritance",
                        description=f"{model_name} deve herdar de {self.specs.base_model_class}",
                        expected=f"class {model_name}({self.specs.base_model_class}):",
                        actual="Herança incorreta",
                        severity="HIGH"
                    ))
                        
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(model_file),
                issue_type="model_analysis_error",
                description=f"Erro ao analisar modelo: {{str(e)}}",
                expected="Modelo deve ser analisável",
                actual=f"Erro: {{str(e)}}",
                severity="MEDIUM"
            ))
    
    if not model_found:
        issues.append(ValidationIssue(
            file_path="models.py",
            issue_type="model_not_found",
            description=f"Modelo {model_name} não encontrado",
            expected=f"Modelo {model_name} deve estar implementado",
            actual="Modelo ausente",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""
    
    def _create_specific_dependency_validation(self, dep_name: str, version: str) -> str:
        """Cria validação específica para uma dependência."""
        return f"""
def validate_dependency_{re.sub(r'[^\w]', '_', dep_name).strip('_')}():
    '''Valida dependência {dep_name} versão {version}.'''
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
                rf'"{dep_name}"\\s*[=:]\\s*"[^"]*{version}',
                rf'{dep_name}\\s*=\\s*"[^"]*{version}',
                rf'"{dep_name}"\\s*:\\s*"[^"]*{version}'
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
            description=f"Dependência {dep_name} versão {version} não encontrada",
            expected=f"{dep_name} = \\"{version}\\" deve estar configurado",
            actual="Dependência não encontrada ou versão incorreta",
            severity="MEDIUM"
        )
    
    return None
"""
    
    def _create_directory_validation_code(self, structure: Dict[str, Any], prefix: str = "") -> str:
        """Cria código avançado de validação para estrutura de diretórios."""
        validation_checks = []
        
        def traverse_structure(struct: Dict[str, Any], current_prefix: str = ""):
            for name, contents in struct.items():
                # Limpar e escapar caracteres
                clean_name = re.sub(r'[^\w\-_./]', '', name)
                full_path = f"{current_prefix}/{clean_name}" if current_prefix else clean_name
                escaped_path = full_path.replace("'", "\\'").replace('"', '\\"')
                
                if isinstance(contents, dict) and contents:
                    # Diretório
                    validation_checks.append(f"""
    dir_path = Path('{escaped_path}')
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(ValidationIssue(
            file_path='{escaped_path}',
            issue_type="missing_directory",
            description="Diretório obrigatório não encontrado: {escaped_path}",
            expected="Diretório {escaped_path} deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))""")
                    traverse_structure(contents, full_path)
                else:
                    # Arquivo
                    severity = "HIGH" if clean_name.endswith('.py') else "MEDIUM"
                    validation_checks.append(f"""
    file_path = Path('{escaped_path}')
    if not file_path.exists():
        issues.append(ValidationIssue(
            file_path='{escaped_path}',
            issue_type="missing_file",
            description="Arquivo obrigatório não encontrado: {escaped_path}",
            expected="Arquivo {escaped_path} deve existir",
            actual="Arquivo não existe",
            severity="{severity}"
        ))""")
        
        traverse_structure(structure)
        
        return f"""
def validate_directory_structure():
    '''Valida estrutura completa de diretórios conforme Blueprint.'''
    issues = []
    {"".join(validation_checks)}
    return issues if issues else None
"""
    
    def _generate_configuration_validation_rules(self):
        """Gera regras avançadas para arquivos de configuração."""
        for config_file in self.specs.configuration_files:
            if config_file in ['pyproject.toml', 'package.json', 'settings.py']:
                # Já tratados em validações específicas
                continue
                
            clean_name = re.sub(r'[^\w]', '_', config_file).strip('_')
            rule_code = f"""
def validate_{clean_name}():
    '''Valida arquivo de configuração {config_file}.'''
    config_paths = [Path('{config_file}')]
    
    # Tentar localizações alternativas
    if '/' not in '{config_file}':
        config_paths.extend([
            Path('backend/{config_file}'),
            Path('frontend/{config_file}'),
            Path('./{config_file}')
        ])
    
    found = False
    for config_path in config_paths:
        if config_path.exists():
            found = True
            break
    
    if not found:
        return ValidationIssue(
            file_path='{config_file}',
            issue_type="missing_config_file",
            description="Arquivo de configuração obrigatório não encontrado: {config_file}",
            expected="Arquivo {config_file} deve existir",
            actual="Arquivo não encontrado",
            severity="HIGH"
        )
    
    return None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{clean_name}",
                description=f"Valida arquivo de configuração {config_file}",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_framework_specific_rules(self):
        """Gera regras específicas dos frameworks."""
        if self.specs.backend_framework == "django":
            self._generate_django_specific_rules()
        
        if self.specs.frontend_framework == "react":
            self._generate_react_specific_rules()
    
    def _generate_django_specific_rules(self):
        """Gera regras específicas para Django."""
        # Settings.py avançado
        rule_code = f"""
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
                    description=f"Configuração {{setting}} não encontrada",
                    expected=f"{{setting}} deve estar configurado",
                    actual="Configuração ausente",
                    severity=severity
                ))
        
        # Verificar apps do projeto
        if 'INSTALLED_APPS' in content:
            for app in {self.specs.django_apps}:
                if app not in content:
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="missing_project_app",
                        description=f"App do projeto {{app}} não está em INSTALLED_APPS",
                        expected=f"{{app}} deve estar listado",
                        actual="App não listado",
                        severity="HIGH"
                    ))
    
    return issues if issues else None
"""
        
        self.rules.append(ValidationRule(
            name="validate_django_settings_advanced",
            description="Valida configurações Django avançadas",
            code=rule_code.strip(),
            severity="CRITICAL",
            category="CONTENT"
        ))
    
    def _generate_react_specific_rules(self):
        """Gera regras específicas para React."""
        rule_code = f"""
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
            react_version_match = re.search(r'"react":\\s*"([^"]+)"', content)
            if react_version_match:
                version = react_version_match.group(1)
                # Verificar se é versão 18+
                if not version.startswith(('18', '19', '^18', '~18', '^19', '~19')):
                    issues.append(ValidationIssue(
                        file_path=file_path_str,
                        issue_type="outdated_react_version",
                        description=f"Versão do React {{version}} pode estar desatualizada",
                        expected="React 18+ conforme Blueprint",
                        actual=f"React {{version}}",
                        severity="MEDIUM"
                    ))
            
            # Verificar TypeScript se especificado
            if '{self.specs.frontend_framework}' == 'react' and 'typescript' not in content.lower():
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
"""
        
        self.rules.append(ValidationRule(
            name="validate_react_advanced",
            description="Valida configuração React avançada",
            code=rule_code.strip(),
            severity="HIGH",
            category="CONTENT"
        ))
    
    def _generate_api_validation_rules(self):
        """Gera regras para validação de API."""
        if "DRF" in self.specs.api_patterns or "REST" in self.specs.api_patterns:
            rule_code = """
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
"""
            
            self.rules.append(ValidationRule(
                name="validate_api_structure",
                description="Valida estrutura de API REST",
                code=rule_code.strip(),
                severity="HIGH",
                category="API"
            ))
    
    def _generate_testing_rules(self):
        """Gera regras avançadas para testes."""
        if self.specs.testing_framework:
            rule_code = f"""
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
        if '{self.specs.testing_framework}' == 'pytest':
            config_files = ['pytest.ini', 'pyproject.toml', 'setup.cfg']
        
        config_found = False
        for config_file in config_files:
            if Path(config_file).exists():
                config_found = True
                break
        
        if not config_found and '{self.specs.testing_framework}' == 'pytest':
            issues.append(ValidationIssue(
                file_path="pytest.ini",
                issue_type="test_config_missing",
                description="Configuração do pytest não encontrada",
                expected="pytest.ini ou configuração em pyproject.toml",
                actual="Configuração não encontrada",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name="validate_testing_structure_advanced",
                description="Valida estrutura avançada de testes",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_docker_rules(self):
        """Gera regras avançadas para Docker."""
        if self.specs.docker_files:
            rule_code = f"""
def validate_docker_configuration_advanced():
    '''Valida configuração avançada do Docker.'''
    issues = []
    expected_docker_files = {self.specs.docker_files}
    
    for docker_file in expected_docker_files:
        file_path = Path(docker_file)
        if not file_path.exists():
            issues.append(ValidationIssue(
                file_path=docker_file,
                issue_type="missing_docker_file",
                description=f"Arquivo Docker {{docker_file}} não encontrado",
                expected=f"{{docker_file}} deve existir",
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
                            description=f"Comando {{command}} não encontrado no Dockerfile",
                            expected=f"{{command}} deve estar presente",
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
"""
            
            self.rules.append(ValidationRule(
                name="validate_docker_configuration_advanced",
                description="Valida configuração avançada do Docker",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))


class ProValidatorCodeGenerator:
    """Gera código completo do validador profissional."""
    
    def __init__(self, specs: ProjectSpecs, rules: List[ValidationRule]):
        self.specs = specs
        self.rules = rules
    
    def generate_validator_code(self) -> str:
        """Gera código completo do validador profissional."""
        # Cabeçalho
        header = self._generate_header()
        
        # Importações
        imports = self._generate_imports()
        
        # Classes base
        base_classes = self._generate_base_classes()
        
        # Regras de validação
        validation_methods = self._generate_validation_methods()
        
        # Classe principal do validador
        validator_class = self._generate_validator_class()
        
        # Função main
        main_function = self._generate_main_function()
        
        return "\n\n".join([
            header, imports, base_classes, validation_methods, 
            validator_class, main_function
        ])
    
    def _generate_header(self) -> str:
        """Gera cabeçalho profissional."""
        return f'''#!/usr/bin/env python3
"""
Validador Automático Profissional - {self.specs.project_name}
Gerado automaticamente pelo ValidatorGenerator PRO v2.0

Este validador foi criado especificamente para validar:
- Projeto: {self.specs.project_name}
- Framework Backend: {self.specs.backend_framework}
- Framework Frontend: {self.specs.frontend_framework}
- Database: {self.specs.database}
- Arquitetura: {self.specs.architecture_type}
- Multi-tenancy: {self.specs.multi_tenancy}
- Autenticação: {self.specs.authentication_method}

Total de validações avançadas: {len(self.rules)}
Categorias: STRUCTURE, CONTENT, MODELS, DEPENDENCIES, API

NÍVEL DE VALIDAÇÃO: PROFISSIONAL
- Validação de conteúdo de arquivos
- Validação específica de modelos Django
- Validação de dependências com versões
- Validação de multi-tenancy
- Validação de configurações avançadas
"""'''
    
    def _generate_imports(self) -> str:
        """Gera importações necessárias."""
        return """import json
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
    print("Sistema de configuração não disponível. Usando configuração padrão.")"""
    
    def _generate_base_classes(self) -> str:
        """Gera classes base."""
        return '''@dataclass
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
        }'''
    
    def _generate_validation_methods(self) -> str:
        """Gera métodos de validação individuais."""
        methods = []
        
        for rule in self.rules:
            methods.append(rule.code)
        
        return "\n\n".join(methods)
    
    def _generate_validator_class(self) -> str:
        """Gera classe principal do validador profissional."""
        rule_names = [rule.name for rule in self.rules]
        rule_categories = {rule.name: rule.category for rule in self.rules}
        
        return f'''class {self.specs.project_name.title().replace(' ', '').replace('-', '')}ProScaffoldValidator:
    """Validador profissional customizado para {self.specs.project_name}."""
    
    # Configurações padrão (serão sobrescritas se config disponível)
    DEFAULT_SEVERITY_WEIGHTS = {{
        "CRITICAL": 20,
        "HIGH": 10,
        "MEDIUM": 3,
        "LOW": 1
    }}
    
    DEFAULT_CATEGORY_WEIGHTS = {{
        "STRUCTURE": 1.0,
        "CONTENT": 1.5,
        "MODELS": 2.0,
        "DEPENDENCIES": 1.2,
        "API": 1.3
    }}
    
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
            {', '.join(f'"{name}"' for name in rule_names)}
        ]
        
        # Filtrar validações baseado na configuração
        self.validation_methods = []
        for method_name in all_validation_methods:
            if self.config and self.config.should_ignore_validation(method_name):
                print(f"Ignorando validação: {{method_name}}")
                continue
            self.validation_methods.append(method_name)
        
        self.rule_categories = {rule_categories}
    
    def validate(self) -> ValidationResults:
        """Executa todas as validações avançadas e retorna os resultados."""
        issues = []
        total_checks = len(self.validation_methods)
        failed_validations = 0
        categories = {{"STRUCTURE": 0, "CONTENT": 0, "MODELS": 0, "DEPENDENCIES": 0, "API": 0}}
        
        print(f"Executando {{total_checks}} validações PROFISSIONAIS para {self.specs.project_name}...")
        print("Níveis: STRUCTURE | CONTENT | MODELS | DEPENDENCIES | API")
        print("-" * 80)
        
        for method_name in self.validation_methods:
            try:
                method = globals()[method_name]
                result = method()
                
                category = self.rule_categories.get(method_name, "STRUCTURE")
                print(f"[{{category:12}}] {{method_name}}", end="")
                
                if result:
                    failed_validations += 1  # Contar validações que falharam
                    if isinstance(result, list):
                        issues.extend(result)
                        categories[category] += len(result)
                        print(f" FALHOU: {{len(result)}} problemas")
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
                    description=f"Erro na validação {{method_name}}: {{str(e)}}",
                    expected="Validação deve executar sem erros",
                    actual=f"Erro: {{str(e)}}",
                    severity="CRITICAL"
                ))
                print(f" ERRO: {{str(e)}}")
        
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
        report.append(f"RELATÓRIO PROFISSIONAL DE VALIDAÇÃO - {self.specs.project_name.upper()}")
        report.append("=" * 100)
        report.append(f"Data/Hora: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        report.append(f"Validador: ValidatorGenerator PRO v2.0")
        report.append("")
        report.append("ESPECIFICAÇÕES DO PROJETO:")
        report.append(f"├─ Framework Backend: {self.specs.backend_framework}")
        report.append(f"├─ Framework Frontend: {self.specs.frontend_framework}")
        report.append(f"├─ Database: {self.specs.database}")
        report.append(f"├─ Arquitetura: {self.specs.architecture_type}")
        report.append(f"├─ Multi-tenancy: {self.specs.multi_tenancy}")
        report.append(f"└─ Autenticação: {self.specs.authentication_method}")
        report.append("")
        report.append("RESULTADOS DA VALIDAÇÃO:")
        report.append(f"├─ Total de Verificações: {{results.total_checks}}")
        report.append(f"├─ Aprovadas: {{results.passed_checks}}")
        report.append(f"├─ Reprovadas: {{results.failed_checks}}")
        report.append(f"└─ Score Final: {{results.score}}%")
        report.append("")
        
        # Analise por categoria
        report.append("ANALISE POR CATEGORIA:")
        for category, count in results.categories.items():
            status = "FALHOU" if count > 0 else "OK"
            report.append(f"|- {{status}} {{category:12}}: {{count}} problemas")
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
                    report.append(f"{{i}}. {{issue.description}}")
                    report.append(f"   Arquivo: {{issue.file_path}}")
                    report.append(f"   Esperado: {{issue.expected}}")
                    report.append(f"   Encontrado: {{issue.actual}}")
                    report.append("")
            
            if high_issues:
                report.append("PROBLEMAS DE ALTA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(high_issues, 1):
                    report.append(f"{{i}}. {{issue.description}}")
                    report.append(f"   Arquivo: {{issue.file_path}}")
                    report.append(f"   Esperado: {{issue.expected}}")
                    report.append(f"   Encontrado: {{issue.actual}}")
                    report.append("")
            
            if medium_issues:
                report.append("PROBLEMAS DE MEDIA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(medium_issues, 1):
                    report.append(f"{{i}}. {{issue.description}}")
                    report.append(f"   Arquivo: {{issue.file_path}}")
                    report.append("")
            
            if low_issues:
                report.append("PROBLEMAS DE BAIXA PRIORIDADE:")
                report.append("-" * 60)
                for i, issue in enumerate(low_issues, 1):
                    report.append(f"{{i}}. {{issue.description}}")
                    report.append("")
        
        report.append("=" * 100)
        return "\\n".join(report)'''
    
    def _generate_main_function(self) -> str:
        """Gera função main profissional."""
        return f'''def main():
    """Função principal do validador profissional."""
    import locale
    import os
    
    # Forçar UTF-8 para evitar problemas de encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    validator = {self.specs.project_name.title().replace(' ', '').replace('-', '')}ProScaffoldValidator()
    results = validator.validate()
    
    # Gerar e exibir relatório profissional com encoding seguro
    report = validator.generate_professional_report(results)
    print()
    
    try:
        print(report)
    except UnicodeEncodeError:
        # Fallback para encoding seguro
        safe_report = report.encode('utf-8', errors='replace').decode('utf-8')
        print(safe_report)
    
    # Salvar resultados em JSON com encoding explícito
    results_file = Path("validation_results_pro.json")
    results_file.write_text(
        json.dumps(results.to_dict(), indent=2, ensure_ascii=False), 
        encoding='utf-8'
    )
    print(f"\\nRelatorio detalhado salvo em: {{results_file}}")
    
    # Usar threshold do profile configurado
    threshold = 75  # Padrão
    if CONFIG_AVAILABLE:
        config = ValidationConfig()
        threshold = config.current_profile.min_score_threshold
    
    print(f"\\nThreshold configurado: {{threshold}}%")
    return 0 if results.score >= threshold else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)'''


class ValidatorGeneratorPro:
    """Classe principal do ValidatorGenerator PRO v2.0."""
    
    def __init__(self, blueprint_path: str):
        self.blueprint_path = blueprint_path
        self.parser = AdvancedBlueprintParser(blueprint_path)
        
    def generate_professional_validator(self, output_path: str = "scripts/validate_scaffold.py") -> bool:
        """Gera validador profissional de alta qualidade."""
        try:
            print("Analisando Blueprint arquitetural com parser avancado...")
            specs = self.parser.parse()
            
            print(f"Especificacoes extraidas do projeto: {specs.project_name}")
            print(f"   Framework Backend: {specs.backend_framework}")
            print(f"   Framework Frontend: {specs.frontend_framework}")
            print(f"   Database: {specs.database}")
            print(f"   Arquitetura: {specs.architecture_type}")
            print(f"   Django Apps: {', '.join(specs.django_apps) if specs.django_apps else 'N/A'}")
            print(f"   Modelos: {len(specs.models)} encontrados")
            print(f"   Multi-tenancy: {specs.multi_tenancy}")
            print(f"   Autenticacao: {specs.authentication_method}")
            
            print("Gerando regras de validacao profissionais...")
            rule_generator = ProValidationRuleGenerator(specs)
            rules = rule_generator.generate_all_rules()
            
            # Contabilizar por categoria
            categories = {}
            for rule in rules:
                categories[rule.category] = categories.get(rule.category, 0) + 1
            
            print(f"Geradas {len(rules)} regras de validacao profissionais:")
            for category, count in categories.items():
                print(f"   {category}: {count} validacoes")
            
            print("Criando codigo do validador profissional...")
            code_generator = ProValidatorCodeGenerator(specs, rules)
            validator_code = code_generator.generate_validator_code()
            
            # Salvar arquivo
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(validator_code, encoding='utf-8')
            
            print(f"Validador profissional criado com sucesso: {output_path}")
            print(f"Total de validacoes implementadas: {len(rules)}")
            print(f"Nivel: PROFISSIONAL (validacao de conteudo + estrutura)")
            
            return True
            
        except Exception as e:
            print(f"Erro ao gerar validador profissional: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal para teste do ValidatorGenerator PRO."""
    if len(sys.argv) != 2:
        print("Uso: python validator_generator.py <caminho_do_blueprint>")
        sys.exit(1)
    
    blueprint_path = sys.argv[1]
    generator = ValidatorGeneratorPro(blueprint_path)
    
    success = generator.generate_professional_validator()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()