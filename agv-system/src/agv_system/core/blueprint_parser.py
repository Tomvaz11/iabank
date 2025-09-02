#!/usr/bin/env python3
"""
AdvancedBlueprintParser - Parser inteligente para extrair especificações do Blueprint AGV.
Componente core reutilizável para todos os geradores de validação.
"""

import re
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


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
            
            # Calcula o nível baseado na indentação total (espaços + símbolos)
            indent_match = re.match(r'^(\s*[├└│─\s]*)', line)
            total_indent = len(indent_match.group(1)) if indent_match else 0
            
            # Calcula nível baseado na indentação total em múltiplos de 4
            indent_level = total_indent // 4
            
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
                # Ajusta current_path para o nível correto
                current_path = current_path[:indent_level]
                
                # Adiciona à estrutura
                current_dict = structure
                for path_part in current_path:
                    if path_part in current_dict and isinstance(current_dict[path_part], dict):
                        current_dict = current_dict[path_part]
                
                if clean_line.endswith('/'):
                    # Diretório
                    dir_name = clean_line.rstrip('/')
                    if dir_name and (dir_name.replace('.', '').replace('_', '').replace('-', '').isalnum() or dir_name.startswith('.')):
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