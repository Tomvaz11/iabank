from importlib import import_module
from pathlib import Path

from django.test import SimpleTestCase

from backend.apps.tenancy.managers import TenantManager


class SeedModelsMigrationTest(SimpleTestCase):
    def test_seed_migration_creates_expected_models(self) -> None:
        migration = import_module("backend.apps.tenancy.migrations.0028_seed_models")
        created = {getattr(op, "name", "") for op in migration.Migration.operations if getattr(op, "name", "")}

        expected = {
            "SeedProfile",
            "SeedRun",
            "SeedBatch",
            "SeedCheckpoint",
            "SeedQueue",
            "SeedDataset",
            "SeedIdempotency",
            "SeedRBAC",
            "BudgetRateLimit",
            "EvidenceWORM",
        }
        self.assertTrue(
            expected.issubset(created),
            f"A migração deve criar todas as tabelas de seeds e auditoria. Encontrado: {sorted(created)}",
        )

    def test_rls_policies_cover_seed_tables(self) -> None:
        sql_path = Path("backend/apps/tenancy/sql/rls_policies.sql")
        self.assertTrue(sql_path.exists(), "O arquivo de políticas RLS deve existir.")

        sql = sql_path.read_text(encoding="utf-8")
        required_tables = [
            "tenancy_seed_profile",
            "tenancy_seed_run",
            "tenancy_seed_batch",
            "tenancy_seed_checkpoint",
            "tenancy_seed_queue",
            "tenancy_seed_dataset",
            "tenancy_seed_idempotency",
            "tenancy_seed_rbac",
            "tenancy_seed_budget_ratelimit",
            "tenancy_seed_evidence",
        ]

        missing = [table for table in required_tables if table not in sql]
        self.assertFalse(
            missing,
            f"As políticas RLS devem contemplar todas as novas tabelas. Ausentes: {missing}",
        )

    def test_seed_models_use_tenant_manager(self) -> None:
        from backend.apps.tenancy import models as tenancy_models

        managed_models = [
            tenancy_models.SeedProfile,
            tenancy_models.SeedRun,
            tenancy_models.SeedBatch,
            tenancy_models.SeedCheckpoint,
            tenancy_models.SeedQueue,
            tenancy_models.SeedDataset,
            tenancy_models.SeedIdempotency,
            tenancy_models.SeedRBAC,
            tenancy_models.BudgetRateLimit,
            tenancy_models.EvidenceWORM,
        ]

        for model in managed_models:
            self.assertIsInstance(
                model.objects,
                TenantManager,
                f"O modelo {model.__name__} deve usar TenantManager para reforçar RLS.",
            )
