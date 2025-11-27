from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from backend.apps.tenancy.managers import TenantManager, use_tenant
from backend.apps.tenancy.models import Tenant


class TenantBaseModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="%(class)ss")

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):  # pragma: no cover - validação é tratada em clean()
        if self.tenant_id:
            with use_tenant(self.tenant_id):
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)


class TimestampedTenantModel(TenantBaseModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(TimestampedTenantModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        BLOCKED = "BLOCKED", "Blocked"
        DELINQUENT = "DELINQUENT", "Delinquent"
        CANCELED = "CANCELED", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=20)
    birth_date = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = "banking_customer"
        unique_together = (("tenant", "document_number"),)
        indexes = [
            models.Index(fields=["tenant", "status"], name="banking_cust_status_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover - auxiliar de debug
        return f"Customer<{self.id}>"


class Address(TimestampedTenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    zip_code = models.CharField(max_length=10)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    complement = models.CharField(max_length=100, null=True, blank=True)
    neighborhood = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "banking_address"
        indexes = [
            models.Index(fields=["customer", "is_primary"], name="banking_address_primary_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "is_primary"],
                condition=models.Q(is_primary=True),
                name="banking_address_primary_unique",
            ),
        ]

    def clean(self) -> None:
        errors: dict[str, list[str]] = {}
        if self.customer_id and self.tenant_id and self.customer.tenant_id != self.tenant_id:
            errors.setdefault("tenant", []).append("Tenant do endereço deve coincidir com o do cliente.")
        if self.state and len(self.state) != 2:
            errors.setdefault("state", []).append("O estado deve ter exatamente 2 caracteres.")
        if errors:
            raise ValidationError(errors)


class Consultant(TimestampedTenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consultant_profile",
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "banking_consultant"
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name="consultant_balance_non_negative"),
        ]


class BankAccount(TimestampedTenantModel):
    class AccountType(models.TextChoices):
        CHECKING = "CHECKING", "Checking"
        SAVINGS = "SAVINGS", "Savings"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        BLOCKED = "BLOCKED", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bank_accounts")
    name = models.CharField(max_length=100)
    agency = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    type = models.CharField(max_length=16, choices=AccountType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = "banking_bank_account"
        indexes = [
            models.Index(fields=["tenant", "status"], name="bank_acct_status_idx"),
            models.Index(fields=["customer"], name="bank_acct_customer_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "account_number"],
                name="banking_bank_account_account_number_uniq",
            ),
            models.UniqueConstraint(
                fields=["tenant", "agency", "account_number"],
                name="banking_bank_account_agency_account_number_uniq",
            ),
        ]


class AccountCategory(TimestampedTenantModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=40)
    description = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "banking_account_category"
        unique_together = (("tenant", "code"),)
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "is_default"],
                condition=models.Q(is_default=True),
                name="account_category_single_default",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "is_default"], name="account_category_default_idx"),
        ]


class Supplier(TimestampedTenantModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        BLOCKED = "BLOCKED", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = "banking_supplier"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "document_number"],
                condition=models.Q(document_number__isnull=False),
                name="supplier_document_unique_per_tenant",
            ),
        ]


class Loan(TimestampedTenantModel):
    class Status(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        PAID_OFF = "PAID_OFF", "Paid off"
        IN_COLLECTION = "IN_COLLECTION", "In collection"
        CANCELED = "CANCELED", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="loans")
    consultant = models.ForeignKey(Consultant, on_delete=models.PROTECT, related_name="loans")
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    number_of_installments = models.PositiveSmallIntegerField()
    contract_date = models.DateField()
    first_installment_date = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    iof_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cet_annual_rate = models.DecimalField(max_digits=7, decimal_places=4)
    cet_monthly_rate = models.DecimalField(max_digits=7, decimal_places=4)

    class Meta:
        db_table = "banking_loan"
        indexes = [
            models.Index(fields=["tenant", "status"], name="banking_loan_status_idx"),
            models.Index(fields=["customer"], name="banking_loan_customer_idx"),
            models.Index(fields=["consultant"], name="banking_loan_consultant_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(number_of_installments__gt=0),
                name="loan_installments_positive",
            ),
        ]


class Installment(TimestampedTenantModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially paid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveSmallIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = "banking_installment"
        unique_together = (("loan", "installment_number"),)
        indexes = [
            models.Index(fields=["tenant", "status"], name="banking_installment_status_idx"),
            models.Index(fields=["loan", "due_date"], name="banking_installment_due_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount_due__gte=0), name="installment_amount_due_positive"),
            models.CheckConstraint(check=models.Q(amount_paid__gte=0), name="installment_amount_paid_positive"),
        ]


class FinancialTransaction(TimestampedTenantModel):
    class TransactionType(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    type = models.CharField(max_length=16, choices=TransactionType.choices)
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transactions",
    )
    category = models.ForeignKey(
        AccountCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    installment = models.ForeignKey(
        Installment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )

    class Meta:
        db_table = "banking_financial_transaction"
        indexes = [
            models.Index(fields=["tenant", "type"], name="financial_tx_type_idx"),
            models.Index(fields=["bank_account"], name="financial_tx_account_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=0), name="financial_tx_amount_positive"),
            models.CheckConstraint(
                check=models.Q(payment_date__isnull=True) | models.Q(is_paid=True),
                name="financial_tx_payment_date_requires_paid",
            ),
        ]


class CreditLimit(TimestampedTenantModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FROZEN = "FROZEN", "Frozen"
        CANCELED = "CANCELED", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="credit_limits")
    current_limit = models.DecimalField(max_digits=12, decimal_places=2)
    used_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    effective_from = models.DateField(null=True, blank=True)
    effective_through = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "banking_credit_limit"
        unique_together = (("tenant", "bank_account"),)
        indexes = [
            models.Index(fields=["tenant", "status"], name="credit_limit_status_idx"),
            models.Index(fields=["bank_account"], name="credit_limit_account_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(current_limit__gte=0), name="credit_limit_non_negative"),
            models.CheckConstraint(check=models.Q(used_amount__gte=0), name="credit_limit_used_non_negative"),
        ]


class Contract(TimestampedTenantModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        REVOKED = "REVOKED", "Revoked"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
    )
    body = models.JSONField()
    etag_payload = models.CharField(max_length=64)
    version = models.CharField(max_length=32)
    signed_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    pii_redacted = models.BooleanField(default=True)

    class Meta:
        db_table = "banking_contract"
        indexes = [
            models.Index(fields=["tenant", "status"], name="contract_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "etag_payload"],
                name="contract_etag_unique_per_tenant",
            ),
        ]
