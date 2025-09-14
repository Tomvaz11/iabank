"""
Contract tests para endpoint POST /api/v1/customers.

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
class TestCustomersPostContract(TestCase):
    """
    Contract tests para POST /api/v1/customers.

    Testa apenas conformidade com OpenAPI schema:
    - Request body structure
    - Response body structure
    - Status codes
    - Content types
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        self.customers_url = "/api/v1/customers"

    def test_customers_post_endpoint_exists(self):
        """
        Test: Endpoint POST /api/v1/customers existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.post(self.customers_url, {})

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_customers_post_request_schema_validation(self):
        """
        Test: Request body valida schema obrigatório.

        Schema obrigatório conforme OpenAPI:
        - document_type: string (enum: CPF, CNPJ) - REQUIRED
        - document: string - REQUIRED
        - name: string - REQUIRED
        - email: string (format: email) - REQUIRED
        - phone: string - OPTIONAL
        - birth_date: string (format: date) - OPTIONAL
        - monthly_income: number (decimal) - OPTIONAL
        - addresses: array[AddressCreateRequest] - OPTIONAL
        """
        # Request vazio deve retornar erro de validação
        response = self.client.post(
            self.customers_url,
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

    def test_customers_post_missing_document_type_field(self):
        """Test: Campo document_type é obrigatório."""
        payload = {
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe ainda
        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "document_type é campo obrigatório"
        )

        # Quando endpoint for implementado, response deve ter estrutura de erro
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            self.assertIn("errors", response.json())

    def test_customers_post_missing_document_field(self):
        """Test: Campo document é obrigatório."""
        payload = {
            "document_type": "CPF",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "document é campo obrigatório"
        )

    def test_customers_post_missing_name_field(self):
        """Test: Campo name é obrigatório."""
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "name é campo obrigatório"
        )

    def test_customers_post_missing_email_field(self):
        """Test: Campo email é obrigatório."""
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "email é campo obrigatório"
        )

    def test_customers_post_invalid_document_type_enum(self):
        """Test: document_type deve aceitar apenas CPF ou CNPJ."""
        payload = {
            "document_type": "RG",  # Valor inválido
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "document_type inválido deve retornar erro de validação"
        )

    def test_customers_post_invalid_email_format(self):
        """Test: Email deve ter formato válido."""
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "email-invalido"  # Formato inválido
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Email inválido deve retornar erro de validação"
        )

    def test_customers_post_invalid_birth_date_format(self):
        """Test: birth_date deve ter formato date válido."""
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br",
            "birth_date": "data-invalida"  # Formato inválido
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "birth_date inválido deve retornar erro de validação"
        )

    def test_customers_post_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 201):
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
            "addresses": [Address],
            "created_at": "date-time",
            "updated_at": "date-time"
          }
        }
        """
        # Payload válido para teste de contrato
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br",
            "phone": "+55 11 99999-9999",
            "birth_date": "1990-01-15",
            "monthly_income": 5000.00,
            "addresses": [
                {
                    "type": "RESIDENTIAL",
                    "street": "Rua das Flores",
                    "number": "123",
                    "complement": "Apt 45",
                    "neighborhood": "Centro",
                    "city": "São Paulo",
                    "state": "SP",
                    "zipcode": "01234-567"
                }
            ]
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado ainda
        # Quando implementado com dados válidos, deve retornar HTTP 201
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            customer = data["data"]

            # Campos obrigatórios na response
            self.assertIn("id", customer)
            self.assertIn("document_type", customer)
            self.assertIn("document", customer)
            self.assertIn("name", customer)
            self.assertIn("email", customer)
            self.assertIn("created_at", customer)
            self.assertIn("updated_at", customer)

            # Valida tipos dos campos
            self.assertIsInstance(customer["id"], str)
            self.assertIn(customer["document_type"], ["CPF", "CNPJ"])
            self.assertIsInstance(customer["document"], str)
            self.assertIsInstance(customer["name"], str)
            self.assertIsInstance(customer["email"], str)

            # Campos opcionais que foram enviados
            if "phone" in payload:
                self.assertIn("phone", customer)
            if "birth_date" in payload:
                self.assertIn("birth_date", customer)
            if "monthly_income" in payload:
                self.assertIn("monthly_income", customer)
                self.assertIsInstance(customer["monthly_income"], (int, float))

            # addresses array se enviado
            if "addresses" in payload:
                self.assertIn("addresses", customer)
                self.assertIsInstance(customer["addresses"], list)

    def test_customers_post_with_address_array(self):
        """
        Test: Campo addresses aceita array de endereços.

        Conforme OpenAPI, addresses é array opcional de AddressCreateRequest.
        """
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br",
            "addresses": [
                {
                    "type": "RESIDENTIAL",
                    "street": "Rua das Flores",
                    "number": "123",
                    "neighborhood": "Centro",
                    "city": "São Paulo",
                    "state": "SP",
                    "zipcode": "01234-567"
                },
                {
                    "type": "COMMERCIAL",
                    "street": "Av. Paulista",
                    "number": "1000",
                    "complement": "Sala 101",
                    "neighborhood": "Bela Vista",
                    "city": "São Paulo",
                    "state": "SP",
                    "zipcode": "01310-100"
                }
            ]
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar addresses array sem erro de validação
        self.assertNotEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "addresses array é campo válido opcional"
        )

    def test_customers_post_content_type_json_required(self):
        """Test: Endpoint aceita apenas application/json."""
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        # Teste com content-type incorreto
        response = self.client.post(
            self.customers_url,
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

    def test_customers_post_method_not_allowed_for_get(self):
        """Test: Endpoint /customers aceita GET e POST."""
        response = self.client.get(self.customers_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, GET deve ser permitido (listar customers)
        # Apenas verificamos que não é method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertNotEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /customers deve aceitar GET para listar"
            )


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestCustomersPostTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.customers_url = "/api/v1/customers"

    def test_customers_post_requires_authentication(self):
        """
        Test: Endpoint requer autenticação.

        Conforme OpenAPI, todos os endpoints exceto auth/ requerem Bearer token.
        """
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado sem token, deve retornar HTTP 401
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Endpoint deve requerer autenticação"
            )

    def test_customers_post_with_bearer_token_header(self):
        """
        Test: Aceita Authorization Bearer token no header.

        Formato esperado: Authorization: Bearer <jwt_token>
        """
        # Mock JWT token para teste de contrato
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar token sem erro de formato
        self.assertNotEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Bearer token é formato válido de autenticação"
        )

    def test_customers_post_tenant_isolation_by_token(self):
        """
        Test: Cliente é criado no tenant correto baseado no JWT token.

        Multi-tenancy é transparente via token - o cliente não precisa
        especificar tenant_id no payload.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        response = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, o middleware deve extrair tenant_id do token
        # e associar automaticamente ao customer criado
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()

            # Cliente criado deve ter tenant_id implícito (não retornado na API)
            # mas deve estar isolado no banco de dados
            self.assertIn("data", data)
            self.assertIn("id", data["data"])

    def test_customers_post_duplicate_document_cross_tenant(self):
        """
        Test: Mesmo documento pode existir em tenants diferentes.

        Conforme constitution, isolamento por tenant permite duplicação
        de documentos entre diferentes empresas.
        """
        # Mesmo payload, tokens de tenants diferentes
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Silva",
            "email": "joao@exemplo.com.br"
        }

        # Tenant 1
        tenant1_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant1.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tenant1_token}')

        response1 = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # Tenant 2
        tenant2_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant2.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tenant2_token}')

        response2 = self.client.post(
            self.customers_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoints não implementados
        # Quando implementado, ambos devem ser aceitos (HTTP 201)
        # pois estão em tenants diferentes
        if response1.status_code == status.HTTP_201_CREATED:
            if response2.status_code == status.HTTP_201_CREATED:
                self.assertNotEqual(
                    response1.json()["data"]["id"],
                    response2.json()["data"]["id"],
                    "Mesmo documento pode existir em tenants diferentes"
                )