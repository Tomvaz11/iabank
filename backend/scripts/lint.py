#!/usr/bin/env python3
"""
IABANK Backend - Script de automação para linting e formatação
Script Python para executar ferramentas de qualidade de código
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


class Colors:
    """Cores ANSI para output colorido"""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    RESET = '\033[0m'


class CodeQualityRunner:
    """Runner para ferramentas de qualidade de código"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.source_dir = self.project_root / "src"
        self.test_dir = self.project_root / "tests"

    def run_command(self, command: List[str], description: str) -> bool:
        """Executa um comando e retorna True se bem-sucedido"""
        print(f"{Colors.BLUE}[INFO] {description}...{Colors.RESET}")

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                print(f"{Colors.GREEN}[OK] {description} concluído com sucesso{Colors.RESET}")
                if result.stdout.strip():
                    print(result.stdout)
                return True
            else:
                print(f"{Colors.RED}[ERROR] {description} falhou{Colors.RESET}")
                if result.stderr:
                    print(f"{Colors.RED}Erro:{Colors.RESET} {result.stderr}")
                if result.stdout:
                    print(f"{Colors.YELLOW}Output:{Colors.RESET} {result.stdout}")
                return False

        except FileNotFoundError:
            print(f"{Colors.RED}[ERROR] Comando não encontrado: {' '.join(command)}{Colors.RESET}")
            print(f"{Colors.YELLOW}[TIP] Certifique-se de que as dependências estão instaladas: pip install -r requirements.txt{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Erro inesperado: {e}{Colors.RESET}")
            return False

    def run_ruff_check(self, fix: bool = False) -> bool:
        """Executa ruff para linting"""
        command = ["ruff", "check", str(self.source_dir), str(self.test_dir)]
        if fix:
            command.append("--fix")

        description = "Ruff linting" + (" com correção automática" if fix else "")
        return self.run_command(command, description)

    def run_black(self, check_only: bool = False) -> bool:
        """Executa black para formatação"""
        command = ["black"]
        if check_only:
            command.append("--check")
        command.extend([str(self.source_dir), str(self.test_dir)])

        description = "Black formatação" + (" (verificação apenas)" if check_only else "")
        return self.run_command(command, description)

    def run_mypy(self) -> bool:
        """Executa mypy para verificação de tipos"""
        command = ["mypy", str(self.source_dir)]
        return self.run_command(command, "MyPy verificação de tipos")

    def run_tests(self, test_type: Optional[str] = None, coverage: bool = False) -> bool:
        """Executa testes com pytest"""
        command = ["pytest"]

        if coverage:
            command.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:coverage_html"
            ])

        if test_type:
            command.extend(["-m", test_type])

        description = f"Testes pytest"
        if test_type:
            description += f" ({test_type})"
        if coverage:
            description += " com cobertura"

        return self.run_command(command, description)

    def run_quality_checks(self, fix: bool = False) -> bool:
        """Executa todas as verificações de qualidade"""
        print(f"{Colors.BLUE}[INFO] Executando verificações de qualidade de código{Colors.RESET}")

        success = True
        success &= self.run_ruff_check(fix=fix)
        success &= self.run_black(check_only=not fix)
        success &= self.run_mypy()

        if success:
            print(f"{Colors.GREEN}[SUCCESS] Todas as verificações de qualidade passaram!{Colors.RESET}")
        else:
            print(f"{Colors.RED}[ERROR] Algumas verificações falharam{Colors.RESET}")

        return success

    def run_full_check(self) -> bool:
        """Executa verificação completa: qualidade + testes"""
        print(f"{Colors.BLUE}[INFO] Executando verificação completa{Colors.RESET}")

        success = True
        success &= self.run_quality_checks(fix=True)
        success &= self.run_tests(coverage=True)

        if success:
            print(f"{Colors.GREEN}[SUCCESS] VERIFICAÇÃO COMPLETA PASSOU!{Colors.RESET}")
        else:
            print(f"{Colors.RED}[ERROR] Verificação completa falhou{Colors.RESET}")

        return success


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="IABANK Backend - Ferramentas de qualidade de código",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python scripts/lint.py --lint              # Apenas linting
  python scripts/lint.py --format            # Apenas formatação
  python scripts/lint.py --typecheck         # Apenas verificação de tipos
  python scripts/lint.py --quality           # Todas as verificações de qualidade
  python scripts/lint.py --quality --fix     # Com correção automática
  python scripts/lint.py --test              # Apenas testes
  python scripts/lint.py --test --coverage   # Testes com cobertura
  python scripts/lint.py --full              # Verificação completa
  python scripts/lint.py --test-unit         # Apenas testes unitários
        """
    )

    # Opções de verificação
    parser.add_argument("--lint", action="store_true", help="Executar ruff linting")
    parser.add_argument("--format", action="store_true", help="Executar black formatação")
    parser.add_argument("--typecheck", action="store_true", help="Executar mypy verificação de tipos")
    parser.add_argument("--quality", action="store_true", help="Executar todas as verificações de qualidade")

    # Opções de teste
    parser.add_argument("--test", action="store_true", help="Executar testes")
    parser.add_argument("--test-unit", action="store_true", help="Executar apenas testes unitários")
    parser.add_argument("--test-integration", action="store_true", help="Executar apenas testes de integração")
    parser.add_argument("--test-contract", action="store_true", help="Executar apenas testes de contrato")
    parser.add_argument("--test-tenant", action="store_true", help="Executar testes de isolamento de tenant")

    # Opções modificadoras
    parser.add_argument("--fix", action="store_true", help="Aplicar correções automáticas quando possível")
    parser.add_argument("--coverage", action="store_true", help="Incluir relatório de cobertura nos testes")
    parser.add_argument("--check-only", action="store_true", help="Apenas verificar, não modificar arquivos")

    # Opção all-in-one
    parser.add_argument("--full", action="store_true", help="Executar verificação completa (qualidade + testes)")

    args = parser.parse_args()

    # Se nenhum argumento foi passado, mostrar ajuda
    if not any(vars(args).values()):
        parser.print_help()
        return 1

    runner = CodeQualityRunner()
    success = True

    try:
        if args.full:
            success = runner.run_full_check()
        else:
            if args.lint:
                success &= runner.run_ruff_check(fix=args.fix and not args.check_only)

            if args.format:
                success &= runner.run_black(check_only=args.check_only)

            if args.typecheck:
                success &= runner.run_mypy()

            if args.quality:
                success &= runner.run_quality_checks(fix=args.fix and not args.check_only)

            if args.test:
                success &= runner.run_tests(coverage=args.coverage)

            if args.test_unit:
                success &= runner.run_tests(test_type="unit", coverage=args.coverage)

            if args.test_integration:
                success &= runner.run_tests(test_type="integration", coverage=args.coverage)

            if args.test_contract:
                success &= runner.run_tests(test_type="contract", coverage=args.coverage)

            if args.test_tenant:
                success &= runner.run_tests(test_type="tenant_isolation", coverage=args.coverage)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[WARNING] Operação cancelada pelo usuário{Colors.RESET}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())