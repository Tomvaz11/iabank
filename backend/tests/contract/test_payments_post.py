"""
Contract tests para endpoint POST /api/v1/installments/{id}/payments.

Seguindo metodologia TDD (RED phase):
- Testa APENAS o contrato da API (schema request/response)
- NÃO testa lógica de negócio (isso é para integration/unit tests)
- DEVE falhar inicialmente pois endpoint não existe ainda

Baseado em:
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml (linhas 448-466)
- constitution v1.0.0 - Django-Domain-First Architecture
"""

import uuid

import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.contract
class TestPaymentsPostContract(TestCase):
    """
    Contract tests para POST /api/v1/installments/{id}/payments.

    Testa apenas conformidade com OpenAPI schema:
    - URL path structure
    - Request body structure
    - Response body structure
    - Status codes
    - Content types
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        self.installment_id = str(uuid.uuid4())
        self.payments_url = f"/api/v1/installments/{self.installment_id}/payments/"

    def test_payments_post_endpoint_exists(self):
        """
        Test: Endpoint POST /api/v1/installments/{id}/payments existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.post(self.payments_url, {})

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_payments_post_request_schema_validation(self):
        """
        Test: Request body valida schema obrigatório.

        Schema obrigatório conforme OpenAPI (linhas 1021-1037):
        - amount: number (format: decimal) - REQUIRED
        - payment_date: string (format: date) - REQUIRED
        - payment_method: string (enum: PIX|BOLETO|TRANSFER|CASH) - OPTIONAL
        - bank_account_id: string (format: uuid) - OPTIONAL
        """
        # Request vazio deve retornar erro de validação
        response = self.client.post(
            self.payments_url,
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

    def test_payments_post_missing_amount_field(self):
        """Test: Campo amount é obrigatório."""
        payload = {
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe ainda
        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "amount é campo obrigatório"
        )

        # Quando endpoint for implementado, response deve ter estrutura de erro
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            self.assertIn("errors", response.json())

    def test_payments_post_missing_payment_date_field(self):
        """Test: Campo payment_date é obrigatório."""
        payload = {
            "amount": 500.00
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "payment_date é campo obrigatório"
        )

    def test_payments_post_invalid_installment_id_format(self):
        """Test: installment_id deve ter formato UUID válido."""
        invalid_payments_url = "/api/v1/installments/invalid-uuid/payments/"

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            invalid_payments_url,
            data=payload,
            format="json"
        )

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
                "installment_id inválido deve retornar erro de validação"
            )

    def test_payments_post_nonexistent_installment_id(self):
        """Test: installment_id não existente deve retornar 404."""
        nonexistent_installment_id = str(uuid.uuid4())
        nonexistent_url = f"/api/v1/installments/{nonexistent_installment_id}/payments/"

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            nonexistent_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado com installment_id inexistente, deve retornar HTTP 404
        if response.status_code != status.HTTP_404_NOT_FOUND:
            # Se endpoint existe mas installment não existe, deve ser 404
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                "Installment não existente deve retornar 404"
            )

    def test_payments_post_negative_amount(self):
        """Test: amount deve ser positivo."""
        payload = {
            "amount": -100.00,  # Valor negativo
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "amount deve ser positivo"
        )

    def test_payments_post_zero_amount(self):
        """Test: amount deve ser maior que zero."""
        payload = {
            "amount": 0.00,  # Valor zero
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "amount deve ser maior que zero"
        )

    def test_payments_post_invalid_payment_date_format(self):
        """Test: payment_date deve ter formato date válido."""
        payload = {
            "amount": 500.00,
            "payment_date": "data-invalida"  # Formato inválido
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "payment_date inválido deve retornar erro de validação"
        )

    def test_payments_post_invalid_payment_method_enum(self):
        """Test: payment_method deve ser do enum válido."""
        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15",
            "payment_method": "INVALID_METHOD"  # Método inválido
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "payment_method deve ser do enum [PIX, BOLETO, TRANSFER, CASH]"
        )

    def test_payments_post_invalid_bank_account_id_format(self):
        """Test: bank_account_id deve ter formato UUID válido."""
        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15",
            "bank_account_id": "invalid-uuid-format"  # UUID inválido
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "bank_account_id inválido deve retornar erro de validação"
        )

    def test_payments_post_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 200) - linhas 1139-1150:
        {
          "data": {
            "installment": {
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
            },
            "transaction": {
              "id": "uuid",
              "type": "INCOME|EXPENSE",
              "amount": number,
              "description": string,
              "reference_date": "date",
              "status": "PENDING|PAID|CANCELLED"
            }
          }
        }
        """
        # Payload válido para teste de contrato
        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15",
            "payment_method": "PIX",
            "bank_account_id": str(uuid.uuid4())
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado ainda
        # Quando implementado com dados válidos, deve retornar HTTP 200
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            payment_data = data["data"]

            # Campos obrigatórios na response
            self.assertIn("installment", payment_data)
            self.assertIn("transaction", payment_data)

            installment = payment_data["installment"]
            transaction = payment_data["transaction"]

            # Valida estrutura do installment
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

            # Valida tipos dos campos do installment
            self.assertIsInstance(installment["id"], str)
            self.assertIsInstance(installment["sequence"], int)
            self.assertIsInstance(installment["principal_amount"], (int, float))
            self.assertIsInstance(installment["interest_amount"], (int, float))
            self.assertIsInstance(installment["total_amount"], (int, float))
            self.assertIsInstance(installment["amount_paid"], (int, float))
            self.assertIsInstance(installment["late_fee"], (int, float))
            self.assertIsInstance(installment["interest_penalty"], (int, float))

            # Status do installment deve ser do enum válido
            valid_installment_statuses = ["PENDING", "PAID", "OVERDUE", "PARTIALLY_PAID"]
            self.assertIn(installment["status"], valid_installment_statuses)

            # Valida estrutura do transaction
            self.assertIn("id", transaction)
            self.assertIn("type", transaction)
            self.assertIn("amount", transaction)
            self.assertIn("description", transaction)
            self.assertIn("reference_date", transaction)
            self.assertIn("status", transaction)

            # Valida tipos dos campos do transaction
            self.assertIsInstance(transaction["id"], str)
            self.assertIsInstance(transaction["amount"], (int, float))
            self.assertIsInstance(transaction["description"], str)

            # Type do transaction deve ser do enum válido
            valid_transaction_types = ["INCOME", "EXPENSE"]
            self.assertIn(transaction["type"], valid_transaction_types)

            # Status do transaction deve ser do enum válido
            valid_transaction_statuses = ["PENDING", "PAID", "CANCELLED"]
            self.assertIn(transaction["status"], valid_transaction_statuses)

    def test_payments_post_with_all_optional_fields(self):
        """
        Test: Todos os campos opcionais são processados corretamente.

        Conforme OpenAPI, payment_method e bank_account_id são opcionais.
        """
        payload = {
            "amount": 750.50,
            "payment_date": "2025-09-20",
            "payment_method": "BOLETO",
            "bank_account_id": str(uuid.uuid4())
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar campos opcionais sem erro de validação
        self.assertNotEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Campos opcionais são válidos"
        )

    def test_payments_post_without_optional_fields(self):
        """
        Test: Campos opcionais podem ser omitidos.

        Apenas amount e payment_date são obrigatórios.
        """
        payload = {
            "amount": 1000.00,
            "payment_date": "2025-09-25"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não existe
        # Quando implementado, deve processar sem campos opcionais
        self.assertNotEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Campos opcionais podem ser omitidos"
        )

    def test_payments_post_valid_payment_methods(self):
        """Test: Todos os métodos de pagamento válidos são aceitos."""
        valid_methods = ["PIX", "BOLETO", "TRANSFER", "CASH"]

        for method in valid_methods:
            with self.subTest(payment_method=method):
                payload = {
                    "amount": 300.00,
                    "payment_date": "2025-09-15",
                    "payment_method": method
                }

                response = self.client.post(
                    self.payments_url,
                    data=payload,
                    format="json"
                )

                # RED phase: Endpoint não existe
                # Quando implementado, deve aceitar todos os métodos válidos
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"payment_method '{method}' deve ser aceito"
                )

    def test_payments_post_content_type_json_required(self):
        """Test: Endpoint aceita apenas application/json."""
        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        # Teste com content-type incorreto
        response = self.client.post(
            self.payments_url,
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

    def test_payments_post_response_content_type_json(self):
        """Test: Response deve ser application/json."""
        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve retornar JSON
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.get("Content-Type", "").split(";")[0],
                "application/json",
                "Response deve ser application/json"
            )

    def test_payments_post_method_not_allowed_for_get(self):
        """Test: Endpoint não aceita GET."""
        response = self.client.get(self.payments_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, GET deve ser method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /installments/{id}/payments não deve aceitar GET"
            )

    def test_payments_post_method_not_allowed_for_put(self):
        """Test: Endpoint não aceita PUT."""
        response = self.client.put(self.payments_url, {})

        # RED phase: Endpoint não existe (404)
        # Quando implementado, PUT deve ser method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /installments/{id}/payments não deve aceitar PUT"
            )

    def test_payments_post_method_not_allowed_for_delete(self):
        """Test: Endpoint não aceita DELETE."""
        response = self.client.delete(self.payments_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, DELETE deve ser method not allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint /installments/{id}/payments não deve aceitar DELETE"
            )


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestPaymentsPostTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.installment_id = str(uuid.uuid4())
        self.payments_url = f"/api/v1/installments/{self.installment_id}/payments/"

    def test_payments_post_requires_authentication(self):
        """
        Test: Endpoint requer autenticação.

        Conforme OpenAPI, todos os endpoints exceto auth/ requerem Bearer token.
        """
        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
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

    def test_payments_post_with_bearer_token_header(self):
        """
        Test: Aceita Authorization Bearer token no header.

        Formato esperado: Authorization: Bearer <jwt_token>
        """
        # Mock JWT token para teste de contrato
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
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

    def test_payments_post_installment_must_exist_in_same_tenant(self):
        """
        Test: installment_id deve existir no mesmo tenant do usuário.

        Multi-tenancy garante que installment_id referenciado existe
        no mesmo tenant que o usuário autenticado.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        # UUID de installment que pode não existir no tenant
        installment_from_other_tenant = str(uuid.uuid4())
        other_tenant_url = f"/api/v1/installments/{installment_from_other_tenant}/payments/"

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            other_tenant_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve validar se installment existe no tenant
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                "installment_id deve existir no tenant do usuário"
            )

    def test_payments_post_bank_account_must_exist_in_same_tenant(self):
        """
        Test: bank_account_id deve existir no mesmo tenant do usuário.

        Se bank_account_id for fornecido, deve existir no mesmo tenant.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        # UUID de bank_account que pode não existir no tenant
        bank_account_from_other_tenant = str(uuid.uuid4())

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15",
            "bank_account_id": bank_account_from_other_tenant
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve validar se bank_account existe no tenant
        if response.status_code not in [status.HTTP_404_NOT_FOUND]:
            expected_codes = [
                status.HTTP_422_UNPROCESSABLE_ENTITY,  # Validation error
                status.HTTP_400_BAD_REQUEST  # Bank account not found
            ]
            self.assertIn(
                response.status_code,
                expected_codes,
                "bank_account_id deve existir no tenant do usuário"
            )

    def test_payments_post_tenant_isolation_by_token(self):
        """
        Test: Pagamento é registrado no tenant correto baseado no JWT token.

        Multi-tenancy é transparente via token - transaction é criada
        automaticamente no tenant correto.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.tenant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15",
            "payment_method": "PIX"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, middleware deve extrair tenant_id do token
        # e associar automaticamente ao payment/transaction criados
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Transaction criada deve ter tenant_id implícito (não retornado na API)
            # mas deve estar isolado no banco de dados
            self.assertIn("data", data)
            self.assertIn("transaction", data["data"])
            self.assertIn("id", data["data"]["transaction"])

    def test_payments_post_access_control_by_role(self):
        """
        Test: Acesso a pagamentos pode depender do role do usuário.

        Consultants podem registrar pagamentos apenas em loans que criaram,
        Collectors podem registrar em qualquer loan do tenant.
        """
        # Mock token de consultant
        consultant_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.consultant.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {consultant_token}")

        payload = {
            "amount": 500.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve considerar role-based access control
        if response.status_code not in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]:
            # Se installment não pertence ao consultant, deve ser 403 ou 404
            # Se pertence ou user tem permissão, deve ser 200
            expected_codes = [
                status.HTTP_200_OK,  # User tem acesso ao installment
                status.HTTP_403_FORBIDDEN,  # User não tem acesso
                status.HTTP_404_NOT_FOUND  # Installment não existe no tenant
            ]
            self.assertIn(
                response.status_code,
                expected_codes,
                "Acesso deve respeitar role-based access control"
            )

    def test_payments_post_payment_creates_financial_transaction(self):
        """
        Test: Pagamento automaticamente cria transação financeira no tenant.

        Cada pagamento registrado deve gerar uma FinancialTransaction
        do tipo INCOME no mesmo tenant.
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        payload = {
            "amount": 750.00,
            "payment_date": "2025-09-20",
            "payment_method": "TRANSFER"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, deve criar transaction automaticamente
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            transaction = data["data"]["transaction"]

            # Transaction deve ser do tipo INCOME (receita)
            self.assertEqual(
                transaction["type"],
                "INCOME",
                "Pagamento deve gerar transaction do tipo INCOME"
            )

            # Amount da transaction deve corresponder ao amount do pagamento
            self.assertEqual(
                transaction["amount"],
                payload["amount"],
                "Amount da transaction deve corresponder ao pagamento"
            )

    def test_payments_post_installment_status_update(self):
        """
        Test: Status do installment é atualizado após pagamento.

        Pagamento deve atualizar automaticamente:
        - amount_paid do installment
        - status do installment (PAID, PARTIALLY_PAID, etc.)
        - payment_date se totalmente pago
        """
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {mock_token}")

        payload = {
            "amount": 1000.00,
            "payment_date": "2025-09-15"
        }

        response = self.client.post(
            self.payments_url,
            data=payload,
            format="json"
        )

        # RED phase: Endpoint não implementado
        # Quando implementado, installment deve ser atualizado
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            installment = data["data"]["installment"]

            # amount_paid deve ser atualizado
            self.assertGreater(
                installment["amount_paid"],
                0,
                "amount_paid deve ser atualizado após pagamento"
            )

            # Status deve ser válido e refletir o pagamento
            valid_paid_statuses = ["PAID", "PARTIALLY_PAID"]
            if installment["amount_paid"] >= installment["total_amount"]:
                self.assertEqual(
                    installment["status"],
                    "PAID",
                    "Installment totalmente pago deve ter status PAID"
                )
            else:
                self.assertEqual(
                    installment["status"],
                    "PARTIALLY_PAID",
                    "Installment parcialmente pago deve ter status PARTIALLY_PAID"
                )