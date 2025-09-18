"""Serviços de domínio para cálculos e regras de empréstimos e parcelas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Iterable, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .entities import (
    InstallmentEntity,
    InstallmentStatus,
    LoanEntity,
    LoanStatus,
    MONEY_QUANTIZER,
    RATE_QUANTIZER,
    REGRET_PERIOD_DAYS,
)


# Configura precisão global para cálculos financeiros
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP


MONEY_ZERO = Decimal("0.00")
RATE_ZERO = Decimal("0.0000")
DEFAULT_IOF_FIXED_RATE = Decimal("0.0038")
DEFAULT_IOF_DAILY_RATE = Decimal("0.000082")
DEFAULT_PAYMENT_TOLERANCE = Decimal("0.01")
DEFAULT_LATE_FEE_RATE = Decimal("0.02")  # 2%
DEFAULT_DAILY_PENALTY_RATE = Decimal("0.00033")  # ~1% ao mês


class LoanDomainError(RuntimeError):
    """Erro genérico da camada de domínio de operações."""


class InterestRateLimitError(LoanDomainError):
    """Indica que a taxa informada excede o limite do tenant."""


class LoanStatusTransitionError(LoanDomainError):
    """Transição de status não permitida."""


class LoanCancellationError(LoanDomainError):
    """Cancelamento inválido de empréstimo."""


class InstallmentPaymentError(LoanDomainError):
    """Erro em operações de pagamento de parcelas."""


class LoanCreateInput(BaseModel):
    """Entrada para criação de empréstimo via domínio."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    customer_id: UUID
    consultant_id: Optional[UUID] = Field(default=None)
    principal_amount: Decimal = Field(gt=MONEY_ZERO)
    interest_rate: Decimal = Field(ge=RATE_ZERO)
    installments_count: int = Field(gt=0)
    first_due_date: date
    contract_date: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(default=None, max_length=2000)
    max_interest_rate: Optional[Decimal] = Field(default=None, ge=RATE_ZERO)
    iof_fixed_rate: Decimal = Field(default=DEFAULT_IOF_FIXED_RATE, ge=RATE_ZERO)
    iof_daily_rate: Decimal = Field(default=DEFAULT_IOF_DAILY_RATE, ge=RATE_ZERO)
    regret_period_days: int = Field(default=REGRET_PERIOD_DAYS, ge=1)

    @field_validator("principal_amount", mode="before")
    @classmethod
    def _normalize_principal(cls, value: Decimal | float | int) -> Decimal:
        return Decimal(value).quantize(MONEY_QUANTIZER)

    @field_validator("interest_rate", "max_interest_rate", mode="before")
    @classmethod
    def _normalize_rate(cls, value: Decimal | float | int | None) -> Optional[Decimal]:
        if value is None:
            return None
        return Decimal(value).quantize(RATE_QUANTIZER)

    @field_validator("notes", mode="before")
    @classmethod
    def _strip_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def _validate_dates(self) -> "LoanCreateInput":
        if self.first_due_date <= self.contract_date:
            raise ValueError("first_due_date deve ser posterior à contract_date")
        return self


class LoanStatusUpdateInput(BaseModel):
    """Entrada suportada para atualização de status."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    status: LoanStatus


class LoanCancellationInput(BaseModel):
    """Dados necessários para cancelamento de empréstimo."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    reason: str = Field(min_length=3, max_length=500)
    requested_by: Optional[str] = Field(default=None, max_length=255)
    reference_date: date = Field(default_factory=date.today)

    @field_validator("reason")
    @classmethod
    def _strip_reason(cls, value: str) -> str:
        return value.strip()


class InstallmentPaymentInput(BaseModel):
    """Informações necessárias para processar pagamento de parcela."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    amount: Decimal = Field(gt=MONEY_ZERO)
    payment_date: date
    bank_account_id: Optional[UUID] = None
    payment_method: Optional[str] = None

    @field_validator("amount", mode="before")
    @classmethod
    def _normalize_amount(cls, value: Decimal | float | int) -> Decimal:
        return Decimal(value).quantize(MONEY_QUANTIZER)


class InstallmentPlan(BaseModel):
    """Representa uma parcela calculada ainda não persistida."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    sequence: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal

    def to_entity(self, *, tenant_id: UUID, loan_id: UUID) -> InstallmentEntity:
        """Converte o plano para uma entidade de domínio persistível."""

        return InstallmentEntity(
            tenant_id=tenant_id,
            loan_id=loan_id,
            sequence=self.sequence,
            due_date=self.due_date,
            principal_amount=self.principal_amount,
            interest_amount=self.interest_amount,
            total_amount=self.total_amount,
            amount_paid=MONEY_ZERO,
            late_fee=MONEY_ZERO,
            interest_penalty=MONEY_ZERO,
            status=InstallmentStatus.PENDING,
        )


@dataclass
class LoanCalculationResult:
    """Resultado da simulação de criação de empréstimo."""

    loan: LoanEntity
    installments: List[InstallmentPlan]
    iof_fixed_rate: Decimal
    iof_daily_rate: Decimal


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def _quantize_rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_QUANTIZER, rounding=ROUND_HALF_UP)


def _add_months(base_date: date, months: int) -> date:
    """Adiciona meses respeitando fim de mês."""

    year = base_date.year + (base_date.month - 1 + months) // 12
    month = (base_date.month - 1 + months) % 12 + 1
    day = min(base_date.day, _last_day_of_month(year, month))
    return date(year, month, day)


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    next_month = date(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    return last_day.day


class LoanService:
    """Serviços principais relacionados a empréstimos."""

    PAYMENT_TOLERANCE = DEFAULT_PAYMENT_TOLERANCE

    @classmethod
    def create_loan(cls, data: LoanCreateInput) -> LoanCalculationResult:
        """Calcula IOF, CET e cronograma de parcelas."""

        cls._validate_interest_rate_limit(data)

        installments = cls._build_price_schedule(
            principal=data.principal_amount,
            interest_rate=data.interest_rate,
            installments_count=data.installments_count,
            first_due_date=data.first_due_date,
            tenant_id=data.tenant_id,
        )

        iof_amount = cls._calculate_iof(
            principal=data.principal_amount,
            installments=installments,
            contract_date=data.contract_date,
            fixed_rate=data.iof_fixed_rate,
            daily_rate=data.iof_daily_rate,
        )

        cet_monthly, cet_yearly = cls._calculate_cet(
            principal=data.principal_amount,
            installments=installments,
            iof_amount=iof_amount,
        )

        total_installments = sum(item.total_amount for item in installments)
        minimum_total = data.principal_amount + iof_amount
        total_amount = _quantize_money(max(total_installments, minimum_total))

        regret_deadline = data.contract_date + timedelta(days=data.regret_period_days)

        loan = LoanEntity(
            tenant_id=data.tenant_id,
            customer_id=data.customer_id,
            consultant_id=data.consultant_id,
            principal_amount=data.principal_amount,
            interest_rate=data.interest_rate,
            installments_count=data.installments_count,
            iof_amount=iof_amount,
            cet_monthly=cet_monthly,
            cet_yearly=cet_yearly,
            total_amount=total_amount,
            contract_date=data.contract_date,
            first_due_date=data.first_due_date,
            status=LoanStatus.ANALYSIS,
            regret_deadline=regret_deadline,
            notes=data.notes,
        )

        return LoanCalculationResult(
            loan=loan,
            installments=installments,
            iof_fixed_rate=data.iof_fixed_rate,
            iof_daily_rate=data.iof_daily_rate,
        )

    @classmethod
    def approve(cls, loan: LoanEntity) -> LoanEntity:
        """Aprova empréstimo se estiver em análise."""

        if loan.status is not LoanStatus.ANALYSIS:
            raise LoanStatusTransitionError("Empréstimo só pode ser aprovado a partir do status ANALYSIS.")
        return loan.model_copy(update={"status": LoanStatus.APPROVED})

    @classmethod
    def change_status(
        cls,
        loan: LoanEntity,
        *,
        new_status: LoanStatus,
        reference_date: Optional[date] = None,
    ) -> LoanEntity:
        """Altera status respeitando transições permitidas."""

        if loan.status == new_status:
            return loan

        allowed_transitions = {
            LoanStatus.ANALYSIS: {LoanStatus.APPROVED, LoanStatus.CANCELLED},
            LoanStatus.APPROVED: {LoanStatus.ACTIVE, LoanStatus.CANCELLED},
            LoanStatus.ACTIVE: {LoanStatus.FINISHED, LoanStatus.COLLECTION, LoanStatus.CANCELLED},
            LoanStatus.COLLECTION: {LoanStatus.FINISHED},
        }

        permitted = allowed_transitions.get(loan.status, set())
        if new_status not in permitted:
            raise LoanStatusTransitionError(
                f"Transição de {loan.status} para {new_status} não é permitida."
            )

        if new_status is LoanStatus.CANCELLED:
            raise LoanCancellationError("Use LoanService.cancel para cancelar empréstimos.")

        if new_status in {LoanStatus.FINISHED, LoanStatus.COLLECTION} and loan.status not in {
            LoanStatus.ACTIVE,
            LoanStatus.COLLECTION,
        }:
            raise LoanStatusTransitionError("Empréstimo precisa estar ativo ou em cobrança para esta transição.")

        return loan.model_copy(update={"status": new_status})

    @classmethod
    def cancel(
        cls,
        loan: LoanEntity,
        cancellation: LoanCancellationInput,
    ) -> LoanEntity:
        """Cancela empréstimo respeitando prazo de arrependimento."""

        if loan.status in {LoanStatus.CANCELLED, LoanStatus.FINISHED}:
            raise LoanCancellationError("Empréstimo já está finalizado ou cancelado.")

        reference = cancellation.reference_date
        deadline = loan.regret_deadline or (loan.contract_date + timedelta(days=REGRET_PERIOD_DAYS))
        if reference > deadline:
            raise LoanCancellationError(
                "Cancelamento fora do prazo legal de arrependimento (7 dias)."
            )

        return loan.model_copy(update={"status": LoanStatus.CANCELLED})

    @classmethod
    def regulatory_snapshot(
        cls,
        loan: LoanEntity,
        *,
        max_interest_rate: Optional[Decimal],
        iof_fixed_rate: Decimal,
        iof_daily_rate: Decimal,
        reference_date: Optional[date] = None,
    ) -> dict:
        """Gera informações de conformidade regulatória."""

        today = reference_date or date.today()
        deadline = loan.regret_deadline or (loan.contract_date + timedelta(days=REGRET_PERIOD_DAYS))

        usury_ok = True
        if max_interest_rate is not None:
            usury_ok = loan.interest_rate <= max_interest_rate

        snapshot = {
            "cet_compliance": loan.cet_monthly <= (max_interest_rate or loan.cet_monthly if max_interest_rate else loan.cet_monthly),
            "iof_compliance": loan.iof_amount >= MONEY_ZERO,
            "usury_law_compliance": usury_ok,
            "regret_period_valid": today <= deadline,
            "calculations": {
                "iof_rate": iof_fixed_rate.quantize(RATE_QUANTIZER),
                "iof_amount": loan.iof_amount,
                "cet_monthly": loan.cet_monthly,
                "cet_yearly": loan.cet_yearly,
                "max_interest_rate": (max_interest_rate or RATE_ZERO).quantize(RATE_QUANTIZER),
            },
        }
        return snapshot

    @classmethod
    def _validate_interest_rate_limit(cls, data: LoanCreateInput) -> None:
        if data.max_interest_rate is not None and data.interest_rate > data.max_interest_rate:
            raise InterestRateLimitError("Taxa de juros excede o limite configurado para o tenant.")

    @classmethod
    def _build_price_schedule(
        cls,
        *,
        principal: Decimal,
        interest_rate: Decimal,
        installments_count: int,
        first_due_date: date,
        tenant_id: UUID,
    ) -> List[InstallmentPlan]:
        installments: List[InstallmentPlan] = []
        outstanding = principal
        rate = interest_rate
        n = installments_count

        if n <= 0:
            raise LoanDomainError("Quantidade de parcelas deve ser maior que zero.")

        if rate == RATE_ZERO:
            payment = _quantize_money(principal / Decimal(n))
        else:
            factor = (Decimal(1) + rate) ** n
            payment = principal * rate * factor / (factor - Decimal(1))
            payment = _quantize_money(payment)

        current_due = first_due_date
        accumulated_principal = MONEY_ZERO

        for sequence in range(1, n + 1):
            if rate == RATE_ZERO:
                interest = MONEY_ZERO
                principal_component = payment
            else:
                interest = _quantize_money(outstanding * rate)
                principal_component = _quantize_money(payment - interest)

            accumulated_principal += principal_component

            if sequence == n:
                adjustment = principal - accumulated_principal
                if adjustment != MONEY_ZERO:
                    principal_component = _quantize_money(principal_component + adjustment)
                    payment = _quantize_money(principal_component + interest)

            total_amount = _quantize_money(principal_component + interest)

            installments.append(
                InstallmentPlan(
                    sequence=sequence,
                    due_date=current_due,
                    principal_amount=principal_component,
                    interest_amount=interest,
                    total_amount=total_amount,
                )
            )

            outstanding = _quantize_money(outstanding - principal_component)
            current_due = _add_months(first_due_date, sequence)

        return installments

    @classmethod
    def _calculate_iof(
        cls,
        *,
        principal: Decimal,
        installments: Iterable[InstallmentPlan],
        contract_date: date,
        fixed_rate: Decimal,
        daily_rate: Decimal,
    ) -> Decimal:
        total = principal * fixed_rate
        total = _quantize_money(total)

        outstanding = principal
        remaining_days_cap = 365
        previous_date = contract_date

        for item in installments:
            days = max((item.due_date - previous_date).days, 0)
            if remaining_days_cap <= 0:
                break

            effective_days = min(days, remaining_days_cap)
            incremental = outstanding * daily_rate * Decimal(effective_days)
            total += incremental
            total = _quantize_money(total)

            remaining_days_cap -= effective_days
            outstanding = _quantize_money(outstanding - item.principal_amount)
            previous_date = item.due_date

        return _quantize_money(max(total, MONEY_ZERO))

    @classmethod
    def _calculate_cet(
        cls,
        *,
        principal: Decimal,
        installments: Iterable[InstallmentPlan],
        iof_amount: Decimal,
    ) -> Tuple[Decimal, Decimal]:
        net_amount = principal - iof_amount
        if net_amount <= MONEY_ZERO:
            return RATE_ZERO, RATE_ZERO

        cash_flows: List[Decimal] = [net_amount]
        cash_flows.extend(-item.total_amount for item in installments)

        rate = Decimal("0.02")
        tolerance = Decimal("0.000001")
        max_iterations = 100

        for _ in range(max_iterations):
            npv = cls._npv(rate, cash_flows)
            derivative = cls._npv_derivative(rate, cash_flows)
            if derivative == MONEY_ZERO:
                break
            new_rate = rate - npv / derivative
            if abs(new_rate - rate) <= tolerance:
                rate = new_rate
                break
            rate = new_rate

        if rate <= -Decimal("0.9999") or rate.is_nan():
            rate = RATE_ZERO

        rate = max(rate, RATE_ZERO)
        monthly = _quantize_rate(rate)
        yearly = _quantize_rate((Decimal(1) + monthly) ** 12 - Decimal(1))
        return monthly, yearly

    @staticmethod
    def _npv(rate: Decimal, cash_flows: List[Decimal]) -> Decimal:
        total = Decimal(0)
        for period, value in enumerate(cash_flows):
            total += value / (Decimal(1) + rate) ** period
        return total

    @staticmethod
    def _npv_derivative(rate: Decimal, cash_flows: List[Decimal]) -> Decimal:
        total = Decimal(0)
        for period, value in enumerate(cash_flows[1:], start=1):
            total -= period * value / (Decimal(1) + rate) ** (period + 1)
        return total


class InstallmentService:
    """Serviços relacionados a parcelas."""

    LATE_FEE_RATE = DEFAULT_LATE_FEE_RATE
    DAILY_PENALTY_RATE = DEFAULT_DAILY_PENALTY_RATE
    PAYMENT_TOLERANCE = DEFAULT_PAYMENT_TOLERANCE

    @classmethod
    def apply_payment(
        cls,
        installment: InstallmentEntity,
        payment: InstallmentPaymentInput,
        *,
        grace_days: int = 5,
    ) -> InstallmentEntity:
        if payment.amount <= MONEY_ZERO:
            raise InstallmentPaymentError("Valor de pagamento deve ser positivo.")

        updated_fields = {}
        total_due = installment.total_amount + installment.late_fee + installment.interest_penalty
        new_amount_paid = _quantize_money(installment.amount_paid + payment.amount)

        if payment.payment_date > installment.due_date + timedelta(days=grace_days):
            late_fee = installment.total_amount * cls.LATE_FEE_RATE
            days_overdue = (payment.payment_date - installment.due_date).days
            penalty = installment.total_amount * cls.DAILY_PENALTY_RATE * Decimal(days_overdue)
            updated_fields["late_fee"] = _quantize_money(installment.late_fee + late_fee)
            updated_fields["interest_penalty"] = _quantize_money(installment.interest_penalty + penalty)
            total_due = installment.total_amount + updated_fields["late_fee"] + updated_fields["interest_penalty"]

        status = installment.status
        payment_date = installment.payment_date

        if new_amount_paid + cls.PAYMENT_TOLERANCE >= total_due:
            status = InstallmentStatus.PAID
            payment_date = payment.payment_date
            new_amount_paid = _quantize_money(total_due)
        elif new_amount_paid > MONEY_ZERO:
            status = InstallmentStatus.PARTIALLY_PAID
            payment_date = payment.payment_date
        else:
            status = InstallmentStatus.PENDING
            payment_date = None

        updated_fields.update(
            {
                "amount_paid": new_amount_paid,
                "status": status,
                "payment_date": payment_date,
            }
        )

        return installment.model_copy(update=updated_fields)


__all__ = [
    "InstallmentPlan",
    "InstallmentPaymentError",
    "InstallmentPaymentInput",
    "InstallmentService",
    "InterestRateLimitError",
    "LoanCalculationResult",
    "LoanCancellationError",
    "LoanCancellationInput",
    "LoanCreateInput",
    "LoanDomainError",
    "LoanService",
    "LoanStatusTransitionError",
    "LoanStatusUpdateInput",
]
