#!/usr/bin/env python3
"""
Metrics & Analytics - Sistema de métricas avançado para AGV v5.0.
Coleta, analisa e reporta métricas de performance, qualidade e uso.
"""

import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict, field
from functools import wraps
from collections import defaultdict, deque
import threading
import statistics

from .logging_config import get_logger
from .cache_system import get_cache


logger = get_logger("metrics")


@dataclass
class QualityMetrics:
    """Métricas de qualidade de código."""
    coverage_score: float = 0.0
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    code_smells: int = 0
    duplicated_lines_ratio: float = 0.0
    
    def overall_quality_score(self) -> float:
        """Calcula score geral de qualidade."""
        scores = [
            self.coverage_score,
            self.complexity_score,
            self.maintainability_index,
            max(0, 100 - self.technical_debt_ratio * 10)  # Penalizar débito técnico
        ]
        return statistics.mean(scores)


@dataclass
class PerformanceMetrics:
    """Métricas de performance."""
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_io_mb: float = 0.0
    network_io_mb: float = 0.0
    cache_hit_rate: float = 0.0
    
    def performance_score(self) -> float:
        """Calcula score de performance (0-100)."""
        # Normalizar métricas (quanto menor, melhor para tempo/recursos)
        time_score = max(0, 100 - (self.execution_time_ms / 1000) * 2)  # Penalizar > 50s
        memory_score = max(0, 100 - (self.memory_usage_mb / 1024) * 50)  # Penalizar > 2GB
        cpu_score = max(0, 100 - self.cpu_usage_percent)
        cache_score = self.cache_hit_rate
        
        return statistics.mean([time_score, memory_score, cpu_score, cache_score])


@dataclass
class ValidationMetrics:
    """Métricas de validação."""
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    validation_score: float = 0.0
    execution_time_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso das validações."""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_checks / self.total_checks) * 100
    
    @property
    def quality_index(self) -> float:
        """Índice de qualidade baseado na severidade."""
        total_issues = self.critical_issues + self.high_issues + self.medium_issues + self.low_issues
        if total_issues == 0:
            return 100.0
        
        # Peso por severidade
        weighted_issues = (
            self.critical_issues * 10 +
            self.high_issues * 5 +
            self.medium_issues * 2 +
            self.low_issues * 1
        )
        
        # Penalizar proporcionalmente
        penalty = min(100, (weighted_issues / self.total_checks) * 20)
        return max(0, 100 - penalty)


@dataclass
class GeneratorMetrics:
    """Métricas específicas de geradores."""
    generator_type: str = ""
    rules_generated: int = 0
    generation_time_ms: float = 0.0
    blueprint_parsing_time_ms: float = 0.0
    code_generation_time_ms: float = 0.0
    file_size_kb: float = 0.0
    complexity_score: float = 0.0
    
    def efficiency_score(self) -> float:
        """Score de eficiência do gerador."""
        if self.generation_time_ms == 0:
            return 0.0
        
        rules_per_second = (self.rules_generated / self.generation_time_ms) * 1000
        time_score = min(100, rules_per_second * 10)  # 10 regras/seg = score 100
        
        # Penalizar arquivos muito grandes
        size_score = max(0, 100 - (self.file_size_kb / 1024) * 20)  # Penalizar > 5MB
        
        return statistics.mean([time_score, size_score])


@dataclass
class ProjectMetrics:
    """Métricas do projeto como um todo."""
    project_name: str = ""
    timestamp: str = ""
    targets_completed: int = 0
    targets_total: int = 0
    integration_tests_passed: int = 0
    integration_tests_total: int = 0
    overall_coverage: float = 0.0
    overall_quality_score: float = 0.0
    overall_performance_score: float = 0.0
    technical_debt_hours: float = 0.0
    
    @property
    def completion_rate(self) -> float:
        """Taxa de completude do projeto."""
        if self.targets_total == 0:
            return 0.0
        return (self.targets_completed / self.targets_total) * 100
    
    @property
    def integration_success_rate(self) -> float:
        """Taxa de sucesso dos testes de integração."""
        if self.integration_tests_total == 0:
            return 0.0
        return (self.integration_tests_passed / self.integration_tests_total) * 100
    
    def project_health_score(self) -> float:
        """Score geral de saúde do projeto."""
        scores = [
            self.completion_rate,
            self.integration_success_rate,
            self.overall_quality_score,
            self.overall_performance_score,
            self.overall_coverage
        ]
        
        # Penalizar débito técnico alto
        debt_penalty = min(50, self.technical_debt_hours * 2)
        base_score = statistics.mean(scores)
        
        return max(0, base_score - debt_penalty)


class MetricsCollector:
    """Coletor central de métricas."""
    
    def __init__(self, storage_path: Union[str, Path] = "metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self._metrics_buffer: Dict[str, List[Dict]] = defaultdict(list)
        self._timeseries_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()
        
        # Contadores globais
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        
        logger.info(
            "Metrics collector initialized",
            extra={'context': {'storage_path': str(self.storage_path)}}
        )
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Registra contador."""
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            self._counters[full_name] += value
            
            # Adicionar à série temporal
            self._timeseries_data[full_name].append({
                'timestamp': time.time(),
                'value': self._counters[full_name],
                'type': 'counter'
            })
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Registra gauge (valor instantâneo)."""
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            self._gauges[full_name] = value
            
            self._timeseries_data[full_name].append({
                'timestamp': time.time(),
                'value': value,
                'type': 'gauge'
            })
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Registra valor em histograma."""
        with self._lock:
            full_name = self._build_metric_name(name, tags)
            self._histograms[full_name].append(value)
            
            # Manter apenas últimos 1000 valores
            if len(self._histograms[full_name]) > 1000:
                self._histograms[full_name] = self._histograms[full_name][-1000:]
            
            self._timeseries_data[full_name].append({
                'timestamp': time.time(),
                'value': value,
                'type': 'histogram'
            })
    
    def record_quality_metrics(self, metrics: QualityMetrics, component: str):
        """Registra métricas de qualidade."""
        tags = {'component': component}
        
        self.record_gauge('quality.coverage_score', metrics.coverage_score, tags)
        self.record_gauge('quality.complexity_score', metrics.complexity_score, tags)
        self.record_gauge('quality.maintainability_index', metrics.maintainability_index, tags)
        self.record_gauge('quality.technical_debt_ratio', metrics.technical_debt_ratio, tags)
        self.record_gauge('quality.overall_score', metrics.overall_quality_score(), tags)
        self.record_counter('quality.code_smells', metrics.code_smells, tags)
    
    def record_performance_metrics(self, metrics: PerformanceMetrics, operation: str):
        """Registra métricas de performance."""
        tags = {'operation': operation}
        
        self.record_histogram('performance.execution_time_ms', metrics.execution_time_ms, tags)
        self.record_gauge('performance.memory_usage_mb', metrics.memory_usage_mb, tags)
        self.record_gauge('performance.cpu_usage_percent', metrics.cpu_usage_percent, tags)
        self.record_gauge('performance.cache_hit_rate', metrics.cache_hit_rate, tags)
        self.record_gauge('performance.overall_score', metrics.performance_score(), tags)
    
    def record_validation_metrics(self, metrics: ValidationMetrics, validator_type: str):
        """Registra métricas de validação."""
        tags = {'validator_type': validator_type}
        
        self.record_counter('validation.total_checks', metrics.total_checks, tags)
        self.record_counter('validation.passed_checks', metrics.passed_checks, tags)
        self.record_counter('validation.failed_checks', metrics.failed_checks, tags)
        self.record_counter('validation.critical_issues', metrics.critical_issues, tags)
        self.record_gauge('validation.success_rate', metrics.success_rate, tags)
        self.record_gauge('validation.quality_index', metrics.quality_index, tags)
        self.record_histogram('validation.execution_time_ms', metrics.execution_time_ms, tags)
    
    def record_generator_metrics(self, metrics: GeneratorMetrics):
        """Registra métricas de gerador."""
        tags = {'generator_type': metrics.generator_type}
        
        self.record_counter('generator.rules_generated', metrics.rules_generated, tags)
        self.record_histogram('generator.generation_time_ms', metrics.generation_time_ms, tags)
        self.record_histogram('generator.blueprint_parsing_time_ms', metrics.blueprint_parsing_time_ms, tags)
        self.record_gauge('generator.file_size_kb', metrics.file_size_kb, tags)
        self.record_gauge('generator.efficiency_score', metrics.efficiency_score(), tags)
    
    def _build_metric_name(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Constrói nome completo da métrica com tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name};{tag_str}"
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Obtém estatísticas de histograma."""
        full_name = self._build_metric_name(name, tags)
        values = self._histograms.get(full_name, [])
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], p: float) -> float:
        """Calcula percentil."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((p / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Exporta métricas em formato especificado."""
        with self._lock:
            if format_type == "json":
                return self._export_json()
            elif format_type == "prometheus":
                return self._export_prometheus()
            else:
                raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_json(self) -> str:
        """Exporta métricas em formato JSON."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'counters': dict(self._counters),
            'gauges': dict(self._gauges),
            'histograms': {
                name: self.get_histogram_stats(name.split(';')[0], self._parse_tags(name))
                for name in self._histograms.keys()
            }
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _parse_tags(self, full_name: str) -> Optional[Dict[str, str]]:
        """Parse tags do nome completo da métrica."""
        if ';' not in full_name:
            return None
        
        _, tag_str = full_name.split(';', 1)
        tags = {}
        
        for tag_pair in tag_str.split(','):
            if '=' in tag_pair:
                key, value = tag_pair.split('=', 1)
                tags[key] = value
        
        return tags if tags else None
    
    def save_metrics(self, filename: Optional[str] = None):
        """Salva métricas em arquivo."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
        
        filepath = self.storage_path / filename
        
        try:
            metrics_data = self.export_metrics("json")
            filepath.write_text(metrics_data, encoding='utf-8')
            
            logger.info(
                f"Metrics saved to {filepath}",
                extra={'context': {'filepath': str(filepath)}}
            )
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


# Context manager para medição de performance
class PerformanceTimer:
    """Context manager para medir performance de operações."""
    
    def __init__(self, collector: MetricsCollector, operation_name: str, **tags):
        self.collector = collector
        self.operation_name = operation_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_histogram(
                f'performance.{self.operation_name}_duration_ms',
                duration_ms,
                self.tags
            )
            
            # Registrar sucesso/falha
            status = 'success' if exc_type is None else 'error'
            tags_with_status = {**self.tags, 'status': status}
            self.collector.record_counter(
                f'operations.{self.operation_name}',
                1,
                tags_with_status
            )


# Decorator para medição automática de performance
def measure_performance(operation_name: str, **tags):
    """Decorator para medir performance de funções."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            
            with PerformanceTimer(collector, operation_name, **tags):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Instância global do coletor
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Obtém instância global do coletor de métricas."""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


# Exemplo de uso
if __name__ == "__main__":
    collector = get_metrics_collector()
    
    # Registrar algumas métricas de exemplo
    quality_metrics = QualityMetrics(
        coverage_score=85.5,
        complexity_score=78.0,
        maintainability_index=82.3,
        technical_debt_ratio=0.15,
        code_smells=5
    )
    
    collector.record_quality_metrics(quality_metrics, "scaffold_validator")
    
    # Testar timer de performance
    with PerformanceTimer(collector, "test_operation", component="test"):
        time.sleep(0.1)  # Simular trabalho
    
    # Testar decorator
    @measure_performance("expensive_calculation", module="test")
    def calculate_something(n: int) -> int:
        time.sleep(0.05)
        return n * n
    
    result = calculate_something(42)
    
    # Exportar métricas
    print(collector.export_metrics("json"))
    
    # Salvar métricas
    collector.save_metrics()