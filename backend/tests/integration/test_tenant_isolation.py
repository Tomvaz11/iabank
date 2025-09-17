"""
Integration test isolamento multi-tenant.

Valida que cada endpoint respeita o isolamento por tenant, cobrindo:
- Criação de recursos atrelados a tenant_id automaticamente
- Listagens retornando apenas dados do tenant autenticado
- Acesso a recursos de outros tenants retornando 404/403
- Processamento de pagamentos e relatórios com segregação rigorosa

Baseado em:
- T017 do tasks.md
- Seção "Multi-Tenancy Validation" do quickstart
- ADR 0003 - Multi-tenancy Row-Level Security
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantFactory
from iabank.core.models import Tenant


User = get_user_model()


@pytest.mark.integration
@pytest.mark.tenant_isolation
class TestTenantIsolation(TransactionTestCase):
    """Integração: garante isolamento completo entre tenants."""

    def setUp(self):
        """Configura dois tenants independentes com usuários próprios."""
        self.client = APIClient()

        self.tenant_a = TenantFactory(name="Tenant Alpha")
        self.tenant_b = TenantFactory(name="Tenant Beta")

        self.user_a = User.objects.create_user(
            username="alpha_admin",
            email="alpha@empresa.com",
            password="SenhaSegura123",
            first_name="Admin",
            last_name="Alpha",
        )
        if hasattr(self.user_a, "tenant_id"):
            self.user_a.tenant_id = self.tenant_a.id
        self.user_a.save()

        self.user_b = User.objects.create_user(
            username="beta_admin",
            email="beta@empresa.com",
            password="SenhaSegura123",
            first_name="Admin",
            last_name="Beta",
        )
        if hasattr(self.user_b, "tenant_id"):
            self.user_b.tenant_id = self.tenant_b.id
        self.user_b.save()

        self.bank_accounts_url = "/api/v1/bank-accounts"
        self.customers_url = "/api/v1/customers"
        self.loans_url = "/api/v1/loans"
        self.loan_detail_url = "/api/v1/loans/{loan_id}"
        self.loan_approve_url = "/api/v1/loans/{loan_id}/approve"
        self.loan_installments_url = "/api/v1/loans/{loan_id}/installments"
        self.installment_payment_url = "/api/v1/installments/{installment_id}/payments"
        self.transactions_url = "/api/v1/financial-transactions"

    def tearDown(self):
        """Limpa dados criados durante os testes."""
        User.objects.all().delete()
        Tenant.objects.all().delete()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _authenticate(self, user):
        self.client.force_authenticate(user=user)

    def _create_customer(self, user, document_suffix: str):
        """Cria cliente identificado pelo sufixo para facilitar assertivas."""
        self._authenticate(user)
        payload = {
            "document_type": "CPF",
            "document": f"123456789{document_suffix}",
            "name": f"Cliente {document_suffix}",
            "email": f"cliente{document_suffix}@empresa.com",
            "phone": "(11) 90000-0000",
            "birth_date": "1990-01-01",
            "monthly_income": "5000.00",
        }
        response = self.client.post(self.customers_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()["data"]

    def _create_bank_account(self, user, suffix: int):
        """Cria conta bancária principal para o tenant informado."""
        self._authenticate(user)
        suffix_str = f"{suffix:02d}"
        payload = {
            "bank_code": "341",  # Itaú
            "bank_name": "Itaú Unibanco",
            "agency": f"{suffix_str}01",
            "account_number": f"{suffix_str}0022-5",
            "account_type": "CHECKING",
            "is_main": True,
        }
        response = self.client.post(self.bank_accounts_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()["data"]["id"]

    def _create_active_loan(self, user, customer_id):
        """Cria empréstimo, aprova e ativa para permitir cenários downstream."""
        self._authenticate(user)
        payload = {
            "customer_id": customer_id,
            "principal_amount": "15000.00",
            "interest_rate": "0.0245",
            "installments_count": 6,
            "first_due_date": "2025-09-25",
        }
        loan_response = self.client.post(self.loans_url, payload, format="json")
        self.assertEqual(loan_response.status_code, status.HTTP_201_CREATED)
        loan = loan_response.json()["data"]

        approve_response = self.client.post(
            self.loan_approve_url.format(loan_id=loan["id"]),
            data={},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

        activate_response = self.client.put(
            self.loan_detail_url.format(loan_id=loan["id"]),
            data={"status": "ACTIVE"},
            format="json",
        )
        self.assertEqual(activate_response.status_code, status.HTTP_200_OK)

        return loan

    def _list_customers(self, user):
        self._authenticate(user)
        response = self.client.get(self.customers_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("data", data)
        return data["data"]

    # ------------------------------------------------------------------
    # Cenários de teste
    # ------------------------------------------------------------------
    def test_customer_list_returns_only_authenticated_tenant_records(self):
        """Listagens devem retornar somente registros do tenant autenticado."""
        customer_a1 = self._create_customer(self.user_a, "01")
        customer_a2 = self._create_customer(self.user_a, "02")
        _ = (customer_a1, customer_a2)  # Evita lint de variável não usada

        self._create_customer(self.user_b, "99")

        customers = self._list_customers(self.user_a)
        self.assertGreaterEqual(len(customers), 2)

        tenant_ids = {customer["tenant_id"] for customer in customers}
        self.assertEqual(tenant_ids, {str(self.tenant_a.id)})

        documents = {customer["document"] for customer in customers}
        self.assertIn("12345678901", documents)
        self.assertIn("12345678902", documents)
        self.assertNotIn("12345678999", documents)

    def test_cross_tenant_loan_access_returns_not_found(self):
        """Recursos de empréstimo não devem ser acessíveis por outro tenant."""
        customer_a = self._create_customer(self.user_a, "11")
        loan_a = self._create_active_loan(self.user_a, customer_a["id"])

        self._authenticate(self.user_b)
        response = self.client.get(
            self.loan_detail_url.format(loan_id=loan_a["id"]),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        if response.status_code != status.HTTP_404_NOT_FOUND:
            payload = response.json()
            self.assertIn("errors", payload)
            self.assertIn("tenant", payload["errors"][0]["detail"].lower())

    def test_payments_and_transactions_do_not_leak_between_tenants(self):
        """Pagamentos e transações de um tenant não devem aparecer em outro."""
        customer_a = self._create_customer(self.user_a, "21")
        loan_a = self._create_active_loan(self.user_a, customer_a["id"])

        customer_b = self._create_customer(self.user_b, "31")
        loan_b = self._create_active_loan(self.user_b, customer_b["id"])

        bank_account_a = self._create_bank_account(self.user_a, 1)
        bank_account_b = self._create_bank_account(self.user_b, 2)

        # Realiza pagamento no tenant A
        self._authenticate(self.user_a)
        installments_a = self.client.get(
            self.loan_installments_url.format(loan_id=loan_a["id"]),
            format="json",
        )
        self.assertEqual(installments_a.status_code, status.HTTP_200_OK)
        first_installment_a = installments_a.json()["data"][0]

        payment_payload = {
            "amount": "2500.00",
            "payment_date": "2025-09-25",
            "payment_method": "PIX",
            "bank_account_id": bank_account_a,
        }
        payment_response = self.client.post(
            self.installment_payment_url.format(installment_id=first_installment_a["id"]),
            data=payment_payload,
            format="json",
        )
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)

        # Garante que tenant B tem sua própria transação
        self._authenticate(self.user_b)
        installments_b = self.client.get(
            self.loan_installments_url.format(loan_id=loan_b["id"]),
            format="json",
        )
        self.assertEqual(installments_b.status_code, status.HTTP_200_OK)
        first_installment_b = installments_b.json()["data"][0]

        payment_payload_b = {
            "amount": "3000.00",
            "payment_date": "2025-09-26",
            "payment_method": "PIX",
            "bank_account_id": bank_account_b,
        }
        response_payment_b = self.client.post(
            self.installment_payment_url.format(installment_id=first_installment_b["id"]),
            data=payment_payload_b,
            format="json",
        )
        self.assertEqual(response_payment_b.status_code, status.HTTP_200_OK)

        # Autentica tenant B e garante que transações listadas pertencem apenas a ele
        self._authenticate(self.user_b)
        transactions_response = self.client.get(
            f"{self.transactions_url}?type=INCOME",
            format="json",
        )
        self.assertEqual(transactions_response.status_code, status.HTTP_200_OK)
        transactions = transactions_response.json()["data"]
        self.assertGreaterEqual(len(transactions), 1)

        for transaction in transactions:
            self.assertEqual(transaction["tenant_id"], str(self.tenant_b.id))
            self.assertNotIn(loan_a["id"], transaction.get("description", ""))

        # Garante que tenant B não visualiza parcelas do empréstimo do tenant A
        response_installments_b = self.client.get(
            self.loan_installments_url.format(loan_id=loan_a["id"]),
            format="json",
        )
        self.assertEqual(response_installments_b.status_code, status.HTTP_404_NOT_FOUND)

        _ = loan_b  # Evita warning de variável não utilizada
