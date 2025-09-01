#!/usr/bin/env python3
"""
AGV Blueprint Conformity Validator v5.0
Valida conformidade da implementação com o Blueprint Arquitetural.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ConformityIssue:
    """Representa um problema de conformidade encontrado"""
    type: str  # MISSING_MODEL, EXTRA_FIELD, STACK_MISMATCH, etc.
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    location: str
    expected: Any = None
    actual: Any = None
    recommendation: str = ""


class BlueprintParser:
    """Extrai especificações estruturadas do Blueprint"""
    
    def __init__(self, blueprint_path: str):
        self.blueprint_path = Path(blueprint_path)
        self.content = self._read_blueprint()
        
    def _read_blueprint(self) -> str:
        """Lê o Blueprint com encoding UTF-8"""
        try:
            with open(self.blueprint_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] Erro ao ler Blueprint: {e}")
            return ""
    
    def extract_specifications(self) -> Dict[str, Any]:
        """Extrai especificações estruturadas do Blueprint"""
        spec = {
            'stack': self._extract_stack_requirements(),
            'models': self._extract_model_specifications(),
            'structure': self._extract_directory_structure(),
            'apis': self._extract_api_specifications(),
            'security': self._extract_security_requirements()
        }
        return spec
    
    def _extract_stack_requirements(self) -> Dict[str, str]:
        """Extrai requisitos de stack tecnológica"""
        stack = {}
        
        # Buscar por menções de tecnologias
        if 'Django' in self.content:
            stack['framework'] = 'Django'
        elif 'Flask' in self.content:
            stack['framework'] = 'Flask'
        elif 'FastAPI' in self.content:
            stack['framework'] = 'FastAPI'
            
        if 'PostgreSQL' in self.content:
            stack['database'] = 'PostgreSQL'
        elif 'MySQL' in self.content:
            stack['database'] = 'MySQL'
            
        if 'Django ORM' in self.content:
            stack['orm'] = 'Django ORM'
        elif 'SQLAlchemy' in self.content:
            stack['orm'] = 'SQLAlchemy'
            
        if 'Django REST Framework' in self.content or 'DRF' in self.content:
            stack['api_framework'] = 'Django REST Framework'
            
        return stack
    
    def _extract_model_specifications(self) -> Dict[str, Dict]:
        """Extrai especificações de modelos do Blueprint"""
        models = {}
        
        # Buscar por blocos de código Python com modelos
        model_blocks = re.findall(r'```python\n(.*?)\n```', self.content, re.DOTALL)
        
        for block in model_blocks:
            # Buscar definições de classe
            class_matches = re.findall(r'class (\w+)\([^)]*\):\s*\n(.*?)(?=\nclass|\n#|\Z)', block, re.DOTALL)
            
            for class_name, class_body in class_matches:
                model_info = {
                    'fields': self._extract_model_fields(class_body),
                    'meta': self._extract_model_meta(class_body),
                    'inheritance': self._extract_inheritance(block, class_name)
                }
                models[class_name] = model_info
        
        return models
    
    def _extract_model_fields(self, class_body: str) -> List[str]:
        """Extrai campos de um modelo"""
        fields = []
        
        # Buscar por definições de campo (patterns para Django e SQLAlchemy)
        field_patterns = [
            r'(\w+)\s*=\s*models\.\w+',  # Django: name = models.CharField()
            r'(\w+)\s*=\s*Column',       # SQLAlchemy: name = Column()
            r'(\w+):\s*\w+',             # Type hints: name: str
        ]
        
        for pattern in field_patterns:
            matches = re.findall(pattern, class_body)
            fields.extend(matches)
        
        return list(set(fields))  # Remove duplicatas
    
    def _extract_model_meta(self, class_body: str) -> Dict[str, Any]:
        """Extrai metadados do modelo (Meta class, __abstract__, etc.)"""
        meta = {}
        
        if 'abstract = True' in class_body or '__abstract__ = True' in class_body:
            meta['abstract'] = True
        
        if 'class Meta:' in class_body:
            meta['has_meta_class'] = True
            
        return meta
    
    def _extract_inheritance(self, block: str, class_name: str) -> str:
        """Extrai herança do modelo"""
        pattern = rf'class {class_name}\(([^)]+)\):'
        match = re.search(pattern, block)
        return match.group(1) if match else ''
    
    def _extract_directory_structure(self) -> Dict[str, List[str]]:
        """Extrai estrutura de diretórios esperada"""
        structure = {}
        
        # Buscar por blocos de estrutura de diretórios
        structure_blocks = re.findall(r'```\n([\w/\s\-│├└\.]+)\n```', self.content, re.MULTILINE)
        
        for block in structure_blocks:
            if '/' in block:  # Parece estrutura de diretórios
                lines = block.split('\n')
                current_structure = []
                for line in lines:
                    if line.strip() and ('/' in line or '.py' in line):
                        current_structure.append(line.strip())
                
                if current_structure:
                    structure['expected_files'] = current_structure
        
        return structure
    
    def _extract_api_specifications(self) -> Dict[str, Any]:
        """Extrai especificações de API"""
        apis = {}
        
        # Buscar por menções de endpoints
        if '/api/v1' in self.content:
            apis['version'] = 'v1'
            apis['base_path'] = '/api/v1'
        
        if 'REST' in self.content or 'RESTful' in self.content:
            apis['type'] = 'REST'
            
        return apis
    
    def _extract_security_requirements(self) -> Dict[str, Any]:
        """Extrai requisitos de segurança"""
        security = {}
        
        if 'multi-tenant' in self.content.lower() or 'tenant' in self.content.lower():
            security['multi_tenancy'] = True
            
        if 'JWT' in self.content:
            security['authentication'] = 'JWT'
            
        return security


class ImplementationAnalyzer:
    """Analisa a implementação atual do código"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def analyze_implementation(self) -> Dict[str, Any]:
        """Analisa a implementação atual"""
        implementation = {
            'stack': self._analyze_stack(),
            'models': self._analyze_models(),
            'structure': self._analyze_structure(),
            'apis': self._analyze_apis()
        }
        return implementation
    
    def _analyze_stack(self) -> Dict[str, str]:
        """Analisa stack tecnológica atual"""
        stack = {}
        
        # Verificar arquivos de dependências
        requirements_files = [
            self.project_path / 'requirements.txt',
            self.project_path / 'pyproject.toml',
            self.project_path / 'package.json'
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                content = req_file.read_text(encoding='utf-8')
                
                if 'Django' in content:
                    stack['framework'] = 'Django'
                elif 'Flask' in content:
                    stack['framework'] = 'Flask'
                elif 'FastAPI' in content:
                    stack['framework'] = 'FastAPI'
                    
                if 'psycopg2' in content:
                    stack['database'] = 'PostgreSQL'
                elif 'SQLAlchemy' in content:
                    stack['orm'] = 'SQLAlchemy'
        
        return stack
    
    def _analyze_models(self) -> Dict[str, Dict]:
        """Analisa modelos implementados"""
        models = {}
        
        # Buscar arquivos models.py
        model_files = list(self.project_path.rglob('*models.py'))
        
        for model_file in model_files:
            try:
                content = model_file.read_text(encoding='utf-8')
                file_models = self._parse_models_from_file(content)
                models.update(file_models)
            except Exception as e:
                print(f"[WARN] Erro ao analisar {model_file}: {e}")
        
        return models
    
    def _parse_models_from_file(self, content: str) -> Dict[str, Dict]:
        """Parse modelos de um arquivo"""
        models = {}
        
        # Buscar definições de classe
        class_pattern = r'class (\w+)(?:\([^)]*\))?:\s*\n(.*?)(?=\nclass|\Z)'
        matches = re.findall(class_pattern, content, re.DOTALL)
        
        for class_name, class_body in matches:
            # Extrair campos (simplificado)
            field_patterns = [
                r'(\w+)\s*=.*?Column',           # SQLAlchemy
                r'(\w+)\s*=.*?models\.\w+',      # Django
                r'(\w+):\s*\w+\s*=',             # Type hints com assignment
            ]
            
            fields = []
            for pattern in field_patterns:
                field_matches = re.findall(pattern, class_body)
                fields.extend(field_matches)
            
            models[class_name] = {
                'fields': list(set(fields)),
                'abstract': '__abstract__ = True' in class_body or 'abstract = True' in class_body
            }
        
        return models
    
    def _analyze_structure(self) -> Dict[str, List[str]]:
        """Analisa estrutura de diretórios atual"""
        structure = {
            'existing_files': [],
            'python_files': [],
            'directories': []
        }
        
        try:
            for item in self.project_path.rglob('*'):
                if item.is_file():
                    rel_path = str(item.relative_to(self.project_path))
                    structure['existing_files'].append(rel_path)
                    
                    if item.suffix == '.py':
                        structure['python_files'].append(rel_path)
                elif item.is_dir():
                    rel_path = str(item.relative_to(self.project_path))
                    structure['directories'].append(rel_path)
        except Exception as e:
            print(f"[WARN] Erro ao analisar estrutura: {e}")
        
        return structure
    
    def _analyze_apis(self) -> Dict[str, Any]:
        """Analisa APIs implementadas"""
        apis = {}
        
        # Buscar arquivos de URLs/rotas
        url_files = list(self.project_path.rglob('*urls.py')) + list(self.project_path.rglob('*routes.py'))
        
        for url_file in url_files:
            try:
                content = url_file.read_text(encoding='utf-8')
                if 'api/v1' in content:
                    apis['version'] = 'v1'
                    apis['base_path'] = '/api/v1'
            except Exception:
                pass
        
        return apis


class ConformityValidator:
    """Validador de conformidade Blueprint vs Implementação"""
    
    def __init__(self, blueprint_spec: Dict, implementation: Dict):
        self.blueprint_spec = blueprint_spec
        self.implementation = implementation
        self.issues: List[ConformityIssue] = []
    
    def validate_conformity(self) -> Dict[str, Any]:
        """Executa validação completa de conformidade"""
        
        # Validar diferentes aspectos
        self._validate_stack_conformity()
        self._validate_model_conformity()
        self._validate_structure_conformity()
        
        # Calcular score de conformidade
        conformity_score = self._calculate_conformity_score()
        
        return {
            'conformity_score': conformity_score,
            'total_issues': len(self.issues),
            'critical_issues': len([i for i in self.issues if i.severity == 'CRITICAL']),
            'high_issues': len([i for i in self.issues if i.severity == 'HIGH']),
            'issues': [self._issue_to_dict(issue) for issue in self.issues],
            'recommendations': self._generate_recommendations()
        }
    
    def _validate_stack_conformity(self):
        """Valida conformidade da stack tecnológica"""
        bp_stack = self.blueprint_spec.get('stack', {})
        impl_stack = self.implementation.get('stack', {})
        
        for component, expected in bp_stack.items():
            actual = impl_stack.get(component)
            
            if not actual:
                self.issues.append(ConformityIssue(
                    type='MISSING_STACK_COMPONENT',
                    severity='HIGH',
                    description=f'Componente de stack {component} não encontrado',
                    location='stack',
                    expected=expected,
                    actual=None,
                    recommendation=f'Instalar e configurar {expected}'
                ))
            elif actual != expected:
                self.issues.append(ConformityIssue(
                    type='STACK_MISMATCH',
                    severity='CRITICAL',
                    description=f'Stack {component} não conforme',
                    location='stack',
                    expected=expected,
                    actual=actual,
                    recommendation=f'Migrar de {actual} para {expected} conforme Blueprint'
                ))
    
    def _validate_model_conformity(self):
        """Valida conformidade dos modelos de dados"""
        bp_models = self.blueprint_spec.get('models', {})
        impl_models = self.implementation.get('models', {})
        
        # Verificar modelos obrigatórios do Blueprint
        for model_name, bp_model in bp_models.items():
            if model_name not in impl_models:
                self.issues.append(ConformityIssue(
                    type='MISSING_MODEL',
                    severity='HIGH',
                    description=f'Modelo {model_name} não implementado',
                    location=f'models.{model_name}',
                    expected=model_name,
                    actual=None,
                    recommendation=f'Implementar modelo {model_name} conforme Blueprint'
                ))
            else:
                # Validar campos do modelo
                self._validate_model_fields(model_name, bp_model, impl_models[model_name])
        
        # Verificar modelos extras não especificados
        for model_name in impl_models:
            if model_name not in bp_models:
                self.issues.append(ConformityIssue(
                    type='EXTRA_MODEL',
                    severity='MEDIUM',
                    description=f'Modelo {model_name} não especificado no Blueprint',
                    location=f'models.{model_name}',
                    expected=None,
                    actual=model_name,
                    recommendation=f'Verificar se modelo {model_name} é necessário ou atualizar Blueprint'
                ))
    
    def _validate_model_fields(self, model_name: str, bp_model: Dict, impl_model: Dict):
        """Valida campos de um modelo específico"""
        bp_fields = set(bp_model.get('fields', []))
        impl_fields = set(impl_model.get('fields', []))
        
        # Campos obrigatórios faltantes
        missing_fields = bp_fields - impl_fields
        for field in missing_fields:
            self.issues.append(ConformityIssue(
                type='MISSING_FIELD',
                severity='HIGH',
                description=f'Campo {field} obrigatório não encontrado no modelo {model_name}',
                location=f'models.{model_name}.{field}',
                expected=field,
                actual=None,
                recommendation=f'Adicionar campo {field} ao modelo {model_name}'
            ))
        
        # Campos extras
        extra_fields = impl_fields - bp_fields
        for field in extra_fields:
            self.issues.append(ConformityIssue(
                type='EXTRA_FIELD',
                severity='LOW',
                description=f'Campo {field} não especificado no Blueprint para modelo {model_name}',
                location=f'models.{model_name}.{field}',
                expected=None,
                actual=field,
                recommendation=f'Verificar se campo {field} é necessário ou atualizar Blueprint'
            ))
    
    def _validate_structure_conformity(self):
        """Valida conformidade da estrutura de diretórios"""
        bp_structure = self.blueprint_spec.get('structure', {})
        impl_structure = self.implementation.get('structure', {})
        
        expected_files = bp_structure.get('expected_files', [])
        existing_files = impl_structure.get('existing_files', [])
        
        # Simplificar comparação de arquivos (apenas nomes base)
        expected_base = {Path(f).name for f in expected_files if f.strip()}
        existing_base = {Path(f).name for f in existing_files}
        
        # Arquivos importantes faltantes
        missing_files = expected_base - existing_base
        for file_name in missing_files:
            if file_name.endswith('.py'):  # Focar em arquivos Python importantes
                self.issues.append(ConformityIssue(
                    type='MISSING_FILE',
                    severity='MEDIUM',
                    description=f'Arquivo {file_name} especificado no Blueprint não encontrado',
                    location=f'structure.{file_name}',
                    expected=file_name,
                    actual=None,
                    recommendation=f'Criar arquivo {file_name} conforme estrutura do Blueprint'
                ))
    
    def _calculate_conformity_score(self) -> float:
        """Calcula score de conformidade (0-100)"""
        if not self.issues:
            return 100.0
        
        # Pesos por severidade
        severity_weights = {
            'CRITICAL': 10,
            'HIGH': 5,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        total_penalty = sum(severity_weights.get(issue.severity, 1) for issue in self.issues)
        
        # Score baseado na quantidade e severidade dos problemas
        # Assumindo um máximo de 100 pontos de penalidade para 0%
        max_penalty = 100
        score = max(0, 100 - (total_penalty / max_penalty * 100))
        
        return round(score, 1)
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos problemas encontrados"""
        recommendations = []
        
        critical_issues = [i for i in self.issues if i.severity == 'CRITICAL']
        if critical_issues:
            recommendations.append("🚨 CRÍTICO: Corrigir incompatibilidades de stack tecnológica primeiro")
        
        high_issues = [i for i in self.issues if i.severity == 'HIGH']
        if high_issues:
            recommendations.append("⚠️ ALTO: Implementar modelos e campos obrigatórios faltantes")
        
        model_issues = [i for i in self.issues if 'MODEL' in i.type]
        if len(model_issues) > 3:
            recommendations.append("📋 Revisar especificação de modelos no Blueprint vs implementação")
        
        return recommendations
    
    def _issue_to_dict(self, issue: ConformityIssue) -> Dict[str, Any]:
        """Converte issue para dicionário"""
        return {
            'type': issue.type,
            'severity': issue.severity,
            'description': issue.description,
            'location': issue.location,
            'expected': issue.expected,
            'actual': issue.actual,
            'recommendation': issue.recommendation
        }


def main():
    """Função principal"""
    
    blueprint_path = os.getenv('BLUEPRINT_PATH', 'BLUEPRINT_ARQUITETURAL.md')
    project_path = os.getenv('PROJECT_PATH', '.')
    
    if not Path(blueprint_path).exists():
        print(f"[ERROR] Blueprint não encontrado: {blueprint_path}")
        sys.exit(1)
    
    print("[INFO] AGV Blueprint Conformity Validator v5.0")
    print(f"[INFO] Blueprint: {blueprint_path}")
    print(f"[INFO] Projeto: {project_path}")
    print("=" * 60)
    
    # Extrair especificações do Blueprint
    print("[1/4] Analisando Blueprint...")
    blueprint_parser = BlueprintParser(blueprint_path)
    blueprint_spec = blueprint_parser.extract_specifications()
    
    # Analisar implementação atual
    print("[2/4] Analisando implementação atual...")
    implementation_analyzer = ImplementationAnalyzer(project_path)
    implementation = implementation_analyzer.analyze_implementation()
    
    # Validar conformidade
    print("[3/4] Validando conformidade...")
    validator = ConformityValidator(blueprint_spec, implementation)
    results = validator.validate_conformity()
    
    # Gerar relatório
    print("[4/4] Gerando relatório...")
    print("\n" + "=" * 60)
    print("RELATÓRIO DE CONFORMIDADE COM BLUEPRINT")
    print("=" * 60)
    
    print(f"\n📊 SCORE GERAL: {results['conformity_score']:.1f}%")
    
    if results['conformity_score'] >= 80:
        print("🎉 EXCELENTE - Alta conformidade com Blueprint")
    elif results['conformity_score'] >= 60:
        print("⚠️ BOM - Conformidade aceitável, alguns ajustes necessários")
    elif results['conformity_score'] >= 40:
        print("🔧 REGULAR - Múltiplos problemas identificados")
    else:
        print("🚨 CRÍTICO - Baixa conformidade, revisão urgente necessária")
    
    print("\n📋 RESUMO:")
    print(f"   Total de problemas: {results['total_issues']}")
    print(f"   Críticos: {results['critical_issues']}")
    print(f"   Altos: {results['high_issues']}")
    
    # Mostrar problemas críticos
    if results['critical_issues'] > 0:
        print("\n🚨 PROBLEMAS CRÍTICOS:")
        for issue in results['issues']:
            if issue['severity'] == 'CRITICAL':
                print(f"   • {issue['description']}")
                print(f"     Localização: {issue['location']}")
                print(f"     Recomendação: {issue['recommendation']}")
    
    # Mostrar recomendações
    if results['recommendations']:
        print("\n🎯 RECOMENDAÇÕES PRINCIPAIS:")
        for rec in results['recommendations']:
            print(f"   {rec}")
    
    # Salvar relatório detalhado
    report_path = Path(project_path) / 'blueprint_conformity_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório detalhado salvo em: {report_path}")
    
    # Exit code baseado na conformidade
    if results['conformity_score'] >= 70:
        sys.exit(0)  # Sucesso
    else:
        sys.exit(1)  # Falhou


if __name__ == '__main__':
    main()