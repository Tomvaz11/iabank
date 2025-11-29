from importlib import import_module

from django.apps import apps
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from backend.apps.tenancy.managers import TenantManager, use_tenant
from backend.apps.tenancy.models import Tenant
from backend.apps.banking.models import Address, Customer


class BankingModelsMigrationTest(SimpleTestCase):
    def test_app_is_registered(self) -> None:
        config = apps.get_app_config("banking")
        self.assertEqual(config.name, "backend.apps.banking")

    def test_initial_migration_creates_expected_models(self) -> None:
        migration = import_module("backend.apps.banking.migrations.0001_initial")
        create_models = {
            op.name
            for op in migration.Migration.operations
            if getattr(op, "name", "").startswith(("Customer", "Address", "Consultant", "BankAccount"))
            or getattr(op, "name", "").startswith(
                ("AccountCategory", "Supplier", "Loan", "Installment", "FinancialTransaction", "CreditLimit", "Contract")
            )
        }

        expected = {
            "Customer",
            "Address",
            "Consultant",
            "BankAccount",
            "AccountCategory",
            "Supplier",
            "Loan",
            "Installment",
            "FinancialTransaction",
            "CreditLimit",
            "Contract",
        }
        self.assertTrue(
            expected.issubset(create_models),
            f"A migração inicial deve criar todos os modelos esperados. Encontrado: {sorted(create_models)}",
        )

    def test_models_use_tenant_manager(self) -> None:
        from backend.apps.banking import models as banking_models

        managed_models = [
            banking_models.Customer,
            banking_models.Address,
            banking_models.Consultant,
            banking_models.BankAccount,
            banking_models.AccountCategory,
            banking_models.Supplier,
            banking_models.Loan,
            banking_models.Installment,
            banking_models.FinancialTransaction,
            banking_models.CreditLimit,
            banking_models.Contract,
        ]

        for model in managed_models:
            self.assertIsInstance(
                model.objects,
                TenantManager,
                f"O modelo {model.__name__} deve usar TenantManager para aplicar RLS por tenant.",
            )


class AddressValidationTest(TestCase):
    databases = {"default"}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug="tenant-alfa",
            display_name="Tenant Alfa",
            primary_domain="alfa.iabank.test",
            status="pilot",
            pii_policy_version="1.0.0",
        )
        self.other_tenant = Tenant.objects.create(
            slug="tenant-beta",
            display_name="Tenant Beta",
            primary_domain="beta.iabank.test",
            status="pilot",
            pii_policy_version="1.0.0",
        )
        with use_tenant(self.tenant.id):
            self.customer = Customer.objects.create(
                tenant_id=self.tenant.id,
                name="Alice",
                document_number="12345678900",
                status=Customer.Status.ACTIVE,
            )

    def test_rejects_mismatched_tenant(self) -> None:
        address = Address(
            tenant=self.other_tenant,
            customer=self.customer,
            zip_code="01310-000",
            street="Av. Paulista",
            number="1000",
            neighborhood="Bela Vista",
            city="Sao Paulo",
            state="SP",
        )

        with self.assertRaises(ValidationError):
            address.clean()

    def test_rejects_invalid_state_length(self) -> None:
        with use_tenant(self.tenant.id):
            address = Address(
                tenant=self.tenant,
                customer=self.customer,
                zip_code="01310-000",
                street="Av. Paulista",
                number="1000",
                neighborhood="Bela Vista",
                city="Sao Paulo",
                state="S",
            )

        with self.assertRaises(ValidationError):
            address.clean()
