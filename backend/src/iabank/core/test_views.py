"""
Endpoints para setup de dados de teste E2E - VERSÃO TEMPORÁRIA.
ATENÇÃO: Apenas para ambiente de desenvolvimento!
"""
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db import transaction
import json

from iabank.core.models import Tenant

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def setup_test_data(request):
    """
    Setup básico de dados de teste (apenas Tenant por enquanto).
    TODO: Expandir quando models forem implementados (T028-T059)
    """
    if not settings.DEBUG:
        return JsonResponse({
            "error": "Test endpoints only available in DEBUG mode"
        }, status=403)

    try:
        data = json.loads(request.body)
        tenant_name = data.get('tenant', 'test-tenant')

        with transaction.atomic():
            # Criar ou buscar tenant
            tenant, created = Tenant.objects.get_or_create(
                name=tenant_name,
                defaults={
                    'cnpj': '12345678000123',
                    'is_active': True,
                    'created_by': 'test-setup'
                }
            )

            logger.info(f"Basic test data setup completed for tenant: {tenant_name}")

            return JsonResponse({
                "status": "success",
                "message": "Basic test setup completed (Tenant only)",
                "data": {
                    "tenant_id": str(tenant.id),
                    "tenant_name": tenant.name,
                    "note": "Full setup will be available after T028-T059 implementation"
                }
            })

    except Exception as e:
        logger.error(f"Error setting up test data: {str(e)}")
        return JsonResponse({
            "error": f"Failed to setup test data: {str(e)}"
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_overdue_loan(request):
    """
    Placeholder para criação de empréstimo em atraso.
    TODO: Implementar quando Loan model for criado (T033-T037)
    """
    return JsonResponse({
        "error": "Loan creation will be available after T033-T037 implementation"
    }, status=501)


@csrf_exempt
@require_http_methods(["POST"])
def create_loan_with_installments(request):
    """
    Placeholder para criação de empréstimo com parcelas.
    TODO: Implementar quando models forem criados (T033-T037)
    """
    return JsonResponse({
        "error": "Loan with installments will be available after T033-T037 implementation"
    }, status=501)