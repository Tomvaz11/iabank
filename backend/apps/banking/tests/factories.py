from __future__ import annotations

import hashlib
import json
import random
import string
import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

import factory
from django.contrib.auth import get_user_model

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
    TenantBaseModel,
)
from backend.apps.banking.services.financial_calculations import LoanInput, calculate_cet, generate_installments
from backend.apps.foundation.services.seed_utils import VaultTransitFPEClient, derive_factory_seed
from backend.apps.tenancy.models import Tenant

User = get_user_model()


@dataclass(slots=True)
class FactoryContext:
    tenant_id: str
    environment: str
    manifest_version: str
    salt_version: str
    reference_date: date = date(2025, 1, 1)

    @property
    def tenant_uuid(self) -> uuid.UUID:
        return uuid.UUID(str(self.tenant_id))

    @property
    def tenant_slug(self) -> str:
        return str(self.tenant_uuid).split("-")[0]

    @property
    def factory_seed(self) -> int:
        return derive_factory_seed(
            str(self.tenant_id),
            self.environment,
            self.manifest_version,
            self.salt_version,
        )

    @property
    def fpe_client(self) -> VaultTransitFPEClient:
        return VaultTransitFPEClient(transit_path=f"transit/seeds/{self.environment}/{self.tenant_id}")

    def _seed(self, label: str) -> int:
        payload = f"{label}|{self.factory_seed}"
        digest = hashlib.sha256(payload.encode()).digest()
        return int.from_bytes(digest[:8], "big")

    def deterministic_digits(self, label: str, length: int) -> str:
        rng = random.Random(self._seed(label))
        return "".join(str(rng.randint(0, 9)) for _ in range(length))

    def deterministic_letters(self, label: str, length: int) -> str:
        rng = random.Random(self._seed(label))
        return "".join(rng.choice(string.ascii_uppercase) for _ in range(length))

    def deterministic_decimal(self, label: str, min_value: Decimal, max_value: Decimal, places: int = 2) -> Decimal:
        rng = random.Random(self._seed(label))
        span = max_value - min_value
        quantize = Decimal("0." + ("0" * (places - 1)) + "1")
        value = min_value + span * Decimal(rng.random())
        return value.quantize(quantize, rounding=ROUND_HALF_UP)

    def masked_digits(self, label: str, length: int) -> str:
        raw = self.deterministic_digits(label, length)
        return self.fpe_client.mask(raw, salt_version=self.salt_version)

    def masked_email(self, prefix: str, suffix: str = "") -> str:
        local_part = f"{prefix}-{suffix or '0'}"
        masked_local = self.fpe_client.mask(local_part, salt_version=self.salt_version)
        return f"{masked_local}@masked.test"

    def with_overrides(self, **kwargs: Any) -> "FactoryContext":
        return replace(self, **kwargs)

    @classmethod
    def default(cls) -> "FactoryContext":
        return cls(
            tenant_id="00000000-0000-0000-0000-000000000000",
            environment="dev",
            manifest_version="0.0.0",
            salt_version="v1",
        )


class BaseBankingFactory(factory.Factory):
    class Meta:
        abstract = True

    factory_context = factory.LazyFunction(FactoryContext.default)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        return cls._construct_instance(model_class, *args, **kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return cls._construct_instance(model_class, *args, **kwargs)

    @classmethod
    def _construct_instance(cls, model_class, *args, **kwargs):
        context = kwargs.pop("factory_context", None) or FactoryContext.default()
        if not isinstance(context, FactoryContext):
            raise TypeError("factory_context deve ser um FactoryContext")
        obj = model_class(*args, **kwargs)
        setattr(obj, "factory_context", context)
        if isinstance(obj, TenantBaseModel):
            obj.tenant = obj.tenant or context.tenant_uuid
        return obj

    @classmethod
    def _normalize_tenant(cls, tenant: Tenant | None, context: FactoryContext) -> Tenant:
        if tenant:
            return tenant
        return Tenant(
            id=context.tenant_uuid,
            slug=context.tenant_slug,
            display_name=f"Tenant {context.tenant_slug}",
            primary_domain=f"{context.tenant_slug}.{context.environment}.seed.test",
            status=Tenant.Status.PILOT,
            pii_policy_version="1.0.0",
        )


def _loan_request_for_stub(stub) -> tuple[LoanInput, Decimal]:
    annual_rate = stub.factory_context.deterministic_decimal(
        "loan-annual-rate",
        Decimal("10.00"),
        Decimal("18.00"),
    )
    request = LoanInput(
        principal_amount=stub.principal_amount,
        annual_rate_pct=annual_rate,
        number_of_installments=stub.number_of_installments,
        contract_date=stub.contract_date,
        first_installment_date=stub.first_installment_date,
    )
    return request, annual_rate


class TenantFactory(BaseBankingFactory):
    class Meta:
        model = Tenant

    id = factory.LazyAttribute(lambda obj: obj.factory_context.tenant_uuid)
    slug = factory.LazyAttribute(lambda obj: obj.factory_context.tenant_slug)
    display_name = factory.LazyAttribute(lambda obj: f"Tenant {obj.factory_context.tenant_slug}")
    primary_domain = factory.LazyAttribute(
        lambda obj: f"{obj.factory_context.tenant_slug}.{obj.factory_context.environment}.seed.test",
    )
    status = Tenant.Status.PILOT
    pii_policy_version = "1.0.0"
    default_theme = None


class CustomerFactory(BaseBankingFactory):
    class Meta:
        model = Customer

    tenant = factory.SubFactory(TenantFactory, factory_context=factory.SelfAttribute("..factory_context"))
    name = factory.LazyAttribute(lambda obj: f"Customer-{obj.factory_context.tenant_slug}")
    document_number = factory.LazyAttribute(lambda obj: obj.factory_context.masked_digits("customer-document", 11))
    birth_date = factory.LazyFunction(lambda: date(1990, 1, 1))
    email = factory.LazyAttribute(lambda obj: obj.factory_context.masked_email("customer", suffix="0"))
    phone = factory.LazyAttribute(lambda obj: obj.factory_context.masked_digits("customer-phone", 11))
    status = Customer.Status.ACTIVE


class AddressFactory(BaseBankingFactory):
    class Meta:
        model = Address

    tenant = factory.SelfAttribute("customer.tenant")
    customer = factory.SubFactory(CustomerFactory, factory_context=factory.SelfAttribute("..factory_context"))
    zip_code = factory.LazyAttribute(lambda obj: obj.factory_context.masked_digits("address-zip", 8))
    street = factory.LazyAttribute(lambda obj: f"Rua {obj.factory_context.masked_digits('address-street', 6)}")
    number = factory.LazyAttribute(lambda obj: obj.factory_context.deterministic_digits("address-number", 4))
    complement = None
    neighborhood = factory.LazyAttribute(lambda obj: f"Bairro {obj.factory_context.deterministic_letters('address-nb', 3)}")
    city = factory.LazyAttribute(lambda obj: f"Cidade {obj.factory_context.deterministic_letters('address-city', 4)}")
    state = factory.LazyAttribute(lambda obj: obj.factory_context.deterministic_letters("address-state", 2))
    is_primary = False


class ConsultantFactory(BaseBankingFactory):
    class Meta:
        model = Consultant

    tenant = factory.SubFactory(TenantFactory, factory_context=factory.SelfAttribute("..factory_context"))
    user = factory.LazyAttribute(
        lambda obj: User(
            id=int(obj.factory_context.deterministic_digits("consultant-user-id", 4)),
            username=f"consultant-{obj.factory_context.tenant_slug}",
            email=obj.factory_context.masked_email("consultant", suffix="0"),
        ),
    )
    balance = Decimal("0.00")


class AccountCategoryFactory(BaseBankingFactory):
    class Meta:
        model = AccountCategory

    tenant = factory.SubFactory(TenantFactory, factory_context=factory.SelfAttribute("..factory_context"))
    code = factory.LazyAttribute(lambda obj: f"C{obj.factory_context.deterministic_digits('account-category-code', 3)}")
    description = factory.LazyAttribute(lambda obj: f"Categoria {obj.code}")
    is_default = False


class BankAccountFactory(BaseBankingFactory):
    class Meta:
        model = BankAccount

    tenant = factory.SelfAttribute("customer.tenant")
    customer = factory.SubFactory(CustomerFactory, factory_context=factory.SelfAttribute("..factory_context"))
    name = factory.LazyAttribute(lambda obj: f"Conta {obj.customer.name}")
    agency = factory.LazyAttribute(lambda obj: obj.factory_context.masked_digits("bank-agency", 10))
    account_number = factory.LazyAttribute(lambda obj: obj.factory_context.masked_digits("bank-account-number", 20))
    initial_balance = Decimal("1000.00")
    type = BankAccount.AccountType.CHECKING
    status = BankAccount.Status.ACTIVE


class SupplierFactory(BaseBankingFactory):
    class Meta:
        model = Supplier

    tenant = factory.SubFactory(TenantFactory, factory_context=factory.SelfAttribute("..factory_context"))
    name = factory.LazyAttribute(lambda obj: f"Fornecedor {obj.factory_context.tenant_slug}")
    document_number = factory.LazyAttribute(lambda obj: obj.factory_context.masked_digits("supplier-document", 14))
    status = Supplier.Status.ACTIVE


class LoanFactory(BaseBankingFactory):
    class Meta:
        model = Loan

    tenant = factory.SelfAttribute("customer.tenant")
    customer = factory.SubFactory(CustomerFactory, factory_context=factory.SelfAttribute("..factory_context"))
    consultant = factory.SubFactory(ConsultantFactory, factory_context=factory.SelfAttribute("..factory_context"))
    principal_amount = factory.LazyAttribute(
        lambda obj: obj.factory_context.deterministic_decimal("loan-principal", Decimal("5000"), Decimal("15000")),
    )
    contract_date = factory.LazyAttribute(lambda obj: obj.factory_context.reference_date)
    first_installment_date = factory.LazyAttribute(lambda obj: obj.contract_date + timedelta(days=30))
    number_of_installments = factory.LazyAttribute(lambda obj: 12)
    status = Loan.Status.IN_PROGRESS

    @factory.lazy_attribute
    def interest_rate(self) -> Decimal:
        _, annual_rate = _loan_request_for_stub(self)
        return (annual_rate / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _quote(self):
        if not hasattr(self, "_cached_quote"):
            request, _ = _loan_request_for_stub(self)
            setattr(self, "_cached_quote", calculate_cet(request))
        return getattr(self, "_cached_quote")

    @factory.lazy_attribute
    def iof_amount(self) -> Decimal:
        request, _ = _loan_request_for_stub(self)
        return calculate_cet(request).iof_amount

    @factory.lazy_attribute
    def cet_annual_rate(self) -> Decimal:
        request, _ = _loan_request_for_stub(self)
        return calculate_cet(request).cet_annual_rate

    @factory.lazy_attribute
    def cet_monthly_rate(self) -> Decimal:
        request, _ = _loan_request_for_stub(self)
        return calculate_cet(request).cet_monthly_rate


class InstallmentFactory(BaseBankingFactory):
    class Meta:
        model = Installment

    tenant = factory.SelfAttribute("loan.tenant")
    loan = factory.SubFactory(LoanFactory, factory_context=factory.SelfAttribute("..factory_context"))
    installment_number = factory.Sequence(lambda n: n + 1)

    @factory.lazy_attribute
    def due_date(self) -> date:
        annual_rate = (self.loan.interest_rate * Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        request = LoanInput(
            principal_amount=self.loan.principal_amount,
            annual_rate_pct=annual_rate,
            number_of_installments=self.loan.number_of_installments,
            contract_date=self.loan.contract_date,
            first_installment_date=self.loan.first_installment_date,
        )
        schedule = generate_installments(request)
        index = max(0, self.installment_number - 1)
        return schedule[index % len(schedule)].due_date

    @factory.lazy_attribute
    def amount_due(self) -> Decimal:
        annual_rate = (self.loan.interest_rate * Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        request = LoanInput(
            principal_amount=self.loan.principal_amount,
            annual_rate_pct=annual_rate,
            number_of_installments=self.loan.number_of_installments,
            contract_date=self.loan.contract_date,
            first_installment_date=self.loan.first_installment_date,
        )
        schedule = generate_installments(request)
        index = max(0, self.installment_number - 1)
        return schedule[index % len(schedule)].amount

    amount_paid = Decimal("0.00")
    payment_date = None
    status = Installment.Status.PENDING


class FinancialTransactionFactory(BaseBankingFactory):
    class Meta:
        model = FinancialTransaction

    tenant = factory.SubFactory(TenantFactory, factory_context=factory.SelfAttribute("..factory_context"))
    description = factory.LazyAttribute(lambda obj: f"Transacao {obj.factory_context.deterministic_digits('tx', 4)}")
    amount = factory.LazyAttribute(lambda obj: obj.factory_context.deterministic_decimal("tx-amount", Decimal("10"), Decimal("500")))
    transaction_date = factory.LazyAttribute(lambda obj: obj.factory_context.reference_date)
    is_paid = True
    payment_date = factory.LazyAttribute(lambda obj: obj.transaction_date)
    type = FinancialTransaction.TransactionType.EXPENSE
    bank_account = factory.SubFactory(BankAccountFactory, factory_context=factory.SelfAttribute("..factory_context"))
    category = factory.SubFactory(AccountCategoryFactory, factory_context=factory.SelfAttribute("..factory_context"))
    supplier = factory.SubFactory(SupplierFactory, factory_context=factory.SelfAttribute("..factory_context"))
    installment = factory.SubFactory(InstallmentFactory, factory_context=factory.SelfAttribute("..factory_context"))


class CreditLimitFactory(BaseBankingFactory):
    class Meta:
        model = CreditLimit

    tenant = factory.SelfAttribute("bank_account.tenant")
    bank_account = factory.SubFactory(BankAccountFactory, factory_context=factory.SelfAttribute("..factory_context"))
    current_limit = factory.LazyAttribute(
        lambda obj: obj.factory_context.deterministic_decimal("credit-limit", Decimal("2000"), Decimal("8000")),
    )
    used_amount = factory.LazyAttribute(lambda obj: (obj.current_limit * Decimal("0.10")).quantize(Decimal("0.01")))
    status = CreditLimit.Status.ACTIVE
    effective_from = factory.LazyAttribute(lambda obj: obj.factory_context.reference_date)
    effective_through = factory.LazyAttribute(lambda obj: obj.effective_from + timedelta(days=365))


class ContractFactory(BaseBankingFactory):
    class Meta:
        model = Contract

    tenant = factory.SelfAttribute("customer.tenant")
    bank_account = factory.SubFactory(BankAccountFactory, factory_context=factory.SelfAttribute("..factory_context"))
    customer = factory.SubFactory(CustomerFactory, factory_context=factory.SelfAttribute("..factory_context"))

    @factory.lazy_attribute
    def body(self) -> dict:
        tenant_ref = self.factory_context.tenant_uuid
        return {
            "tenant": str(tenant_ref),
            "account_ref": str(self.bank_account.id),
            "customer_ref": str(self.customer.id),
            "masked_account_number": self.bank_account.account_number,
            "masked_document": self.customer.document_number,
        }

    @factory.lazy_attribute
    def etag_payload(self) -> str:
        payload = json.dumps(self.body, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    version = "1.0.0"
    signed_at = factory.LazyAttribute(lambda obj: datetime.combine(obj.factory_context.reference_date, datetime.min.time(), tzinfo=timezone.utc))
    status = Contract.Status.ACTIVE
    pii_redacted = True


def build_batch(factory_class: type[BaseBankingFactory], size: int, **kwargs: Any) -> Iterable[Any]:
    return [factory_class.build(**kwargs) for _ in range(size)]
