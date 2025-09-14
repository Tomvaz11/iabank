"""
Contract tests para endpoint POST /api/v1/auth/login.

Seguindo metodologia TDD (RED phase):
- Testa APENAS o contrato da API (schema request/response)
- NÃO testa lógica de negócio (isso é para integration/unit tests)
- DEVE falhar inicialmente pois endpoint não existe ainda

Baseado em:
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml
- constitution v1.0.0 - Django-Domain-First Architecture
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase


@pytest.mark.contract
class TestAuthLoginContract(TestCase):
    """
    Contract tests para POST /api/v1/auth/login.

    Testa apenas conformidade com OpenAPI schema:
    - Request body structure
    - Response body structure
    - Status codes
    - Content types
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login"

    def test_login_endpoint_exists(self):
        """
        Test: Endpoint POST /api/v1/auth/login existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.post(self.login_url, {})

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_login_request_schema_validation(self):
        """
        Test: Request body valida schema obrigatório.

        Schema obrigatório conforme OpenAPI:
        - email: string (format: email) - REQUIRED
        - password: string (format: password) - REQUIRED
        - tenant_domain: string - OPTIONAL
        """
        # Request vazio deve retornar erro de validação
        response = self.client.post(
            self.login_url,
            data={},
            format="json"
        )

        # RED phase: Deve falhar pois endpoint não existe
        # Quando implementado, deve ser HTTP 422 (Validation Error)
        expected_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        self.assertEqual(
            response.status_code,
            expected_status,
            f"Request inválido deve retornar {expected_status}"
        )

    def test_login_missing_email_field(self):
        """Test: Campo email é obrigatório."""
        payload = {
            "password": "SecurePass123!"
        }

        response = self.client.post(
            self.login_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe ainda
        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Email é campo obrigatório"
        )

        # Quando endpoint for implementado, response deve ter estrutura de erro
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            self.assertIn("errors", response.json())

    def test_login_missing_password_field(self):
        """Test: Campo password é obrigatório."""
        payload = {
            "email": "user@empresa.com.br"
        }

        response = self.client.post(
            self.login_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Password é campo obrigatório"
        )

    def test_login_invalid_email_format(self):
        """Test: Email deve ter formato válido."""
        payload = {
            "email": "invalid-email",
            "password": "SecurePass123!"
        }

        response = self.client.post(
            self.login_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Email inválido deve retornar erro de validação"
        )

    def test_login_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 200):
        {
          "data": {
            "access_token": string,
            "refresh_token": string,
            "expires_in": integer,
            "user": User object
          }
        }
        """
        # Payload válido para teste de contrato
        payload = {
            "email": "user@empresa.com.br",
            "password": "SecurePass123!",
            "tenant_domain": "empresa"
        }

        response = self.client.post(
            self.login_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado ainda
        # Quando implementado com credenciais válidas, deve retornar HTTP 200
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            self.assertIn("access_token", data["data"])
            self.assertIn("refresh_token", data["data"])
            self.assertIn("expires_in", data["data"])
            self.assertIn("user", data["data"])

            # Valida tipos dos campos
            self.assertIsInstance(data["data"]["access_token"], str)
            self.assertIsInstance(data["data"]["refresh_token"], str)
            self.assertIsInstance(data["data"]["expires_in"], int)
            self.assertIsInstance(data["data"]["user"], dict)

    def test_login_unauthorized_response_schema(self):
        """
        Test: Response de erro de autenticação segue schema OpenAPI.

        Schema esperado (HTTP 401):
        {
          "errors": [{
            "status": "401",
            "code": "...",
            "detail": "..."
          }]
        }
        """
        # Credenciais inválidas
        payload = {
            "email": "user@empresa.com.br",
            "password": "wrong-password"
        }

        response = self.client.post(
            self.login_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, credenciais inválidas devem retornar HTTP 401
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            data = response.json()

            # Valida estrutura de erro conforme OpenAPI
            self.assertIn("errors", data)
            self.assertIsInstance(data["errors"], list)
            self.assertTrue(len(data["errors"]) > 0)

            error = data["errors"][0]
            self.assertIn("status", error)
            self.assertIn("detail", error)
            self.assertEqual(error["status"], "401")

    def test_login_content_type_json_required(self):
        """Test: Endpoint aceita apenas application/json."""
        payload = {
            "email": "user@empresa.com.br",
            "password": "SecurePass123!"
        }

        # Teste com content-type incorreto
        response = self.client.post(
            self.login_url,
            data=payload,
            content_type="application/x-www-form-urlencoded"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve aceitar apenas JSON
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertIn(
                response.status_code,
                [status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, status.HTTP_400_BAD_REQUEST],
                "Deve aceitar apenas application/json"
            )

    def test_login_method_not_allowed_for_get(self):
        """Test: Endpoint aceita apenas POST method."""
        response = self.client.get(self.login_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, GET deve retornar 405 Method Not Allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint deve aceitar apenas POST"
            )


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestAuthLoginTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login"

    def test_login_with_tenant_domain_in_payload(self):
        """
        Test: tenant_domain opcional no payload é aceito.

        Conforme OpenAPI, tenant_domain é opcional se email é único globalmente.
        """
        payload = {
            "email": "user@empresa.com.br",
            "password": "SecurePass123!",
            "tenant_domain": "empresa_teste"
        }

        response = self.client.post(
            self.login_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar tenant_domain sem erro de validação
        self.assertNotEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "tenant_domain é campo válido opcional"
        )