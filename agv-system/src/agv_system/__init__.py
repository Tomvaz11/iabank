"""
AGV System v5.0 - Método de Desenvolvimento Acelerado com Validação Rigorosa

Este pacote contém todos os componentes do sistema AGV:
- Sistema de geração de validadores modular
- Parsing inteligente de Blueprint
- Cache e métricas avançadas
- Logging estruturado
- Exceções personalizadas

Uso:
    from agv_system.validator_generator import ModularValidatorGenerator
    from agv_system.core.logging_config import get_logger
    from agv_system.core.cache_system import get_cache
    from agv_system.core.metrics import get_metrics_collector
"""

__version__ = "5.0.0"
__author__ = "Antonio"
__email__ = "antonio@iabank.com"

# Imports principais para facilitar uso
from .validator_generator import ModularValidatorGenerator
from .core.logging_config import get_logger
from .core.cache_system import get_cache
from .core.metrics import get_metrics_collector
from .core.exceptions import (
    AGVException,
    BlueprintException,
    ValidationException,
    GeneratorException
)

# Configurar logging do pacote
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "ModularValidatorGenerator",
    "get_logger",
    "get_cache", 
    "get_metrics_collector",
    "AGVException",
    "BlueprintException",
    "ValidationException",
    "GeneratorException",
]