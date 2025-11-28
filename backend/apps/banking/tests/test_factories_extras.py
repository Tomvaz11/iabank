from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import SimpleTestCase

from backend.apps.banking.tests.factories import (
    CustomerFactory,
    FactoryContext,
    LoanFactory,
    TenantFactory,
    build_batch,
)
from backend.apps.tenancy.models import Tenant


class BankingFactoriesEdgeCasesTest(SimpleTestCase):
    def setUp(self) -> None:
        self.context = FactoryContext.default()

    def test_factory_context_default_is_valid(self) -> None:
        default_ctx = FactoryContext.default()
        self.assertEqual(default_ctx.tenant_slug, "00000000")
        self.assertIsInstance(default_ctx.factory_seed, int)

    def test_construct_instance_requires_factory_context_type(self) -> None:
        with self.assertRaises(TypeError):
            TenantFactory._construct_instance(Tenant, factory_context="invalid")  # type: ignore[arg-type]

    def test_create_uses_construct_instance_and_sets_tenant(self) -> None:
        customer = CustomerFactory.create()
        self.assertEqual(customer.tenant_id, self.context.tenant_uuid)

    def test_normalize_tenant_returns_existing_instance(self) -> None:
        tenant = Tenant(
            id=self.context.tenant_uuid,
            slug="custom",
            display_name="x",
            primary_domain="custom.seed.test",
            pii_policy_version="1.0.0",
        )
        returned = TenantFactory._normalize_tenant(tenant, self.context)
        self.assertIs(returned, tenant)

    def test_normalize_tenant_builds_from_context_when_missing(self) -> None:
        returned = TenantFactory._normalize_tenant(None, self.context)
        self.assertEqual(returned.id, self.context.tenant_uuid)
        self.assertIn(self.context.tenant_slug, returned.primary_domain)

    def test_loan_quote_is_cached_between_calls(self) -> None:
        stub = type(
            "LoanStub",
            (),
            {
                "factory_context": self.context,
                "principal_amount": self.context.deterministic_decimal(
                    "loan-principal",
                    Decimal("5000"),
                    Decimal("15000"),
                ),
                "number_of_installments": 12,
                "contract_date": self.context.reference_date,
                "first_installment_date": self.context.reference_date + timedelta(days=30),
            },
        )()

        first = LoanFactory._quote(stub)
        second = LoanFactory._quote(stub)
        self.assertIs(first, second)
        self.assertTrue(hasattr(stub, "_cached_quote"))

    def test_build_batch_creates_requested_size(self) -> None:
        batch = build_batch(CustomerFactory, size=3, factory_context=self.context)
        self.assertEqual(len(batch), 3)
