"""
Django management command to enable Row-Level Security on all tenant tables.
This ensures complete data isolation at the PostgreSQL level.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Enable Row-Level Security on all tables with tenant relationships"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force enable RLS even if already enabled",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write(
            self.style.SUCCESS(
                "Enabling Row-Level Security for IABANK multi-tenant architecture"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        try:
            with connection.cursor() as cursor:
                if not dry_run:
                    # Call the PostgreSQL function to enable RLS
                    cursor.execute("SELECT enable_rls_for_tenant_tables();")

                    # Get the notices from PostgreSQL
                    for notice in connection.notices:
                        if "RLS enabled for table" in notice:
                            table_name = notice.split(": ")[-1]
                            self.stdout.write(f"  RLS enabled: {table_name}")

                    self.stdout.write("")
                    self.stdout.write(
                        self.style.SUCCESS("Row-Level Security enabled successfully!")
                    )
                else:
                    # In dry-run, just show what tables would be affected
                    cursor.execute(
                        """
                        SELECT DISTINCT t.table_name
                        FROM information_schema.tables t
                        JOIN information_schema.columns c ON t.table_name = c.table_name
                        WHERE t.table_schema = 'public'
                          AND t.table_type = 'BASE TABLE'
                          AND t.table_name != 'core_tenant'
                          AND t.table_name NOT LIKE 'django_%'
                          AND t.table_name NOT LIKE 'auth_%'
                          AND (c.column_name = 'tenant_id' OR c.column_name = 'tenant')
                        ORDER BY t.table_name;
                    """
                    )

                    tables = cursor.fetchall()
                    if tables:
                        self.stdout.write("Tables that would have RLS enabled:")
                        for table in tables:
                            self.stdout.write(f"  📋 {table[0]}")
                    else:
                        self.stdout.write("No tenant tables found to enable RLS on.")

                # Show usage instructions
                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS("🔧 Usage in Django:"))
                self.stdout.write("  from django.db import connection")
                self.stdout.write("  with connection.cursor() as cursor:")
                self.stdout.write(
                    '      cursor.execute("SELECT set_tenant_context(%s)", [tenant_id])'
                )
                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS("🔧 Usage in middleware:"))
                self.stdout.write(
                    "  Add call to set_tenant_context() in TenantMiddleware"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error enabling RLS: {e}"))
            raise
