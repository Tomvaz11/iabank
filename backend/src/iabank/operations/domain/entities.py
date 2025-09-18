"""Entidades de domínio para empréstimos e parcelas."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


REGRET_PERIOD_DAYS = 7
MIN_INSTALLMENTS = 1
MAX_INSTALLMENTS = 120
MONEY_QUANTIZER = Decimal("0.01")
RATE_QUANTIZER = Decimal("0.0001")


class LoanStatus(StrEnum):
    """Estados permitidos para um empréstimo dentro do domínio."""

    ANALYSIS = "ANALYSIS"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"
    COLLECTION = "COLLECTION"
    CANCELLED = "CANCELLED"


class InstallmentStatus(StrEnum):
    """Estados permitidos para uma parcela de empréstimo."""

    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


def _ensure_money(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        raise ValueError("Valor monetário é obrigatório")

    decimal_value = Decimal(value)
    if decimal_value < Decimal("0.00"):
        raise ValueError("Valor monetário não pode ser negativo")
    return decimal_value.quantize(MONEY_QUANTIZER)


def _ensure_rate(value: Decimal | int | float | None) -> Decimal:
    if value is None:
        raise ValueError("Valor de taxa é obrigatório")

    decimal_value = Decimal(value)
    if decimal_value < Decimal("0.0000"):
        raise ValueError("Taxa não pode ser negativa")
    return decimal_value.quantize(RATE_QUANTIZER)


class LoanEntity(BaseModel):
    """Entidade de domínio representando empréstimos multi-tenant."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID = Field(description="Tenant proprietário do empréstimo")
    customer_id: UUID = Field(description="Cliente vinculado ao empréstimo")
    consultant_id: Optional[UUID] = Field(default=None, description="Consultor responsável")
    principal_amount: Decimal = Field(gt=Decimal("0.00"))
    interest_rate: Decimal = Field(ge=Decimal("0.0000"))
    installments_count: int = Field(ge=MIN_INSTALLMENTS, le=MAX_INSTALLMENTS)
    iof_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    cet_monthly: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    cet_yearly: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    total_amount: Decimal = Field(ge=Decimal("0.00"))
    contract_date: date = Field(default_factory=date.today)
    first_due_date: date = Field(description="Vencimento da primeira parcela")
    status: LoanStatus = Field(default=LoanStatus.ANALYSIS)
    regret_deadline: Optional[date] = Field(default=None, description="Prazo de arrependimento legal")
    notes: Optional[str] = Field(default=None, max_length=2000)
    version: int = Field(default=1, ge=1)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("principal_amount", "iof_amount", "total_amount", mode="before")
    @classmethod
    def _normalize_money(cls, value: Decimal | int | float | None) -> Decimal:
        return _ensure_money(value)

    @field_validator("interest_rate", "cet_monthly", "cet_yearly", mode="before")
    @classmethod
    def _normalize_rate(cls, value: Decimal | int | float | None) -> Decimal:
        return _ensure_rate(value)

    @field_validator("notes", mode="before")
    @classmethod
    def _normalize_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _validate_business_rules(self) -> "LoanEntity":
        if self.first_due_date <= self.contract_date:
            raise ValueError("first_due_date deve ser posterior à contract_date")

        expected_deadline = self.contract_date + timedelta(days=REGRET_PERIOD_DAYS)
        if self.regret_deadline is None:
            object.__setattr__(self, "regret_deadline", expected_deadline)
        elif self.regret_deadline != expected_deadline:
            raise ValueError("regret_deadline deve ser exatamente 7 dias após contract_date")

        minimum_total = (self.principal_amount + self.iof_amount).quantize(MONEY_QUANTIZER)
        if self.total_amount.quantize(MONEY_QUANTIZER) < minimum_total:
            raise ValueError("total_amount deve ser maior ou igual à soma de principal e IOF")

        return self

    def is_within_regret_period(self, reference_date: Optional[date] = None) -> bool:
        """Indica se o empréstimo ainda está dentro do período de arrependimento."""

        today = reference_date or date.today()
        return today <= (self.regret_deadline or (self.contract_date + timedelta(days=REGRET_PERIOD_DAYS)))


class InstallmentEntity(BaseModel):
    """Entidade de domínio representando uma parcela de empréstimo."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID = Field(description="Tenant proprietário da parcela")
    loan_id: UUID = Field(description="Empréstimo associado")
    sequence: int = Field(ge=1)
    due_date: date = Field(description="Data de vencimento da parcela")
    principal_amount: Decimal = Field(ge=Decimal("0.00"))
    interest_amount: Decimal = Field(ge=Decimal("0.00"))
    total_amount: Decimal = Field(ge=Decimal("0.00"))
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    payment_date: Optional[date] = Field(default=None)
    late_fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    interest_penalty: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    status: InstallmentStatus = Field(default=InstallmentStatus.PENDING)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator(
        "principal_amount",
        "interest_amount",
        "total_amount",
        "amount_paid",
        "late_fee",
        "interest_penalty",
        mode="before",
    )
    @classmethod
    def _normalize_money(cls, value: Decimal | int | float | None) -> Decimal:
        return _ensure_money(value if value is not None else Decimal("0.00"))

    @model_validator(mode="after")
    def _validate_business_rules(self) -> "InstallmentEntity":
        expected_total = (self.principal_amount + self.interest_amount).quantize(MONEY_QUANTIZER)
        if self.total_amount.quantize(MONEY_QUANTIZER) != expected_total:
            raise ValueError("total_amount deve ser igual à soma de principal e juros")

        total_with_penalties = self.total_amount + self.late_fee + self.interest_penalty
        if self.amount_paid > total_with_penalties:
            raise ValueError("amount_paid não pode exceder o total devido incluindo encargos")

        if self.status == InstallmentStatus.PAID:
            if not self.payment_date:
                raise ValueError("payment_date é obrigatório quando a parcela está paga")
            if self.amount_paid.quantize(MONEY_QUANTIZER) < total_with_penalties.quantize(MONEY_QUANTIZER):
                raise ValueError("Parcelas pagas devem ter quitação total incluindo encargos")

        if self.status == InstallmentStatus.PARTIALLY_PAID:
            if self.amount_paid <= Decimal("0.00"):
                raise ValueError("Pagamento parcial requer valor pago maior que zero")
            if self.amount_paid >= total_with_penalties:
                raise ValueError("Pagamento parcial não pode quitar totalmente a parcela")

        if self.status == InstallmentStatus.PENDING:
            if self.amount_paid > Decimal("0.00"):
                raise ValueError("Parcelas pendentes não devem possuir valor pago")
            if self.payment_date is not None:
                raise ValueError("Parcelas pendentes não devem ter payment_date preenchido")

        if self.payment_date and self.amount_paid <= Decimal("0.00"):
            raise ValueError("payment_date só pode ser informado quando houver pagamento")

        return self

    def remaining_balance(self) -> Decimal:
        """Calcula o saldo pendente considerando encargos."""

        total_with_penalties = self.total_amount + self.late_fee + self.interest_penalty
        remaining = total_with_penalties - self.amount_paid
        if remaining <= Decimal("0.00"):
            return Decimal("0.00")
        return remaining.quantize(MONEY_QUANTIZER)

    def is_overdue(self, reference_date: Optional[date] = None) -> bool:
        """Indica se a parcela está vencida considerando data de referência."""

        if self.status == InstallmentStatus.PAID:
            return False

        today = reference_date or date.today()
        return today > self.due_date
