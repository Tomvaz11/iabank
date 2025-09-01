#!/usr/bin/env python3
"""
Setup script para o sistema AGV v5.0.
Instala o sistema em modo desenvolvimento e configura o ambiente.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Executa comando e reporta resultado."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True
        else:
            print(f"❌ {description} - Erro: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False


def setup_agv_system():
    """Configura o sistema AGV v5.0."""
    
    print("🚀 Configurando Sistema AGV v5.0")
    print("=" * 50)
    
    # Verificar Python
    python_version = sys.version_info
    if python_version < (3, 9):
        print(f"❌ Python {python_version.major}.{python_version.minor} não suportado. Necessário Python 3.9+")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} - OK")
    
    # Instalar em modo desenvolvimento
    success = run_command(
        "pip install -e .",
        "Instalando pacote AGV em modo desenvolvimento"
    )
    
    if not success:
        return False
    
    # Instalar dependências de desenvolvimento
    success = run_command(
        "pip install -e .[dev]",
        "Instalando dependências de desenvolvimento"
    )
    
    if not success:
        print("⚠️  Dependências dev opcionais falharam, continuando...")
    
    # Criar diretórios necessários
    directories = ["logs", ".agv_cache", "metrics", "tests"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Diretório criado: {directory}")
    
    # Configurar pre-commit se disponível
    if Path(".pre-commit-config.yaml").exists():
        run_command("pre-commit install", "Configurando pre-commit hooks")
    
    # Testar importações
    print("\n🧪 Testando importações...")
    try:
        from scripts import ModularValidatorGenerator, get_logger, get_cache, get_metrics_collector
        print("✅ Importações principais - OK")
        
        # Teste básico
        logger = get_logger("setup_test")
        logger.info("Sistema AGV configurado com sucesso!")
        print("✅ Logging - OK")
        
        cache = get_cache()
        cache.set("test", "ok")
        result = cache.get("test")
        assert result == "ok"
        print("✅ Cache - OK")
        
        metrics = get_metrics_collector()
        metrics.record_counter("setup.test", 1)
        print("✅ Métricas - OK")
        
    except Exception as e:
        print(f"❌ Teste de importação falhou: {e}")
        return False
    
    print("\n🎉 Sistema AGV v5.0 configurado com sucesso!")
    print("\nComandos disponíveis:")
    print("  agv-validator <blueprint.md> scaffold")
    print("  agv-validator <blueprint.md> target --target-number 3")
    print("  agv-context <blueprint.md> --target 3")
    print("\nPython imports:")
    print("  from scripts import ModularValidatorGenerator")
    print("  from scripts.core import get_logger, get_cache, get_metrics_collector")
    
    return True


if __name__ == "__main__":
    success = setup_agv_system()
    sys.exit(0 if success else 1)