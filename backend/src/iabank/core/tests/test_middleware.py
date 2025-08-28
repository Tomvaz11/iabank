"""
Testes unitários para o middleware de isolamento de tenant do IABANK.

Este módulo contém testes abrangentes para validar o funcionamento correto
do TenantIsolationMiddleware, garantindo isolamento adequado entre tenants
e tratamento apropriado de cenários de erro.
"""

import json

from django.http import HttpRequest, JsonResponse
from django.test import TestCase

from iabank.core.middleware import TenantIsolationMiddleware
from iabank.core.tests.factories import TenantFactory


class TenantIsolationMiddlewareTestCase(TestCase):
    """
    Testes para o middleware de isolamento de tenant.

    Valida todos os cenários possíveis de uso do middleware, incluindo
    casos de sucesso, paths isentos, e diferentes tipos de erro.
    """

    def setUp(self):
        """Configura o ambiente de teste."""
        # Mock get_response para inicialização do middleware
        def get_response(request):
            return None

        self.middleware = TenantIsolationMiddleware(get_response)
        self.tenant = TenantFactory(name="Test Tenant", is_active=True)
        self.inactive_tenant = TenantFactory(name="Inactive Tenant", is_active=False)

    def _create_request(self, path='/', tenant_id=None):
        """
        Helper para criar requisições HTTP de teste.

        Args:
            path: Path da requisição
            tenant_id: ID do tenant para o header X-Tenant-ID

        Returns:
            HttpRequest configurado para teste
        """
        request = HttpRequest()
        request.path = path
        request.method = 'GET'

        if tenant_id is not None:
            request.META['HTTP_X_TENANT_ID'] = str(tenant_id)

        return request

    def test_exempt_paths_do_not_require_tenant(self):
        """Testa que paths isentos não exigem header de tenant."""
        exempt_paths = ['/admin/', '/health/', '/api-auth/']

        for path in exempt_paths:
            with self.subTest(path=path):
                request = self._create_request(path=path)

                response = self.middleware.process_request(request)

                self.assertIsNone(response)
                self.assertIsNone(request.tenant)

    def test_missing_tenant_header_returns_error(self):
        """Testa erro quando header X-Tenant-ID está ausente."""
        request = self._create_request(path='/api/v1/loans/')

        response = self.middleware.process_request(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 400)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['errors'][0]['code'], 'missing_tenant')
        self.assertEqual(response_data['errors'][0]['status'], '400')

    def test_invalid_tenant_format_returns_error(self):
        """Testa erro quando X-Tenant-ID não é um número válido."""
        invalid_values = ['invalid', 'abc123', '12.5', '']

        for invalid_value in invalid_values:
            with self.subTest(tenant_id=invalid_value):
                request = self._create_request(
                    path='/api/v1/loans/',
                    tenant_id=invalid_value
                )

                response = self.middleware.process_request(request)

                self.assertIsInstance(response, JsonResponse)
                self.assertEqual(response.status_code, 400)

                response_data = json.loads(response.content)
                self.assertEqual(
                    response_data['errors'][0]['code'], 'invalid_tenant_format'
                )

    def test_nonexistent_tenant_returns_error(self):
        """Testa erro quando tenant não existe no banco."""
        nonexistent_id = 99999
        request = self._create_request(
            path='/api/v1/loans/',
            tenant_id=nonexistent_id
        )

        response = self.middleware.process_request(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 404)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['errors'][0]['code'], 'tenant_not_found')

    def test_inactive_tenant_returns_error(self):
        """Testa erro quando tenant existe mas está inativo."""
        request = self._create_request(
            path='/api/v1/loans/',
            tenant_id=self.inactive_tenant.id
        )

        response = self.middleware.process_request(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 404)

        response_data = json.loads(response.content)
        self.assertEqual(response_data['errors'][0]['code'], 'tenant_not_found')

    def test_valid_tenant_sets_request_tenant(self):
        """Testa sucesso com tenant válido e ativo."""
        request = self._create_request(
            path='/api/v1/loans/',
            tenant_id=self.tenant.id
        )

        response = self.middleware.process_request(request)

        self.assertIsNone(response)  # None indica sucesso
        self.assertEqual(request.tenant, self.tenant)
        self.assertEqual(request.tenant.name, "Test Tenant")
        self.assertTrue(request.tenant.is_active)

    def test_multiple_valid_tenants_isolation(self):
        """Testa que diferentes tenants são isolados corretamente."""
        tenant_a = TenantFactory(name="Tenant A")
        tenant_b = TenantFactory(name="Tenant B")

        # Testa requisição para tenant A
        request_a = self._create_request(
            path='/api/v1/customers/',
            tenant_id=tenant_a.id
        )
        response_a = self.middleware.process_request(request_a)

        self.assertIsNone(response_a)
        self.assertEqual(request_a.tenant, tenant_a)

        # Testa requisição para tenant B
        request_b = self._create_request(
            path='/api/v1/customers/',
            tenant_id=tenant_b.id
        )
        response_b = self.middleware.process_request(request_b)

        self.assertIsNone(response_b)
        self.assertEqual(request_b.tenant, tenant_b)

        # Verifica isolamento
        self.assertNotEqual(request_a.tenant, request_b.tenant)

    def test_tenant_id_zero_returns_error(self):
        """Testa que tenant_id = 0 resulta em erro."""
        request = self._create_request(path='/api/v1/loans/', tenant_id=0)

        response = self.middleware.process_request(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 404)

    def test_negative_tenant_id_returns_error(self):
        """Testa que tenant_id negativo resulta em erro."""
        request = self._create_request(path='/api/v1/loans/', tenant_id=-1)

        response = self.middleware.process_request(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 404)
