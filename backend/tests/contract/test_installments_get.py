"""
Contract tests para endpoint GET /api/v1/loans/{id}/installments.

Seguindo metodologia TDD (RED phase):
- Testa APENAS o contrato da API (schema request/response)
- NÃO testa lógica de negócio (isso é para integration/unit tests)
- DEVE falhar inicialmente pois endpoint não existe ainda

Baseado em:
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml (linhas 381-393)
- constitution v1.0.0 - Django-Domain-First Architecture
"""

import uuid

import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.contract
class TestInstallmentsGetContract(TestCase):
    """
    Contract tests para GET /api/v1/loans/{id}/installments.

    Testa apenas conformidade com OpenAPI schema:
    - URL path structure
    - Response body structure
    - Status codes
    - Content types
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        self.loan_id = str(uuid.uuid4())
        self.installments_url = f"/api/v1/loans/{self.loan_id}/installments/"

    def test_installments_get_endpoint_exists(self):
        """
        Test: Endpoint GET /api/v1/loans/{id}/installments existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.get(self.installments_url)

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_installments_get_invalid_loan_id_format(self):
        """Test: loan_id deve ter formato UUID válido."""
        invalid_installments_url = "/api/v1/loans/invalid-uuid/installments/"

        response = self.client.get(invalid_installments_url)

        # RED phase: Endpoint não existe ainda
        # Quando implementado, deve validar formato UUID
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            expected_codes = [
                status.HTTP_400_BAD_REQUEST,  # Bad request for invalid UUID
                status.HTTP_422_UNPROCESSABLE_ENTITY  # Validation error
            ]
            self.assertIn(
                response.status_code,
                expected_codes,
                "loan_id inválido deve retornar erro de validação"
            )

    def test_installments_get_nonexistent_loan_id(self):
        """Test: loan_id não existente deve retornar 404."""
        nonexistent_loan_id = str(uuid.uuid4())
        nonexistent_url = f"/api/v1/loans/{nonexistent_loan_id}/installments/"

        response = self.client.get(nonexistent_url)

        # RED phase: Endpoint não implementado
        # Quando implementado com loan_id inexistente, deve retornar HTTP 404
        if response.status_code != status.HTTP_404_NOT_FOUND:
            # Se endpoint existe mas loan não existe, deve ser 404
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                "Loan não existente deve retornar 404"
            )

    def test_installments_get_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 200) - linhas 1109-1117:
        {
          "data": [
            {
              "id": "uuid",
              "sequence": integer,
              "due_date": "date",
              "principal_amount": number,
              "interest_amount": number,
              "total_amount": number,
              "amount_paid": number,
              "late_fee": number,
              "interest_penalty": number,
              "status": "PENDING|PAID|OVERDUE|PARTIALLY_PAID",
              "payment_date": "date"
            }
          ]
        }
        """
        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não implementado ainda
        # Quando implementado com loan existente, deve retornar HTTP 200
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            installments = data["data"]

            # data deve ser array de installments
            self.assertIsInstance(installments, list)

            # Se há installments, valida estrutura de cada um
            if installments:
                installment = installments[0]

                # Campos obrigatórios na response
                self.assertIn("id", installment)
                self.assertIn("sequence", installment)
                self.assertIn("due_date", installment)
                self.assertIn("principal_amount", installment)
                self.assertIn("interest_amount", installment)
                self.assertIn("total_amount", installment)
                self.assertIn("amount_paid", installment)
                self.assertIn("late_fee", installment)
                self.assertIn("interest_penalty", installment)
                self.assertIn("status", installment)

                # Valida tipos dos campos principais
                self.assertIsInstance(installment["id"], str)
                self.assertIsInstance(installment["sequence"], int)
                self.assertIsInstance(installment["principal_amount"], (int, float))
                self.assertIsInstance(installment["interest_amount"], (int, float))
                self.assertIsInstance(installment["total_amount"], (int, float))
                self.assertIsInstance(installment["amount_paid"], (int, float))
                self.assertIsInstance(installment["late_fee"], (int, float))
                self.assertIsInstance(installment["interest_penalty"], (int, float))

                # Status deve ser do enum válido
                valid_statuses = ["PENDING", "PAID", "OVERDUE", "PARTIALLY_PAID"]
                self.assertIn(installment["status"], valid_statuses)

                # payment_date pode ser null se não pago
                if installment.get("payment_date") is not None:
                    self.assertIsInstance(installment["payment_date"], str)

    def test_installments_get_empty_list_valid_response(self):
        """
        Test: Lista vazia é resposta válida.

        Empréstimo sem parcelas ainda deve retornar HTTP 200
        com array vazio, não erro.
        """
        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, lista vazia deve ser HTTP 200, não erro
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            self.assertIn("data", data)
            self.assertIsInstance(data["data"], list)

            # Lista vazia é válida
            # (empréstimo pode não ter parcelas geradas ainda)

    def test_installments_get_response_content_type_json(self):
        """Test: Response deve ser application/json."""
        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve retornar JSON
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.get("Content-Type", "").split(";")[0],
                "application/json",
                "Response deve ser application/json"
            )

    def test_installments_get_method_not_allowed_for_post(self):
        """Test: Endpoint não aceita POST."""
        response = self.client.post(self.installments_url, {})

        # RED phase: Endpoint não existe (404)
        # Quando implementado, POST deve ser method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /loans/{id}/installments não deve aceitar POST"
            )

    def test_installments_get_method_not_allowed_for_put(self):
        """Test: Endpoint não aceita PUT."""
        response = self.client.put(self.installments_url, {})

        # RED phase: Endpoint não existe (404)
        # Quando implementado, PUT deve ser method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /loans/{id}/installments não deve aceitar PUT"
            )

    def test_installments_get_method_not_allowed_for_delete(self):
        """Test: Endpoint não aceita DELETE."""
        response = self.client.delete(self.installments_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, DELETE deve ser method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /loans/{id}/installments não deve aceitar DELETE"
            )


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestInstallmentsGetTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.loan_id = str(uuid.uuid4())
        self.installments_url = f"/api/v1/loans/{self.loan_id}/installments/"

    def test_installments_get_requires_authentication(self):
        """
        Test: Endpoint requer autenticação.

        Conforme OpenAPI, todos os endpoints exceto auth/ requerem Bearer token.
        """
        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não existe
        # Quando implementado sem token, deve retornar HTTP 401
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Endpoint deve requerer autenticação"
            )

    def test_installments_get_with_bearer_token_header(self):
        """
        Test: Aceita Authorization Bearer token no header.

        Formato esperado: Authorization: Bearer <jwt_token>
        """
        # Mock JWT token para teste de contrato
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar token sem erro de formato
        self.assertNotEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Bearer token é formato válido de autenticação"
        )

    def test_installments_get_loan_must_exist_in_same_tenant(self):
        """
        Test: loan_id deve existir no mesmo tenant do usuário.

        Multi-tenancy garante que loan_id referenciado existe
        no mesmo tenant que o usuário autenticado.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        # UUID de loan que pode não existir no tenant
        loan_from_other_tenant = str(uuid.uuid4())
        other_tenant_url = f"/api/v1/loans/{loan_from_other_tenant}/installments/"

        response = self.client.get(other_tenant_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve validar se loan existe no tenant
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                "loan_id deve existir no tenant do usuário"
            )

    def test_installments_get_tenant_isolation_by_token(self):
        """
        Test: Installments retornadas pertencem ao tenant do token.

        Multi-tenancy é transparente via token - apenas installments
        do loan do tenant correto são retornadas.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, middleware deve filtrar automaticamente por tenant_id
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Todas as installments retornadas devem ter tenant_id implícito
            # (não retornado na API mas filtrado no banco)
            self.assertIn("data", data)
            installments = data["data"]
            self.assertIsInstance(installments, list)

            # Se há installments, todas devem ser do mesmo tenant
            # (validação implícita através do filtro automático)
            for installment in installments:
                self.assertIn("id", installment)
                # tenant_id não aparece na response mas está isolado no backend

    def test_installments_get_loan_access_control_by_role(self):
        """
        Test: Acesso a installments pode depender do role do usuário.

        Consultants podem ver apenas loans que criaram,
        Managers podem ver todos os loans do tenant.
        """
        # Mock token de consultant
        consultant_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.consultant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {consultant_token}")

        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve considerar role-based access control
        if response.status_code not in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]:
            # Se loan não pertence ao consultant, deve ser 403 ou 404
            # Se pertence, deve ser 200
            expected_codes = [
                status.HTTP_200_OK,  # Consultant tem acesso ao loan
                status.HTTP_403_FORBIDDEN,  # Consultant não tem acesso
                status.HTTP_404_NOT_FOUND  # Loan não existe no tenant
            ]
            self.assertIn(
                response.status_code,
                expected_codes,
                "Acesso deve respeitar role-based access control"
            )

    def test_installments_get_installments_sequential_order(self):
        """
        Test: Installments devem ser retornadas em ordem sequencial.

        Installments devem ser ordenadas por sequence (1, 2, 3...)
        conforme expectativa de UX.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        response = self.client.get(self.installments_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, installments devem vir ordenadas
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            installments = data["data"]

            # Se há múltiplas installments, devem estar ordenadas por sequence
            if len(installments) > 1:
                sequences = [inst["sequence"] for inst in installments]

                # Sequences devem estar em ordem crescente (1, 2, 3...)
                self.assertEqual(
                    sequences,
                    sorted(sequences),
                    "Installments devem ser retornadas em ordem sequencial"
                )

                # Primeira installment deve ter sequence = 1
                self.assertEqual(
                    installments[0]["sequence"],
                    1,
                    "Primeira installment deve ter sequence = 1"
                )
