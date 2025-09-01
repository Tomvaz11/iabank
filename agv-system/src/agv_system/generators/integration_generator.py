#!/usr/bin/env python3
"""
IntegrationGenerator - Gerador especializado para validação de paradas de testes de integração (T1-T8).
Foco em validar colaboração entre módulos, interfaces e integrações do sistema.
"""

from typing import List, Dict, Any
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.base_generator import BaseGenerator
from core.validation_rules import ValidationRule
from core.blueprint_parser import ProjectSpecs


class IntegrationGenerator(BaseGenerator):
    """Gerador especializado para validação de testes de integração (T1-T8)."""
    
    def __init__(self, specs: ProjectSpecs, integration_phase: str, integration_context: Dict[str, Any] = None):
        super().__init__(specs)
        self.integration_phase = integration_phase  # T1, T2, etc.
        self.integration_context = integration_context or {}
        
    def generate_rules(self) -> List[ValidationRule]:
        """Gera regras específicas para uma fase de integração."""
        self.rules = []
        
        # Validações de integração entre módulos
        self._generate_module_integration_rules()
        
        # Validações de interfaces e contratos
        self._generate_interface_validation_rules()
        
        # Validações de comunicação entre componentes
        self._generate_component_communication_rules()
        
        # Validações de banco de dados e migrações
        self._generate_database_integration_rules()
        
        # Validações de APIs e endpoints
        self._generate_api_integration_rules()
        
        # Validações de testes de integração
        self._generate_integration_test_rules()
        
        # Validações de configurações de integração
        self._generate_integration_config_rules()
        
        return self.rules
    
    def _generate_module_integration_rules(self):
        """Gera regras para validar integração entre módulos."""
        modules = self.integration_context.get('modules', [])
        
        if modules:
            rule_code = f"""
def validate_{self.integration_phase.lower()}_module_integration():
    '''Valida integração entre módulos na fase {self.integration_phase}.'''
    issues = []
    modules = {modules}
    
    # Verificar se todos os módulos existem
    for module in modules:
        module_paths = (
            list(Path('.').rglob(f'**/{module}/__init__.py')) +
            list(Path('.').rglob(f'**/{module}.py'))
        )
        
        if not module_paths:
            issues.append(ValidationIssue(
                file_path=f"{module}/",
                issue_type="missing_integration_module",
                description=f"Módulo {{module}} da fase {self.integration_phase} não encontrado",
                expected=f"Módulo {{module}} deve existir",
                actual="Módulo não existe",
                severity="HIGH"
            ))
            continue
            
        # Verificar imports entre módulos
        for module_path in module_paths:
            if module_path.exists():
                content = module_path.read_text(encoding='utf-8', errors='ignore')
                
                # Contar importações de outros módulos da integração
                other_modules = [m for m in modules if m != module]
                import_count = 0
                
                for other_module in other_modules:
                    if f'from {other_module}' in content or f'import {other_module}' in content:
                        import_count += 1
                
                # Se há múltiplos módulos mas poucas integrações, pode ser problema
                if len(other_modules) > 1 and import_count == 0:
                    issues.append(ValidationIssue(
                        file_path=str(module_path),
                        issue_type="missing_module_integration",
                        description=f"Módulo {{module}} não integra com outros módulos",
                        expected="Integração com outros módulos",
                        actual="Nenhuma integração encontrada",
                        severity="MEDIUM"
                    ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{self.integration_phase.lower()}_module_integration",
                description=f"Valida integração entre módulos na fase {self.integration_phase}",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_interface_validation_rules(self):
        """Gera regras para validar interfaces e contratos."""
        interfaces = self.integration_context.get('interfaces', [])
        contracts = self.integration_context.get('contracts', [])
        
        if interfaces or contracts:
            rule_code = f"""
def validate_{self.integration_phase.lower()}_interfaces():
    '''Valida interfaces e contratos da fase {self.integration_phase}.'''
    issues = []
    interfaces = {interfaces}
    contracts = {contracts}
    
    # Verificar definições de interfaces
    python_files = list(Path('.').rglob('**/*.py'))
    found_interfaces = set()
    
    for py_file in python_files:
        if py_file.exists():
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            
            # Buscar classes abstratas ou interfaces
            for interface in interfaces:
                if f'class {interface}' in content:
                    found_interfaces.add(interface)
                    
                    # Verificar se é abstrata (ABC)
                    if 'ABC' not in content and '@abstractmethod' not in content:
                        issues.append(ValidationIssue(
                            file_path=str(py_file),
                            issue_type="interface_not_abstract",
                            description=f"Interface {{interface}} deveria ser abstrata",
                            expected="Interface deve herdar de ABC ou usar @abstractmethod",
                            actual="Interface não é abstrata",
                            severity="MEDIUM"
                        ))
    
    # Verificar interfaces não encontradas
    missing_interfaces = set(interfaces) - found_interfaces
    for missing_interface in missing_interfaces:
        issues.append(ValidationIssue(
            file_path="interfaces/",
            issue_type="missing_interface",
            description=f"Interface {{missing_interface}} da fase {self.integration_phase} não encontrada",
            expected=f"Interface {{missing_interface}} deve estar definida",
            actual="Interface não existe",
            severity="HIGH"
        ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{self.integration_phase.lower()}_interfaces",
                description=f"Valida interfaces e contratos da fase {self.integration_phase}",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_component_communication_rules(self):
        """Gera regras para validar comunicação entre componentes."""
        communication_patterns = self.integration_context.get('communication_patterns', [])
        
        if communication_patterns:
            rule_code = f"""
def validate_{self.integration_phase.lower()}_communication():
    '''Valida padrões de comunicação da fase {self.integration_phase}.'''
    issues = []
    patterns = {communication_patterns}
    
    # Verificar padrões de comunicação
    python_files = list(Path('.').rglob('**/*.py'))
    
    for pattern in patterns:
        pattern_found = False
        
        for py_file in python_files:
            if py_file.exists():
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                # Verificar padrões específicos
                if pattern == 'signal':
                    if 'django.dispatch' in content or '@receiver' in content:
                        pattern_found = True
                elif pattern == 'event':
                    if 'Event' in content and 'trigger' in content:
                        pattern_found = True
                elif pattern == 'message_queue':
                    if 'celery' in content or 'queue' in content:
                        pattern_found = True
                elif pattern == 'api_call':
                    if 'requests.' in content or 'httpx.' in content:
                        pattern_found = True
        
        if not pattern_found:
            issues.append(ValidationIssue(
                file_path="components/",
                issue_type="missing_communication_pattern",
                description=f"Padrão de comunicação {{pattern}} não encontrado na fase {self.integration_phase}",
                expected=f"Padrão {{pattern}} deve estar implementado",
                actual="Padrão não encontrado",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{self.integration_phase.lower()}_communication",
                description=f"Valida comunicação entre componentes da fase {self.integration_phase}",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="STRUCTURE"
            ))
    
    def _generate_database_integration_rules(self):
        """Gera regras para validar integrações de banco de dados."""
        db_operations = self.integration_context.get('database_operations', [])
        
        if db_operations:
            rule_code = f"""
def validate_{self.integration_phase.lower()}_database_integration():
    '''Valida integrações de banco de dados da fase {self.integration_phase}.'''
    issues = []
    db_operations = {db_operations}
    
    # Verificar migrações para a integração
    migration_dirs = list(Path('.').rglob('**/migrations/'))
    migration_files = []
    
    for migration_dir in migration_dirs:
        migration_files.extend(list(migration_dir.rglob('*.py')))
    
    if not migration_files:
        issues.append(ValidationIssue(
            file_path="migrations/",
            issue_type="missing_integration_migrations",
            description=f"Nenhuma migração encontrada para fase {self.integration_phase}",
            expected="Migrações devem existir para integração",
            actual="Migrações não encontradas",
            severity="HIGH"
        ))
        return issues
    
    # Verificar operações específicas nas migrações
    all_migration_content = ""
    for migration_file in migration_files:
        if migration_file.exists():
            all_migration_content += migration_file.read_text(encoding='utf-8', errors='ignore')
    
    for operation in db_operations:
        if operation == 'create_table' and 'CreateModel' not in all_migration_content:
            issues.append(ValidationIssue(
                file_path="migrations/",
                issue_type="missing_table_creation",
                description=f"Operação de criação de tabela não encontrada na fase {self.integration_phase}",
                expected="CreateModel deve estar nas migrações",
                actual="Operação não encontrada",
                severity="MEDIUM"
            ))
        elif operation == 'add_field' and 'AddField' not in all_migration_content:
            issues.append(ValidationIssue(
                file_path="migrations/",
                issue_type="missing_field_addition",
                description=f"Operação de adição de campo não encontrada na fase {self.integration_phase}",
                expected="AddField deve estar nas migrações",
                actual="Operação não encontrada",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{self.integration_phase.lower()}_database_integration",
                description=f"Valida integrações de banco de dados da fase {self.integration_phase}",
                code=rule_code.strip(),
                severity="HIGH",
                category="MODELS"
            ))
    
    def _generate_api_integration_rules(self):
        """Gera regras para validar integração de APIs."""
        api_endpoints = self.integration_context.get('api_endpoints', [])
        external_apis = self.integration_context.get('external_apis', [])
        
        if api_endpoints:
            rule_code = f"""
def validate_{self.integration_phase.lower()}_api_integration():
    '''Valida integração de APIs da fase {self.integration_phase}.'''
    issues = []
    api_endpoints = {api_endpoints}
    external_apis = {external_apis or []}
    
    # Verificar endpoints internos
    urls_files = list(Path('.').rglob('**/urls.py'))
    all_urls_content = ""
    
    for urls_file in urls_files:
        if urls_file.exists():
            all_urls_content += urls_file.read_text(encoding='utf-8', errors='ignore')
    
    for endpoint in api_endpoints:
        if endpoint not in all_urls_content:
            issues.append(ValidationIssue(
                file_path="urls.py",
                issue_type="missing_api_endpoint",
                description=f"Endpoint {{endpoint}} da fase {self.integration_phase} não encontrado",
                expected=f"Endpoint {{endpoint}} deve estar configurado",
                actual="Endpoint não encontrado",
                severity="HIGH"
            ))
    
    # Verificar integrações com APIs externas
    python_files = list(Path('.').rglob('**/*.py'))
    
    for external_api in external_apis:
        api_found = False
        
        for py_file in python_files:
            if py_file.exists():
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if external_api.lower() in content.lower():
                    api_found = True
                    break
        
        if not api_found:
            issues.append(ValidationIssue(
                file_path="integrations/",
                issue_type="missing_external_api_integration",
                description=f"Integração com API externa {{external_api}} não encontrada na fase {self.integration_phase}",
                expected=f"Integração com {{external_api}} deve existir",
                actual="Integração não encontrada",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{self.integration_phase.lower()}_api_integration",
                description=f"Valida integração de APIs da fase {self.integration_phase}",
                code=rule_code.strip(),
                severity="HIGH",
                category="API"
            ))
    
    def _generate_integration_test_rules(self):
        """Gera regras específicas para testes de integração."""
        test_scenarios = self.integration_context.get('test_scenarios', [])
        
        rule_code = f"""
def validate_{self.integration_phase.lower()}_integration_tests():
    '''Valida testes de integração da fase {self.integration_phase}.'''
    issues = []
    test_scenarios = {test_scenarios}
    
    # Buscar arquivos de teste de integração
    integration_test_files = (
        list(Path('.').rglob('**/test_integration*.py')) +
        list(Path('.').rglob('**/integration_test*.py')) +
        list(Path('.').rglob('**/tests/integration/*.py'))
    )
    
    if not integration_test_files:
        issues.append(ValidationIssue(
            file_path="tests/integration/",
            issue_type="missing_integration_tests",
            description=f"Nenhum teste de integração encontrado para fase {self.integration_phase}",
            expected="Testes de integração devem existir",
            actual="Testes não encontrados",
            severity="HIGH"
        ))
        return issues
    
    # Verificar cenários específicos
    all_test_content = ""
    for test_file in integration_test_files:
        if test_file.exists():
            all_test_content += test_file.read_text(encoding='utf-8', errors='ignore')
    
    for scenario in test_scenarios:
        scenario_patterns = [
            f'test_{{scenario.lower()}}',
            f'Test{{scenario.title()}}',
            scenario.lower().replace(' ', '_')
        ]
        
        scenario_found = any(pattern in all_test_content for pattern in scenario_patterns)
        
        if not scenario_found:
            issues.append(ValidationIssue(
                file_path="tests/integration/",
                issue_type="missing_test_scenario",
                description=f"Cenário de teste {{scenario}} não encontrado na fase {self.integration_phase}",
                expected=f"Teste para cenário {{scenario}} deve existir",
                actual="Cenário não testado",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
        
        self.rules.append(ValidationRule(
            name=f"validate_{self.integration_phase.lower()}_integration_tests",
            description=f"Valida testes de integração da fase {self.integration_phase}",
            code=rule_code.strip(),
            severity="HIGH",
            category="CONTENT"
        ))
    
    def _generate_integration_config_rules(self):
        """Gera regras para validar configurações específicas de integração."""
        config_keys = self.integration_context.get('config_keys', [])
        
        if config_keys:
            rule_code = f"""
def validate_{self.integration_phase.lower()}_configuration():
    '''Valida configurações específicas da fase {self.integration_phase}.'''
    issues = []
    config_keys = {config_keys}
    
    # Verificar em settings.py
    settings_files = list(Path('.').rglob('**/settings.py'))
    
    for settings_file in settings_files:
        if settings_file.exists():
            content = settings_file.read_text(encoding='utf-8', errors='ignore')
            
            for config_key in config_keys:
                if config_key not in content:
                    issues.append(ValidationIssue(
                        file_path=str(settings_file),
                        issue_type="missing_integration_config",
                        description=f"Configuração {{config_key}} da fase {self.integration_phase} não encontrada",
                        expected=f"{{config_key}} deve estar configurado",
                        actual="Configuração ausente",
                        severity="MEDIUM"
                    ))
    
    # Verificar variáveis de ambiente
    env_files = list(Path('.').rglob('**/.env*'))
    
    if env_files:
        for env_file in env_files:
            if env_file.exists():
                content = env_file.read_text(encoding='utf-8', errors='ignore')
                
                for config_key in config_keys:
                    # Buscar por variáveis de ambiente relacionadas
                    env_var_pattern = f'{config_key.upper()}_'
                    if config_key.upper() not in content and env_var_pattern not in content:
                        issues.append(ValidationIssue(
                            file_path=str(env_file),
                            issue_type="missing_env_config",
                            description=f"Variável de ambiente para {{config_key}} pode estar faltando",
                            expected=f"Variável relacionada a {{config_key}} deve existir",
                            actual="Variável não encontrada",
                            severity="LOW"
                        ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name=f"validate_{self.integration_phase.lower()}_configuration",
                description=f"Valida configurações da fase {self.integration_phase}",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="CONTENT"
            ))