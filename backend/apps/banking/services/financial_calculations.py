from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List


@dataclass(slots=True)
class LoanInput:
    principal_amount: Decimal
    annual_rate_pct: Decimal
    number_of_installments: int
    contract_date: date
    first_installment_date: date


@dataclass(slots=True)
class InstallmentQuote:
    number: int
    due_date: date
    amount: Decimal


@dataclass(slots=True)
class CETBreakdown:
    cet_annual_rate: Decimal
    cet_monthly_rate: Decimal
    iof_amount: Decimal
    installments: List[InstallmentQuote]


def _monthly_rate_pct(request: LoanInput) -> Decimal:
    return (request.annual_rate_pct / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _add_months(start: date, offset: int) -> date:
    month = start.month - 1 + offset
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_iof(request: LoanInput) -> Decimal:
    if request.number_of_installments < 1:
        raise ValueError("number_of_installments deve ser positivo para calcular IOF.")

    base_rate = Decimal("0.0104")  # 1,04%
    dynamic_component = Decimal(request.number_of_installments) * Decimal("0.00002")
    rate = base_rate + dynamic_component
    return (request.principal_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_installments(request: LoanInput) -> List[InstallmentQuote]:
    if request.number_of_installments < 1:
        raise ValueError("number_of_installments deve ser pelo menos 1.")

    monthly_rate_pct = _monthly_rate_pct(request)
    iof_amount = calculate_iof(request)
    total_amount = request.principal_amount + iof_amount

    rate_fraction = (monthly_rate_pct / Decimal("100")).quantize(Decimal("0.0001"))
    if rate_fraction == 0:
        payment = (total_amount / request.number_of_installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        denominator = Decimal(1) - (Decimal(1) + rate_fraction) ** Decimal(-request.number_of_installments)
        payment = (total_amount * rate_fraction / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    installments: list[InstallmentQuote] = []
    for idx in range(request.number_of_installments):
        due_date = _add_months(request.first_installment_date, idx)
        installments.append(InstallmentQuote(number=idx + 1, due_date=due_date, amount=payment))
    return installments


def calculate_cet(request: LoanInput) -> CETBreakdown:
    monthly_rate_pct = _monthly_rate_pct(request)
    rate_fraction = (monthly_rate_pct / Decimal("100")).quantize(Decimal("0.0001"))
    annual_rate = (((Decimal(1) + rate_fraction) ** 12) - Decimal(1)) * Decimal("100")

    iof_amount = calculate_iof(request)
    installments = generate_installments(request)

    return CETBreakdown(
        cet_annual_rate=annual_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        cet_monthly_rate=monthly_rate_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        iof_amount=iof_amount,
        installments=installments,
    )
