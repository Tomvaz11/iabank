"""
Celery configuration for IABANK project.
Enterprise-grade task processing with idempotency and DLQ support.
"""

import os
import uuid
from typing import Any, Dict, Optional

from celery import Celery, shared_task
from django.core.cache import cache
from django.utils import timezone

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("iabank")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    "update-iof-rates": {
        "task": "iabank.operations.tasks.update_iof_rates",
        "schedule": 86400.0,  # Daily
    },
    "calculate-overdue-interest": {
        "task": "iabank.operations.tasks.calculate_overdue_interest",
        "schedule": 3600.0,  # Hourly
    },
    "generate-daily-reports": {
        "task": "iabank.finance.tasks.generate_daily_reports",
        "schedule": 86400.0,  # Daily
    },
}
app.conf.timezone = "America/Sao_Paulo"

# T079 - Celery Advanced Configuration
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
app.conf.task_reject_on_worker_lost = True
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_max_retries = 5

# Dead Letter Queue configuration
app.conf.task_routes = {
    'iabank.*.critical_*': {
        'queue': 'critical',
        'routing_key': 'critical',
    },
    'iabank.*.failed_*': {
        'queue': 'dlq',
        'routing_key': 'dlq',
    },
}


# T079 - Idempotency Functions and Decorator
def generate_operation_id() -> str:
    """
    Gera um ID único para operações idempotentes.

    Returns:
        UUID string único
    """
    return str(uuid.uuid4())


def is_operation_completed(operation_id: str) -> bool:
    """
    Verifica se uma operação já foi completada.

    Args:
        operation_id: ID da operação a verificar

    Returns:
        True se operação já foi completada
    """
    cache_key = f"celery:idempotent:{operation_id}"
    return cache.get(cache_key) is not None


def is_operation_processing(operation_id: str) -> bool:
    """
    Verifica se uma operação está em processamento.

    Args:
        operation_id: ID da operação a verificar

    Returns:
        True se operação está sendo processada
    """
    cache_key = f"celery:idempotent:{operation_id}:processing"
    return cache.get(cache_key) is not None


def idempotent_task(*task_args, **task_kwargs):
    """
    Decorator para criar tarefas idempotentes críticas.

    Usage:
        @idempotent_task
        def my_critical_task(operation_id, data):
            # task logic here
            return result
    """
    def decorator(func):
        @shared_task(
            bind=True,
            autoretry_for=(Exception,),
            retry_kwargs={'max_retries': 5},
            retry_backoff=True,
            acks_late=True
        )
        def wrapper(self, operation_id: str, *args, **kwargs):
            cache_key = f"celery:idempotent:{operation_id}"

            # Verificar se operação já foi executada
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            processing_key = f"{cache_key}:processing"

            try:
                # Marcar operação como em processamento
                cache.set(processing_key, True, timeout=300)  # 5 minutos

                # Executar a função original
                result = func(operation_id, *args, **kwargs)

                # Marcar como concluída (24 horas de cache para evitar reprocessamento)
                cache.set(cache_key, result, timeout=86400)

                return result

            except Exception as exc:
                # Remover flag de processamento em caso de erro
                cache.delete(processing_key)

                # Log do erro para monitoramento
                self.retry(countdown=60 * (self.request.retries + 1), exc=exc)

            finally:
                # Sempre limpar flag de processamento
                cache.delete(processing_key)

        return wrapper

    # Se chamado sem parênteses: @idempotent_task
    if len(task_args) == 1 and callable(task_args[0]):
        return decorator(task_args[0])

    # Se chamado com parênteses: @idempotent_task()
    return decorator


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Example usage of idempotent_task
@idempotent_task
def example_critical_task(operation_id: str, data: dict) -> dict:
    """
    Exemplo de task crítica com idempotência.

    Args:
        operation_id: ID único da operação
        data: Dados da operação

    Returns:
        Resultado processado
    """
    # Simular processamento crítico
    return {
        "operation_id": operation_id,
        "status": "processed",
        "processed_at": timezone.now().isoformat(),
        "data": data
    }
