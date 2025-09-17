"""
Endpoints para setup de dados de teste E2E - VERSAO TEMPORARIA.
ATENCAO: Apenas para ambiente de desenvolvimento!
"""
import json
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from iabank.core.factories import generate_cnpj
from iabank.core.models import Tenant

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def setup_test_data(request):
    """
    Setup basico de dados de teste (apenas Tenant por enquanto).
    TODO: Expandir quando models forem implementados (T028-T059)
    """
    if not settings.DEBUG:
        return JsonResponse({"error": "Test endpoints only available in DEBUG mode"}, status=403)

    try:
        data = json.loads(request.body or "{}")
        tenant_name = data.get("tenant", "test-tenant")
        slug = slugify(tenant_name)
        domain = data.get("domain", f"{slug}.tests.iabank.local")

        with transaction.atomic():
            tenant, created = Tenant.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": tenant_name,
                    "document": data.get("document", generate_cnpj()),
                    "domain": domain,
                    "contact_email": data.get("email", "qa@iabank.local"),
                    "phone_number": data.get("phone", "(11) 98888-7777"),
                    "created_by": "test_setup_endpoint",
                    "is_active": True,
                },
            )

            logger.info("Basic test data setup completed for tenant: %s", tenant_name)

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Basic test setup completed (Tenant only)",
                    "data": {
                        "tenant_id": str(tenant.id),
                        "tenant_name": tenant.name,
                        "tenant_slug": tenant.slug,
                        "tenant_domain": tenant.domain,
                        "note": "Full setup will be available after T028-T059 implementation",
                    },
                }
            )

    except Exception as e:
        logger.error("Error setting up test data: %s", e, exc_info=True)
        return JsonResponse({"error": f"Failed to setup test data: {e}"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_overdue_loan(request):
    """
    Placeholder para criacao de emprestimo em atraso.
    TODO: Implementar quando Loan model for criado (T033-T037)
    """
    return JsonResponse(
        {"error": "Loan creation will be available after T033-T037 implementation"},
        status=501,
    )


@csrf_exempt
@require_http_methods(["POST"])
def create_loan_with_installments(request):
    """
    Placeholder para criacao de emprestimo com parcelas.
    TODO: Implementar quando Loan model for criado (T033-T037)
    """
    return JsonResponse(
        {"error": "Loan creation will be available after T033-T037 implementation"},
        status=501,
    )
