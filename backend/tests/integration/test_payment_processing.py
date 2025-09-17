"""
Integration test processamento de pagamentos.

Cobre o fluxo completo de pagamentos de parcelas, incluindo:
- Criação de conta bancária principal do tenant
- Pagamento integral de parcela com atualização de status
- Pagamentos parciais e complementares com múltiplas transações
- Criação automática de transações financeiras vinculadas
- Isolamento estrito entre tenants durante o processamento
- Auditoria e respostas estruturadas conforme padrões da API

Baseado em:
- T016 do tasks.md
- Fluxo 4 (Processamento de Pagamentos) do quickstart
- Requisitos de multi-tenancy e auditoria da constitution v1.0.0
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantFactory
from iabank.core.models import Tenant


User = get_user_model()


@pytest.mark.integration
class TestPaymentProcessingFlow(TransactionTestCase):
    """Integration tests para o fluxo completo de processamento de pagamentos."""

    def setUp(self):
        """Configura ambiente multi-tenant e usuários de teste."""
        self.client = APIClient()

        # Tenants para validar isolamento
        self.tenant = TenantFactory(name="Empresa Pagamentos LTDA")
        self.other_tenant = TenantFactory(name="Outra Empresa Pagadora")

        # Usuário principal do tenant
        self.user = User.objects.create_user(
            username="gestor_pagamentos",
            email="gestor@pagamentos.com",
            password="SenhaForte123",
            first_name="Gestor",
            last_name="Pagamentos",
        )
        if hasattr(self.user, "tenant_id"):
            self.user.tenant_id = self.tenant.id
        if hasattr(self.user, "role"):
            self.user.role = "FINANCE_MANAGER"
        self.user.save()

        # Usuário de outro tenant para testes de isolamento
        self.other_user = User.objects.create_user(
            username="gestor_outro",
            email="gestor@outro.com",
            password="SenhaForte123",
            first_name="Gestor",
            last_name="Outro",
        )
        if hasattr(self.other_user, "tenant_id"):
            self.other_user.tenant_id = self.other_tenant.id
        if hasattr(self.other_user, "role"):
            self.other_user.role = "FINANCE_MANAGER"
        self.other_user.save()

        # URLs bases utilizadas nos cenários
        self.bank_accounts_url = "/api/v1/bank-accounts"
        self.customers_url = "/api/v1/customers"
        self.loans_url = "/api/v1/loans"
        self.loan_detail_url = "/api/v1/loans/{loan_id}"
        self.loan_approve_url = "/api/v1/loans/{loan_id}/approve"
        self.loan_installments_url = "/api/v1/loans/{loan_id}/installments"
        self.installment_payment_url = "/api/v1/installments/{installment_id}/payments"
        self.financial_transactions_url = "/api/v1/financial-transactions"

    def tearDown(self):
        """Limpa dados criados durante os testes."""
        User.objects.all().delete()
        Tenant.objects.all().delete()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _authenticate(self, user):
        """Autentica cliente da API com usuário informado."""
        self.client.force_authenticate(user=user)

    def _create_main_bank_account(self, tenant_user):
        """Cria conta bancária principal do tenant via API."""
        self._authenticate(tenant_user)
        payload = {
            "bank_code": "001",
            "bank_name": "Banco do Brasil",
            "agency": "1234-5",
            "account_number": "67890-1",
            "account_type": "CHECKING",
            "is_main": True,
        }
        response = self.client.post(self.bank_accounts_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()["data"]
        self.assertTrue(data["is_main"])
        return data["id"]

    def _create_customer(self, tenant_user):
        """Cria cliente com dados válidos e retorna response."""
        self._authenticate(tenant_user)
        payload = {
            "document_type": "CPF",
            "document": "12345678901",
            "name": "João Pagador",
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
                    "city": "São Paulo",
                    "state": "SP",
                    "zipcode": "01000-000",
                    "is_primary": True,
                }
            ],
        }
        response = self.client.post(self.customers_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def _create_loan(self, tenant_user, customer_id):
        """Cria empréstimo para o cliente informado."""
        self._authenticate(tenant_user)
        payload = {
            "customer_id": customer_id,
            "principal_amount": "10000.00",
            "interest_rate": "0.0299",
            "installments_count": 12,
            "first_due_date": "2025-10-15",
            "notes": "Empréstimo teste para pagamentos",
        }
        response = self.client.post(self.loans_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def _activate_loan(self, tenant_user, loan_id):
        """Aprova e ativa empréstimo para permitir pagamentos."""
        self._authenticate(tenant_user)
        approve_response = self.client.post(
            self.loan_approve_url.format(loan_id=loan_id),
            data={},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)

        activate_payload = {"status": "ACTIVE"}
        activate_response = self.client.put(
            self.loan_detail_url.format(loan_id=loan_id),
            data=activate_payload,
            format="json",
        )
        self.assertEqual(activate_response.status_code, status.HTTP_200_OK)
        return activate_response

    def _list_installments(self, tenant_user, loan_id):
        """Retorna parcelas do empréstimo via API."""
        self._authenticate(tenant_user)
        response = self.client.get(
            self.loan_installments_url.format(loan_id=loan_id),
            data={},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("data", data)
        self.assertTrue(len(data["data"]) >= 1)
        return data["data"]

    def _prepare_active_loan_dataset(self, tenant_user):
        """Cria conta, cliente, empréstimo e retorna dados úteis."""
        bank_account_id = self._create_main_bank_account(tenant_user)
        customer_response = self._create_customer(tenant_user)
        customer_id = customer_response.json()["data"]["id"]

        loan_response = self._create_loan(tenant_user, customer_id)
        loan_data = loan_response.json()["data"]
        loan_id = loan_data["id"]

        self._activate_loan(tenant_user, loan_id)
        installments = self._list_installments(tenant_user, loan_id)

        return {
            "bank_account_id": bank_account_id,
            "customer": loan_data["customer"],
            "loan": loan_data,
            "loan_id": loan_id,
            "installments": installments,
        }

    # ------------------------------------------------------------------
    # Cenários de teste
    # ------------------------------------------------------------------
    def test_full_payment_marks_installment_as_paid(self):
        """Pagamentos integrais devem liquidar a parcela e registrar transação."""
        dataset = self._prepare_active_loan_dataset(self.user)
        first_installment = dataset["installments"][0]

        payment_payload = {
            "amount": "937.05",
            "payment_date": "2025-10-15",
            "payment_method": "PIX",
            "bank_account_id": dataset["bank_account_id"],
        }

        payment_response = self.client.post(
            self.installment_payment_url.format(installment_id=first_installment["id"]),
            data=payment_payload,
            format="json",
        )

        # RED phase: endpoint ainda não implementado, deve falhar até implementação
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)

        payment_data = payment_response.json()["data"]
        installment = payment_data["installment"]
        transaction = payment_data["transaction"]

        self.assertEqual(Decimal(str(installment["amount_paid"])), Decimal("937.05"))
        self.assertEqual(installment["status"], "PAID")
        self.assertEqual(installment["payment_date"], "2025-10-15")

        self.assertEqual(transaction["type"], "INCOME")
        self.assertEqual(Decimal(str(transaction["amount"])), Decimal("937.05"))
        self.assertEqual(transaction["status"], "PAID")
        self.assertIn("Pagamento parcela", transaction["description"])

    def test_partial_payments_create_multiple_transactions(self):
        """Pagamentos parciais devem acumular valor pago e gerar múltiplas transações."""
        dataset = self._prepare_active_loan_dataset(self.user)
        second_installment = dataset["installments"][1]

        first_partial_payload = {
            "amount": "500.00",
            "payment_date": "2025-11-15",
            "payment_method": "BOLETO",
            "bank_account_id": dataset["bank_account_id"],
        }
        first_partial_response = self.client.post(
            self.installment_payment_url.format(installment_id=second_installment["id"]),
            data=first_partial_payload,
            format="json",
        )
        self.assertEqual(first_partial_response.status_code, status.HTTP_200_OK)
        first_installment_state = first_partial_response.json()["data"]["installment"]
        self.assertEqual(first_installment_state["status"], "PARTIALLY_PAID")
        self.assertEqual(Decimal(str(first_installment_state["amount_paid"])), Decimal("500.00"))

        complement_payload = {
            "amount": "437.05",
            "payment_date": "2025-11-20",
            "payment_method": "TRANSFER",
            "bank_account_id": dataset["bank_account_id"],
        }
        complement_response = self.client.post(
            self.installment_payment_url.format(installment_id=second_installment["id"]),
            data=complement_payload,
            format="json",
        )
        self.assertEqual(complement_response.status_code, status.HTTP_200_OK)
        final_installment_state = complement_response.json()["data"]["installment"]
        self.assertEqual(final_installment_state["status"], "PAID")
        self.assertEqual(Decimal(str(final_installment_state["amount_paid"])), Decimal("937.05"))

        # Verifica que múltiplas transações foram registradas
        transactions_response = self.client.get(
            f"{self.financial_transactions_url}?type=INCOME&loan_id={dataset['loan_id']}",
            format="json",
        )
        self.assertEqual(transactions_response.status_code, status.HTTP_200_OK)
        transactions = transactions_response.json()["data"]
        self.assertGreaterEqual(len(transactions), 2)

    def test_payment_from_other_tenant_is_not_allowed(self):
        """Tentativa de pagamento por usuário de outro tenant deve falhar."""
        dataset = self._prepare_active_loan_dataset(self.user)
        installment_id = dataset["installments"][0]["id"]

        self._authenticate(self.other_user)
        payload = {
            "amount": "937.05",
            "payment_date": "2025-10-15",
            "payment_method": "PIX",
            "bank_account_id": str(uuid4()),
        }

        response = self.client.post(
            self.installment_payment_url.format(installment_id=installment_id),
            data=payload,
            format="json",
        )

        # RLS deve impedir acesso e retornar not found para mascarar recursos de outro tenant
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        if response.status_code != status.HTTP_404_NOT_FOUND:
            data = response.json()
            self.assertIn("errors", data)
            error = data["errors"][0]
            self.assertIn(error["status"], {"403", "404"})
            self.assertIn("tenant", error["detail"])  # Mensagem deve referenciar isolamento
