from __future__ import annotations

import decimal
import uuid

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('foundation', '0002_frontend_foundation_backfill'),
    ]

    operations = [
        migrations.CreateModel(
            name='DesignSystemStory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('component_id', models.CharField(max_length=128)),
                ('story_id', models.CharField(max_length=128)),
                ('tags', models.JSONField(blank=True, default=list)),
                (
                    'coverage_percent',
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(decimal.Decimal('0')),
                            django.core.validators.MaxValueValidator(decimal.Decimal('100')),
                        ],
                    ),
                ),
                (
                    'axe_status',
                    models.CharField(
                        choices=[('pass', 'Pass'), ('fail', 'Fail'), ('warn', 'Warn')],
                        max_length=8,
                    ),
                ),
                ('axe_results', models.JSONField(blank=True, default=dict)),
                ('chromatic_build', models.CharField(max_length=128)),
                ('storybook_url', models.URLField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'tenant',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name='design_system_stories',
                        to='tenancy.tenant',
                    ),
                ),
                (
                    'theme_token',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='design_system_stories',
                        to='tenancy.tenantthemetoken',
                    ),
                ),
            ],
            options={
                'db_table': 'design_system_stories',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='designsystemstory',
            constraint=models.UniqueConstraint(
                fields=('component_id', 'story_id', 'tenant', 'chromatic_build'),
                name='unique_story_per_build_tenant',
            ),
        ),
    ]
