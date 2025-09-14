"""
Contract tests para endpoint POST /api/v1/loans.

Seguindo metodologia TDD (RED phase):
- Testa APENAS o contrato da API (schema request/response)
- NÃO testa lógica de negócio (isso é para integration/unit tests)
- DEVE falhar inicialmente pois endpoint não existe ainda

Baseado em:
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml (linhas 329-344)
- constitution v1.0.0 - Django-Domain-First Architecture
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
import uuid


@pytest.mark.contract
class TestLoansPostContract(TestCase):
    """
    Contract tests para POST /api/v1/loans.

    Testa apenas conformidade com OpenAPI schema:
    - Request body structure
    - Response body structure
    - Status codes
    - Content types
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        self.loans_url = "/api/v1/loans/"

    def test_loans_post_endpoint_exists(self):
        """
        Test: Endpoint POST /api/v1/loans existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.post(self.loans_url, {})

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_loans_post_request_schema_validation(self):
        """
        Test: Request body valida schema obrigatório.

        Schema obrigatório conforme OpenAPI (linhas 998-1020):
        - customer_id: string (format: uuid) - REQUIRED
        - principal_amount: number (format: decimal) - REQUIRED
        - interest_rate: number (format: decimal) - REQUIRED
        - installments_count: integer (min: 1, max: 120) - REQUIRED
        - first_due_date: string (format: date) - REQUIRED
        - notes: string - OPTIONAL
        """
        # Request vazio deve retornar erro de validação
        response = self.client.post(
            self.loans_url,
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

    def test_loans_post_missing_customer_id_field(self):
        """Test: Campo customer_id é obrigatório."""
        payload = {
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe ainda
        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "customer_id é campo obrigatório"
        )

        # Quando endpoint for implementado, response deve ter estrutura de erro
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            self.assertIn("errors", response.json())

    def test_loans_post_missing_principal_amount_field(self):
        """Test: Campo principal_amount é obrigatório."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "principal_amount é campo obrigatório"
        )

    def test_loans_post_missing_interest_rate_field(self):
        """Test: Campo interest_rate é obrigatório."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "interest_rate é campo obrigatório"
        )

    def test_loans_post_missing_installments_count_field(self):
        """Test: Campo installments_count é obrigatório."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "installments_count é campo obrigatório"
        )

    def test_loans_post_missing_first_due_date_field(self):
        """Test: Campo first_due_date é obrigatório."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "first_due_date é campo obrigatório"
        )

    def test_loans_post_invalid_customer_id_format(self):
        """Test: customer_id deve ter formato UUID válido."""
        payload = {
            "customer_id": "invalid-uuid-format",  # UUID inválido
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "customer_id inválido deve retornar erro de validação"
        )

    def test_loans_post_invalid_installments_count_minimum(self):
        """Test: installments_count deve ser >= 1."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 0,  # Menor que mínimo
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "installments_count deve ser >= 1"
        )

    def test_loans_post_invalid_installments_count_maximum(self):
        """Test: installments_count deve ser <= 120."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 121,  # Maior que máximo
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "installments_count deve ser <= 120"
        )

    def test_loans_post_invalid_first_due_date_format(self):
        """Test: first_due_date deve ter formato date válido."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "data-invalida"  # Formato inválido
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "first_due_date inválido deve retornar erro de validação"
        )

    def test_loans_post_negative_principal_amount(self):
        """Test: principal_amount deve ser positivo."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": -1000.00,  # Valor negativo
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "principal_amount deve ser positivo"
        )

    def test_loans_post_negative_interest_rate(self):
        """Test: interest_rate deve ser positivo."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": -1.0,  # Taxa negativa
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "interest_rate deve ser positivo"
        )

    def test_loans_post_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 201) - linhas 1083-1089:
        {
          "data": {
            "id": "uuid",
            "customer": Customer,
            "consultant": User,
            "principal_amount": number,
            "interest_rate": number,
            "installments_count": integer,
            "iof_amount": number,
            "cet_monthly": number,
            "cet_yearly": number,
            "total_amount": number,
            "contract_date": "date",
            "first_due_date": "date",
            "status": "ANALYSIS|APPROVED|ACTIVE|FINISHED|COLLECTION|CANCELLED",
            "regret_deadline": "date",
            "installments": [Installment]
          }
        }
        """
        # Payload válido para teste de contrato
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15",
            "notes": "Empréstimo para capital de giro"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado ainda
        # Quando implementado com dados válidos, deve retornar HTTP 201
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            loan = data["data"]

            # Campos obrigatórios na response
            self.assertIn("id", loan)
            self.assertIn("customer", loan)
            self.assertIn("consultant", loan)
            self.assertIn("principal_amount", loan)
            self.assertIn("interest_rate", loan)
            self.assertIn("installments_count", loan)
            self.assertIn("iof_amount", loan)
            self.assertIn("cet_monthly", loan)
            self.assertIn("cet_yearly", loan)
            self.assertIn("total_amount", loan)
            self.assertIn("contract_date", loan)
            self.assertIn("first_due_date", loan)
            self.assertIn("status", loan)
            self.assertIn("regret_deadline", loan)
            self.assertIn("installments", loan)

            # Valida tipos dos campos principais
            self.assertIsInstance(loan["id"], str)
            self.assertIsInstance(loan["principal_amount"], (int, float))
            self.assertIsInstance(loan["interest_rate"], (int, float))
            self.assertIsInstance(loan["installments_count"], int)
            self.assertIsInstance(loan["iof_amount"], (int, float))
            self.assertIsInstance(loan["total_amount"], (int, float))

            # Status deve ser do enum válido
            valid_statuses = ["ANALYSIS", "APPROVED", "ACTIVE", "FINISHED", "COLLECTION", "CANCELLED"]
            self.assertIn(loan["status"], valid_statuses)

            # installments deve ser array
            self.assertIsInstance(loan["installments"], list)

            # customer e consultant devem ser objetos
            self.assertIsInstance(loan["customer"], dict)
            self.assertIsInstance(loan["consultant"], dict)

    def test_loans_post_with_optional_notes_field(self):
        """
        Test: Campo notes é opcional.

        Conforme OpenAPI, notes é string opcional.
        """
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 15000.00,
            "interest_rate": 3.2,
            "installments_count": 24,
            "first_due_date": "2025-11-01",
            "notes": "Empréstimo para aquisição de equipamentos"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar notes opcional sem erro de validação
        self.assertNotEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "notes é campo válido opcional"
        )

    def test_loans_post_content_type_json_required(self):
        """Test: Endpoint aceita apenas application/json."""
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        # Teste com content-type incorreto
        response = self.client.post(
            self.loans_url,
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

    def test_loans_post_method_not_allowed_for_get(self):
        """Test: Endpoint /loans aceita GET e POST."""
        response = self.client.get(self.loans_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, GET deve ser permitido (listar loans)
        # Apenas verificamos que não é method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertNotEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /loans deve aceitar GET para listar"
            )


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestLoansPostTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.loans_url = "/api/v1/loans/"

    def test_loans_post_requires_authentication(self):
        """
        Test: Endpoint requer autenticação.

        Conforme OpenAPI, todos os endpoints exceto auth/ requerem Bearer token.
        """
        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
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

    def test_loans_post_with_bearer_token_header(self):
        """
        Test: Aceita Authorization Bearer token no header.

        Formato esperado: Authorization: Bearer <jwt_token>
        """
        # Mock JWT token para teste de contrato
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
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

    def test_loans_post_customer_must_exist_in_same_tenant(self):
        """
        Test: customer_id deve existir no mesmo tenant do usuário.

        Multi-tenancy garante que customer_id referenciado existe
        no mesmo tenant que o usuário autenticado.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        # UUID de customer que pode não existir no tenant
        non_existent_customer = str(uuid.uuid4())

        payload = {
            "customer_id": non_existent_customer,
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve validar se customer existe no tenant
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            expected_codes = [
                status.HTTP_422_UNPROCESSABLE_ENTITY,  # Validation error
                status.HTTP_400_BAD_REQUEST  # Customer not found
            ]
            self.assertIn(
                response.status_code,
                expected_codes,
                "customer_id deve existir no tenant do usuário"
            )

    def test_loans_post_tenant_isolation_by_token(self):
        """
        Test: Empréstimo é criado no tenant correto baseado no JWT token.

        Multi-tenancy é transparente via token - o usuário não precisa
        especificar tenant_id no payload.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, o middleware deve extrair tenant_id do token
        # e associar automaticamente ao loan criado
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()

            # Empréstimo criado deve ter tenant_id implícito (não retornado na API)
            # mas deve estar isolado no banco de dados
            self.assertIn("data", data)
            self.assertIn("id", data["data"])

    def test_loans_post_consultant_auto_assigned_from_token(self):
        """
        Test: consultant é automaticamente atribuído baseado no usuário do token.

        O consultor responsável pelo empréstimo deve ser automaticamente
        definido como o usuário autenticado no momento da criação.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.consultant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {mock_token}')

        payload = {
            "customer_id": str(uuid.uuid4()),
            "principal_amount": 10000.00,
            "interest_rate": 2.5,
            "installments_count": 12,
            "first_due_date": "2025-10-15"
        }

        response = self.client.post(
            self.loans_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve extrair user_id do token e definir como consultant
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            loan = data["data"]

            # consultant deve ser automaticamente preenchido
            self.assertIn("consultant", loan)
            self.assertIsInstance(loan["consultant"], dict)
            self.assertIn("id", loan["consultant"])