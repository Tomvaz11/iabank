from django.db import migrations

import backend.apps.tenancy.fields


class Migration(migrations.Migration):
    dependencies = [
        ('tenancy', '0025_enable_rls_frontend'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenantthemetoken',
            name='json_payload',
            field=backend.apps.tenancy.fields.EncryptedJSONField(),
        ),
    ]
