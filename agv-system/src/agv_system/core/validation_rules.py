#!/usr/bin/env python3
"""
ValidationRule and validation utilities shared across all generators.
"""

from dataclasses import dataclass


@dataclass
class ValidationRule:
    """Representa uma regra de validação específica."""
    name: str
    description: str
    code: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # STRUCTURE, CONTENT, DEPENDENCIES, MODELS, API