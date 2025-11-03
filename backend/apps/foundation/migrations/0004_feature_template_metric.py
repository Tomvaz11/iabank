from __future__ import annotations

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('tenancy', '0026_encrypt_theme_payload'),
        ('foundation', '0003_design_system_story'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureTemplateMetric',
            fields=[
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    'metric_code',
                    models.CharField(
                        choices=[
                            ('SC-001', 'SC-001'),
                            ('SC-002', 'SC-002'),
                            ('SC-003', 'SC-003'),
                            ('SC-004', 'SC-004'),
                            ('SC-005', 'SC-005'),
                        ],
                        max_length=6,
                    ),
                ),
                ('value', models.DecimalField(decimal_places=3, max_digits=9)),
                ('collected_at', models.DateTimeField()),
                (
                    'source',
                    models.CharField(
                        choices=[
                            ('ci', 'CI'),
                            ('chromatic', 'Chromatic'),
                            ('lighthouse', 'Lighthouse'),
                            ('manual', 'Manual'),
                        ],
                        max_length=16,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'registration',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='metrics',
                        to='foundation.featuretemplateregistration',
                    ),
                ),
                (
                    'tenant',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='success_metrics',
                        to='tenancy.tenant',
                    ),
                ),
            ],
            options={
                'db_table': 'feature_template_metrics',
                'ordering': ['-collected_at', '-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='featuretemplatemetric',
            constraint=models.UniqueConstraint(
                fields=('tenant', 'registration', 'metric_code', 'collected_at'),
                name='unique_metric_collection_per_registration',
            ),
        ),
        migrations.AddIndex(
            model_name='featuretemplatemetric',
            index=models.Index(
                fields=('tenant', 'metric_code', '-collected_at'),
                name='idx_metric_tenant_code',
            ),
        ),
    ]
