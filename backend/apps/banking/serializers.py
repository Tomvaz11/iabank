from __future__ import annotations

from rest_framework import serializers

from backend.apps.banking.models import (
    AccountCategory,
    Address,
    BankAccount,
    Consultant,
    Contract,
    CreditLimit,
    Customer,
    FinancialTransaction,
    Installment,
    Loan,
    Supplier,
)


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        validators: list = []


class CustomerSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    document_number = serializers.CharField(max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Customer.Status.choices, default=Customer.Status.ACTIVE)

    class Meta(BaseModelSerializer.Meta):
        model = Customer
        fields = [
            "id",
            "tenant",
            "name",
            "document_number",
            "birth_date",
            "email",
            "phone",
            "status",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "document_number": {"validators": []},
            "email": {"validators": []},
        }


class AddressSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    customer = serializers.UUIDField(source="customer_id")
    zip_code = serializers.CharField(max_length=10)
    street = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=20)
    complement = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    neighborhood = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=2)
    is_primary = serializers.BooleanField(default=False)

    class Meta(BaseModelSerializer.Meta):
        model = Address
        fields = [
            "id",
            "tenant",
            "customer",
            "zip_code",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "is_primary",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"zip_code": {"validators": []}}


class ConsultantSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    user = serializers.CharField(source="user_id")
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta(BaseModelSerializer.Meta):
        model = Consultant
        fields = ["id", "tenant", "user", "balance"]
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"validators": []}}


class AccountCategorySerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    code = serializers.CharField(max_length=40)
    description = serializers.CharField(max_length=255)
    is_default = serializers.BooleanField(default=False)

    class Meta(BaseModelSerializer.Meta):
        model = AccountCategory
        fields = ["id", "tenant", "code", "description", "is_default"]
        read_only_fields = ["id"]
        extra_kwargs = {"code": {"validators": []}}


class BankAccountSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    customer = serializers.UUIDField(source="customer_id")
    name = serializers.CharField(max_length=100)
    agency = serializers.CharField(max_length=10)
    account_number = serializers.CharField(max_length=20)
    initial_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    type = serializers.ChoiceField(choices=BankAccount.AccountType.choices)
    status = serializers.ChoiceField(choices=BankAccount.Status.choices, default=BankAccount.Status.ACTIVE)

    class Meta(BaseModelSerializer.Meta):
        model = BankAccount
        fields = [
            "id",
            "tenant",
            "customer",
            "name",
            "agency",
            "account_number",
            "initial_balance",
            "type",
            "status",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "agency": {"validators": []},
            "account_number": {"validators": []},
        }


class SupplierSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    name = serializers.CharField(max_length=255)
    document_number = serializers.CharField(allow_null=True, allow_blank=True, max_length=20)
    status = serializers.ChoiceField(choices=Supplier.Status.choices, default=Supplier.Status.ACTIVE)

    class Meta(BaseModelSerializer.Meta):
        model = Supplier
        fields = ["id", "tenant", "name", "document_number", "status"]
        read_only_fields = ["id"]
        extra_kwargs = {"document_number": {"validators": []}}


class LoanSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    customer = serializers.UUIDField(source="customer_id")
    consultant = serializers.UUIDField(source="consultant_id")
    principal_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    number_of_installments = serializers.IntegerField()
    contract_date = serializers.DateField()
    first_installment_date = serializers.DateField()
    status = serializers.ChoiceField(choices=Loan.Status.choices, default=Loan.Status.IN_PROGRESS)
    iof_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    cet_annual_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    cet_monthly_rate = serializers.DecimalField(max_digits=7, decimal_places=4)

    class Meta(BaseModelSerializer.Meta):
        model = Loan
        fields = [
            "id",
            "tenant",
            "customer",
            "consultant",
            "principal_amount",
            "interest_rate",
            "number_of_installments",
            "contract_date",
            "first_installment_date",
            "status",
            "iof_amount",
            "cet_annual_rate",
            "cet_monthly_rate",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"customer": {"validators": []}}


class InstallmentSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    loan = serializers.UUIDField(source="loan_id")
    installment_number = serializers.IntegerField()
    due_date = serializers.DateField()
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Installment.Status.choices, default=Installment.Status.PENDING)

    class Meta(BaseModelSerializer.Meta):
        model = Installment
        fields = [
            "id",
            "tenant",
            "loan",
            "installment_number",
            "due_date",
            "amount_due",
            "amount_paid",
            "payment_date",
            "status",
        ]
        read_only_fields = ["id"]


class FinancialTransactionSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    description = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = serializers.DateField()
    is_paid = serializers.BooleanField(default=False)
    payment_date = serializers.DateField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=FinancialTransaction.TransactionType.choices)
    bank_account = serializers.UUIDField(required=False, allow_null=True, source="bank_account_id")
    category = serializers.UUIDField(required=False, allow_null=True, source="category_id")
    supplier = serializers.UUIDField(required=False, allow_null=True, source="supplier_id")
    installment = serializers.UUIDField(required=False, allow_null=True, source="installment_id")

    class Meta(BaseModelSerializer.Meta):
        model = FinancialTransaction
        fields = [
            "id",
            "tenant",
            "description",
            "amount",
            "transaction_date",
            "is_paid",
            "payment_date",
            "type",
            "bank_account",
            "category",
            "supplier",
            "installment",
        ]
        read_only_fields = ["id"]


class CreditLimitSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    bank_account = serializers.UUIDField(source="bank_account_id")
    current_limit = serializers.DecimalField(max_digits=12, decimal_places=2)
    used_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    status = serializers.ChoiceField(choices=CreditLimit.Status.choices, default=CreditLimit.Status.ACTIVE)
    effective_from = serializers.DateField(required=False, allow_null=True)
    effective_through = serializers.DateField(required=False, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = CreditLimit
        fields = [
            "id",
            "tenant",
            "bank_account",
            "current_limit",
            "used_amount",
            "status",
            "effective_from",
            "effective_through",
        ]
        read_only_fields = ["id"]


class ContractSerializer(BaseModelSerializer):
    tenant = serializers.UUIDField(source="tenant_id")
    bank_account = serializers.UUIDField(required=False, allow_null=True, source="bank_account_id")
    customer = serializers.UUIDField(required=False, allow_null=True, source="customer_id")
    body = serializers.DictField()
    etag_payload = serializers.CharField(max_length=64)
    version = serializers.CharField(max_length=32)
    signed_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=Contract.Status.choices, default=Contract.Status.ACTIVE)
    pii_redacted = serializers.BooleanField(default=True)

    class Meta(BaseModelSerializer.Meta):
        model = Contract
        fields = [
            "id",
            "tenant",
            "bank_account",
            "customer",
            "body",
            "etag_payload",
            "version",
            "signed_at",
            "status",
            "pii_redacted",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"etag_payload": {"validators": []}}
