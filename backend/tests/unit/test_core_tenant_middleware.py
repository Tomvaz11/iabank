"""Testes para o TenantMiddleware garantindo isolamento multi-tenant."""
import json
import uuid

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from iabank.core.factories import generate_cnpj
from iabank.core.middleware import TenantMiddleware
from iabank.core.models import Tenant


@override_settings(DEBUG=False)
class TenantMiddlewareTests(TestCase):
    """Casos de teste para middleware de tenant."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(lambda request: HttpResponse("OK"))
        self.tenant = Tenant.objects.create(
            name="Tenant Middleware",
            document=generate_cnpj(),
        )

    def test_sem_header_retorna_erro(self):
        """Middleware deve exigir X-Tenant-ID quando nenhum contexto esta disponivel."""
        request = self.factory.get("/")

        response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertEqual(payload["errors"][0]["code"], "TENANT_REQUIRED")

    def test_tenant_inexistente_retorna_404(self):
        """Tenant nao encontrado precisa retornar 404."""
        request = self.factory.get("/")
        request.META["HTTP_X_TENANT_ID"] = str(uuid.uuid4())

        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 404)
        payload = json.loads(response.content)
        self.assertEqual(payload["errors"][0]["code"], "TENANT_NOT_FOUND")

    def test_tenant_inativo_retorna_403(self):
        """Tenant inativo nao deve permitir acesso."""
        inactive_tenant = Tenant.objects.create(
            name="Tenant Inativo",
            document=generate_cnpj(),
            is_active=False,
        )
        request = self.factory.get("/")
        request.META["HTTP_X_TENANT_ID"] = str(inactive_tenant.id)

        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 403)
        payload = json.loads(response.content)
        self.assertEqual(payload["errors"][0]["code"], "TENANT_INACTIVE")

    def test_header_valido_define_contexto(self):
        """Tenant valido deve ser carregado e contexto limpo ao final."""
        request = self.factory.get("/")
        request.META["HTTP_X_TENANT_ID"] = str(self.tenant.id)

        response = self.middleware.process_request(request)

        self.assertIsNone(response)
        self.assertEqual(request.tenant.id, self.tenant.id)
        self.assertEqual(request.tenant_id, self.tenant.id)
        self.assertEqual(
            TenantMiddleware.get_current_tenant().id,
            self.tenant.id,
        )

        cleanup_response = self.middleware.process_response(request, HttpResponse("OK"))
        self.assertEqual(cleanup_response.status_code, 200)
        self.assertIsNone(TenantMiddleware.get_current_tenant())

    def test_header_invalido_retorna_erro(self):
        """UUID malformado deve retornar erro 400 especifico."""
        request = self.factory.get("/")
        request.META["HTTP_X_TENANT_ID"] = "nao-e-uuid"

        response = self.middleware.process_request(request)

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertEqual(payload["errors"][0]["code"], "TENANT_INVALID")
