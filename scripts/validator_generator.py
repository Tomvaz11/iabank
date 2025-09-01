#!/usr/bin/env python3
"""
ValidatorGenerator v3.0 - Sistema Modular de Geração de Validadores AGV
Ponto de entrada único para todos os tipos de validação: scaffold, targets, integração e evolução.

NOVA ARQUITETURA MODULAR v5.0:
- Ponto de entrada único com dispatch para geradores especializados
- Core components reutilizáveis (blueprint_parser, base_generator, validation_rules)
- Generators especializados (scaffold, target, integration, evolution)
- Context otimizado para alvos específicos (reduz contexto de 1500+ para ~500 linhas)
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Imports dos components core
from core.blueprint_parser import AdvancedBlueprintParser, ProjectSpecs
from core.validation_rules import ValidationRule
from generators.scaffold_generator import ScaffoldGenerator
from generators.target_generator import TargetGenerator
from generators.integration_generator import IntegrationGenerator
from generators.evolution_generator import EvolutionGenerator


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


class ModularValidatorGenerator:
    """Gerador modular de validadores AGV v3.0."""
    
    VALIDATION_TYPES = {
        'scaffold': 'Validação completa de scaffold (Alvo 0)',
        'target': 'Validação de alvo específico (Alvos 1-N)',
        'integration': 'Validação de teste de integração (T1-T8)',
        'evolution': 'Validação de evolução e manutenção (F7-Evolucionista)'
    }
    
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
    
    def __init__(self, blueprint_path: str):
        self.blueprint_path = Path(blueprint_path)
        self.parser = AdvancedBlueprintParser(str(self.blueprint_path))
        self.specs: Optional[ProjectSpecs] = None
        
    def parse_blueprint(self) -> ProjectSpecs:
        """Parse do Blueprint arquitetural."""
        if self.specs is None:
            print("Analisando Blueprint arquitetural com parser avançado...")
            self.specs = self.parser.parse()
            
            print(f"Especificações extraídas do projeto: {self.specs.project_name}")
            print(f"   Framework Backend: {self.specs.backend_framework}")
            print(f"   Framework Frontend: {self.specs.frontend_framework}")
            print(f"   Database: {self.specs.database}")
            print(f"   Arquitetura: {self.specs.architecture_type}")
            print(f"   Django Apps: {', '.join(self.specs.django_apps) if self.specs.django_apps else 'N/A'}")
            print(f"   Modelos: {len(self.specs.models)} encontrados")
            print(f"   Multi-tenancy: {self.specs.multi_tenancy}")
            print(f"   Autenticação: {self.specs.authentication_method}")
            
        return self.specs
    
    def generate_scaffold_validator(self, output_path: str = "scripts/validate_scaffold.py") -> bool:
        """Gera validador especializado para scaffold (Alvo 0)."""
        try:
            specs = self.parse_blueprint()
            
            print("Gerando validador de SCAFFOLD com ScaffoldGenerator...")
            generator = ScaffoldGenerator(specs)
            rules = generator.generate_rules()
            
            self._generate_validator_file(
                rules, 
                output_path,
                validator_class_name=f"{self._clean_project_name()}ScaffoldValidator",
                validator_description="Validador especializado para scaffold completo (Alvo 0)"
            )
            
            print(f"Validador de scaffold criado: {output_path}")
            print(f"Total de validações: {len(rules)}")
            return True
            
        except Exception as e:
            print(f"Erro ao gerar validador de scaffold: {e}")
            return False
    
    def generate_target_validator(self, target_number: int, target_context: Dict[str, Any] = None, 
                                 output_path: str = None) -> bool:
        """Gera validador especializado para alvo específico."""
        try:
            specs = self.parse_blueprint()
            
            if output_path is None:
                output_path = f"scripts/validate_target_{target_number}.py"
            
            print(f"Gerando validador para ALVO {target_number} com TargetGenerator...")
            generator = TargetGenerator(specs, target_number, target_context or {})
            rules = generator.generate_rules()
            
            self._generate_validator_file(
                rules,
                output_path,
                validator_class_name=f"{self._clean_project_name()}Target{target_number}Validator",
                validator_description=f"Validador especializado para Alvo {target_number}"
            )
            
            print(f"Validador do Alvo {target_number} criado: {output_path}")
            print(f"Total de validações: {len(rules)}")
            return True
            
        except Exception as e:
            print(f"Erro ao gerar validador do Alvo {target_number}: {e}")
            return False
    
    def generate_integration_validator(self, integration_phase: str, integration_context: Dict[str, Any] = None,
                                     output_path: str = None) -> bool:
        """Gera validador especializado para fase de integração."""
        try:
            specs = self.parse_blueprint()
            
            if output_path is None:
                output_path = f"scripts/validate_{integration_phase.lower()}.py"
            
            print(f"Gerando validador para {integration_phase} com IntegrationGenerator...")
            generator = IntegrationGenerator(specs, integration_phase, integration_context or {})
            rules = generator.generate_rules()
            
            self._generate_validator_file(
                rules,
                output_path,
                validator_class_name=f"{self._clean_project_name()}{integration_phase}Validator",
                validator_description=f"Validador especializado para fase de integração {integration_phase}"
            )
            
            print(f"Validador de integração {integration_phase} criado: {output_path}")
            print(f"Total de validações: {len(rules)}")
            return True
            
        except Exception as e:
            print(f"Erro ao gerar validador de integração {integration_phase}: {e}")
            return False
    
    def generate_evolution_validator(self, evolution_context: Dict[str, Any] = None,
                                   output_path: str = "scripts/validate_evolution.py") -> bool:
        """Gera validador especializado para evolução e manutenção."""
        try:
            specs = self.parse_blueprint()
            
            print("Gerando validador de EVOLUÇÃO com EvolutionGenerator...")
            generator = EvolutionGenerator(specs, evolution_context or {})
            rules = generator.generate_rules()
            
            self._generate_validator_file(
                rules,
                output_path,
                validator_class_name=f"{self._clean_project_name()}EvolutionValidator",
                validator_description="Validador especializado para evolução e manutenção (F7-Evolucionista)"
            )
            
            print(f"Validador de evolução criado: {output_path}")
            print(f"Total de validações: {len(rules)}")
            return True
            
        except Exception as e:
            print(f"Erro ao gerar validador de evolução: {e}")
            return False
    
    def _generate_validator_file(self, rules: List[ValidationRule], output_path: str, 
                                validator_class_name: str, validator_description: str):
        """Gera arquivo de validador com as regras fornecidas."""
        code = self._generate_validator_code(rules, validator_class_name, validator_description)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code, encoding='utf-8')
    
    def _generate_validator_code(self, rules: List[ValidationRule], validator_class_name: str, 
                                validator_description: str) -> str:
        """Gera código completo do validador."""
        # Header
        code_parts = [
            "#!/usr/bin/env python3",
            '"""',
            f"{validator_description}",
            "Gerado automaticamente pelo ValidatorGenerator v3.0 - Sistema Modular AGV",
            '"""',
            "",
            "import sys",
            "import json",
            "import re",
            "from pathlib import Path",
            "from typing import Dict, List, Any, Optional, Union",
            "from dataclasses import dataclass, asdict",
            "from datetime import datetime",
            "",
        ]
        
        # ValidationIssue class
        code_parts.extend([
            "@dataclass",
            "class ValidationIssue:",
            '    """Representa um problema encontrado na validação."""',
            "    file_path: str",
            "    issue_type: str", 
            "    description: str",
            "    expected: str",
            "    actual: str",
            "    severity: str  # CRITICAL, HIGH, MEDIUM, LOW",
            "",
        ])
        
        # ValidationResults class
        code_parts.extend([
            "@dataclass",
            "class ValidationResults:",
            '    """Resultados completos da validação."""',
            "    total_checks: int",
            "    passed_checks: int",
            "    failed_checks: int",
            "    issues: List[ValidationIssue]",
            "    score: float",
            "    categories: Dict[str, int]",
            "",
            "    def to_dict(self) -> Dict[str, Any]:",
            '        """Converte para dicionário para serialização JSON."""',
            "        return {",
            '            "total_checks": self.total_checks,',
            '            "passed_checks": self.passed_checks,',
            '            "failed_checks": self.failed_checks,',
            '            "issues": [asdict(issue) for issue in self.issues],',
            '            "score": self.score,',
            '            "categories": self.categories',
            "        }",
            "",
        ])
        
        # Validation functions
        for rule in rules:
            code_parts.extend([
                rule.code,
                ""
            ])
        
        # Validator class
        code_parts.extend([
            f"class {validator_class_name}:",
            f'    """{validator_description}."""',
            "",
            "    SEVERITY_WEIGHTS = {",
            '        "CRITICAL": 15,',
            '        "HIGH": 8,',
            '        "MEDIUM": 2,',
            '        "LOW": 1',
            "    }",
            "",
            "    CATEGORY_WEIGHTS = {",
            '        "STRUCTURE": 1.0,',
            '        "CONTENT": 1.5,',
            '        "MODELS": 2.0,',
            '        "DEPENDENCIES": 1.2,',
            '        "API": 1.3',
            "    }",
            "",
            "    def __init__(self):",
            "        self.validation_methods = [",
        ])
        
        # Add validation method names
        for rule in rules:
            code_parts.append(f'            "{rule.name}",')
        
        code_parts.extend([
            "        ]",
            "",
            "        self.rule_categories = {",
        ])
        
        # Add rule categories
        for rule in rules:
            code_parts.append(f'            "{rule.name}": "{rule.category}",')
        
        code_parts.extend([
            "        }",
            "",
            "    def validate(self) -> ValidationResults:",
            '        """Executa todas as validações e retorna os resultados."""',
            "        issues = []",
            "        total_checks = len(self.validation_methods)",
            "        failed_validations = 0",
            '        categories = {"STRUCTURE": 0, "CONTENT": 0, "MODELS": 0, "DEPENDENCIES": 0, "API": 0}',
            "",
            "        print(f\"Executando {total_checks} validações especializadas...\")",
            "        print(\"Níveis: STRUCTURE | CONTENT | MODELS | DEPENDENCIES | API\")",
            "        print(\"-\" * 80)",
            "",
            "        for method_name in self.validation_methods:",
            "            try:",
            "                method = globals()[method_name]",
            "                result = method()",
            "",
            "                category = self.rule_categories.get(method_name, \"STRUCTURE\")",
            "                print(f\"[{category:12}] {method_name}\", end=\"\")",
            "",
            "                if result:",
            "                    failed_validations += 1",
            "                    if isinstance(result, list):",
            "                        issues.extend(result)",
            "                        categories[category] += len(result)",
            "                        print(f\" FALHOU: {len(result)} problemas\")",
            "                    else:",
            "                        issues.append(result)",
            "                        categories[category] += 1",
            "                        print(\" FALHOU: 1 problema\")",
            "                else:",
            "                    print(\" OK\")",
            "",
            "            except Exception as e:",
            "                failed_validations += 1",
            "                issues.append(ValidationIssue(",
            '                    file_path="validator",',
            '                    issue_type="validation_error",',
            "                    description=f\"Erro na validação {method_name}: {str(e)}\",",
            '                    expected="Validação deve executar sem erros",',
            "                    actual=f\"Erro: {str(e)}\",",
            '                    severity="CRITICAL"',
            "                ))",
            "                print(f\" ERRO: {str(e)}\")",
            "",
            "        passed_checks = total_checks - failed_validations",
            "        score = self._calculate_score(total_checks, failed_validations, issues)",
            "",
            "        return ValidationResults(",
            "            total_checks=total_checks,",
            "            passed_checks=passed_checks,",
            "            failed_checks=failed_validations,",
            "            issues=issues,",
            "            score=score,",
            "            categories=categories",
            "        )",
            "",
            "    def _calculate_score(self, total_checks: int, failed_validations: int, issues: List[ValidationIssue]) -> float:",
            '        """Calcula score baseado na severidade e categoria dos problemas."""',
            "        if failed_validations == 0:",
            "            return 100.0",
            "",
            "        total_penalty = 0",
            "        for issue in issues:",
            "            severity_weight = self.SEVERITY_WEIGHTS.get(issue.severity, 1)",
            "            category_weight = 1.0",
            "",
            "            if \"model\" in issue.issue_type.lower():",
            "                category_weight = self.CATEGORY_WEIGHTS[\"MODELS\"]",
            "            elif \"content\" in issue.issue_type.lower() or \"config\" in issue.issue_type.lower():",
            "                category_weight = self.CATEGORY_WEIGHTS[\"CONTENT\"]",
            "            elif \"api\" in issue.issue_type.lower():",
            "                category_weight = self.CATEGORY_WEIGHTS[\"API\"]",
            "            elif \"dependency\" in issue.issue_type.lower():",
            "                category_weight = self.CATEGORY_WEIGHTS[\"DEPENDENCIES\"]",
            "            else:",
            "                category_weight = self.CATEGORY_WEIGHTS[\"STRUCTURE\"]",
            "",
            "            penalty = severity_weight * category_weight",
            "            total_penalty += penalty",
            "",
            "        base_score = ((total_checks - failed_validations) / total_checks) * 100",
            "        penalty_factor = min(total_penalty / (failed_validations * 10), 0.5)",
            "        final_score = max(0, base_score - (base_score * penalty_factor))",
            "",
            "        return round(final_score, 2)",
            "",
            "    def generate_report(self, results: ValidationResults) -> str:",
            '        """Gera relatório detalhado dos resultados."""',
            "        report = []",
            "        report.append(\"=\" * 100)",
            f"        report.append(f\"RELATÓRIO DE VALIDAÇÃO - {validator_description.upper()}\")",
            "        report.append(\"=\" * 100)",
            "        report.append(f\"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")",
            f"        report.append(f\"Validador: {validator_class_name}\")",
            "        report.append(\"\")",
            "        report.append(\"RESULTADOS:\")",
            "        report.append(f\"├─ Total de Verificações: {results.total_checks}\")",
            "        report.append(f\"├─ Aprovadas: {results.passed_checks}\")",
            "        report.append(f\"├─ Reprovadas: {results.failed_checks}\")",
            "        report.append(f\"└─ Score Final: {results.score}%\")",
            "        report.append(\"\")",
            "",
            "        # Análise por categoria",
            "        report.append(\"ANÁLISE POR CATEGORIA:\")",
            "        for category, count in results.categories.items():",
            "            status = \"FALHOU\" if count > 0 else \"OK\"",
            "            report.append(f\"|- {status} {category:12}: {count} problemas\")",
            "        report.append(\"\")",
            "",
            "        # Status",
            "        if results.score >= 90:",
            "            report.append(\"STATUS: EXCELENTE\")",
            "        elif results.score >= 85:",
            "            report.append(\"STATUS: APROVADO\")",
            "        elif results.score >= 70:",
            "            report.append(\"STATUS: NECESSITA MELHORIAS\")",
            "        else:",
            "            report.append(\"STATUS: REJEITADO\")",
            "",
            "        report.append(\"\")",
            "",
            "        if results.issues:",
            "            # Agrupar por severidade",
            "            critical_issues = [i for i in results.issues if i.severity == \"CRITICAL\"]",
            "            high_issues = [i for i in results.issues if i.severity == \"HIGH\"]",
            "            medium_issues = [i for i in results.issues if i.severity == \"MEDIUM\"]",
            "            low_issues = [i for i in results.issues if i.severity == \"LOW\"]",
            "",
            "            if critical_issues:",
            "                report.append(\"PROBLEMAS CRÍTICOS:\")",
            "                report.append(\"-\" * 60)",
            "                for i, issue in enumerate(critical_issues, 1):",
            "                    report.append(f\"{i}. {issue.description}\")",
            "                    report.append(f\"   Arquivo: {issue.file_path}\")",
            "                    report.append(f\"   Esperado: {issue.expected}\")",
            "                    report.append(f\"   Encontrado: {issue.actual}\")",
            "                    report.append(\"\")",
            "",
            "            if high_issues:",
            "                report.append(\"PROBLEMAS DE ALTA PRIORIDADE:\")",
            "                report.append(\"-\" * 60)",
            "                for i, issue in enumerate(high_issues, 1):",
            "                    report.append(f\"{i}. {issue.description}\")",
            "                    report.append(f\"   Arquivo: {issue.file_path}\")",
            "                    report.append(\"\")",
            "",
            "            if medium_issues:",
            "                report.append(\"PROBLEMAS DE MÉDIA PRIORIDADE:\")",
            "                report.append(\"-\" * 60)", 
            "                for i, issue in enumerate(medium_issues, 1):",
            "                    report.append(f\"{i}. {issue.description}\")",
            "                    report.append(\"\")",
            "",
            "            if low_issues:",
            "                report.append(\"PROBLEMAS DE BAIXA PRIORIDADE:\")",
            "                report.append(\"-\" * 60)",
            "                for i, issue in enumerate(low_issues, 1):",
            "                    report.append(f\"{i}. {issue.description}\")",
            "                    report.append(\"\")",
            "",
            "        report.append(\"=\" * 100)",
            "        return \"\\n\".join(report)",
            "",
        ])
        
        # Main function
        code_parts.extend([
            "def main():",
            '    """Função principal do validador."""',
            "    import os",
            "    import sys",
            "    ",
            "    # Configurar encoding para Windows",
            "    os.environ['PYTHONIOENCODING'] = 'utf-8'",
            "    if hasattr(sys.stdout, 'reconfigure'):",
            "        sys.stdout.reconfigure(encoding='utf-8')",
            "    if hasattr(sys.stderr, 'reconfigure'):",
            "        sys.stderr.reconfigure(encoding='utf-8')",
            "",
            f"    validator = {validator_class_name}()",
            "    results = validator.validate()",
            "",
            "    # Gerar e exibir relatório",
            "    report = validator.generate_report(results)",
            "    print()",
            "    ",
            "    # Exibir relatório com tratamento de encoding",
            "    try:",
            "        print(report)",
            "    except UnicodeEncodeError:",
            "        # Fallback para encoding seguro",
            "        safe_report = report.encode('utf-8', errors='replace').decode('utf-8')",
            "        print(safe_report)",
            "",
            "    # Salvar resultados em JSON",
            "    results_file = Path(\"validation_results.json\")",
            "    results_file.write_text(",
            "        json.dumps(results.to_dict(), indent=2, ensure_ascii=False),", 
            "        encoding='utf-8'",
            "    )",
            "    print(f\"\\nRelatório detalhado salvo em: {results_file}\")",
            "",
            "    return 0 if results.score >= 75 else 1",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    exit_code = main()",
            "    sys.exit(exit_code)",
        ])
        
        return "\n".join(code_parts)
    
    def _clean_project_name(self) -> str:
        """Limpa o nome do projeto para usar em nomes de classe."""
        if self.specs:
            name = self.specs.project_name
        else:
            name = "Project"
        
        # Remove caracteres especiais e torna camelCase
        clean_name = re.sub(r'[^\w\s]', '', name)
        clean_name = ''.join(word.title() for word in clean_name.split())
        return clean_name or "Project"


def main():
    """Função principal do ValidatorGenerator v3.0 - Sistema Modular."""
    parser = argparse.ArgumentParser(
        description="ValidatorGenerator v3.0 - Sistema Modular de Geração de Validadores AGV"
    )
    
    parser.add_argument("blueprint", help="Caminho do arquivo Blueprint arquitetural")
    parser.add_argument("type", choices=ModularValidatorGenerator.VALIDATION_TYPES.keys(),
                       help="Tipo de validador a ser gerado")
    
    # Argumentos específicos por tipo
    parser.add_argument("--target-number", type=int, help="Número do alvo (para type=target)")
    parser.add_argument("--integration-phase", help="Fase de integração (para type=integration, ex: T1, T2)")
    parser.add_argument("--context", help="Arquivo JSON com contexto específico")
    parser.add_argument("--output", help="Caminho do arquivo de saída (opcional)")
    
    args = parser.parse_args()
    
    # Validar argumentos específicos
    if args.type == "target" and not args.target_number:
        print("Erro: --target-number é obrigatório para type=target")
        sys.exit(1)
    
    if args.type == "integration" and not args.integration_phase:
        print("Erro: --integration-phase é obrigatório para type=integration")
        sys.exit(1)
    
    # Carregar contexto se fornecido
    context = {}
    if args.context:
        try:
            context_file = Path(args.context)
            if context_file.exists():
                context = json.loads(context_file.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"Erro ao carregar contexto: {e}")
            sys.exit(1)
    
    # Criar gerador
    try:
        generator = ModularValidatorGenerator(args.blueprint)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo Blueprint não encontrado: {args.blueprint}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Erro ao inicializar gerador: {e}")
        sys.exit(1)
    
    print("ValidatorGenerator v3.0 - Sistema Modular AGV")
    print(f"Tipo de validação: {ModularValidatorGenerator.VALIDATION_TYPES[args.type]}")
    print(f"Blueprint: {args.blueprint}")
    print("-" * 80)
    
    # Executar geração baseada no tipo
    success = False
    
    if args.type == "scaffold":
        output_path = args.output or "scripts/validate_scaffold_new.py"
        success = generator.generate_scaffold_validator(output_path)
        
    elif args.type == "target":
        success = generator.generate_target_validator(
            args.target_number, 
            context, 
            args.output
        )
        
    elif args.type == "integration":
        success = generator.generate_integration_validator(
            args.integration_phase,
            context,
            args.output
        )
        
    elif args.type == "evolution":
        output_path = args.output or "scripts/validate_evolution.py"
        success = generator.generate_evolution_validator(
            context,
            output_path
        )
    
    if success:
        print("\n[OK] Validador gerado com sucesso!")
        print(f"Tipo: {args.type}")
        if args.type == "target":
            print(f"Alvo: {args.target_number}")
        elif args.type == "integration":
            print(f"Fase: {args.integration_phase}")
    else:
        print("\n[ERRO] Erro ao gerar validador!")
        sys.exit(1)


if __name__ == "__main__":
    main()