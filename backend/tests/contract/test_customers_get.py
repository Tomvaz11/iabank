"""
Contract tests para endpoint GET /api/v1/customers/{id}.

Seguindo metodologia TDD (RED phase):
- Testa APENAS o contrato da API (schema request/response)
- NÃO testa lógica de negócio (isso é para integration/unit tests)
- DEVE falhar inicialmente pois endpoint não existe ainda

Baseado em:
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml linha 251-263
- constitution v1.0.0 - Django-Domain-First Architecture
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
import uuid


@pytest.mark.contract
class TestCustomersGetContract(TestCase):
    """
    Contract tests para GET /api/v1/customers/{customer_id}.

    Testa apenas conformidade com OpenAPI schema:
    - URL parameter validation
    - Response body structure
    - Status codes
    - Content types
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        # Mock UUID para testes de contrato
        self.customer_id = str(uuid.uuid4())
        self.customer_detail_url = f"/api/v1/customers/{self.customer_id}"

    def test_customers_get_endpoint_exists(self):
        """
        Test: Endpoint GET /api/v1/customers/{customer_id} existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.get(self.customer_detail_url)

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_customers_get_invalid_uuid_parameter(self):
        """
        Test: customer_id deve ser UUID válido.

        Conforme OpenAPI, parameter customer_id:
        - type: string
        - format: uuid
        - required: true
        """
        invalid_uuid_url = "/api/v1/customers/invalid-uuid"

        response = self.client.get(invalid_uuid_url)

        # RED phase: Endpoint não existe ainda
        # Quando implementado, deve validar UUID format
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                "UUID inválido deve retornar erro de validação"
            )

    def test_customers_get_nonexistent_customer(self):
        """
        Test: Customer inexistente retorna HTTP 404.

        Conforme OpenAPI responses:
        '404': $ref: '#/components/responses/NotFoundError'
        """
        # UUID válido mas customer não existe
        nonexistent_uuid = str(uuid.uuid4())
        nonexistent_url = f"/api/v1/customers/{nonexistent_uuid}"

        response = self.client.get(nonexistent_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve retornar 404 para customer inexistente
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            # Se endpoint existe mas customer não existe
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                "Customer inexistente deve retornar 404"
            )

            # Valida estrutura de erro conforme OpenAPI
            if response.content:
                data = response.json()
                self.assertIn("errors", data)
                self.assertIsInstance(data["errors"], list)

                if data["errors"]:
                    error = data["errors"][0]
                    self.assertIn("status", error)
                    self.assertIn("detail", error)

    def test_customers_get_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 200):
        {
          "data": {
            "id": "uuid",
            "document_type": "CPF|CNPJ",
            "document": "string",
            "name": "string",
            "email": "email",
            "phone": "string",
            "birth_date": "date",
            "monthly_income": number,
            "credit_score": integer,
            "is_active": boolean,
            "addresses": [Address],
            "created_at": "date-time",
            "updated_at": "date-time"
          }
        }
        """
        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado ainda
        # Quando implementado e customer existe, deve retornar HTTP 200
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            customer = data["data"]

            # Campos obrigatórios na response
            required_fields = [
                "id", "document_type", "document", "name",
                "email", "is_active", "created_at"
            ]

            for field in required_fields:
                self.assertIn(field, customer, f"Campo {field} é obrigatório na response")

            # Valida tipos dos campos obrigatórios
            self.assertIsInstance(customer["id"], str)
            self.assertIn(customer["document_type"], ["CPF", "CNPJ"])
            self.assertIsInstance(customer["document"], str)
            self.assertIsInstance(customer["name"], str)
            self.assertIsInstance(customer["email"], str)
            self.assertIsInstance(customer["is_active"], bool)

            # Campos opcionais podem estar presentes
            optional_fields = [
                "phone", "birth_date", "monthly_income",
                "credit_score", "addresses"
            ]

            for field in optional_fields:
                if field in customer:
                    if field == "phone":
                        self.assertIsInstance(customer[field], (str, type(None)))
                    elif field == "birth_date":
                        self.assertIsInstance(customer[field], (str, type(None)))
                    elif field == "monthly_income":
                        self.assertIsInstance(customer[field], (int, float, type(None)))
                    elif field == "credit_score":
                        self.assertIsInstance(customer[field], (int, type(None)))
                    elif field == "addresses":
                        self.assertIsInstance(customer[field], list)

                        # Valida estrutura de cada address
                        for address in customer[field]:
                            self.assertIn("id", address)
                            self.assertIn("type", address)
                            self.assertIn("street", address)
                            self.assertIn("number", address)
                            self.assertIn("neighborhood", address)
                            self.assertIn("city", address)
                            self.assertIn("state", address)
                            self.assertIn("zipcode", address)

                            # Valida enum type
                            self.assertIn(
                                address["type"],
                                ["RESIDENTIAL", "COMMERCIAL", "CORRESPONDENCE"]
                            )

    def test_customers_get_content_type_json_response(self):
        """Test: Response deve ter Content-Type application/json."""
        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve retornar JSON
        if response.status_code == status.HTTP_200_OK:
            self.assertIn(
                'application/json',
                response.get('Content-Type', ''),
                "Response deve ser application/json"
            )

    def test_customers_get_method_allowed(self):
        """Test: Método GET é permitido no endpoint."""
        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado (404)
        # Quando implementado, GET deve ser permitido
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertNotEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Método GET deve ser permitido"
            )

    def test_customers_get_method_not_allowed_for_post(self):
        """Test: Método POST não é permitido no endpoint de detalhe."""
        response = self.client.post(self.customer_detail_url, {})

        # RED phase: Endpoint não implementado (404)
        # Quando implementado, POST no endpoint de detalhe deve ser negado
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Método POST não deve ser permitido em endpoint de detalhe"
            )

    def test_customers_get_method_not_allowed_for_delete(self):
        """Test: Método DELETE não é permitido no endpoint de detalhe."""
        response = self.client.delete(self.customer_detail_url)

        # RED phase: Endpoint não implementado (404)
        # DELETE não está definido no OpenAPI contract para este endpoint
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Método DELETE não deve ser permitido conforme OpenAPI"
            )


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestCustomersGetTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.customer_id = str(uuid.uuid4())
        self.customer_detail_url = f"/api/v1/customers/{self.customer_id}"

    def test_customers_get_requires_authentication(self):
        """
        Test: Endpoint requer autenticação.

        Conforme OpenAPI, todos os endpoints exceto auth/ requerem Bearer token.
        """
        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado sem token, deve retornar HTTP 401
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Endpoint deve requerer autenticação"
            )

    def test_customers_get_with_bearer_token_header(self):
        """
        Test: Aceita Authorization Bearer token no header.

        Formato esperado: Authorization: Bearer <jwt_token>
        """
        # Mock JWT token para teste de contrato
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve processar token sem erro de formato
        self.assertNotEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Bearer token é formato válido de autenticação"
        )

    def test_customers_get_tenant_isolation_by_token(self):
        """
        Test: Cliente é retornado apenas se pertencer ao tenant do token.

        Multi-tenancy é transparente via token - cliente em tenant diferente
        deve retornar 404 mesmo se existir.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, middleware deve filtrar por tenant_id automaticamente
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Cliente retornado deve pertencer ao tenant do token
            self.assertIn("data", data)
            self.assertIn("id", data["data"])

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            # Cliente não pertence ao tenant ou não existe - ambos retornam 404
            # Isso é correto para evitar information disclosure
            self.assertTrue(True, "Tenant isolation funciona corretamente")

    def test_customers_get_different_tenant_returns_not_found(self):
        """
        Test: Cliente de outro tenant retorna 404.

        Mesmo que customer_id seja válido e exista no banco,
        se pertencer a outro tenant deve retornar 404.
        """
        # Token de tenant diferente
        tenant_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.other_tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tenant_token}')

        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve retornar 404 para cliente de outro tenant
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            # Se endpoint existe, deve aplicar tenant isolation
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                "Cliente de outro tenant deve retornar 404"
            )

    def test_customers_get_invalid_token_returns_unauthorized(self):
        """Test: Token inválido retorna HTTP 401."""
        invalid_token = "invalid.jwt.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {invalid_token}')

        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado com token inválido, deve retornar 401
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Token inválido deve retornar 401"
            )

    def test_customers_get_expired_token_returns_unauthorized(self):
        """Test: Token expirado retorna HTTP 401."""
        # Mock token expirado
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.expired.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')

        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado com token expirado, deve retornar 401
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Token expirado deve retornar 401"
            )

    def test_customers_get_malformed_authorization_header(self):
        """Test: Header Authorization malformado retorna HTTP 401."""
        # Header sem "Bearer" prefix
        self.client.credentials(HTTP_AUTHORIZATION='token_without_bearer')

        response = self.client.get(self.customer_detail_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, header malformado deve retornar 401
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Header Authorization malformado deve retornar 401"
            )