"""Testes de integração para tasks Celery do IABANK."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils import timezone

from iabank.core.factories import TenantFactory
from iabank.core.models import Tenant
from iabank.customers.models import Customer, CustomerDocumentType
from iabank.finance.models import (
    AccountType,
    BankAccount,
    FinancialTransaction,
    PaymentCategory,
    PaymentCategoryType,
    TransactionStatus,
    TransactionType,
)
from iabank.operations.models import (
    Installment,
    InstallmentStatus,
    Loan,
    LoanStatus,
)


pytestmark = pytest.mark.integration


class TestCeleryTasks(TransactionTestCase):
    """Validações completas das tasks Celery configuradas no projeto."""

    reset_sequences = True

    def setUp(self):
        super().setUp()
        cache.clear()
        self.today = timezone.localdate()
        self.tenant = TenantFactory()
        self.user_model = get_user_model()

    def tearDown(self):
        cache.clear()
        Tenant.objects.all().delete()
        self.user_model.objects.all().delete()
        super().tearDown()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_customer(self) -> Customer:
        customer = Customer.objects.create(
            tenant_id=self.tenant.id,
            document_type=CustomerDocumentType.CPF,
            document="39053344705",  # CPF válido conhecido
            name="Cliente Task Celery",
            email="cliente.celery@example.com",
            phone="11988887777",
        )
        return customer

    def _create_active_loan_with_overdue_installment(self) -> tuple[Loan, Installment]:
        customer = self._create_customer()
        contract_date = self.today - timedelta(days=40)
        first_due_date = self.today - timedelta(days=30)

        loan = Loan.objects.create(
            tenant_id=self.tenant.id,
            customer=customer,
            principal_amount=Decimal("10000.00"),
            interest_rate=Decimal("0.0200"),
            installments_count=12,
            iof_amount=Decimal("100.00"),
            cet_monthly=Decimal("0.0250"),
            cet_yearly=Decimal("0.3000"),
            total_amount=Decimal("10100.00"),
            contract_date=contract_date,
            first_due_date=first_due_date,
            status=LoanStatus.ACTIVE,
            regret_deadline=contract_date + timedelta(days=7),
            notes="Loan para testes de atraso",
        )

        installment = Installment.objects.create(
            tenant_id=self.tenant.id,
            loan=loan,
            sequence=1,
            due_date=self.today - timedelta(days=20),
            principal_amount=Decimal("800.00"),
            interest_amount=Decimal("50.00"),
            total_amount=Decimal("850.00"),
            amount_paid=Decimal("0.00"),
            late_fee=Decimal("0.00"),
            interest_penalty=Decimal("0.00"),
            status=InstallmentStatus.PENDING,
        )
        return loan, installment

    def _create_financial_income(self) -> None:
        bank_account = BankAccount.objects.create(
            tenant_id=self.tenant.id,
            bank_code="001",
            bank_name="Banco do Brasil S.A.",
            agency="1234",
            account_number="1234567",
            account_type=AccountType.CHECKING,
            balance=Decimal("0.00"),
            is_main=True,
        )

        category = PaymentCategory.objects.create(
            tenant_id=self.tenant.id,
            name="Receitas de Juros",
            type=PaymentCategoryType.INCOME,
            is_active=True,
        )

        FinancialTransaction.objects.create(
            tenant_id=self.tenant.id,
            bank_account=bank_account,
            type=TransactionType.INCOME,
            category=category,
            amount=Decimal("1500.00"),
            description="Receita diária",
            reference_date=self.today,
            payment_date=self.today,
            status=TransactionStatus.PAID,
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_update_iof_rates_updates_all_tenants(self):
        from iabank.operations import tasks as operations_tasks

        other_tenant = TenantFactory()
        # Remove configurações específicas de IOF para garantir atualização
        for tenant in (self.tenant, other_tenant):
            tenant.settings.pop("iof_fixed_rate", None)
            tenant.settings.pop("iof_daily_rate", None)
            tenant.save(update_fields=["settings", "updated_at"])

        result = operations_tasks.update_iof_rates.apply()
        self.assertTrue(result.successful())

        refreshed_main = Tenant.objects.get(pk=self.tenant.pk)
        refreshed_other = Tenant.objects.get(pk=other_tenant.pk)

        for tenant in (refreshed_main, refreshed_other):
            self.assertIn("iof_fixed_rate", tenant.settings)
            self.assertIn("iof_daily_rate", tenant.settings)
            self.assertGreater(Decimal(str(tenant.settings["iof_fixed_rate"])), Decimal("0"))
            self.assertGreater(Decimal(str(tenant.settings["iof_daily_rate"])), Decimal("0"))

    def test_calculate_overdue_interest_marks_installment_and_moves_loan(self):
        from iabank.operations import tasks as operations_tasks

        loan, installment = self._create_active_loan_with_overdue_installment()

        result = operations_tasks.calculate_overdue_interest.apply()
        self.assertTrue(result.successful())

        installment.refresh_from_db()
        loan.refresh_from_db()

        self.assertEqual(installment.status, InstallmentStatus.OVERDUE)
        self.assertGreater(installment.late_fee, Decimal("0"))
        self.assertGreater(installment.interest_penalty, Decimal("0"))
        self.assertEqual(loan.status, LoanStatus.COLLECTION)

    def test_generate_daily_reports_persists_cache_snapshot(self):
        from iabank.finance import tasks as finance_tasks

        self._create_financial_income()

        result = finance_tasks.generate_daily_reports.apply()
        self.assertTrue(result.successful())

        cache_key = f"finance:reports:daily:{self.tenant.id}:{self.today.isoformat()}"
        snapshot = cache.get(cache_key)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["income"], "1500.00")
        self.assertEqual(snapshot["net"], "1500.00")
        self.assertEqual(snapshot["currency"], "BRL")
