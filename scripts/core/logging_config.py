#!/usr/bin/env python3
"""
LoggingConfig - Sistema de logging estruturado para AGV v5.0.
Implementa logging profissional com múltiplos handlers e formatação consistente.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class LogEvent:
    """Evento de log estruturado."""
    timestamp: str
    level: str
    component: str
    message: str
    context: Dict[str, Any]
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)


class StructuredFormatter(logging.Formatter):
    """Formatter personalizado para logs estruturados."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata record como JSON estruturado."""
        # Extrair contexto adicional se existir
        context = getattr(record, 'context', {})
        duration_ms = getattr(record, 'duration_ms', None)
        error = getattr(record, 'error', None)
        
        log_event = LogEvent(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            component=record.name,
            message=record.getMessage(),
            context=context,
            duration_ms=duration_ms,
            error=error
        )
        
        return json.dumps(log_event.to_dict(), ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Formatter para console mais legível."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata record para console com cores."""
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        component = record.name.split('.')[-1]  # Apenas o último componente
        
        # Contexto adicional se existir
        context = getattr(record, 'context', {})
        duration_ms = getattr(record, 'duration_ms', None)
        
        base_msg = f"[{timestamp}] {color}{record.levelname:8}{reset} {component:15} {record.getMessage()}"
        
        # Adicionar contexto se relevante
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            base_msg += f" | {context_str}"
            
        if duration_ms:
            base_msg += f" | {duration_ms:.2f}ms"
        
        return base_msg


class AGVLogger:
    """Logger principal do sistema AGV v5.0."""
    
    _instance: Optional['AGVLogger'] = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls) -> 'AGVLogger':
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa sistema de logging."""
        if self._initialized:
            return
            
        self._initialized = True
        self.setup_logging()
    
    def setup_logging(self):
        """Configura handlers e formatters."""
        # Criar diretório de logs
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Configuração root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)
        
        # File Handler para logs estruturados
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / 'agv.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
        
        # Error File Handler separado
        error_handler = logging.handlers.RotatingFileHandler(
            logs_dir / 'agv-errors.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Obtém logger para componente específico."""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(f"agv.{name}")
        return self._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Função helper para obter logger."""
    agv_logger = AGVLogger()
    return agv_logger.get_logger(name)


class LogContext:
    """Context manager para logging com contexto adicional."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        """Inicia operação."""
        self.start_time = datetime.now()
        self.logger.info(
            f"Starting {self.operation}",
            extra={'context': self.context}
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza operação."""
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        
        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                extra={
                    'context': self.context,
                    'duration_ms': duration_ms
                }
            )
        else:
            self.logger.error(
                f"Failed {self.operation}",
                extra={
                    'context': self.context,
                    'duration_ms': duration_ms,
                    'error': str(exc_val)
                }
            )
    
    def log(self, level: str, message: str, **extra_context):
        """Log com contexto atual."""
        full_context = {**self.context, **extra_context}
        getattr(self.logger, level.lower())(
            message,
            extra={'context': full_context}
        )


# Loggers pré-configurados para componentes principais
validator_logger = get_logger("validator")
parser_logger = get_logger("parser") 
generator_logger = get_logger("generator")
scaffold_logger = get_logger("scaffold")
target_logger = get_logger("target")
integration_logger = get_logger("integration")
evolution_logger = get_logger("evolution")


# Exemplo de uso
if __name__ == "__main__":
    # Teste do sistema de logging
    logger = get_logger("test")
    
    logger.info("Sistema de logging inicializado")
    logger.debug("Debug message com contexto", extra={'context': {'user': 'test', 'target': 3}})
    
    # Teste com context manager
    with LogContext(logger, "test_operation", target=3, user="antonio") as ctx:
        ctx.log("info", "Executando operação de teste")
        ctx.log("warning", "Aviso durante operação")
    
    logger.info("Teste finalizado")