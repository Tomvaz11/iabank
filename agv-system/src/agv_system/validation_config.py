#!/usr/bin/env python3
"""
Sistema de Configuração de Validação AGV v5.0
Gerencia profiles e configurações personalizadas do validador.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationProfile:
    """Representa um profile de validação."""
    name: str
    min_score_threshold: float
    max_penalty_factor: float
    required_categories: List[str]
    focus_categories: Optional[List[str]] = None
    ignore_missing_files: Optional[List[str]] = None


class ValidationConfig:
    """Gerenciador de configurações de validação."""
    
    DEFAULT_CONFIG = {
        "validation_profile": "moderate",
        "profiles": {
            "strict": {
                "min_score_threshold": 90,
                "max_penalty_factor": 0.8,
                "required_categories": ["STRUCTURE", "CONTENT", "MODELS", "DEPENDENCIES", "API"]
            },
            "moderate": {
                "min_score_threshold": 75,
                "max_penalty_factor": 0.5,
                "required_categories": ["STRUCTURE", "CONTENT", "MODELS"]
            },
            "permissive": {
                "min_score_threshold": 60,
                "max_penalty_factor": 0.3,
                "required_categories": ["STRUCTURE"]
            }
        },
        "severity_weights": {
            "CRITICAL": 20,
            "HIGH": 10,
            "MEDIUM": 3,
            "LOW": 1
        },
        "category_weights": {
            "STRUCTURE": 1.0,
            "CONTENT": 1.5,
            "MODELS": 2.0,
            "DEPENDENCIES": 1.2,
            "API": 1.3
        },
        "ignored_validations": [],
        "mandatory_validations": [
            "validate_directory_structure",
            "validate_django_models",
            "validate_django_settings_advanced"
        ],
        "tolerance": {
            "missing_documentation": True,
            "missing_ci_cd": True,
            "missing_docker": False
        },
        "output": {
            "encoding": "utf-8",
            "safe_mode": True,
            "detailed_report": True,
            "save_json": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("validation_config.yaml")
        self.config = self._load_config()
        self.current_profile = self._load_profile()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo YAML ou usa padrão."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                # Merge com configuração padrão
                merged_config = self.DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                print(f"Erro ao carregar configuração {self.config_path}: {e}")
                print("Usando configuração padrão...")
        
        return self.DEFAULT_CONFIG.copy()
    
    def _load_profile(self) -> ValidationProfile:
        """Carrega o profile de validação configurado."""
        profile_name = self.config.get("validation_profile", "moderate")
        profile_data = self.config["profiles"].get(profile_name, self.config["profiles"]["moderate"])
        
        # Adicionar configurações específicas do projeto se existirem
        project_type = self.config.get("project_type")
        if project_type and project_type in self.config.get("project_types", {}):
            project_config = self.config["project_types"][project_type]
            profile_data.update(project_config)
        
        return ValidationProfile(
            name=profile_name,
            min_score_threshold=profile_data.get("min_score_threshold", 75),
            max_penalty_factor=profile_data.get("max_penalty_factor", 0.5),
            required_categories=profile_data.get("required_categories", ["STRUCTURE"]),
            focus_categories=profile_data.get("focus_categories"),
            ignore_missing_files=profile_data.get("ignore_missing_files", [])
        )
    
    def get_severity_weights(self) -> Dict[str, int]:
        """Retorna pesos de severidade."""
        return self.config.get("severity_weights", self.DEFAULT_CONFIG["severity_weights"])
    
    def get_category_weights(self) -> Dict[str, float]:
        """Retorna pesos de categoria."""
        return self.config.get("category_weights", self.DEFAULT_CONFIG["category_weights"])
    
    def should_ignore_validation(self, validation_name: str) -> bool:
        """Verifica se uma validação deve ser ignorada."""
        ignored = self.config.get("ignored_validations", [])
        return validation_name in ignored
    
    def is_mandatory_validation(self, validation_name: str) -> bool:
        """Verifica se uma validação é obrigatória."""
        mandatory = self.config.get("mandatory_validations", [])
        return validation_name in mandatory
    
    def should_tolerate_missing_file(self, file_type: str) -> bool:
        """Verifica se deve tolerar arquivo ausente."""
        tolerance = self.config.get("tolerance", {})
        return tolerance.get(file_type, False)
    
    def get_output_config(self) -> Dict[str, Any]:
        """Retorna configurações de output."""
        return self.config.get("output", self.DEFAULT_CONFIG["output"])
    
    def save_config(self):
        """Salva configuração atual em arquivo."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            print(f"Configuração salva em: {self.config_path}")
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
    
    def create_profile(self, name: str, threshold: float = 75, penalty: float = 0.5, 
                      categories: List[str] = None):
        """Cria um novo profile personalizado."""
        if categories is None:
            categories = ["STRUCTURE", "CONTENT"]
        
        self.config["profiles"][name] = {
            "min_score_threshold": threshold,
            "max_penalty_factor": penalty,
            "required_categories": categories
        }
        
        print(f"Profile '{name}' criado com sucesso!")
    
    def switch_profile(self, profile_name: str):
        """Muda para outro profile."""
        if profile_name in self.config["profiles"]:
            self.config["validation_profile"] = profile_name
            self.current_profile = self._load_profile()
            print(f"Profile alterado para: {profile_name}")
        else:
            print(f"Profile '{profile_name}' não encontrado!")
            print(f"Profiles disponíveis: {list(self.config['profiles'].keys())}")
    
    def get_current_threshold(self) -> Dict[str, Any]:
        """Retorna threshold e informações do profile ativo."""
        return {
            'threshold': self.current_profile.min_score_threshold,
            'profile_name': self.current_profile.name,
            'display': f"{self.current_profile.min_score_threshold}% (profile {self.current_profile.name})"
        }
    
    def list_profiles(self):
        """Lista todos os profiles disponíveis."""
        print("Profiles de validação disponíveis:")
        current = self.config.get("validation_profile", "moderate")
        
        for name, config in self.config["profiles"].items():
            marker = " (ATUAL)" if name == current else ""
            print(f"  • {name}{marker}")
            print(f"    - Threshold: {config['min_score_threshold']}%")
            print(f"    - Penalty: {config['max_penalty_factor']}")
            print(f"    - Categorias: {', '.join(config['required_categories'])}")
            print()


def main():
    """Função para gerenciar configurações via CLI."""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python validation_config.py <comando>")
        print("Comandos:")
        print("  list       - Lista profiles disponíveis")
        print("  switch     - Muda profile: switch <nome>")
        print("  create     - Cria profile: create <nome> <threshold> <penalty>")
        print("  threshold  - Mostra threshold atual")
        return
    
    config = ValidationConfig()
    command = sys.argv[1]
    
    if command == "list":
        config.list_profiles()
    elif command == "threshold":
        threshold_info = config.get_current_threshold()
        print(threshold_info['display'])
    elif command == "switch" and len(sys.argv) > 2:
        config.switch_profile(sys.argv[2])
        config.save_config()
    elif command == "create" and len(sys.argv) > 4:
        name = sys.argv[2]
        threshold = float(sys.argv[3])
        penalty = float(sys.argv[4])
        config.create_profile(name, threshold, penalty)
        config.save_config()
    else:
        print("Comando inválido ou parâmetros insuficientes!")


if __name__ == "__main__":
    main()