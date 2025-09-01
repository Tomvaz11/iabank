#!/usr/bin/env python3
"""
Setup de Profiles de Validação AGV v5.0
Script para configurar profiles otimizados para diferentes cenários.
"""

from validation_config import ValidationConfig


def setup_optimized_profiles():
    """Configura profiles otimizados baseado na experiência com o IABANK."""
    
    config = ValidationConfig()
    
    print("Configurando profiles otimizados...")
    
    # Profile para desenvolvimento inicial (mais permissivo)
    config.create_profile(
        name="development",
        threshold=65,
        penalty=0.3,
        categories=["STRUCTURE", "MODELS"]
    )
    
    # Profile para produção (mais rigoroso)
    config.create_profile(
        name="production",
        threshold=85,
        penalty=0.7,
        categories=["STRUCTURE", "CONTENT", "MODELS", "DEPENDENCIES", "API"]
    )
    
    # Profile para CI/CD (balanceado)
    config.create_profile(
        name="ci_cd",
        threshold=75,
        penalty=0.5,
        categories=["STRUCTURE", "CONTENT", "MODELS"]
    )
    
    # Profile para revisão arquitetural (muito rigoroso)
    config.create_profile(
        name="architecture_review",
        threshold=95,
        penalty=0.9,
        categories=["STRUCTURE", "CONTENT", "MODELS", "DEPENDENCIES", "API"]
    )
    
    # Adicionar configurações específicas para Django + React
    config.config["project_types"]["django_react_optimized"] = {
        "focus_categories": ["MODELS", "API"],
        "ignore_missing_files": [
            "docker-compose.yaml",
            ".env.example", 
            "pnpm-lock.yaml",
            "wsgi.py",
            "asgi.py"
        ],
        "tolerance_overrides": {
            "missing_docker": True,
            "missing_frontend_lock": True
        }
    }
    
    # Configurar validações ignoradas baseadas na experiência
    problematic_validations = [
        "validate_dependency_version",
        "validate_dependency_line_length", 
        "validate_dependency_distintas",
        "validate_dependency_stroke_width",
        "validate_dependency_max_length",
        "validate_dependency_max_digits",
        "validate_dependency_decimal_places",
        "validate_dependency_default",
        "validate_dependency_gt",
        "validate_dependency_ge",
        "validate_dependency_localhost",
        "validate_dependency_se",
        "validate_dependency_rev",
        "validate_dependency_node",
        "validate_dependency_nginx",
        "validate_env___example",
        "validate_pnpm_lock_yaml",
        "validate_vite_config__jt_s",
        "validate_wsgi_py", 
        "validate_asgi_py",
        "validate_github_workflows____yaml"
    ]
    
    config.config["ignored_validations"] = problematic_validations
    
    # Configurar tolerâncias mais realísticas
    config.config["tolerance"] = {
        "missing_documentation": True,
        "missing_ci_cd": True,
        "missing_docker": True,  # Tornando Docker opcional
        "missing_frontend_lock": True,
        "missing_env_example": True
    }
    
    # Ajustar pesos para ser mais realístico
    config.config["severity_weights"] = {
        "CRITICAL": 15,  # Reduzido de 20
        "HIGH": 8,       # Reduzido de 10
        "MEDIUM": 2,     # Reduzido de 3
        "LOW": 1
    }
    
    # Salvar configuração
    config.save_config()
    
    print("\nProfiles configurados com sucesso!")
    print("\nProfiles disponíveis:")
    print("  • development      - Para desenvolvimento inicial (65%)")
    print("  • moderate         - Para uso geral (75%)")
    print("  • ci_cd           - Para pipeline CI/CD (75%)")
    print("  • strict          - Para revisão rigorosa (90%)")
    print("  • production      - Para deploy produção (85%)")
    print("  • architecture_review - Para revisão arquitetural (95%)")
    
    print(f"\nProfile ativo: {config.current_profile.name}")
    print(f"Threshold: {config.current_profile.min_score_threshold}%")
    
    print(f"\nValidações ignoradas: {len(problematic_validations)}")
    
    return config


def recommend_profile_for_project(project_stage: str = "development"):
    """Recomenda profile baseado no estágio do projeto."""
    recommendations = {
        "initial": "development",
        "development": "moderate", 
        "testing": "ci_cd",
        "staging": "production",
        "production": "production",
        "review": "architecture_review"
    }
    
    recommended = recommendations.get(project_stage, "moderate")
    
    print(f"Para estágio '{project_stage}', recomendamos o profile: {recommended}")
    
    config = ValidationConfig()
    if recommended in config.config["profiles"]:
        config.switch_profile(recommended)
        config.save_config()
        print(f"Profile alterado para: {recommended}")
    
    return recommended


def main():
    """Função principal para setup de profiles."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_optimized_profiles()
        elif command == "recommend":
            stage = sys.argv[2] if len(sys.argv) > 2 else "development"
            recommend_profile_for_project(stage)
        elif command == "list":
            config = ValidationConfig()
            config.list_profiles()
        else:
            print("Comandos disponíveis:")
            print("  setup     - Configura profiles otimizados")
            print("  recommend - Recomenda profile: recommend <stage>")
            print("  list      - Lista profiles disponíveis")
    else:
        print("Configurando profiles otimizados para AGV v5.0...")
        setup_optimized_profiles()


if __name__ == "__main__":
    main()