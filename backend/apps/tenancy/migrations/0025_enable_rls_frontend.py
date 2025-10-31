from __future__ import annotations

from pathlib import Path

from django.db import migrations

SQL_DIR = Path(__file__).resolve().parent.parent / 'sql'
RLS_SQL_FILE = SQL_DIR / 'rls_policies.sql'

if not RLS_SQL_FILE.exists():
    raise RuntimeError('Arquivo de políticas RLS não encontrado. Execute T020 antes da migração.')

RLS_SQL = RLS_SQL_FILE.read_text(encoding='utf-8')


class Migration(migrations.Migration):
    dependencies = [
        ('tenancy', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS pgcrypto;',
            reverse_sql='DROP EXTENSION IF EXISTS pgcrypto;',
        ),
        migrations.RunSQL(
            sql=RLS_SQL,
            reverse_sql="""
                DROP FUNCTION IF EXISTS iabank.apply_tenant_rls_policies();
                DROP FUNCTION IF EXISTS iabank.revert_tenant_rls_policies();
            """,
        ),
        migrations.RunSQL(
            sql='SELECT iabank.apply_tenant_rls_policies();',
            reverse_sql='SELECT iabank.revert_tenant_rls_policies();',
        ),
    ]
