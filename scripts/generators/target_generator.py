#!/usr/bin/env python3
"""
TargetGenerator - Gerador especializado para validação de alvos específicos (Alvos 1-N).
Foco em implementações específicas de funcionalidades conforme Blueprint.
"""

from typing import List, Dict, Any
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.base_generator import BaseGenerator
from core.validation_rules import ValidationRule
from core.blueprint_parser import ProjectSpecs


class TargetGenerator(BaseGenerator):
    """Gerador especializado para validação de alvos específicos (Alvos 1-N)."""
    
    def __init__(self, specs: ProjectSpecs, target_number: int, target_context: Dict[str, Any] = None):
        super().__init__(specs)
        self.target_number = target_number
        self.target_context = target_context or {}
        
    def generate_rules(self) -> List[ValidationRule]:
        """Gera regras específicas para um alvo particular."""
        self.rules = []
        
        # Se não temos contexto específico, gerar contexto baseado no número do alvo
        if not self.target_context or not any(self.target_context.values()):
            self._infer_target_context_from_specs()
        
        # Validações específicas do alvo
        self._generate_target_specific_rules()
        
        # Validações de modelos relacionados ao alvo
        self._generate_target_model_rules()
        
        # Validações de APIs relacionadas ao alvo  
        self._generate_target_api_rules()
        
        # Validações de templates/views relacionadas
        self._generate_target_view_rules()
        
        # Validações de testes específicos do alvo
        self._generate_target_test_rules()
        
        # Validações de migração/banco de dados se aplicável
        self._generate_target_migration_rules()
        
        # Validações de configurações específicas
        self._generate_target_config_rules()
        
        return self.rules
    
    def _infer_target_context_from_specs(self):
        """Infere contexto do alvo baseado no Blueprint e número do alvo."""
        # Criar contexto baseado no que sabemos sobre o projeto
        models_list = list(self.specs.models.keys()) if self.specs.models else []
        
        # Distribuir modelos pelos alvos de forma inteligente
        if models_list:
            models_per_target = max(1, len(models_list) // 8)  # Assumindo até 8 alvos
            start_idx = (self.target_number - 1) * models_per_target
            end_idx = min(start_idx + models_per_target, len(models_list))
            target_models = models_list[start_idx:end_idx]
        else:
            target_models = []
        
        # Definir contexto baseado no número do alvo e tipo de sistema
        self.target_context = {
            'models': target_models,
            'views': self._infer_target_views(),
            'urls': self._infer_target_urls(), 
            'files': self._infer_target_files(),
            'templates': self._infer_target_templates(),
            'components': self._infer_target_components(),
            'settings': self._infer_target_settings()
        }
    
    def _infer_target_views(self):
        """Infere views baseado no tipo de alvo."""
        if self.target_number <= 3:  # Alvos iniciais: autenticação/usuários
            return ['LoginView', 'RegisterView', 'UserProfileView']
        elif self.target_number <= 5:  # Alvos de negócio
            if 'finance' in self.specs.django_apps:
                return ['LoanListView', 'LoanDetailView', 'TransactionView']
            else:
                return ['DashboardView', 'ReportView']
        else:  # Alvos avançados
            return ['AdminView', 'AnalyticsView', 'ExportView']
    
    def _infer_target_urls(self):
        """Infere URLs baseado no tipo de alvo.""" 
        if self.target_number <= 3:
            return ['api/auth/', 'api/users/', 'api/profile/']
        elif self.target_number <= 5:
            if 'finance' in self.specs.django_apps:
                return ['api/loans/', 'api/transactions/']
            else:
                return ['api/dashboard/', 'api/reports/']
        else:
            return ['api/admin/', 'api/analytics/']
    
    def _infer_target_files(self):
        """Infere arquivos específicos baseado no alvo."""
        files = []
        
        # Arquivos baseados no Django app relacionado
        if self.target_number <= 3 and 'core' in self.specs.django_apps:
            files.extend(['core/views.py', 'core/serializers.py'])
        elif self.target_number <= 5 and 'finance' in self.specs.django_apps:
            files.extend(['finance/views.py', 'finance/serializers.py'])
        elif 'operations' in self.specs.django_apps:
            files.extend(['operations/views.py', 'operations/serializers.py'])
            
        return files
    
    def _infer_target_templates(self):
        """Infere templates baseado no alvo."""
        if self.specs.frontend_framework == 'react':
            return []  # React não usa templates Django
        else:
            if self.target_number <= 3:
                return ['login.html', 'register.html']
            else:
                return ['dashboard.html', 'report.html']
    
    def _infer_target_components(self):
        """Infere componentes React baseado no alvo."""
        if self.specs.frontend_framework != 'react':
            return []
            
        if self.target_number <= 3:
            return ['LoginForm', 'RegisterForm', 'UserProfile']
        elif self.target_number <= 5:
            return ['Dashboard', 'DataTable', 'FilterPanel']
        else:
            return ['AdminPanel', 'Analytics', 'ExportDialog']
    
    def _infer_target_settings(self):
        """Infere configurações específicas baseado no alvo."""
        settings = []
        
        if self.target_number <= 2:  # Alvos de autenticação
            if self.specs.authentication_method == 'JWT':
                settings.extend(['JWT_SECRET_KEY', 'JWT_EXPIRATION_DELTA'])
        elif self.target_number <= 4:  # Alvos de banco de dados
            if self.specs.database == 'postgresql':
                settings.extend(['DATABASES', 'DATABASE_URL'])
        
        return settings
    
    def _generate_target_specific_rules(self):
        """Gera regras específicas baseadas no contexto do alvo."""
        # Extrair informações específicas do contexto do alvo
        target_models = self.target_context.get('models', [])
        target_views = self.target_context.get('views', [])
        target_urls = self.target_context.get('urls', [])
        target_files = self.target_context.get('files', [])
        
        # Validação de existência de arquivos do alvo
        if target_files:
            rule_code = f"""
def validate_target_{self.target_number}_files():
    '''Valida arquivos específicos do Alvo {self.target_number}.'''
    issues = []
    required_files = {target_files}
    
    for required_file in required_files:
        file_paths = list(Path('.').rglob(f'**/{{required_file}}'))
        if not file_paths:
            issues.append(ValidationIssue(
                file_path=required_file,
                issue_type="missing_target_file",
                description=f"Arquivo do Alvo {self.target_number} não encontrado: {{required_file}}",
                expected=f"Arquivo {{required_file}} deve existir",
                actual="Arquivo não existe",
                severity="HIGH"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_files",
                description=f"Valida arquivos específicos do Alvo {self.target_number}",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_target_model_rules(self):
        """Gera regras para validação de modelos específicos do alvo."""
        target_models = self.target_context.get('models', [])
        
        for model_name in target_models:
            if model_name in self.specs.models:
                model_info = self.specs.models[model_name]
                rule_code = self._create_specific_model_validation(model_name, model_info)
                
                self.rules.append(ValidationRule(
                    name=f"validate_target_{self.target_number}_model_{model_name.lower()}",
                    description=f"Valida modelo {model_name} do Alvo {self.target_number}",
                    code=rule_code,
                    severity="HIGH",
                    category="MODELS"
                ))
        
        # Validação de relacionamentos entre modelos do alvo
        if len(target_models) > 1:
            rule_code = self._create_target_model_relationships_validation(target_models)
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_model_relationships",
                description=f"Valida relacionamentos entre modelos do Alvo {self.target_number}",
                code=rule_code,
                severity="MEDIUM",
                category="MODELS"
            ))
    
    def _generate_target_api_rules(self):
        """Gera regras para APIs específicas do alvo."""
        target_views = self.target_context.get('views', [])
        target_urls = self.target_context.get('urls', [])
        
        if target_views:
            rule_code = f"""
def validate_target_{self.target_number}_api_views():
    '''Valida views/APIs do Alvo {self.target_number}.'''
    issues = []
    required_views = {target_views}
    
    views_files = list(Path('.').rglob('**/views.py'))
    found_views = set()
    
    for views_file in views_files:
        if views_file.exists():
            content = views_file.read_text(encoding='utf-8', errors='ignore')
            
            for required_view in required_views:
                # Buscar definições de classe ou função
                class_pattern = rf'class {{required_view}}\\([^)]*\\):'
                func_pattern = rf'def {{required_view}}\\('
                
                if re.search(class_pattern, content) or re.search(func_pattern, content):
                    found_views.add(required_view)
    
    missing_views = set(required_views) - found_views
    for missing_view in missing_views:
        issues.append(ValidationIssue(
            file_path="views.py",
            issue_type="missing_target_view",
            description=f"View {{missing_view}} do Alvo {self.target_number} não encontrada",
            expected=f"View {{missing_view}} deve estar implementada",
            actual="View não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_api_views",
                description=f"Valida views/APIs do Alvo {self.target_number}",
                code=rule_code.strip(),
                severity="HIGH",
                category="API"
            ))
        
        if target_urls:
            rule_code = self._create_target_urls_validation(target_urls)
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_urls",
                description=f"Valida URLs do Alvo {self.target_number}",
                code=rule_code,
                severity="MEDIUM",
                category="API"
            ))
    
    def _generate_target_view_rules(self):
        """Gera regras para templates e views frontend."""
        target_templates = self.target_context.get('templates', [])
        target_components = self.target_context.get('components', [])
        
        if target_templates:
            rule_code = f"""
def validate_target_{self.target_number}_templates():
    '''Valida templates do Alvo {self.target_number}.'''
    issues = []
    required_templates = {target_templates}
    
    for required_template in required_templates:
        template_paths = list(Path('.').rglob(f'**/{required_template}'))
        if not template_paths:
            issues.append(ValidationIssue(
                file_path=required_template,
                issue_type="missing_target_template",
                description=f"Template do Alvo {self.target_number} não encontrado: {{required_template}}",
                expected=f"Template {{required_template}} deve existir",
                actual="Template não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_templates",
                description=f"Valida templates do Alvo {self.target_number}",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="CONTENT"
            ))
        
        if target_components:
            rule_code = self._create_target_components_validation(target_components)
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_components",
                description=f"Valida componentes React do Alvo {self.target_number}",
                code=rule_code,
                severity="MEDIUM",
                category="CONTENT"
            ))
    
    def _generate_target_test_rules(self):
        """Gera regras para testes específicos do alvo."""
        target_models = self.target_context.get('models', [])
        target_views = self.target_context.get('views', [])
        
        if target_models or target_views:
            rule_code = f"""
def validate_target_{self.target_number}_tests():
    '''Valida testes do Alvo {self.target_number}.'''
    issues = []
    
    # Buscar arquivos de teste
    test_files = list(Path('.').rglob('**/test*.py')) + list(Path('.').rglob('**/*_test.py'))
    
    if not test_files:
        issues.append(ValidationIssue(
            file_path="tests/",
            issue_type="missing_target_tests",
            description="Nenhum arquivo de teste encontrado para Alvo {self.target_number}",
            expected="Pelo menos um arquivo de teste deve existir",
            actual="Nenhum teste encontrado",
            severity="HIGH"
        ))
        return issues
    
    # Verificar se modelos têm testes
    target_models = {target_models}
    target_views = {target_views}
    
    all_test_content = ""
    for test_file in test_files:
        if test_file.exists():
            all_test_content += test_file.read_text(encoding='utf-8', errors='ignore')
    
    # Verificar testes para modelos
    for model in target_models:
        if model.lower() not in all_test_content.lower():
            issues.append(ValidationIssue(
                file_path="tests/",
                issue_type="missing_model_tests",
                description=f"Testes para modelo {{model}} do Alvo {self.target_number} não encontrados",
                expected=f"Testes para {{model}} devem existir",
                actual="Testes não encontrados",
                severity="MEDIUM"
            ))
    
    # Verificar testes para views
    for view in target_views:
        if view.lower() not in all_test_content.lower():
            issues.append(ValidationIssue(
                file_path="tests/",
                issue_type="missing_view_tests",
                description=f"Testes para view {{view}} do Alvo {self.target_number} não encontrados",
                expected=f"Testes para {{view}} devem existir",
                actual="Testes não encontrados",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_tests",
                description=f"Valida testes do Alvo {self.target_number}",
                code=rule_code.strip(),
                severity="HIGH",
                category="CONTENT"
            ))
    
    def _generate_target_migration_rules(self):
        """Gera regras para migrações relacionadas ao alvo."""
        target_models = self.target_context.get('models', [])
        
        if target_models:
            rule_code = f"""
def validate_target_{self.target_number}_migrations():
    '''Valida migrações para modelos do Alvo {self.target_number}.'''
    issues = []
    
    migration_dirs = list(Path('.').rglob('**/migrations/'))
    if not migration_dirs:
        issues.append(ValidationIssue(
            file_path="migrations/",
            issue_type="missing_migrations_dir",
            description="Diretório migrations não encontrado",
            expected="Diretório migrations/ deve existir",
            actual="Diretório não existe",
            severity="HIGH"
        ))
        return issues
    
    # Verificar se existem arquivos de migração
    migration_files = []
    for migration_dir in migration_dirs:
        migration_files.extend(list(migration_dir.rglob('*.py')))
    
    if not migration_files:
        issues.append(ValidationIssue(
            file_path="migrations/",
            issue_type="no_migration_files",
            description="Nenhum arquivo de migração encontrado para Alvo {self.target_number}",
            expected="Pelo menos um arquivo de migração deve existir",
            actual="Nenhuma migração encontrada",
            severity="MEDIUM"
        ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_migrations",
                description=f"Valida migrações do Alvo {self.target_number}",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="MODELS"
            ))
    
    def _generate_target_config_rules(self):
        """Gera regras para configurações específicas do alvo."""
        target_settings = self.target_context.get('settings', [])
        
        if target_settings:
            rule_code = f"""
def validate_target_{self.target_number}_settings():
    '''Valida configurações específicas do Alvo {self.target_number}.'''
    issues = []
    required_settings = {target_settings}
    
    settings_files = list(Path('.').rglob('**/settings.py'))
    
    for settings_file in settings_files:
        if settings_file.exists():
            content = settings_file.read_text(encoding='utf-8', errors='ignore')
            
            for required_setting in required_settings:
                if required_setting not in content:
                    issues.append(ValidationIssue(
                        file_path=str(settings_file),
                        issue_type="missing_target_setting",
                        description=f"Configuração {{required_setting}} do Alvo {self.target_number} não encontrada",
                        expected=f"{{required_setting}} deve estar configurado",
                        actual="Configuração ausente",
                        severity="MEDIUM"
                    ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_target_{self.target_number}_settings",
                description=f"Valida configurações do Alvo {self.target_number}",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="CONTENT"
            ))
    
    def _create_target_model_relationships_validation(self, target_models: List[str]) -> str:
        """Cria validação para relacionamentos entre modelos do alvo."""
        return f"""
def validate_target_{self.target_number}_model_relationships():
    '''Valida relacionamentos entre modelos do Alvo {self.target_number}.'''
    issues = []
    target_models = {target_models}
    
    models_files = list(Path('.').rglob('**/models.py'))
    
    for model_file in models_files:
        if model_file.exists():
            content = model_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar se relacionamentos estão implementados
            for model in target_models:
                # Buscar definição do modelo
                model_pattern = rf'class {model}\\([^)]*\\):(.*?)(?=^class |^def |\\Z)'
                model_match = re.search(model_pattern, content, re.MULTILINE | re.DOTALL)
                
                if model_match:
                    model_body = model_match.group(1)
                    
                    # Verificar se tem relacionamentos adequados
                    fk_count = len(re.findall(r'ForeignKey', model_body))
                    if fk_count == 0 and len(target_models) > 1:
                        # Se tem múltiplos modelos mas este não tem FK, pode ser um problema
                        issues.append(ValidationIssue(
                            file_path=str(model_file),
                            issue_type="missing_model_relationships",
                            description=f"Modelo {{model}} pode estar faltando relacionamentos",
                            expected="Relacionamentos adequados entre modelos",
                            actual="Poucos ou nenhum relacionamento encontrado",
                            severity="LOW"
                        ))
    
    return issues if issues else None
"""

    def _create_target_urls_validation(self, target_urls: List[str]) -> str:
        """Cria validação para URLs específicas do alvo."""
        return f"""
def validate_target_{self.target_number}_urls():
    '''Valida URLs do Alvo {self.target_number}.'''
    issues = []
    required_urls = {target_urls}
    
    urls_files = list(Path('.').rglob('**/urls.py'))
    all_urls_content = ""
    
    for urls_file in urls_files:
        if urls_file.exists():
            all_urls_content += urls_file.read_text(encoding='utf-8', errors='ignore')
    
    for required_url in required_urls:
        if required_url not in all_urls_content:
            issues.append(ValidationIssue(
                file_path="urls.py",
                issue_type="missing_target_url",
                description=f"URL {{required_url}} do Alvo {self.target_number} não encontrada",
                expected=f"URL {{required_url}} deve estar configurada",
                actual="URL não encontrada",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""

    def _create_target_components_validation(self, target_components: List[str]) -> str:
        """Cria validação para componentes React específicos do alvo."""
        return f"""
def validate_target_{self.target_number}_components():
    '''Valida componentes React do Alvo {self.target_number}.'''
    issues = []
    required_components = {target_components}
    
    for required_component in required_components:
        # Buscar arquivo do componente (.jsx, .tsx, .js, .ts)
        component_files = (
            list(Path('.').rglob(f'**/{{required_component}}.jsx')) +
            list(Path('.').rglob(f'**/{{required_component}}.tsx')) +
            list(Path('.').rglob(f'**/{{required_component}}.js')) +
            list(Path('.').rglob(f'**/{{required_component}}.ts'))
        )
        
        if not component_files:
            issues.append(ValidationIssue(
                file_path=f"{{required_component}}.jsx",
                issue_type="missing_target_component",
                description=f"Componente React {{required_component}} do Alvo {self.target_number} não encontrado",
                expected="Componente {{required_component}} deve existir",
                actual="Componente não existe",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""