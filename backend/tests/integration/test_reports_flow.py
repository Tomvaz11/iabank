"""
Integration test relatórios e dashboard financeiro.

Garante que relatórios agregados reflitam os dados de negócios, incluindo:
- Dashboard principal com métricas de empréstimos e pagamentos
- Relatório de fluxo de caixa consolidado por período
- Listagem de transações financeiras com filtros e isolamento
- Consistência entre pagamentos registrados e indicadores apresentados

Baseado em:
- T019 do tasks.md
- Fluxo 5 do quickstart (Relatórios e Dashboard)
- Requisitos de observabilidade e métricas (constitution v1.0.0)
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantFactory
from iabank.core.models import Tenant


User = get_user_model()


@pytest.mark.integration
class TestReportsDashboardFlow(TransactionTestCase):
    """Integração: valida exposição dos relatórios financeiros do tenant."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = TenantFactory(name="Tenant Reports")

        self.user = User.objects.create_user(
            username="reports_admin",
            email="reports@empresa.com",
            password="SenhaRelatorios123",
            first_name="Reports",
            last_name="Admin",
        )
        if hasattr(self.user, "tenant_id"):
            self.user.tenant_id = self.tenant.id
        if hasattr(self.user, "role"):
            self.user.role = "FINANCE_ANALYST"
        self.user.save()

        self.bank_accounts_url = "/api/v1/bank-accounts"
        self.customers_url = "/api/v1/customers"
        self.loans_url = "/api/v1/loans"
        self.loan_detail_url = "/api/v1/loans/{loan_id}"
        self.loan_approve_url = "/api/v1/loans/{loan_id}/approve"
        self.loan_installments_url = "/api/v1/loans/{loan_id}/installments"
        self.installment_payment_url = "/api/v1/installments/{installment_id}/payments"
        self.dashboard_url = "/api/v1/reports/dashboard"
        self.cash_flow_url = "/api/v1/reports/cash-flow"
        self.transactions_url = "/api/v1/financial-transactions"

    def tearDown(self):
        User.objects.all().delete()
        Tenant.objects.all().delete()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _authenticate(self):
        self.client.force_authenticate(user=self.user)

    def _create_bank_account(self):
        self._authenticate()
        payload = {
            "bank_code": "237",
            "bank_name": "Bradesco",
            "agency": "4321-0",
            "account_number": "112233-4",
            "account_type": "CHECKING",
            "is_main": True,
        }
        response = self.client.post(self.bank_accounts_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()["data"]["id"]

    def _create_customer(self):
        self._authenticate()
        payload = {
            "document_type": "CPF",
            "document": "55566677788",
            "name": "Cliente Relatórios",
            "email": "cliente.relatorios@example.com",
            "phone": "(11) 97777-6666",
            "birth_date": "1992-03-10",
            "monthly_income": "15000.00",
        }
        response = self.client.post(self.customers_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()["data"]["id"]

    def _create_and_activate_loan(self, customer_id):
        self._authenticate()
        payload = {
            "customer_id": customer_id,
            "principal_amount": "18000.00",
            "interest_rate": "0.031",
            "installments_count": 12,
            "first_due_date": "2025-10-10",
            "notes": "Empréstimo para testes de relatórios",
        }
        create_response = self.client.post(self.loans_url, payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        loan = create_response.json()["data"]

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

        installments_response = self.client.get(
            self.loan_installments_url.format(loan_id=loan["id"]),
            format="json",
        )
        self.assertEqual(installments_response.status_code, status.HTTP_200_OK)
        installments = installments_response.json()["data"]

        return loan, installments

    def _register_payments_for_reports(self):
        bank_account_id = self._create_bank_account()
        customer_id = self._create_customer()
        loan, installments = self._create_and_activate_loan(customer_id)

        first_installment = installments[0]
        second_installment = installments[1]

        full_payment_payload = {
            "amount": "950.00",
            "payment_date": "2025-10-10",
            "payment_method": "PIX",
            "bank_account_id": bank_account_id,
        }
        response_full = self.client.post(
            self.installment_payment_url.format(installment_id=first_installment["id"]),
            data=full_payment_payload,
            format="json",
        )
        self.assertEqual(response_full.status_code, status.HTTP_200_OK)

        partial_payment_payload = {
            "amount": "400.00",
            "payment_date": "2025-11-10",
            "payment_method": "BOLETO",
            "bank_account_id": bank_account_id,
        }
        response_partial = self.client.post(
            self.installment_payment_url.format(installment_id=second_installment["id"]),
            data=partial_payment_payload,
            format="json",
        )
        self.assertEqual(response_partial.status_code, status.HTTP_200_OK)

        complement_payload = {
            "amount": "550.00",
            "payment_date": "2025-11-20",
            "payment_method": "TRANSFER",
            "bank_account_id": bank_account_id,
        }
        response_complement = self.client.post(
            self.installment_payment_url.format(installment_id=second_installment["id"]),
            data=complement_payload,
            format="json",
        )
        self.assertEqual(response_complement.status_code, status.HTTP_200_OK)

        return {
            "loan": loan,
            "installments": installments,
            "bank_account_id": bank_account_id,
        }

    # ------------------------------------------------------------------
    # Cenários
    # ------------------------------------------------------------------
    def test_dashboard_metrics_reflect_recent_payments(self):
        """Dashboard deve apresentar métricas consistentes após pagamentos."""
        dataset = self._register_payments_for_reports()
        _ = dataset  # evita warning

        response = self.client.get(
            f"{self.dashboard_url}?period=30d",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()["data"]
        expected_fields = {
            "total_active_loans",
            "total_loan_amount",
            "default_rate",
            "monthly_revenue",
            "loans_by_status",
            "payments_trend",
        }
        self.assertTrue(expected_fields.issubset(data.keys()))

        self.assertGreaterEqual(data["total_active_loans"], 1)
        self.assertGreater(Decimal(str(data["monthly_revenue"])), Decimal("0"))
        self.assertIn("ACTIVE", data["loans_by_status"])  # status agregado
        self.assertTrue(len(data["payments_trend"]) >= 1)

    def test_cash_flow_report_summarizes_income(self):
        """Relatório de fluxo de caixa deve refletir receitas registradas."""
        self._register_payments_for_reports()

        response = self.client.get(
            f"{self.cash_flow_url}?start_date=2025-09-01&end_date=2025-12-31",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        report = response.json()["data"]
        self.assertIn("period", report)
        self.assertIn("income", report)
        self.assertIn("expenses", report)
        self.assertIn("net_flow", report)
        self.assertIn("daily_flow", report)
        self.assertGreater(Decimal(str(report["income"])), Decimal("0"))
        self.assertGreaterEqual(Decimal(str(report["net_flow"])), Decimal("0"))

    def test_financial_transactions_listing_supports_filters(self):
        """Listagem de transações deve aplicar filtros e manter isolamento do tenant."""
        dataset = self._register_payments_for_reports()

        response = self.client.get(
            f"{self.transactions_url}?type=INCOME&start_date=2025-10-01",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payload = response.json()
        self.assertIn("data", payload)
        self.assertIn("meta", payload)

        for transaction in payload["data"]:
            self.assertEqual(transaction["type"], "INCOME")
            self.assertEqual(transaction["tenant_id"], str(self.tenant.id))
            self.assertIn(dataset["loan"]["id"], transaction.get("description", ""))
