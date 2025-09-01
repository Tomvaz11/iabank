"""
Middleware customizado para o sistema IABANK.

Implementa funcionalidades transversais como isolamento de tenant,
logging contextual e outras funcionalidades de infraestrutura.
"""

import logging
from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware para isolamento de tenant baseado no subdomínio ou header.
    
    Determina o tenant atual baseado na requisição e o torna disponível
    globalmente para uso nos views, serializers e modelos.
    """

    def process_request(self, request):
        """
        Identifica o tenant baseado no subdomínio ou header X-Tenant.
        Por enquanto, utiliza um tenant padrão para desenvolvimento.
        """
        # TODO: Implementar lógica de identificação de tenant por subdomínio
        # Por enquanto, utiliza tenant padrão para desenvolvimento
        try:
            request.tenant = Tenant.objects.get(slug='default')
        except Tenant.DoesNotExist:
            # Se não existe tenant padrão, cria um para desenvolvimento
            request.tenant = Tenant.objects.create(
                name='Default Tenant',
                slug='default'
            )
        
        return None

    def process_exception(self, request, exception):
        """Loga exceções relacionadas ao tenant."""
        if hasattr(request, 'tenant'):
            logger.error(
                f"Exception in tenant {request.tenant.slug}: {exception}",
                exc_info=True
            )
        return None