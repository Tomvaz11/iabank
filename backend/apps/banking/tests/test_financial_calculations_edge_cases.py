from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from backend.apps.banking.services.financial_calculations import (
    LoanInput,
    calculate_iof,
    generate_installments,
)


class FinancialCalculationsEdgeCasesTest(SimpleTestCase):
    def test_calculate_iof_requires_positive_installments(self) -> None:
        request = LoanInput(
            principal_amount=Decimal("1000"),
            annual_rate_pct=Decimal("10"),
            number_of_installments=0,
            contract_date=date(2025, 1, 1),
            first_installment_date=date(2025, 2, 1),
        )
        with self.assertRaises(ValueError):
            calculate_iof(request)

    def test_generate_installments_requires_positive_installments(self) -> None:
        request = LoanInput(
            principal_amount=Decimal("1000"),
            annual_rate_pct=Decimal("10"),
            number_of_installments=0,
            contract_date=date(2025, 1, 1),
            first_installment_date=date(2025, 2, 1),
        )
        with self.assertRaises(ValueError):
            generate_installments(request)

    def test_generate_installments_handles_zero_rate(self) -> None:
        request = LoanInput(
            principal_amount=Decimal("1000"),
            annual_rate_pct=Decimal("0"),
            number_of_installments=3,
            contract_date=date(2025, 1, 1),
            first_installment_date=date(2025, 2, 1),
        )
        installments = generate_installments(request)

        self.assertEqual(len(installments), 3)
        total_amount = request.principal_amount + Decimal("10.46")  # IOF with 3 parcelas
        expected_payment = (total_amount / Decimal("3")).quantize(Decimal("0.01"))
        for installment in installments:
            self.assertEqual(installment.amount, expected_payment)
