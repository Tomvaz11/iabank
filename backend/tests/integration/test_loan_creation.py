"""
Integration test criacao de emprestimos.

Cobre o fluxo completo definido em T015 do tasks.md, incluindo:
- Autenticacao de usuarios (admin e consultor)
- Cadastro de cliente para o tenant principal
- Criacao de emprestimo com calculos automaticos e parcelas
- Transicoes de status (ANALYSIS -> APPROVED -> ACTIVE)
- Validacoes de isolamento multi-tenant e limites regulatorios

Documentacao de referencia:
- specs/001-eu-escrevi-um/quickstart.md (Flow 3)
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml
- specs/001-eu-escrevi-um/data-model.md
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import ProgrammingError, connection
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantFactory, set_tenant_context
from iabank.users.models import Consultant


User = get_user_model()

@pytest.mark.integration
class TestLoanCreationFlow(TransactionTestCase):
    """Integration tests para criacao de emprestimos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_tenant_context_function()

    @staticmethod
    def _ensure_tenant_context_function() -> None:
        """Garante que a funcao set_tenant_context exista no banco de testes."""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid uuid)
                    RETURNS void AS '
                    BEGIN
                        PERFORM set_config(''iabank.current_tenant_id'', tenant_uuid::text, true);
                    END;
                    ' LANGUAGE plpgsql;
                    """
                )
        except ProgrammingError:
            pass

    reset_sequences = True

    def setUp(self) -> None:
        """Configura tenants, usuarios e URLs basicas para os testes."""
        set_tenant_context(None)

        self.login_url = "/api/v1/auth/login"
        self.customers_url = "/api/v1/customers"
        self.loans_url = "/api/v1/loans/"
        self.loan_detail_url = "/api/v1/loans/{loan_id}/"
        self.loan_approve_url = "/api/v1/loans/{loan_id}/approve/"
        self.loan_installments_url = "/api/v1/loans/{loan_id}/installments/"

        self.tenant = TenantFactory(
            name="Empresa Integracao LTDA",
            domain="empresa-integracao.com.br",
            settings={
                "max_interest_rate": 0.035,
                "max_loan_amount": 200000.00,
                "currency": "BRL",
                "arrears_grace_days": 5,
            },
        )
        self.tenant_domain = self.tenant.domain
        self.assertAlmostEqual(
            Decimal(str(self.tenant.settings.get("max_interest_rate"))),
            Decimal("0.035"),
        )

        self.other_tenant = TenantFactory(name="Outra Empresa LTDA", domain="outra-empresa.com.br")
        self.other_tenant_domain = self.other_tenant.domain

        self.admin_password = "AdminPass123!"
        self.consultant_password = "ConsultorPass123!"
        self.other_password = "OutraSenha123!"

        self.admin_user = User.objects.create_user(
            username="admin.integracao",
            email="admin.integracao@empresa.com",
            password=self.admin_password,
            first_name="Admin",
            last_name="Integracao",
            is_staff=True,
            is_active=True,
        )
        if hasattr(self.admin_user, "tenant_id"):
            self.admin_user.tenant_id = self.tenant.id
        if hasattr(self.admin_user, "role"):
            self.admin_user.role = "ADMIN"
        self.admin_user.save()

        self.consultant_user = User.objects.create_user(
            username="consultor.integracao",
            email="consultor.integracao@empresa.com",
            password=self.consultant_password,
            first_name="Consultor",
            last_name="Integracao",
            is_active=True,
        )
        if hasattr(self.consultant_user, "tenant_id"):
            self.consultant_user.tenant_id = self.tenant.id
        if hasattr(self.consultant_user, "role"):
            self.consultant_user.role = "CONSULTANT"
        self.consultant_user.save()
        self.consultant_profile = Consultant.objects.create(
            user=self.consultant_user,
            commission_rate=Decimal("0.0100"),
        )

        self.other_user = User.objects.create_user(
            username="consultor.outra",
            email="consultor.outra@empresa.com",
            password=self.other_password,
            first_name="Consultor",
            last_name="Externo",
            is_active=True,
        )
        if hasattr(self.other_user, "tenant_id"):
            self.other_user.tenant_id = self.other_tenant.id
        if hasattr(self.other_user, "role"):
            self.other_user.role = "CONSULTANT"
        self.other_user.save()

        self.contract_date = timezone.localdate()
        self.first_due_date = self.contract_date + timedelta(days=30)
        self.loan_notes = "Emprestimo para capital de giro (teste integracao)"

    def tearDown(self) -> None:
        """Limpa contexto de tenant ao final de cada teste."""
        set_tenant_context(None)

    def _authenticate_client(self, email: str, password: str, tenant) -> tuple[APIClient, dict]:
        """Realiza login no tenant informado e retorna cliente autenticado."""
        if tenant is None:
            raise AssertionError("Tenant deve ser informado para autenticacao")

        client = APIClient()
        tenant_id = str(getattr(tenant, "id"))
        tenant_domain = getattr(tenant, "domain", None)

        client.credentials(HTTP_X_TENANT_ID=tenant_id)

        payload = {
            "email": email,
            "password": password,
        }
        if tenant_domain:
            payload["tenant_domain"] = tenant_domain

        self._login_counter = getattr(self, "_login_counter", 0) + 1
        remote_octet = (self._login_counter % 254) + 1
        remote_addr = f"127.0.0.{remote_octet}"
        response = client.post(self.login_url, data=payload, format="json", REMOTE_ADDR=remote_addr)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=f"Login falhou para {email}: {response.status_code} - {response.content!r}",
        )
        body = response.json()
        token = body["data"]["access_token"]
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=tenant_id,
        )
        return client, body

    @staticmethod
    def _generate_valid_cpf() -> str:
        """Gera CPF valido para uso nos payloads de teste."""

        def _calculate_digit(digits, weights):
            total = sum(d * w for d, w in zip(digits, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder

        while True:
            numbers = [random.randint(0, 9) for _ in range(9)]
            if len(set(numbers)) == 1:
                continue
            first_digit = _calculate_digit(numbers, list(range(10, 1, -1)))
            second_digit = _calculate_digit(numbers + [first_digit], list(range(11, 1, -1)))
            cpf_digits = numbers + [first_digit, second_digit]
            return ''.join(str(d) for d in cpf_digits)

    def _build_customer_payload(self) -> dict:
        """Gera payload valido para criar cliente do tenant principal."""
        document = self._generate_valid_cpf()
        return {
            "document_type": "CPF",
            "document": document,
            "name": "Cliente Fluxo Integracao",
            "email": f"{document}@clientes.com",
            "phone": "+55 (11) 99999-0000",
            "birth_date": "1988-05-20",
            "monthly_income": "8500.00",
            "credit_score": 780,
        }

    def _create_customer(self, client: APIClient) -> tuple[dict, dict]:
        """Cria cliente via API e retorna dados do response e payload enviado."""
        payload = self._build_customer_payload()
        response = client.post(self.customers_url, data=payload, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Falha ao criar cliente: {response.status_code} - {response.content!r}",
        )
        return response.json()["data"], payload

    def _build_loan_payload(self, customer_id: str, overrides: dict | None = None) -> dict:
        """Gera payload padrao para criacao de emprestimo."""
        payload = {
            "customer_id": customer_id,
            "principal_amount": "10000.00",
            "interest_rate": "0.0299",
            "installments_count": 12,
            "first_due_date": self.first_due_date.isoformat(),
            "notes": self.loan_notes,
        }
        if overrides:
            payload.update(overrides)
        return payload

    def _assert_installments_structure(self, installments: list[dict], expected_count: int) -> None:
        """Valida estrutura padrao das parcelas retornadas pela API."""
        self.assertEqual(len(installments), expected_count)
        for index, item in enumerate(installments, start=1):
            self.assertIn("sequence", item)
            self.assertIn("due_date", item)
            self.assertIn("total_amount", item)
            self.assertIn("status", item)
            self.assertEqual(item["sequence"], index)
            due_date = date.fromisoformat(item["due_date"])
            self.assertGreaterEqual(due_date, self.first_due_date)

    def test_loan_creation_success_flow(self) -> None:
        """Fluxo completo de criacao, aprovacao e ativacao de emprestimo."""
        admin_client, _ = self._authenticate_client(
            self.admin_user.email,
            self.admin_password,
            self.tenant,
        )
        customer_data, _ = self._create_customer(admin_client)

        consultant_client, _ = self._authenticate_client(
            self.consultant_user.email,
            self.consultant_password,
            self.tenant,
        )

        loan_payload = self._build_loan_payload(customer_data["id"])
        response = consultant_client.post(self.loans_url, data=loan_payload, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Falha ao criar emprestimo: {response.status_code} - {response.content!r}",
        )

        body = response.json()
        self.assertIn("data", body)
        self.assertIn("meta", body)
        loan = body["data"]

        self.assertEqual(loan["customer"]["id"], customer_data["id"])
        self.assertEqual(loan["status"], "ANALYSIS")
        self.assertEqual(loan["installments_count"], loan_payload["installments_count"])
        self.assertEqual(loan["notes"], loan_payload["notes"])
        self.assertEqual(
            Decimal(str(loan["principal_amount"])),
            Decimal(str(loan_payload["principal_amount"])),
        )

        self.assertGreater(Decimal(str(loan["iof_amount"])), Decimal("0"))
        self.assertGreater(Decimal(str(loan["cet_monthly"])), Decimal("0"))
        self.assertGreater(Decimal(str(loan["cet_yearly"])), Decimal("0"))
        self.assertGreater(Decimal(str(loan["total_amount"])), Decimal(loan_payload["principal_amount"]))

        contract_date = date.fromisoformat(loan["contract_date"])
        regret_deadline = date.fromisoformat(loan["regret_deadline"])
        self.assertEqual(regret_deadline, contract_date + timedelta(days=7))

        self.assertIn("consultant", loan)
        consultant_info = loan["consultant"]
        self.assertIn("id", consultant_info)
        self.assertEqual(consultant_info.get("first_name"), self.consultant_user.first_name)

        installments = loan.get("installments", [])
        self._assert_installments_structure(installments, loan_payload["installments_count"])
        self.assertEqual(installments[0]["due_date"], loan_payload["first_due_date"])

        loan_id = loan["id"]
        detail_response = consultant_client.get(
            self.loan_detail_url.format(loan_id=loan_id)
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        detail_body = detail_response.json()
        loan_detail = detail_body.get("data", detail_body)
        self.assertEqual(loan_detail["id"], loan_id)

        installments_response = consultant_client.get(
            self.loan_installments_url.format(loan_id=loan_id)
        )
        self.assertEqual(installments_response.status_code, status.HTTP_200_OK)
        installments_body = installments_response.json()
        installments_data = installments_body.get("data", installments_body)
        self._assert_installments_structure(
            installments_data,
            loan_payload["installments_count"],
        )

        approve_response = consultant_client.post(
            self.loan_approve_url.format(loan_id=loan_id),
            data={},
            format="json",
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_response.json()["data"]["status"], "APPROVED")

        activate_response = consultant_client.put(
            self.loan_detail_url.format(loan_id=loan_id),
            data={"status": "ACTIVE"},
            format="json",
        )
        self.assertEqual(activate_response.status_code, status.HTTP_200_OK)
        self.assertEqual(activate_response.json()["data"]["status"], "ACTIVE")

        final_detail = consultant_client.get(self.loan_detail_url.format(loan_id=loan_id))
        self.assertEqual(final_detail.status_code, status.HTTP_200_OK)
        final_body = final_detail.json()
        final_data = final_body.get("data", final_body)
        self.assertEqual(final_data["status"], "ACTIVE")

    def test_loan_creation_respects_tenant_isolation(self) -> None:
        """Garante que um tenant nao consegue criar emprestimo para cliente de outro tenant."""
        admin_client, _ = self._authenticate_client(
            self.admin_user.email,
            self.admin_password,
            self.tenant,
        )
        customer_data, _ = self._create_customer(admin_client)

        other_client, _ = self._authenticate_client(
            self.other_user.email,
            self.other_password,
            self.other_tenant,
        )

        payload = self._build_loan_payload(customer_data["id"])
        response = other_client.post(self.loans_url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertIn("errors", body)
        self.assertTrue(body["errors"])
        self.assertTrue(
            any(
                error.get("source", {}).get("field") == "customer_id"
                for error in body["errors"]
            ),
            "Esperado erro associado ao campo customer_id",
        )

    def test_loan_creation_validates_interest_rate_limit(self) -> None:
        """Valida erro quando taxa informada ultrapassa limite configurado do tenant."""
        admin_client, _ = self._authenticate_client(
            self.admin_user.email,
            self.admin_password,
            self.tenant,
        )
        customer_data, _ = self._create_customer(admin_client)

        consultant_client, _ = self._authenticate_client(
            self.consultant_user.email,
            self.consultant_password,
            self.tenant,
        )

        high_rate_payload = self._build_loan_payload(
            customer_data["id"],
            overrides={"interest_rate": "0.0800"},
        )
        response = consultant_client.post(
            self.loans_url,
            data=high_rate_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertIn("errors", body)
        self.assertTrue(body["errors"])
        self.assertTrue(
            any(
                "Taxa de juros" in (error.get("detail") or "")
                for error in body["errors"]
            ),
            "Esperado erro indicando limite de taxa excedido",
        )


