from importlib import import_module
from pathlib import Path

from django.test import SimpleTestCase


class MigrationRlsTest(SimpleTestCase):
    def test_migration_enables_pgcrypto_and_executes_sql_policies(self) -> None:
        migration = import_module("backend.apps.tenancy.migrations.0025_enable_rls_frontend")
        operations = migration.Migration.operations

        enable_extension = [
            op for op in operations if getattr(op, "sql", "").lower().startswith("create extension")
        ]
        self.assertTrue(
            enable_extension,
            "A migração deve habilitar a extensão pgcrypto.",
        )

        sql_operations = [
            op
            for op in operations
            if getattr(op, "sql", "").strip().startswith("SELECT iabank.apply_tenant_rls_policies()")
        ]
        self.assertTrue(
            sql_operations,
            "A migração deve aplicar as políticas RLS através do SQL dedicado.",
        )

        sql_path = Path("backend/apps/tenancy/sql/rls_policies.sql")
        self.assertTrue(sql_path.exists(), "O arquivo com as políticas RLS deve existir.")
