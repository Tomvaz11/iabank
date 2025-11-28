from __future__ import annotations

from django.test import SimpleTestCase

from backend.apps.banking.tests.factories import (
    AddressFactory,
    BankAccountFactory,
    CustomerFactory,
    FactoryContext,
)


class BankingFactoriesPIITest(SimpleTestCase):
    def setUp(self) -> None:
        self.context = FactoryContext(
            tenant_id="11111111-1111-1111-1111-111111111111",
            environment="staging",
            manifest_version="1.0.0",
            salt_version="2025-q1",
        )

    def test_customer_factory_is_deterministic_and_masks_pii(self) -> None:
        customer_a = CustomerFactory.build(factory_context=self.context)
        customer_b = CustomerFactory.build(factory_context=self.context)

        expected_document = self.context.masked_digits("customer-document", length=11)
        expected_email = self.context.masked_email("customer", suffix="0")

        self.assertEqual(customer_a.document_number, expected_document)
        self.assertEqual(customer_b.document_number, expected_document)
        self.assertEqual(customer_a.email, expected_email)
        self.assertEqual(customer_a.phone, self.context.masked_digits("customer-phone", length=11))

        raw_document = self.context.deterministic_digits("customer-document", length=11)
        self.assertNotEqual(customer_a.document_number, raw_document)

        alt_context = self.context.with_overrides(salt_version="2025-q2")
        customer_c = CustomerFactory.build(factory_context=alt_context)
        self.assertNotEqual(customer_a.document_number, customer_c.document_number)

    def test_related_factories_share_tenant_and_mask_sensitive_fields(self) -> None:
        customer = CustomerFactory.build(factory_context=self.context)
        address = AddressFactory.build(factory_context=self.context, customer=customer)
        bank_account = BankAccountFactory.build(factory_context=self.context, customer=customer)

        self.assertEqual(address.customer.tenant_id, address.tenant_id)
        self.assertEqual(bank_account.customer.tenant_id, bank_account.tenant_id)

        self.assertEqual(
            bank_account.agency,
            self.context.masked_digits("bank-agency", length=10),
        )
        self.assertEqual(
            bank_account.account_number,
            self.context.masked_digits("bank-account-number", length=20),
        )

        other_context = self.context.with_overrides(tenant_id="22222222-2222-2222-2222-222222222222")
        other_account = BankAccountFactory.build(factory_context=other_context)
        self.assertNotEqual(bank_account.agency, other_account.agency)
