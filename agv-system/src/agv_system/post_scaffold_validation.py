#!/usr/bin/env python3
"""
Post-Scaffold Validation Hook v5.0
Hook automático executado após scaffold para validação profunda.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Hook principal executado após scaffold"""
    print("\n" + "="*60)
    print("HOOK: VALIDACAO AUTOMATICA POS-SCAFFOLD")  
    print("="*60)
    
    # Executar validação profunda
    try:
        result = subprocess.run([
            sys.executable, 
            "validate_scaffold.py"
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        # Mostrar output da validação
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
            
        # Verificar se passou
        if result.returncode == 0:
            print("\nHOOK RESULTADO: SCAFFOLD APROVADO")
            print("Prosseguir para proximo alvo quando pronto.")
            return True
        else:
            print("\nHOOK RESULTADO: SCAFFOLD REJEITADO")
            print("Corrigir problemas antes de prosseguir para implementacao.")
            return False
            
    except Exception as e:
        print(f"\nERRO no hook de validacao: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)