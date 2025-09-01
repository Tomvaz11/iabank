#!/usr/bin/env python3
"""
EvolutionGenerator - Gerador especializado para validação de evolução e manutenção (F7-Evolucionista).
Foco em validar modificações, refatorações e melhorias em código existente.
"""

from typing import List, Dict, Any
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.base_generator import BaseGenerator
from core.validation_rules import ValidationRule
from core.blueprint_parser import ProjectSpecs


class EvolutionGenerator(BaseGenerator):
    """Gerador especializado para validação de evolução e manutenção (F7-Evolucionista)."""
    
    def __init__(self, specs: ProjectSpecs, evolution_context: Dict[str, Any] = None):
        super().__init__(specs)
        self.evolution_context = evolution_context or {}
        
    def generate_rules(self) -> List[ValidationRule]:
        """Gera regras específicas para evolução e manutenção."""
        self.rules = []
        
        # Validações de compatibilidade com código existente
        self._generate_backward_compatibility_rules()
        
        # Validações de refatoração segura
        self._generate_refactoring_safety_rules()
        
        # Validações de manutenção de testes
        self._generate_test_maintenance_rules()
        
        # Validações de performance e otimização
        self._generate_performance_rules()
        
        # Validações de documentação atualizada
        self._generate_documentation_update_rules()
        
        # Validações de versionamento e changelog
        self._generate_versioning_rules()
        
        # Validações de migração de dados
        self._generate_data_migration_rules()
        
        # Validações de configuração evolutiva
        self._generate_configuration_evolution_rules()
        
        return self.rules
    
    def _generate_backward_compatibility_rules(self):
        """Gera regras para validar compatibilidade com versões anteriores."""
        breaking_changes = self.evolution_context.get('breaking_changes', [])
        deprecated_features = self.evolution_context.get('deprecated_features', [])
        
        rule_code = f"""
def validate_backward_compatibility():
    '''Valida compatibilidade com versões anteriores após evolução.'''
    issues = []
    breaking_changes = {breaking_changes}
    deprecated_features = {deprecated_features}
    
    python_files = list(Path('.').rglob('**/*.py'))
    
    # Verificar se breaking changes estão documentados
    changelog_files = list(Path('.').rglob('**/CHANGELOG.md'))
    changelog_content = ""
    
    if changelog_files:
        for changelog in changelog_files:
            if changelog.exists():
                changelog_content += changelog.read_text(encoding='utf-8', errors='ignore')
    
    for breaking_change in breaking_changes:
        if breaking_change.lower() not in changelog_content.lower():
            issues.append(ValidationIssue(
                file_path="CHANGELOG.md",
                issue_type="undocumented_breaking_change",
                description=f"Breaking change não documentado: {{breaking_change}}",
                expected="Breaking changes devem estar documentados no CHANGELOG",
                actual="Change não documentado",
                severity="HIGH"
            ))
    
    # Verificar se features deprecated têm warnings
    for py_file in python_files:
        if py_file.exists():
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            
            for deprecated_feature in deprecated_features:
                if deprecated_feature in content:
                    # Verificar se há warning de depreciação próximo
                    lines = content.split('\\n')
                    for i, line in enumerate(lines):
                        if deprecated_feature in line:
                            # Verificar 5 linhas antes e depois
                            context_start = max(0, i - 5)
                            context_end = min(len(lines), i + 6)
                            context = '\\n'.join(lines[context_start:context_end])
                            
                            if 'deprecated' not in context.lower() and 'warning' not in context.lower():
                                issues.append(ValidationIssue(
                                    file_path=str(py_file),
                                    issue_type="missing_deprecation_warning",
                                    description=f"Feature deprecated sem warning: {{deprecated_feature}}",
                                    expected="Features deprecated devem ter warnings",
                                    actual="Warning não encontrado",
                                    severity="MEDIUM"
                                ))
    
    return issues if issues else None
"""
        
        self.rules.append(ValidationRule(
            name="validate_backward_compatibility",
            description="Valida compatibilidade com versões anteriores",
            code=rule_code.strip(),
            severity="HIGH",
            category="CONTENT"
        ))
    
    def _generate_refactoring_safety_rules(self):
        """Gera regras para validar segurança de refatorações."""
        refactored_components = self.evolution_context.get('refactored_components', [])
        
        if refactored_components:
            rule_code = f"""
def validate_refactoring_safety():
    '''Valida segurança das refatorações realizadas.'''
    issues = []
    refactored_components = {refactored_components}
    
    # Verificar se componentes refatorados mantêm interfaces públicas
    python_files = list(Path('.').rglob('**/*.py'))
    
    for component in refactored_components:
        component_found = False
        
        for py_file in python_files:
            if py_file.exists():
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                # Buscar definição do componente (classe ou função)
                if f'class {component}' in content or f'def {component}' in content:
                    component_found = True
                    
                    # Verificar se interface pública está preservada
                    # (métodos públicos não devem ter mudado)
                    public_methods = re.findall(r'def ([a-zA-Z][a-zA-Z0-9_]*)', content)
                    public_methods = [m for m in public_methods if not m.startswith('_')]
                    
                    if len(public_methods) == 0:
                        issues.append(ValidationIssue(
                            file_path=str(py_file),
                            issue_type="refactoring_removed_public_interface",
                            description=f"Componente {{component}} pode ter perdido interface pública",
                            expected="Interface pública deve ser preservada",
                            actual="Nenhum método público encontrado",
                            severity="HIGH"
                        ))
        
        if not component_found:
            issues.append(ValidationIssue(
                file_path="components/",
                issue_type="refactored_component_missing",
                description=f"Componente refatorado {{component}} não encontrado",
                expected="Componente deve existir após refatoração",
                actual="Componente não encontrado",
                severity="HIGH"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name="validate_refactoring_safety",
                description="Valida segurança das refatorações realizadas",
                code=rule_code.strip(),
                severity="HIGH",
                category="STRUCTURE"
            ))
    
    def _generate_test_maintenance_rules(self):
        """Gera regras para validar manutenção de testes."""
        modified_modules = self.evolution_context.get('modified_modules', [])
        
        rule_code = f"""
def validate_test_maintenance():
    '''Valida que testes foram mantidos/atualizados após evolução.'''
    issues = []
    modified_modules = {modified_modules}
    
    # Buscar arquivos de teste
    test_files = list(Path('.').rglob('**/test*.py')) + list(Path('.').rglob('**/*_test.py'))
    
    if not test_files:
        issues.append(ValidationIssue(
            file_path="tests/",
            issue_type="no_tests_found",
            description="Nenhum arquivo de teste encontrado após evolução",
            expected="Testes devem existir e ser mantidos",
            actual="Nenhum teste encontrado",
            severity="HIGH"
        ))
        return issues
    
    # Verificar se módulos modificados têm testes correspondentes
    all_test_content = ""
    for test_file in test_files:
        if test_file.exists():
            all_test_content += test_file.read_text(encoding='utf-8', errors='ignore')
    
    for modified_module in modified_modules:
        # Verificar se há testes para o módulo
        test_patterns = [
            f'test_{{modified_module.lower()}}',
            f'Test{{modified_module.title()}}',
            f'{{modified_module.lower()}}_test'
        ]
        
        module_tested = any(pattern in all_test_content.lower() for pattern in test_patterns)
        
        if not module_tested:
            issues.append(ValidationIssue(
                file_path="tests/",
                issue_type="missing_tests_for_modified_module",
                description=f"Módulo modificado {{modified_module}} sem testes correspondentes",
                expected="Módulos modificados devem ter testes atualizados",
                actual="Testes não encontrados",
                severity="HIGH"
            ))
    
    # Verificar cobertura de testes (se possível estimar)
    test_function_count = all_test_content.count('def test_')
    if test_function_count < len(modified_modules) * 2:  # Heurística: pelo menos 2 testes por módulo
        issues.append(ValidationIssue(
            file_path="tests/",
            issue_type="insufficient_test_coverage",
            description="Cobertura de testes pode ser insuficiente após evolução",
            expected="Cobertura adequada de testes",
            actual=f"Apenas {{test_function_count}} funções de teste encontradas",
            severity="MEDIUM"
        ))
    
    return issues if issues else None
"""
        
        self.rules.append(ValidationRule(
            name="validate_test_maintenance",
            description="Valida manutenção de testes após evolução",
            code=rule_code.strip(),
            severity="HIGH",
            category="CONTENT"
        ))
    
    def _generate_performance_rules(self):
        """Gera regras para validar melhorias de performance."""
        performance_optimizations = self.evolution_context.get('performance_optimizations', [])
        
        if performance_optimizations:
            rule_code = f"""
def validate_performance_improvements():
    '''Valida implementação de melhorias de performance.'''
    issues = []
    optimizations = {performance_optimizations}
    
    python_files = list(Path('.').rglob('**/*.py'))
    
    for optimization in optimizations:
        optimization_found = False
        
        for py_file in python_files:
            if py_file.exists():
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                # Verificar padrões de otimização
                if optimization == 'database_indexing':
                    if 'db_index=True' in content or 'Index(' in content:
                        optimization_found = True
                elif optimization == 'caching':
                    if '@cache' in content or 'cache.' in content:
                        optimization_found = True
                elif optimization == 'lazy_loading':
                    if 'select_related' in content or 'prefetch_related' in content:
                        optimization_found = True
                elif optimization == 'pagination':
                    if 'Paginator' in content or 'PageNumberPagination' in content:
                        optimization_found = True
                elif optimization == 'async_operations':
                    if 'async def' in content or 'await ' in content:
                        optimization_found = True
        
        if not optimization_found:
            issues.append(ValidationIssue(
                file_path="performance/",
                issue_type="missing_performance_optimization",
                description=f"Otimização de performance não implementada: {{optimization}}",
                expected=f"{{optimization}} deve estar implementado",
                actual="Otimização não encontrada",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name="validate_performance_improvements",
                description="Valida implementação de melhorias de performance",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="CONTENT"
            ))
    
    def _generate_documentation_update_rules(self):
        """Gera regras para validar atualização de documentação."""
        rule_code = """
def validate_documentation_updates():
    '''Valida que documentação foi atualizada após evolução.'''
    issues = []
    
    # Verificar README.md
    readme_files = list(Path('.').rglob('**/README.md'))
    if not readme_files:
        issues.append(ValidationIssue(
            file_path="README.md",
            issue_type="missing_readme",
            description="README.md não encontrado após evolução",
            expected="README.md deve existir e estar atualizado",
            actual="README não encontrado",
            severity="MEDIUM"
        ))
    
    # Verificar CHANGELOG.md
    changelog_files = list(Path('.').rglob('**/CHANGELOG.md'))
    if not changelog_files:
        issues.append(ValidationIssue(
            file_path="CHANGELOG.md",
            issue_type="missing_changelog",
            description="CHANGELOG.md não encontrado após evolução",
            expected="CHANGELOG.md deve existir para rastrear mudanças",
            actual="CHANGELOG não encontrado",
            severity="HIGH"
        ))
    else:
        # Verificar se CHANGELOG tem entradas recentes
        for changelog in changelog_files:
            if changelog.exists():
                content = changelog.read_text(encoding='utf-8', errors='ignore')
                
                # Heurística: deve ter pelo menos uma data recente ou "unreleased"
                recent_indicators = ['unreleased', '2024', '2025']
                has_recent = any(indicator.lower() in content.lower() for indicator in recent_indicators)
                
                if not has_recent:
                    issues.append(ValidationIssue(
                        file_path=str(changelog),
                        issue_type="outdated_changelog",
                        description="CHANGELOG parece desatualizado",
                        expected="CHANGELOG deve ter entradas recentes",
                        actual="Nenhuma entrada recente encontrada",
                        severity="MEDIUM"
                    ))
    
    # Verificar docstrings em código modificado
    python_files = list(Path('.').rglob('**/*.py'))
    
    for py_file in python_files:
        if py_file.exists():
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            
            # Contar funções/classes vs docstrings
            functions = len(re.findall(r'def [a-zA-Z_][a-zA-Z0-9_]*', content))
            classes = len(re.findall(r'class [a-zA-Z_][a-zA-Z0-9_]*', content))
            # Heurística simples: assumir que há pelo menos alguns docstrings
            docstrings = content.count(chr(34)*3) // 2
            
            total_definitions = functions + classes
            if total_definitions > 0 and docstrings < total_definitions:
                issues.append(ValidationIssue(
                    file_path=str(py_file),
                    issue_type="insufficient_docstrings",
                    description="Documentação insuficiente no código",
                    expected="Funções e classes devem ter docstrings",
                    actual=f"{docstrings} docstrings para {total_definitions} definições",
                    severity="LOW"
                ))
    
    return issues if issues else None
"""
        
        self.rules.append(ValidationRule(
            name="validate_documentation_updates",
            description="Valida atualização de documentação após evolução",
            code=rule_code.strip(),
            severity="MEDIUM",
            category="CONTENT"
        ))
    
    def _generate_versioning_rules(self):
        """Gera regras para validar versionamento correto."""
        rule_code = """
def validate_versioning():
    '''Valida versionamento correto após evolução.'''
    issues = []
    
    # Verificar versioning em pyproject.toml
    pyproject_files = list(Path('.').rglob('**/pyproject.toml'))
    version_found = False
    
    for pyproject in pyproject_files:
        if pyproject.exists():
            content = pyproject.read_text(encoding='utf-8', errors='ignore')
            
            # Buscar versão
            version_match = re.search(r'version\\s*=\\s*[\"\\\']([\\.\\w]+)[\"\\\'\\']', content)
            if version_match:
                version_found = True
                version = version_match.group(1)
                
                # Verificar formato semântico (x.y.z)
                if not re.match(r'^\\d+\\.\\d+\\.\\d+', version):
                    issues.append(ValidationIssue(
                        file_path=str(pyproject),
                        issue_type="invalid_version_format",
                        description=f"Formato de versão inválido: {version}",
                        expected="Versão deve seguir formato semântico (x.y.z)",
                        actual=f"Versão: {version}",
                        severity="MEDIUM"
                    ))
    
    if not version_found:
        issues.append(ValidationIssue(
            file_path="pyproject.toml",
            issue_type="missing_version",
            description="Versão não encontrada no pyproject.toml",
            expected="Projeto deve ter versão definida",
            actual="Versão não encontrada",
            severity="MEDIUM"
        ))
    
    # Verificar tags de versão no git (se aplicável)
    try:
        import subprocess
        result = subprocess.run(['git', 'tag', '--list'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and not result.stdout.strip():
            issues.append(ValidationIssue(
                file_path=".git/",
                issue_type="no_version_tags",
                description="Nenhuma tag de versão encontrada no git",
                expected="Projeto deve ter tags de versão",
                actual="Nenhuma tag encontrada",
                severity="LOW"
            ))
    except:
        # Ignorar erros de git (pode não estar disponível)
        pass
    
    return issues if issues else None
"""
        
        self.rules.append(ValidationRule(
            name="validate_versioning",
            description="Valida versionamento correto após evolução",
            code=rule_code.strip(),
            severity="MEDIUM",
            category="CONTENT"
        ))
    
    def _generate_data_migration_rules(self):
        """Gera regras para validar migrações de dados."""
        data_migrations = self.evolution_context.get('data_migrations', [])
        
        if data_migrations:
            rule_code = f"""
def validate_data_migrations():
    '''Valida migrações de dados após evolução.'''
    issues = []
    data_migrations = {data_migrations}
    
    # Verificar arquivos de migração
    migration_dirs = list(Path('.').rglob('**/migrations/'))
    
    if not migration_dirs:
        issues.append(ValidationIssue(
            file_path="migrations/",
            issue_type="missing_migrations_directory",
            description="Diretório de migrações não encontrado",
            expected="Diretório migrations/ deve existir",
            actual="Diretório não encontrado",
            severity="HIGH"
        ))
        return issues
    
    migration_files = []
    for migration_dir in migration_dirs:
        migration_files.extend(list(migration_dir.rglob('*.py')))
    
    # Verificar migrações de dados específicas
    all_migration_content = ""
    for migration_file in migration_files:
        if migration_file.exists():
            all_migration_content += migration_file.read_text(encoding='utf-8', errors='ignore')
    
    for data_migration in data_migrations:
        if data_migration not in all_migration_content:
            issues.append(ValidationIssue(
                file_path="migrations/",
                issue_type="missing_data_migration",
                description=f"Migração de dados não encontrada: {{data_migration}}",
                expected=f"Migração {{data_migration}} deve existir",
                actual="Migração não encontrada",
                severity="HIGH"
            ))
    
    # Verificar se migrações são reversíveis
    if 'RunPython' in all_migration_content:
        # Heurística: se usa RunPython, deveria ter reverse_code
        if 'reverse_code' not in all_migration_content and 'migrations.RunPython.noop' not in all_migration_content:
            issues.append(ValidationIssue(
                file_path="migrations/",
                issue_type="non_reversible_migration",
                description="Migração de dados pode não ser reversível",
                expected="Migrações RunPython devem ter reverse_code",
                actual="reverse_code não encontrado",
                severity="MEDIUM"
            ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name="validate_data_migrations",
                description="Valida migrações de dados após evolução",
                code=rule_code.strip(),
                severity="HIGH",
                category="MODELS"
            ))
    
    def _generate_configuration_evolution_rules(self):
        """Gera regras para validar evolução de configurações."""
        new_config_keys = self.evolution_context.get('new_config_keys', [])
        
        if new_config_keys:
            rule_code = f"""
def validate_configuration_evolution():
    '''Valida evolução de configurações.'''
    issues = []
    new_config_keys = {new_config_keys}
    
    # Verificar settings.py
    settings_files = list(Path('.').rglob('**/settings.py'))
    
    for settings_file in settings_files:
        if settings_file.exists():
            content = settings_file.read_text(encoding='utf-8', errors='ignore')
            
            for config_key in new_config_keys:
                if config_key not in content:
                    issues.append(ValidationIssue(
                        file_path=str(settings_file),
                        issue_type="missing_new_config",
                        description=f"Nova configuração não encontrada: {{config_key}}",
                        expected=f"{{config_key}} deve estar configurado",
                        actual="Configuração ausente",
                        severity="MEDIUM"
                    ))
    
    # Verificar .env.example
    env_example_files = list(Path('.').rglob('**/.env.example'))
    
    for env_example in env_example_files:
        if env_example.exists():
            content = env_example.read_text(encoding='utf-8', errors='ignore')
            
            for config_key in new_config_keys:
                # Verificar se variável de ambiente correspondente existe
                env_var = config_key.upper().replace(' ', '_')
                if env_var not in content:
                    issues.append(ValidationIssue(
                        file_path=str(env_example),
                        issue_type="missing_env_example",
                        description=f"Exemplo de variável de ambiente ausente: {{env_var}}",
                        expected=f"{{env_var}} deve estar no .env.example",
                        actual="Variável não encontrada",
                        severity="LOW"
                    ))
    
    return issues if issues else None
"""
            
            self.rules.append(ValidationRule(
                name="validate_configuration_evolution",
                description="Valida evolução de configurações",
                code=rule_code.strip(),
                severity="MEDIUM",
                category="CONTENT"
            ))