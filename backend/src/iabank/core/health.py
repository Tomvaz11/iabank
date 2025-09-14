"""
Health check endpoint para CI/CD e monitoring.
Implementa verificações de infraestrutura essenciais.
"""
import time
from typing import Dict, Any

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache


@never_cache
@require_http_methods(["GET"])
def health_check(request) -> JsonResponse:
    """
    Health check endpoint com verificações de infraestrutura.

    Returns:
        JsonResponse: Status da aplicação e dependências
    """
    start_time = time.time()

    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
        "application": _check_application()
    }

    # Status geral baseado em todas as verificações
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in checks.values()
    ) else "unhealthy"

    response_data = {
        "status": overall_status,
        "timestamp": int(time.time()),
        "response_time_ms": round((time.time() - start_time) * 1000, 2),
        "version": getattr(settings, "VERSION", "unknown"),
        "checks": checks
    }

    status_code = 200 if overall_status == "healthy" else 503
    return JsonResponse(response_data, status=status_code)


def _check_database() -> Dict[str, Any]:
    """Verifica conectividade com PostgreSQL."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


def _check_cache() -> Dict[str, Any]:
    """Verifica conectividade com Redis/Cache."""
    try:
        cache.set("health_check", "test", 30)
        if cache.get("health_check") == "test":
            cache.delete("health_check")
            return {
                "status": "healthy",
                "message": "Cache connection successful"
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Cache write/read failed"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Cache connection failed: {str(e)}"
        }


def _check_application() -> Dict[str, Any]:
    """Verifica status geral da aplicação Django."""
    try:
        return {
            "status": "healthy",
            "message": "Application running",
            "debug_mode": settings.DEBUG,
            "django_version": getattr(settings, "DJANGO_VERSION", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Application check failed: {str(e)}"
        }