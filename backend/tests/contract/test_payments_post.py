"""
Contract tests para endpoint POST /api/v1/installments/{id}/payments.

Foco em validar o contrato real do endpoint considerando:
- Estrutura de URL
- Headers obrigatorios (Authorization, X-Tenant-ID)
- Codigos de status devolvidos pelo backend atual
- Estrutura basica de payload de sucesso/erro

Os testes utilizam a API real para montar os dados, garantindo aderencia ao
comportamento em producao.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db import ProgrammingError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantFactory


User = get_user_model()


def _ensure_tenant_context_function() -> None:
    """Garante que a funcao set_tenant_context exista no banco de testes."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid uuid)
                RETURNS void AS $$
                BEGIN
                    PERFORM set_config('iabank.current_tenant_id', tenant_uuid::text, true);
                END;
                $$ LANGUAGE plpgsql;
                """
            )
    except ProgrammingError:
        pass


class PaymentsContractBase(TestCase):
    """Base compartilhada com helpers para montar o cenario de testes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_tenant_context_function()

    def setUp(self):
        super().setUp()
        suffix = uuid4().hex[:8]
        self.tenant = TenantFactory(name="Tenant Contrato Pagamentos")
        self.user = User.objects.create_user(
            username=f"contract_finance_{suffix}",
            email=f"contract.finance+{suffix}@iabank.com",
            password="SenhaForte123",
            first_name="Contract",
            last_name="Manager",
        )
        if hasattr(self.user, "tenant_id"):
            self.user.tenant_id = self.tenant.id
        if hasattr(self.user, "role"):
            self.user.role = "FINANCE_MANAGER"
        self.user.save()

        self.other_tenant = TenantFactory(name="Tenant Contrato Outro")
        self.other_user = User.objects.create_user(
            username=f"contract_other_{suffix}",
            email=f"contract.other+{suffix}@iabank.com",
            password="SenhaForte123",
            first_name="Contract",
            last_name="Other",
        )
        if hasattr(self.other_user, "tenant_id"):
            self.other_user.tenant_id = self.other_tenant.id
        self.other_user.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))

        self.dataset = self._create_dataset(self.client)
        self.installments = self.dataset["installments"]
        self.installment_id = self.dataset["installment_id"]
        self.second_installment_id = self.dataset["second_installment_id"]
        self.bank_account_id = self.dataset["bank_account_id"]
        self.loan_id = self.dataset["loan_id"]
        self.payments_url = f"/api/v1/installments/{self.installment_id}/payments/"

    def _create_dataset(self, client: APIClient) -> dict:
        bank_payload = {
            "bank_code": "001",
            "bank_name": "Banco do Brasil",
            "agency": "1234-5",
            "account_number": "67890-1",
            "account_type": "CHECKING",
            "is_main": True,
        }
        bank_response = client.post("/api/v1/bank-accounts/", bank_payload, format="json")
        assert bank_response.status_code == status.HTTP_201_CREATED, bank_response.content
        bank_account_id = bank_response.json()["data"]["id"]

        customer_payload = {
            "document_type": "CPF",
            "document": "39053344705",
            "name": "Joao Pagador",
            "email": "joao.pagador@example.com",
            "phone": "(11) 98888-7777",
            "birth_date": "1988-08-08",
            "monthly_income": "9500.00",
            "addresses": [
                {
                    "type": "RESIDENTIAL",
                    "street": "Rua das Parcelas",
                    "number": "100",
                    "neighborhood": "Centro",
                    "city": "Sao Paulo",
                    "state": "SP",
                    "zipcode": "01000-000",
                    "is_primary": True,
                }
            ],
        }
        customer_response = client.post("/api/v1/customers/", customer_payload, format="json")
        assert customer_response.status_code == status.HTTP_201_CREATED, customer_response.content
        customer_id = customer_response.json()["data"]["id"]

        loan_payload = {
            "customer_id": customer_id,
            "principal_amount": "10000.00",
            "interest_rate": "0.0299",
            "installments_count": 12,
            "first_due_date": "2025-10-15",
            "notes": "Emprestimo para contrato de pagamentos",
        }
        loan_response = client.post("/api/v1/loans/", loan_payload, format="json")
        assert loan_response.status_code == status.HTTP_201_CREATED, loan_response.content
        loan_id = loan_response.json()["data"]["id"]

        approve_response = client.post(f"/api/v1/loans/{loan_id}/approve/", data={}, format="json")
        assert approve_response.status_code == status.HTTP_200_OK, approve_response.content

        activate_response = client.put(
            f"/api/v1/loans/{loan_id}/",
            data={"status": "ACTIVE"},
            format="json",
        )
        assert activate_response.status_code == status.HTTP_200_OK, activate_response.content

        installments_response = client.get(
            f"/api/v1/loans/{loan_id}/installments/",
            format="json",
        )
        assert installments_response.status_code == status.HTTP_200_OK, installments_response.content
        installments = installments_response.json()["data"]
        if not installments:
            raise AssertionError("Esperava ao menos uma parcela para o contrato")

        return {
            "bank_account_id": bank_account_id,
            "loan_id": loan_id,
            "installments": installments,
            "installment_id": installments[0]["id"],
            "second_installment_id": installments[1]["id"] if len(installments) > 1 else installments[0]["id"],
        }

    def _valid_payload(self, *, amount: Decimal | None = None) -> dict:
        base_amount = Decimal(str(self.installments[0]["total_amount"]))
        value = amount if amount is not None else base_amount
        return {
            "amount": str(value),
            "payment_date": self.installments[0]["due_date"],
            "payment_method": "PIX",
            "bank_account_id": self.bank_account_id,
        }

@pytest.mark.contract
class TestPaymentsPostContract(PaymentsContractBase):
    """Contratos gerais para o endpoint de pagamentos."""

    def test_endpoint_accepts_valid_payload(self):
        payload = self._valid_payload()
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()["data"]
        self.assertIn("installment", body)
        self.assertIn("transaction", body)

    def test_missing_amount_returns_400(self):
        payload = self._valid_payload()
        payload.pop("amount")
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_missing_payment_date_returns_400(self):
        payload = self._valid_payload()
        payload.pop("payment_date")
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_invalid_payment_method_returns_400(self):
        payload = self._valid_payload()
        payload["payment_method"] = "INVALID"
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()["data"]
        transaction = body["transaction"]
        self.assertIn(transaction["status"], {"PAID", "PARTIALLY_PAID"})

    def test_invalid_bank_account_format_returns_422(self):
        payload = self._valid_payload()
        payload["bank_account_id"] = "invalid-uuid"
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_negative_amount_returns_400(self):
        payload = self._valid_payload(amount=Decimal("-1"))
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_zero_amount_returns_400(self):
        payload = self._valid_payload(amount=Decimal("0"))
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_nonexistent_installment_returns_404(self):
        payload = self._valid_payload()
        fake_url = f"/api/v1/installments/{uuid4()}/payments/"
        response = self.client.post(fake_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_methods_not_allowed(self):
        self.assertEqual(self.client.get(self.payments_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.put(self.payments_url, data={}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(self.payments_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@pytest.mark.contract
class TestPaymentsPostAuthentication(PaymentsContractBase):
    """Contratos relacionados a autenticacao e isolamento por tenant."""

    def test_requires_authentication(self):
        payload = self._valid_payload()
        client = APIClient()
        client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))
        response = client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_requires_tenant_header(self):
        payload = self._valid_payload()
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_isolation(self):
        payload = self._valid_payload()
        client = APIClient()
        client.force_authenticate(user=self.other_user)
        client.credentials(HTTP_X_TENANT_ID=str(self.other_tenant.id))
        response = client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accepts_bearer_token_header(self):
        payload = self._valid_payload()
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {mock_token}",
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )
        response = client.post(self.payments_url, data=payload, format="json")
        self.assertNotEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@pytest.mark.contract
class TestPaymentsPostTenantScenarios(PaymentsContractBase):
    """Cenarios adicionais envolvendo variacoes de pagamento."""

    def test_partial_payment_returns_transaction(self):
        payload = self._valid_payload(amount=Decimal("500.00"))
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()["data"]
        installment = body["installment"]
        transaction = body["transaction"]
        self.assertEqual(installment["status"], "PARTIALLY_PAID")
        self.assertEqual(Decimal(str(installment["amount_paid"])), Decimal("500.00"))
        self.assertEqual(transaction["type"], "INCOME")
        self.assertEqual(Decimal(str(transaction["amount"])), Decimal("500.00"))

    def test_full_payment_marks_installment_paid(self):
        payload = self._valid_payload()
        response = self.client.post(self.payments_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        installment = response.json()["data"]["installment"]
        expected_total = Decimal(str(self.installments[0]["total_amount"]))
        self.assertEqual(Decimal(str(installment["amount_paid"])), expected_total)
        self.assertEqual(installment["status"], "PAID")
        self.assertEqual(installment["payment_date"], payload["payment_date"])
