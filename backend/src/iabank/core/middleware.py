"""
Middleware de isolamento de tenant para o sistema multi-tenant do IABANK.

Este módulo contém o middleware responsável por identificar e isolar dados por tenant
em todas as requisições HTTP, garantindo que usuários de diferentes organizações
não tenham acesso aos dados uns dos outros.
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .models import Tenant


class TenantIsolationMiddleware(MiddlewareMixin):
    """
    Middleware para isolamento de tenant baseado em header HTTP.

    Este middleware intercepta todas as requisições HTTP e:
    1. Extrai o identificador do tenant do header 'X-Tenant-ID'
    2. Busca e associa o objeto Tenant à requisição
    3. Bloqueia acesso se o tenant não existir ou estiver inativo
    4. Disponibiliza o tenant via request.tenant para toda a aplicação
    """

    def process_request(self, request):
        """
        Processa a requisição para identificar e validar o tenant.

        Args:
            request: Objeto HttpRequest do Django

        Returns:
            None se o tenant for válido, JsonResponse com erro caso contrário
        """
        # Lista de paths que não precisam de validação de tenant
        # (útil para health checks, admin, etc.)
        exempt_paths = [
            '/admin/',
            '/health/',
            '/api-auth/',
        ]

        # Verifica se o path atual está isento da validação de tenant
        if any(request.path.startswith(path) for path in exempt_paths):
            request.tenant = None
            return None

        # Extrai o tenant ID do header HTTP
        tenant_id = request.META.get('HTTP_X_TENANT_ID')

        if tenant_id is None:
            return JsonResponse(
                {
                    'errors': [{
                        'status': '400',
                        'code': 'missing_tenant',
                        'detail': (
                            'Header X-Tenant-ID é obrigatório para esta requisição.'
                        )
                    }]
                },
                status=400
            )

        try:
            # Converte para inteiro e busca o tenant
            tenant_id = int(tenant_id)
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)

            # Associa o tenant à requisição
            request.tenant = tenant

        except ValueError:
            return JsonResponse(
                {
                    'errors': [{
                        'status': '400',
                        'code': 'invalid_tenant_format',
                        'detail': 'X-Tenant-ID deve ser um número inteiro válido.'
                    }]
                },
                status=400
            )

        except Tenant.DoesNotExist:
            return JsonResponse(
                {
                    'errors': [{
                        'status': '404',
                        'code': 'tenant_not_found',
                        'detail': 'Tenant não encontrado ou inativo.'
                    }]
                },
                status=404
            )

        return None
