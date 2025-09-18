"""Testes para modelos de finanças (BankAccount e FinancialTransaction)."""
import os
from datetime import timedelta
from decimal import Decimal

# Garantir chave de criptografia disponível para campos sensíveis
os.environ.setdefault(
    "ENCRYPTION_KEY",
    "pKM2-Nf11oppjimJrQylaVXkLZWVLNDuDyNcyYB5y4U=",
)

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from iabank.core.factories import TenantFactory, generate_cnpj
from iabank.customers.models import Customer, CustomerDocumentType
from iabank.finance.models import (
    AccountType,
    BankAccount,
    FinancialTransaction,
    PaymentCategoryType,
    TransactionStatus,
    TransactionType,
)
from iabank.operations.models import Installment, Loan, LoanStatus


@pytest.mark.django_db
class TestBankAccountModel:
    """Casos de teste para BankAccount."""

    def _create_customer(self, tenant):
        """Helper para criar cliente válido."""
        customer = Customer(
            tenant_id=tenant.id,
            document_type=CustomerDocumentType.CNPJ,
            document=generate_cnpj(),
            name="Empresa Exemplo Ltda",
            email="financeiro@exemplo.com",
            phone="11999999999",
        )
        customer.full_clean()
        customer.save()
        return customer

    def _create_bank_account(self, tenant, **kwargs):
        defaults = {
            "bank_code": "001",
            "bank_name": "Banco do Brasil",
            "agency": "1234",
            "account_number": "123456-7",
            "account_type": AccountType.CHECKING,
            "balance": Decimal("0.00"),
            "is_active": True,
            "is_main": False,
        }
        defaults.update(kwargs)
        account = BankAccount(tenant_id=tenant.id, **defaults)
        account.full_clean()
        account.save()
        return account

    def test_bank_account_valid_creation(self):
        tenant = TenantFactory()
        account = self._create_bank_account(tenant, is_main=True)

        assert account.id is not None
        assert account.account_identifier_hash
        assert account.is_main is True

    def test_bank_account_invalid_bank_code(self):
        tenant = TenantFactory()
        account = BankAccount(
            tenant_id=tenant.id,
            bank_code="999",
            bank_name="Banco Inválido",
            agency="1234",
            account_number="98765-4",
            account_type=AccountType.CHECKING,
            balance=Decimal("0.00"),
        )

        with pytest.raises(ValidationError) as exc:
            account.full_clean()
        assert "bank_code" in exc.value.message_dict

    def test_bank_account_unique_main_per_tenant(self):
        tenant = TenantFactory()
        self._create_bank_account(tenant, is_main=True)

        with pytest.raises(ValidationError):
            new_account = BankAccount(
                tenant_id=tenant.id,
                bank_code="237",
                bank_name="Bradesco",
                agency="9999",
                account_number="11111-1",
                account_type=AccountType.CHECKING,
                is_main=True,
            )
            new_account.full_clean()

        other_tenant = TenantFactory()
        other_account = self._create_bank_account(
            other_tenant,
            bank_code="237",
            bank_name="Bradesco",
            is_main=True,
        )
        assert other_account.is_main is True

    def test_bank_account_unique_account_identifier_per_tenant(self):
        tenant = TenantFactory()
        self._create_bank_account(tenant, agency="4444", account_number="0001-9")

        duplicate = BankAccount(
            tenant_id=tenant.id,
            bank_code="001",
            bank_name="Banco do Brasil",
            agency="4444",
            account_number="0001-9",
            account_type=AccountType.CHECKING,
        )

        with pytest.raises(ValidationError) as exc:
            duplicate.full_clean()
        assert "account_number" in exc.value.message_dict

        other_tenant = TenantFactory()
        other_account = self._create_bank_account(
            other_tenant,
            agency="4444",
            account_number="0001-9",
        )
        assert other_account.account_identifier_hash


@pytest.mark.django_db
class TestFinancialTransactionModel:
    """Casos de teste para FinancialTransaction."""

    def _setup_base_structures(self):
        tenant = TenantFactory()
        bank_account = BankAccount(
            tenant_id=tenant.id,
            bank_code="001",
            bank_name="Banco do Brasil",
            agency="1234",
            account_number="123456-7",
            account_type=AccountType.CHECKING,
            balance=Decimal("100.00"),
            is_main=True,
            is_active=True,
        )
        bank_account.full_clean()
        bank_account.save()

        category = self._create_payment_category(tenant)
        cost_center = self._create_cost_center(tenant)
        supplier = self._create_supplier(tenant)

        return tenant, bank_account, category, cost_center, supplier

    def _create_payment_category(
        self,
        tenant,
        category_type=PaymentCategoryType.INCOME,
        name="Receitas Operacionais",
    ):
        from iabank.finance.models import PaymentCategory

        category = PaymentCategory(
            tenant_id=tenant.id,
            name=name,
            type=category_type,
            is_active=True,
        )
        category.full_clean()
        category.save()
        return category

    def _create_cost_center(self, tenant):
        from iabank.finance.models import CostCenter

        cost_center = CostCenter(
            tenant_id=tenant.id,
            code="CC-001",
            name="Operações",
            description="Centro de custos principal",
            is_active=True,
        )
        cost_center.full_clean()
        cost_center.save()
        return cost_center

    def _create_supplier(self, tenant):
        from iabank.finance.models import Supplier, SupplierDocumentType

        supplier = Supplier(
            tenant_id=tenant.id,
            document_type=SupplierDocumentType.CNPJ,
            document=generate_cnpj(),
            name="Fornecedor Serviços",
            email="contato@fornecedor.com",
            phone="11988887777",
        )
        supplier.full_clean()
        supplier.save()
        return supplier

    def _create_installment(self, tenant):
        customer = Customer(
            tenant_id=tenant.id,
            document_type=CustomerDocumentType.CNPJ,
            document=generate_cnpj(),
            name="Cliente Pagador",
            email="cliente@empresa.com",
            phone="11977776666",
        )
        customer.full_clean()
        customer.save()

        loan = Loan(
            tenant_id=tenant.id,
            customer=customer,
            principal_amount=Decimal("1000.00"),
            interest_rate=Decimal("0.0200"),
            installments_count=12,
            iof_amount=Decimal("10.00"),
            cet_monthly=Decimal("0.0250"),
            cet_yearly=Decimal("0.3000"),
            total_amount=Decimal("1100.00"),
            first_due_date=timezone.localdate() + timedelta(days=30),
            status=LoanStatus.ACTIVE,
        )
        loan.full_clean()
        loan.save()

        installment = Installment(
            tenant_id=tenant.id,
            loan=loan,
            sequence=1,
            due_date=loan.first_due_date,
            principal_amount=Decimal("100.00"),
            interest_amount=Decimal("10.00"),
            total_amount=Decimal("110.00"),
        )
        installment.full_clean()
        installment.save()
        return installment

    def test_financial_transaction_income_updates_balance(self):
        tenant, account, category, cost_center, supplier = self._setup_base_structures()

        transaction = FinancialTransaction(
            tenant_id=tenant.id,
            bank_account=account,
            type=TransactionType.INCOME,
            category=category,
            cost_center=cost_center,
            amount=Decimal("250.00"),
            description="Recebimento parcela",
            reference_date=timezone.localdate(),
            status=TransactionStatus.PAID,
            payment_date=timezone.localdate(),
        )
        transaction.full_clean()
        transaction.save()

        account.refresh_from_db()
        assert account.balance == Decimal("350.00")

        transaction.amount = Decimal("300.00")
        transaction.full_clean()
        transaction.save()

        account.refresh_from_db()
        assert account.balance == Decimal("400.00")

    def test_financial_transaction_expense_requires_supplier(self):
        tenant, account, _category, cost_center, _supplier = self._setup_base_structures()
        expense_category = self._create_payment_category(
            tenant,
            PaymentCategoryType.EXPENSE,
            name="Despesas Operacionais",
        )

        transaction = FinancialTransaction(
            tenant_id=tenant.id,
            bank_account=account,
            type=TransactionType.EXPENSE,
            category=expense_category,
            cost_center=cost_center,
            amount=Decimal("150.00"),
            description="Pagamento fornecedor",
            reference_date=timezone.localdate(),
            status=TransactionStatus.PENDING,
        )

        with pytest.raises(ValidationError) as exc:
            transaction.full_clean()
        assert "supplier" in exc.value.message_dict

    def test_financial_transaction_paid_requires_payment_date(self):
        tenant, account, _category, cost_center, supplier = self._setup_base_structures()
        expense_category = self._create_payment_category(
            tenant,
            PaymentCategoryType.EXPENSE,
            name="Despesas Operacionais",
        )

        transaction = FinancialTransaction(
            tenant_id=tenant.id,
            bank_account=account,
            type=TransactionType.EXPENSE,
            category=expense_category,
            cost_center=cost_center,
            supplier=supplier,
            amount=Decimal("150.00"),
            description="Pagamento fornecedor",
            reference_date=timezone.localdate(),
            status=TransactionStatus.PAID,
        )

        with pytest.raises(ValidationError) as exc:
            transaction.full_clean()
        assert "payment_date" in exc.value.message_dict

    def test_financial_transaction_installment_only_for_income(self):
        tenant, account, category, cost_center, supplier = self._setup_base_structures()
        expense_category = self._create_payment_category(
            tenant,
            PaymentCategoryType.EXPENSE,
            name="Despesas Operacionais",
        )
        installment = self._create_installment(tenant)

        valid_transaction = FinancialTransaction(
            tenant_id=tenant.id,
            bank_account=account,
            type=TransactionType.INCOME,
            category=category,
            cost_center=cost_center,
            amount=Decimal("500.00"),
            description="Receita vinculada a parcela",
            reference_date=timezone.localdate(),
            status=TransactionStatus.PAID,
            payment_date=timezone.localdate(),
            installment=installment,
        )
        valid_transaction.full_clean()
        valid_transaction.save()

        invalid_transaction = FinancialTransaction(
            tenant_id=tenant.id,
            bank_account=account,
            type=TransactionType.EXPENSE,
            category=expense_category,
            cost_center=cost_center,
            amount=Decimal("100.00"),
            description="Despesa indevida",
            reference_date=timezone.localdate(),
            status=TransactionStatus.PENDING,
            installment=installment,
            supplier=supplier,
        )

        with pytest.raises(ValidationError) as exc:
            invalid_transaction.full_clean()
        assert "installment" in exc.value.message_dict

    def test_financial_transaction_tenant_consistency(self):
        tenant, account, _category, cost_center, supplier = self._setup_base_structures()
        expense_category = self._create_payment_category(
            tenant,
            PaymentCategoryType.EXPENSE,
            name="Despesas Operacionais",
        )
        other_tenant = TenantFactory()

        with pytest.raises(ValidationError) as exc:
            transaction = FinancialTransaction(
                tenant_id=tenant.id,
                bank_account=account,
                type=TransactionType.EXPENSE,
                category=expense_category,
                cost_center=cost_center,
                supplier=supplier,
                amount=Decimal("80.00"),
                description="Despesa inválida",
                reference_date=timezone.localdate(),
                status=TransactionStatus.PENDING,
            )
            transaction.supplier = self._create_supplier(other_tenant)
            transaction.full_clean()
        assert "supplier" in exc.value.message_dict
