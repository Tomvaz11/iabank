"""
Integration test conformidade e auditoria regulatória.

Abrange:
- Cancelamento de empréstimos dentro do período de arrependimento (Lei do CDC)
- Bloqueio de cancelamentos após o deadline legal
- Histórico completo via django-simple-history
- Validação de cálculos regulatórios (IOF, CET, Lei da Usura)
- Auditoria estruturada com eventos de segurança

Baseado em:
- T018 do tasks.md
- Fluxo 6 do quickstart (Conformidade e Auditoria)
- Requisitos de auditoria e LGPD da constitution v1.0.0
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantFactory
from iabank.core.models import Tenant


User = get_user_model()


@pytest.mark.integration
class TestComplianceAndAuditFlow(TransactionTestCase):
    """Integração: garante conformidade regulatória e auditoria completa."""

    def setUp(self):
        """Configura tenant e usuário administrativo para os testes."""
        self.client = APIClient()
        self.tenant = TenantFactory(name="Tenant Compliance")

        self.user = User.objects.create_user(
            username="compliance_admin",
            email="compliance@empresa.com",
            password="SenhaMuitoSegura123",
            first_name="Compliance",
            last_name="Admin",
        )
        if hasattr(self.user, "tenant_id"):
            self.user.tenant_id = self.tenant.id
        if hasattr(self.user, "role"):
            self.user.role = "COMPLIANCE_MANAGER"
        self.user.save()

        self.customers_url = "/api/v1/customers"
        self.loans_url = "/api/v1/loans"
        self.loan_detail_url = "/api/v1/loans/{loan_id}"
        self.loan_approve_url = "/api/v1/loans/{loan_id}/approve"
        self.loan_cancel_url = "/api/v1/loans/{loan_id}/cancel"
        self.loan_history_url = "/api/v1/loans/{loan_id}/history"
        self.loan_regulatory_validation_url = "/api/v1/loans/{loan_id}/regulatory-validation"

    def tearDown(self):
        User.objects.all().delete()
        Tenant.objects.all().delete()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _authenticate(self):
        self.client.force_authenticate(user=self.user)

    def _create_customer(self):
        self._authenticate()
        payload = {
            "document_type": "CPF",
            "document": "98765432100",
            "name": "Cliente Compliance",
            "email": "cliente.compliance@example.com",
            "phone": "(11) 95555-4444",
            "birth_date": "1987-07-20",
            "monthly_income": "12000.00",
        }
        response = self.client.post(self.customers_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()["data"]["id"]

    def _create_and_activate_loan(self):
        customer_id = self._create_customer()
        loan_payload = {
            "customer_id": customer_id,
            "principal_amount": "20000.00",
            "interest_rate": "0.0285",
            "installments_count": 12,
            "first_due_date": "2025-10-05",
            "notes": "Empréstimo para teste de compliance",
        }
        create_response = self.client.post(self.loans_url, loan_payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        loan_data = create_response.json()["data"]

        approve_response = self.client.post(
            self.loan_approve_url.format(loan_id=loan_data["id"]),
            data={"approved_by": "compliance@empresa.com"},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

        activate_response = self.client.put(
            self.loan_detail_url.format(loan_id=loan_data["id"]),
            data={"status": "ACTIVE"},
            format="json",
        )
        self.assertEqual(activate_response.status_code, status.HTTP_200_OK)

        return loan_data

    # ------------------------------------------------------------------
    # Cenários de teste
    # ------------------------------------------------------------------
    def test_cancellation_within_regret_period_creates_history(self):
        """Cancelamento dentro do prazo deve ser permitido e registrado na auditoria."""
        loan_data = self._create_and_activate_loan()

        cancel_payload = {
            "reason": "Cancelamento solicitado pelo cliente dentro do prazo legal",
        }
        cancel_response = self.client.post(
            self.loan_cancel_url.format(loan_id=loan_data["id"]),
            data=cancel_payload,
            format="json",
        )
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        cancel_data = cancel_response.json()["data"]
        self.assertEqual(cancel_data["status"], "CANCELLED")
        self.assertEqual(cancel_data["regret_deadline"], loan_data["regret_deadline"])

        history_response = self.client.get(
            self.loan_history_url.format(loan_id=loan_data["id"]),
            format="json",
        )
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        history_entries = history_response.json()["data"]
        self.assertGreaterEqual(len(history_entries), 2)
        last_entry = history_entries[-1]
        self.assertEqual(last_entry["history_type"], "UPDATE")
        self.assertIn("status", last_entry["changes"])
        self.assertEqual(last_entry["changes"]["status"], "CANCELLED")

    def test_cancellation_after_regret_period_is_blocked(self):
        """Cancelamento fora do prazo legal deve retornar erro de validação."""
        loan_data = self._create_and_activate_loan()
        regret_deadline = datetime.strptime(loan_data["regret_deadline"], "%Y-%m-%d")
        after_deadline = regret_deadline + timedelta(days=2)

        with patch("django.utils.timezone.now", return_value=timezone.make_aware(after_deadline)):
            cancel_response = self.client.post(
                self.loan_cancel_url.format(loan_id=loan_data["id"]),
                data={"reason": "Tentativa fora do prazo"},
                format="json",
            )

        self.assertEqual(cancel_response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        error_payload = cancel_response.json()
        self.assertIn("errors", error_payload)
        error_detail = error_payload["errors"][0]["detail"].lower()
        self.assertIn("arrependimento", error_detail)
        self.assertIn("prazo", error_detail)

    def test_regulatory_validation_returns_full_compliance_snapshot(self):
        """Endpoint de validação regulatória deve trazer todos os indicadores necessários."""
        loan_data = self._create_and_activate_loan()

        response = self.client.get(
            self.loan_regulatory_validation_url.format(loan_id=loan_data["id"]),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        validation = response.json()["data"]
        expected_flags = {
            "cet_compliance",
            "iof_compliance",
            "usury_law_compliance",
            "regret_period_valid",
        }
        self.assertTrue(expected_flags.issubset(validation.keys()))

        calculations = validation["calculations"]
        for field in [
            "iof_rate",
            "iof_amount",
            "cet_monthly",
            "cet_yearly",
            "max_interest_rate",
        ]:
            self.assertIn(field, calculations)

        self.assertGreaterEqual(calculations["max_interest_rate"], 0)
