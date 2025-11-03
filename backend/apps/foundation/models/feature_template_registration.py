from __future__ import annotations

import uuid
from typing import Dict

from django.db import models

from backend.apps.foundation.managers import FeatureTemplateRegistrationManager


class FeatureTemplateRegistration(models.Model):
    class Slice(models.TextChoices):
        APP = 'app', 'App'
        PAGES = 'pages', 'Pages'
        FEATURES = 'features', 'Features'
        ENTITIES = 'entities', 'Entities'
        SHARED = 'shared', 'Shared'

    class Status(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        LINTED = 'linted', 'Linted'
        TESTED = 'tested', 'Tested'
        PUBLISHED = 'published', 'Published'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.CASCADE,
        related_name='feature_template_registrations',
    )
    feature_slug = models.CharField(max_length=64)
    slice = models.CharField(max_length=16, choices=Slice.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.INITIATED,
    )
    scaffold_manifest = models.JSONField()
    lint_commit_hash = models.CharField(max_length=40)
    sc_references = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.UUIDField()
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FeatureTemplateRegistrationManager()

    class Meta:
        db_table = 'feature_template_registrations'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'feature_slug'],
                name='unique_feature_template_per_tenant',
            ),
            models.UniqueConstraint(
                fields=['tenant', 'idempotency_key'],
                name='unique_feature_template_idempotency_per_tenant',
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - representação auxiliar
        return f'FeatureTemplateRegistration<{self.tenant_id}:{self.feature_slug}>'

    @classmethod
    def slice_order(cls) -> Dict[str, int]:
        return {
            cls.Slice.APP: 0,
            cls.Slice.PAGES: 1,
            cls.Slice.FEATURES: 2,
            cls.Slice.ENTITIES: 3,
            cls.Slice.SHARED: 4,
        }
