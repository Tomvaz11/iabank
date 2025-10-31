from django.conf import settings
from django.db import migrations

import backend.apps.tenancy.fields


def _pgcrypto_key() -> str:
    return getattr(settings, 'PGCRYPTO_KEY', 'dev-only-pgcrypto-key')


def _encrypt_json_payload(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'postgresql':
        return

    key = _pgcrypto_key()
    schema_editor.execute(
        """
        ALTER TABLE tenant_theme_tokens
        ALTER COLUMN json_payload TYPE bytea
        USING pgp_sym_encrypt(json_payload::text, %s)
        """,
        [key],
    )


def _decrypt_json_payload(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'postgresql':
        return

    key = _pgcrypto_key()
    schema_editor.execute(
        """
        ALTER TABLE tenant_theme_tokens
        ALTER COLUMN json_payload TYPE jsonb
        USING pgp_sym_decrypt(json_payload::bytea, %s)::jsonb
        """,
        [key],
    )


class Migration(migrations.Migration):
    dependencies = [
        ('tenancy', '0025_enable_rls_frontend'),
    ]

    operations = [
        migrations.RunPython(_encrypt_json_payload, _decrypt_json_payload),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='tenantthemetoken',
                    name='json_payload',
                    field=backend.apps.tenancy.fields.EncryptedJSONField(),
                ),
            ],
        ),
    ]
