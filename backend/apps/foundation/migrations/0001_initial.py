from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('tenancy', '0026_encrypt_theme_payload'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureTemplateRegistration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('feature_slug', models.CharField(max_length=64)),
                ('slice', models.CharField(choices=[('app', 'App'), ('pages', 'Pages'), ('features', 'Features'), ('entities', 'Entities'), ('shared', 'Shared')], max_length=16)),
                ('status', models.CharField(choices=[('initiated', 'Initiated'), ('linted', 'Linted'), ('tested', 'Tested'), ('published', 'Published')], default='initiated', max_length=16)),
                ('scaffold_manifest', models.JSONField()),
                ('lint_commit_hash', models.CharField(max_length=40)),
                ('sc_references', models.JSONField(blank=True, default=list)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_by', models.UUIDField()),
                ('duration_ms', models.PositiveIntegerField(blank=True, null=True)),
                ('idempotency_key', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='feature_template_registrations', to='tenancy.tenant')),
            ],
            options={
                'db_table': 'feature_template_registrations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='featuretemplateregistration',
            constraint=models.UniqueConstraint(fields=('tenant', 'feature_slug'), name='unique_feature_template_per_tenant'),
        ),
        migrations.AddConstraint(
            model_name='featuretemplateregistration',
            constraint=models.UniqueConstraint(fields=('tenant', 'idempotency_key'), name='unique_feature_template_idempotency_per_tenant'),
        ),
    ]
