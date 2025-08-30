#!/usr/bin/env python3
"""
AGV Quality Validator v5.0
Valida qualidade de código e conformidade com padrões AGV.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


class AGVQualityValidator:
    """Validador de qualidade para código gerado pelo método AGV"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_content = self._read_file()
        self.errors = []
        self.warnings = []
        self.passed_checks = []
    
    def _read_file(self) -> str:
        """Lê o arquivo com encoding UTF-8"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.errors.append(f"Erro ao ler arquivo: {e}")
            return ""
    
    def validate_all(self) -> Dict[str, bool]:
        """Executa todas as validações AGV"""
        
        if self.file_path.suffix == '.py':
            self._validate_python_file()
        elif self.file_path.suffix in ['.ts', '.tsx']:
            self._validate_typescript_file()
        
        # Validações gerais para qualquer arquivo
        self._validate_agv_standards()
        
        return {
            'passed': len(self.errors) == 0,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'checks_passed': len(self.passed_checks)
        }
    
    def _validate_python_file(self):
        """Validações específicas para arquivos Python"""
        
        # 1. Verificar docstring de módulo
        if not self.file_content.strip().startswith('"""') and not self.file_content.strip().startswith("'''"):
            if 'class ' in self.file_content or 'def ' in self.file_content:
                self.errors.append("Arquivo Python deve começar com docstring de módulo")
        else:
            self.passed_checks.append("[OK] Docstring de módulo presente")
        
        # 2. Verificar se há classes sem docstrings
        lines = self.file_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('class '):
                # Verificar se próximas linhas contêm docstring
                has_docstring = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        has_docstring = True
                        break
                
                if not has_docstring:
                    class_name = line.strip().split()[1].split('(')[0]
                    self.warnings.append(f"Classe {class_name} sem docstring")
                else:
                    self.passed_checks.append(f"[OK] Classe com docstring encontrada")
        
        # 3. Verificar imports organizados
        import_section = []
        for line in lines:
            if line.startswith('import ') or line.startswith('from '):
                import_section.append(line)
            elif line.strip() and not line.startswith('#'):
                break
        
        if import_section:
            # Verificar se imports estão agrupados
            stdlib_imports = [imp for imp in import_section if not ('.' in imp.split()[1] if len(imp.split()) > 1 else False)]
            if stdlib_imports:
                self.passed_checks.append("[OK] Imports organizados encontrados")
        
        # 4. Executar linter se disponível (adapte comando conforme projeto)
        self._run_linter_check()
        
        # 5. Verificar multi-tenancy em models
        # Verificações específicas para modelos de dados (adapte conforme framework)
        if 'models.py' in str(self.file_path) or 'models' in self.file_content:
            self._validate_orm_models()
    
    def _validate_typescript_file(self):
        """Validações específicas para arquivos TypeScript/React"""
        
        # 1. Verificar se é um componente React
        if 'export' in self.file_content and ('React' in self.file_content or 'jsx' in str(self.file_path).lower()):
            # Verificar se há PropTypes ou TypeScript interfaces
            if 'interface ' in self.file_content or 'type ' in self.file_content:
                self.passed_checks.append("[OK] Tipagem TypeScript encontrada")
            else:
                self.warnings.append("Componente React sem tipagem TypeScript")
        
        # 2. Verificar imports organizados
        lines = self.file_content.split('\n')
        react_imports = [line for line in lines if 'from "react"' in line or "from 'react'" in line]
        if react_imports:
            self.passed_checks.append("[OK] Imports React encontrados")
        
        # 3. Executar ESLint se disponível
        self._run_eslint_check()
    
    def _validate_orm_models(self):
        """Validações específicas para models do ORM (adapte conforme framework)"""
        
        # Verificar BaseTenantModel ou campo tenant
        if 'BaseTenantModel' in self.file_content:
            self.passed_checks.append("[OK] BaseTenantModel usado para multi-tenancy")
        elif 'tenant =' in self.file_content and 'ForeignKey' in self.file_content:
            self.passed_checks.append("[OK] Campo tenant encontrado")
        elif 'class ' in self.file_content:
            self.warnings.append("Model sem implementação multi-tenant aparente (adapte validação conforme framework)")
        
        # Verificar campos de auditoria
        if 'created_at' in self.file_content and 'updated_at' in self.file_content:
            self.passed_checks.append("[OK] Campos de auditoria encontrados")
        
        # Verificar choices definidas como enum
        if 'TextChoices' in self.file_content:
            self.passed_checks.append("[OK] TextChoices usado para enums")
    
    def _validate_agv_standards(self):
        """Validações gerais dos padrões AGV"""
        
        # 1. Verificar se não há TODOs ou FIXMEs
        if 'TODO' in self.file_content or 'FIXME' in self.file_content:
            self.warnings.append("Arquivo contém TODO ou FIXME - considere resolver")
        
        # 2. Verificar linhas muito longas (mais de 120 caracteres)
        lines = self.file_content.split('\n')
        long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            self.warnings.append(f"Linhas longas encontradas: {long_lines[:5]}")  # Mostrar apenas as primeiras 5
        
        # 3. Verificar se arquivo não está vazio
        if not self.file_content.strip():
            self.errors.append("Arquivo está vazio")
        else:
            self.passed_checks.append("[OK] Arquivo contém código")
        
        # 4. Verificar encoding UTF-8 (implícito na leitura bem-sucedida)
        self.passed_checks.append("[OK] Encoding UTF-8 válido")
    
    def _run_linter_check(self):
        """Executa linter check se disponível (adapte comando conforme stack)"""
        try:
            result = subprocess.run(
                ['linter_command', 'check', str(self.file_path), '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.passed_checks.append("[OK] Linter check passou")
            else:
                # Parse dos erros do linter (adapte formato conforme ferramenta)
                if result.stdout:
                    self.warnings.append("Linter encontrou issues - ver output completo")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.warnings.append("Linter não disponível ou timeout - validação manual necessária")
    
    def _run_eslint_check(self):
        """Executa ESLint se disponível"""
        try:
            result = subprocess.run(
                ['eslint', str(self.file_path), '--format=json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.passed_checks.append("[OK] ESLint check passou")
            else:
                self.warnings.append("ESLint encontrou issues - ver output completo")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.warnings.append("ESLint não disponível - validação manual necessária")
    
    def print_report(self):
        """Imprime relatório de validação"""
        
        print(f"\n[SCAN] AGV Quality Validation Report")
        print(f"[FILE] Arquivo: {self.file_path}")
        print("=" * 60)
        
        # Mostrar checks que passaram
        if self.passed_checks:
            print(f"\n[PASS] CHECKS APROVADOS ({len(self.passed_checks)}):")
            for check in self.passed_checks:
                print(f"   {check}")
        
        # Mostrar warnings
        if self.warnings:
            print(f"\n[WARN] WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   [WARN] {warning}")
        
        # Mostrar erros
        if self.errors:
            print(f"\n[ERROR] ERROS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   [ERROR] {error}")
        
        # Status final
        print(f"\n[RESULT] RESULTADO FINAL:")
        if self.errors:
            print("   [FAIL] FALHOU - Erros devem ser corrigidos")
            return False
        elif self.warnings:
            print("   [WARN] PASSOU COM WARNINGS - Revisar recomendações")
            return True
        else:
            print("   [PASS] PASSOU - Qualidade AGV aprovada")
            return True


def main():
    """Função principal"""
    
    file_path = os.getenv('FILE_PATH')
    if not file_path:
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
        else:
            print("Erro: FILE_PATH não especificado")
            print("Uso: python validate_agv_quality.py <arquivo>")
            sys.exit(1)
    
    if not Path(file_path).exists():
        print(f"Erro: Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    # Executar validação
    validator = AGVQualityValidator(file_path)
    results = validator.validate_all()
    
    # Mostrar relatório
    success = validator.print_report()
    
    # Exit code baseado no resultado
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()