from __future__ import annotations

import uuid

from django.db import models

from backend.apps.foundation.models.feature_template_registration import FeatureTemplateRegistration


class FeatureTemplateMetric(models.Model):
    class MetricCode(models.TextChoices):
        SC_001 = 'SC-001', 'SC-001'
        SC_002 = 'SC-002', 'SC-002'
        SC_003 = 'SC-003', 'SC-003'
        SC_004 = 'SC-004', 'SC-004'
        SC_005 = 'SC-005', 'SC-005'

    class Source(models.TextChoices):
        CI = 'ci', 'CI'
        CHROMATIC = 'chromatic', 'Chromatic'
        LIGHTHOUSE = 'lighthouse', 'Lighthouse'
        MANUAL = 'manual', 'Manual'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='success_metrics',
    )
    registration = models.ForeignKey(
        FeatureTemplateRegistration,
        on_delete=models.CASCADE,
        related_name='metrics',
    )
    metric_code = models.CharField(max_length=6, choices=MetricCode.choices)
    value = models.DecimalField(max_digits=9, decimal_places=3)
    collected_at = models.DateTimeField()
    source = models.CharField(max_length=16, choices=Source.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feature_template_metrics'
        ordering = ['-collected_at', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'registration', 'metric_code', 'collected_at'],
                name='unique_metric_collection_per_registration',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'metric_code', '-collected_at'], name='idx_metric_tenant_code'),
        ]

    def __str__(self) -> str:  # pragma: no cover - representação auxiliar
        return f'FeatureTemplateMetric<{self.metric_code} @ {self.tenant_id}>'
