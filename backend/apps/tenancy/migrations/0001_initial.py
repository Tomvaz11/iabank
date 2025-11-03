from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('slug', models.SlugField(max_length=32, unique=True)),
                ('display_name', models.CharField(max_length=128)),
                ('primary_domain', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(choices=[('pilot', 'Piloto'), ('production', 'Produção'), ('decommissioned', 'Descomissionado')], default='pilot', max_length=32)),
                ('pii_policy_version', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'tenants',
            },
        ),
        migrations.CreateModel(
            name='TenantThemeToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version', models.CharField(max_length=32)),
                ('category', models.CharField(choices=[('foundation', 'Fundacional'), ('semantic', 'Semântico'), ('component', 'Componente')], max_length=16)),
                ('json_payload', models.JSONField(default=dict)),
                ('wcag_report', models.JSONField(blank=True, null=True)),
                ('chromatic_snapshot_id', models.CharField(blank=True, max_length=128, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='theme_tokens', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'tenant_theme_tokens',
                'ordering': ['-created_at'],
                'unique_together': {('tenant', 'version', 'category')},
            },
        ),
        migrations.AddField(
            model_name='tenant',
            name='default_theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_for_tenants', to='tenancy.tenantthemetoken'),
        ),
    ]
