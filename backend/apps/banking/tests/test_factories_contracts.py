from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase

from backend.apps.banking.serializers import (
    AccountCategorySerializer,
    AddressSerializer,
    BankAccountSerializer,
    ContractSerializer,
    ConsultantSerializer,
    CreditLimitSerializer,
    CustomerSerializer,
    FinancialTransactionSerializer,
    InstallmentSerializer,
    LoanSerializer,
    SupplierSerializer,
)
from backend.apps.banking.services.financial_calculations import LoanInput, calculate_cet
from backend.apps.banking.tests.factories import (
    AccountCategoryFactory,
    AddressFactory,
    BankAccountFactory,
    ConsultantFactory,
    ContractFactory,
    CreditLimitFactory,
    CustomerFactory,
    FactoryContext,
    FinancialTransactionFactory,
    InstallmentFactory,
    LoanFactory,
    SupplierFactory,
)


def _payload(serializer_cls, instance) -> dict:
    serialized = serializer_cls(instance=instance).data
    readonly = set(getattr(serializer_cls.Meta, "read_only_fields", []))
    return {key: value for key, value in serialized.items() if key not in readonly}


class BankingFactoryContractTest(SimpleTestCase):
    def setUp(self) -> None:
        self.context = FactoryContext(
            tenant_id="11111111-1111-1111-1111-111111111111",
            environment="staging",
            manifest_version="1.0.0",
            salt_version="2025-q1",
        )

    def test_factory_payloads_validate_against_serializers(self) -> None:
        customer = CustomerFactory.build(factory_context=self.context)
        consultant = ConsultantFactory.build(factory_context=self.context)
        address = AddressFactory.build(factory_context=self.context, customer=customer)
        account_category = AccountCategoryFactory.build(factory_context=self.context)
        bank_account = BankAccountFactory.build(factory_context=self.context, customer=customer)
        supplier = SupplierFactory.build(factory_context=self.context)
        loan = LoanFactory.build(factory_context=self.context, customer=customer, consultant=consultant)
        installment = InstallmentFactory.build(
            factory_context=self.context,
            loan=loan,
            installment_number=1,
        )
        transaction = FinancialTransactionFactory.build(
            factory_context=self.context,
            bank_account=bank_account,
            category=account_category,
            supplier=supplier,
            installment=installment,
        )
        credit_limit = CreditLimitFactory.build(factory_context=self.context, bank_account=bank_account)
        contract = ContractFactory.build(
            factory_context=self.context,
            bank_account=bank_account,
            customer=customer,
        )

        cases = [
            (CustomerSerializer, customer),
            (AddressSerializer, address),
            (ConsultantSerializer, consultant),
            (AccountCategorySerializer, account_category),
            (BankAccountSerializer, bank_account),
            (SupplierSerializer, supplier),
            (LoanSerializer, loan),
            (InstallmentSerializer, installment),
            (FinancialTransactionSerializer, transaction),
            (CreditLimitSerializer, credit_limit),
            (ContractSerializer, contract),
        ]

        for serializer_cls, instance in cases:
            payload = _payload(serializer_cls, instance)
            serializer = serializer_cls(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_financial_calculator_contract_fixture_is_aligned(self) -> None:
        request = LoanInput(
            principal_amount=Decimal("10000"),
            annual_rate_pct=Decimal("12.5"),
            number_of_installments=12,
            contract_date=date(2025, 1, 10),
            first_installment_date=date(2025, 2, 10),
        )
        breakdown = calculate_cet(request)

        pact_path = Path(__file__).resolve().parents[4] / "contracts" / "pacts" / "financial-calculator.json"
        with pact_path.open() as fp:
            pact = json.load(fp)

        expected = pact["interactions"][0]["response"]["body"]

        self.assertAlmostEqual(float(breakdown.cet_annual_rate), float(expected["cet_annual_rate"]), places=2)
        self.assertAlmostEqual(float(breakdown.cet_monthly_rate), float(expected["cet_monthly_rate"]), places=2)
        self.assertAlmostEqual(float(breakdown.iof_amount), float(expected["iof_amount"]), places=2)
        self.assertEqual(len(breakdown.installments), len(expected["installments"]))
        self.assertAlmostEqual(
            float(breakdown.installments[0].amount),
            float(expected["installments"][0]["amount"]),
            places=2,
        )
