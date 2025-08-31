"""
Views do app Core.

Implementa endpoints básicos de infraestrutura como health check,
métricas e outros endpoints que não pertencem ao domínio de negócio.
"""

from django.db import connection
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """
    Endpoint de health check para verificar o status da aplicação.
    
    Verifica a conectividade com o banco de dados e cache Redis,
    retornando status 200 se tudo estiver funcionando corretamente.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """Executa verificações de saúde do sistema."""
        health_status = {
            'status': 'healthy',
            'database': self._check_database(),
            'cache': self._check_cache(),
            'version': '0.1.0',
        }

        # Se algum serviço estiver com problema, retorna status 503
        if not all([health_status['database'], health_status['cache']]):
            health_status['status'] = 'unhealthy'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_status, status=status.HTTP_200_OK)

    def _check_database(self):
        """Verifica conectividade com o banco de dados."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _check_cache(self):
        """Verifica conectividade com o cache Redis."""
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception:
            return False