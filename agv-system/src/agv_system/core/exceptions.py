#!/usr/bin/env python3
"""
Exceções personalizadas para o sistema AGV v5.0.
Hierarquia de exceções específicas para melhor debugging e tratamento de erros.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ErrorContext:
    """Contexto adicional para exceções."""
    component: str
    operation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = None


class AGVException(Exception):
    """Exceção base para todas as exceções do sistema AGV."""
    
    def __init__(
        self, 
        message: str, 
        context: Optional[ErrorContext] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.context = context
        self.original_exception = original_exception
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Formata mensagem de erro com contexto."""
        formatted = f"AGV Error: {self.message}"
        
        if self.context:
            formatted += f"\n  Component: {self.context.component}"
            formatted += f"\n  Operation: {self.context.operation}"
            
            if self.context.file_path:
                formatted += f"\n  File: {self.context.file_path}"
                
            if self.context.line_number:
                formatted += f"\n  Line: {self.context.line_number}"
                
            if self.context.additional_info:
                for key, value in self.context.additional_info.items():
                    formatted += f"\n  {key}: {value}"
        
        if self.original_exception:
            formatted += f"\n  Original: {type(self.original_exception).__name__}: {self.original_exception}"
        
        return formatted


# === BLUEPRINT PARSING EXCEPTIONS ===

class BlueprintException(AGVException):
    """Exceção base para erros de Blueprint."""
    pass


class BlueprintFileNotFoundError(BlueprintException):
    """Blueprint arquivo não encontrado."""
    
    def __init__(self, blueprint_path: str):
        context = ErrorContext(
            component="BlueprintParser",
            operation="read_blueprint",
            file_path=blueprint_path,
            additional_info={"expected_path": blueprint_path}
        )
        super().__init__(f"Blueprint file not found: {blueprint_path}", context)


class BlueprintParseError(BlueprintException):
    """Erro no parsing do Blueprint."""
    
    def __init__(self, message: str, section: Optional[str] = None, line_number: Optional[int] = None):
        context = ErrorContext(
            component="BlueprintParser",
            operation="parse_blueprint",
            line_number=line_number,
            additional_info={"section": section} if section else None
        )
        super().__init__(f"Blueprint parsing failed: {message}", context)


class InvalidBlueprintStructureError(BlueprintException):
    """Estrutura inválida no Blueprint."""
    
    def __init__(self, expected: str, found: str, section: str):
        context = ErrorContext(
            component="BlueprintParser",
            operation="validate_structure",
            additional_info={
                "expected": expected,
                "found": found,
                "section": section
            }
        )
        super().__init__(f"Invalid Blueprint structure in section '{section}'", context)


# === VALIDATION EXCEPTIONS ===

class ValidationException(AGVException):
    """Exceção base para erros de validação."""
    pass


class ValidationGenerationError(ValidationException):
    """Erro na geração de validador."""
    
    def __init__(self, generator_type: str, reason: str, target: Optional[str] = None):
        context = ErrorContext(
            component="ValidatorGenerator",
            operation="generate_validator",
            additional_info={
                "generator_type": generator_type,
                "target": target,
                "reason": reason
            }
        )
        super().__init__(f"Failed to generate {generator_type} validator: {reason}", context)


class ValidationRuleError(ValidationException):
    """Erro na criação de regra de validação."""
    
    def __init__(self, rule_name: str, error_details: str):
        context = ErrorContext(
            component="ValidationRule",
            operation="create_rule",
            additional_info={
                "rule_name": rule_name,
                "error_details": error_details
            }
        )
        super().__init__(f"Validation rule '{rule_name}' creation failed", context)


class ValidationExecutionError(ValidationException):
    """Erro durante execução de validação."""
    
    def __init__(self, validator_name: str, rule_name: str, error_details: str):
        context = ErrorContext(
            component="ValidatorExecution",
            operation="execute_validation",
            additional_info={
                "validator_name": validator_name,
                "rule_name": rule_name,
                "error_details": error_details
            }
        )
        super().__init__(f"Validation execution failed in rule '{rule_name}'", context)


# === GENERATOR EXCEPTIONS ===

class GeneratorException(AGVException):
    """Exceção base para erros de geradores."""
    pass


class ScaffoldGenerationError(GeneratorException):
    """Erro na geração de scaffold."""
    
    def __init__(self, operation: str, details: str):
        context = ErrorContext(
            component="ScaffoldGenerator",
            operation=operation,
            additional_info={"details": details}
        )
        super().__init__(f"Scaffold generation failed during {operation}", context)


class TargetGenerationError(GeneratorException):
    """Erro na geração de alvo."""
    
    def __init__(self, target_number: int, operation: str, details: str):
        context = ErrorContext(
            component="TargetGenerator",
            operation=operation,
            additional_info={
                "target_number": target_number,
                "details": details
            }
        )
        super().__init__(f"Target {target_number} generation failed during {operation}", context)


class IntegrationGenerationError(GeneratorException):
    """Erro na geração de integração."""
    
    def __init__(self, integration_phase: str, operation: str, details: str):
        context = ErrorContext(
            component="IntegrationGenerator", 
            operation=operation,
            additional_info={
                "integration_phase": integration_phase,
                "details": details
            }
        )
        super().__init__(f"Integration {integration_phase} generation failed during {operation}", context)


class EvolutionGenerationError(GeneratorException):
    """Erro na geração de evolução."""
    
    def __init__(self, operation: str, details: str):
        context = ErrorContext(
            component="EvolutionGenerator",
            operation=operation,
            additional_info={"details": details}
        )
        super().__init__(f"Evolution generation failed during {operation}", context)


# === CONTEXT EXCEPTIONS ===

class ContextException(AGVException):
    """Exceção base para erros de contexto."""
    pass


class ContextExtractionError(ContextException):
    """Erro na extração de contexto."""
    
    def __init__(self, target: str, reason: str):
        context = ErrorContext(
            component="ContextExtractor",
            operation="extract_context",
            additional_info={
                "target": target,
                "reason": reason
            }
        )
        super().__init__(f"Context extraction failed for {target}", context)


class ContextInjectionError(ContextException):
    """Erro na injeção de contexto."""
    
    def __init__(self, target: str, reason: str):
        context = ErrorContext(
            component="ContextInjector",
            operation="inject_context",
            additional_info={
                "target": target, 
                "reason": reason
            }
        )
        super().__init__(f"Context injection failed for {target}", context)


# === FILE SYSTEM EXCEPTIONS ===

class FileSystemException(AGVException):
    """Exceção base para erros de sistema de arquivos."""
    pass


class FileCreationError(FileSystemException):
    """Erro na criação de arquivo."""
    
    def __init__(self, file_path: str, reason: str):
        context = ErrorContext(
            component="FileSystem",
            operation="create_file",
            file_path=file_path,
            additional_info={"reason": reason}
        )
        super().__init__(f"Failed to create file: {file_path}", context)


class FileReadError(FileSystemException):
    """Erro na leitura de arquivo."""
    
    def __init__(self, file_path: str, reason: str):
        context = ErrorContext(
            component="FileSystem",
            operation="read_file",
            file_path=file_path,
            additional_info={"reason": reason}
        )
        super().__init__(f"Failed to read file: {file_path}", context)


class DirectoryCreationError(FileSystemException):
    """Erro na criação de diretório."""
    
    def __init__(self, dir_path: str, reason: str):
        context = ErrorContext(
            component="FileSystem",
            operation="create_directory",
            file_path=dir_path,
            additional_info={"reason": reason}
        )
        super().__init__(f"Failed to create directory: {dir_path}", context)


# === CONFIGURATION EXCEPTIONS ===

class ConfigurationException(AGVException):
    """Exceção base para erros de configuração."""
    pass


class InvalidConfigurationError(ConfigurationException):
    """Configuração inválida."""
    
    def __init__(self, config_name: str, expected: str, actual: str):
        context = ErrorContext(
            component="Configuration",
            operation="validate_config",
            additional_info={
                "config_name": config_name,
                "expected": expected,
                "actual": actual
            }
        )
        super().__init__(f"Invalid configuration for {config_name}", context)


class MissingConfigurationError(ConfigurationException):
    """Configuração obrigatória ausente."""
    
    def __init__(self, config_name: str, location: str):
        context = ErrorContext(
            component="Configuration",
            operation="load_config",
            additional_info={
                "config_name": config_name,
                "location": location
            }
        )
        super().__init__(f"Missing required configuration: {config_name}", context)


# === DEPENDENCY EXCEPTIONS ===

class DependencyException(AGVException):
    """Exceção base para erros de dependências."""
    pass


class MissingDependencyError(DependencyException):
    """Dependência obrigatória ausente."""
    
    def __init__(self, dependency_name: str, required_version: Optional[str] = None):
        context = ErrorContext(
            component="DependencyManager",
            operation="check_dependency",
            additional_info={
                "dependency_name": dependency_name,
                "required_version": required_version
            }
        )
        message = f"Missing required dependency: {dependency_name}"
        if required_version:
            message += f" (version {required_version})"
        super().__init__(message, context)


class IncompatibleDependencyError(DependencyException):
    """Versão de dependência incompatível."""
    
    def __init__(self, dependency_name: str, current_version: str, required_version: str):
        context = ErrorContext(
            component="DependencyManager",
            operation="validate_dependency",
            additional_info={
                "dependency_name": dependency_name,
                "current_version": current_version,
                "required_version": required_version
            }
        )
        super().__init__(f"Incompatible version for {dependency_name}", context)


# === UTILITY FUNCTIONS ===

def handle_exception(
    func_name: str,
    component: str,
    original_exception: Exception,
    additional_context: Optional[Dict[str, Any]] = None
) -> AGVException:
    """
    Converte exceção genérica em exceção AGV específica.
    
    Args:
        func_name: Nome da função onde ocorreu o erro
        component: Nome do componente
        original_exception: Exceção original
        additional_context: Contexto adicional
    
    Returns:
        Exceção AGV apropriada
    """
    context = ErrorContext(
        component=component,
        operation=func_name,
        additional_info=additional_context
    )
    
    # Mapear tipos de exceção comum
    if isinstance(original_exception, FileNotFoundError):
        if "Blueprint" in str(original_exception):
            return BlueprintFileNotFoundError(str(original_exception))
        else:
            return FileReadError(str(original_exception), str(original_exception))
    
    elif isinstance(original_exception, PermissionError):
        return FileSystemException(
            f"Permission denied: {original_exception}",
            context,
            original_exception
        )
    
    elif isinstance(original_exception, (ValueError, TypeError)):
        return ValidationException(
            f"Invalid data: {original_exception}",
            context,
            original_exception
        )
    
    else:
        return AGVException(
            f"Unexpected error in {func_name}: {original_exception}",
            context,
            original_exception
        )


# Exemplo de uso
if __name__ == "__main__":
    # Exemplos de exceções
    try:
        raise BlueprintFileNotFoundError("BLUEPRINT.md")
    except AGVException as e:
        print("Blueprint Error:")
        print(e)
        print()
    
    try:
        raise TargetGenerationError(3, "model_creation", "Missing Loan model definition")
    except AGVException as e:
        print("Target Generation Error:")
        print(e)
        print()
    
    try:
        # Simular erro genérico
        raise FileNotFoundError("test.py")
    except Exception as e:
        agv_exception = handle_exception("test_function", "TestComponent", e)
        print("Handled Generic Error:")
        print(agv_exception)