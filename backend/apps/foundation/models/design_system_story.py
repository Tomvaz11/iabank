from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class DesignSystemStory(models.Model):
    class AxeStatus(models.TextChoices):
        PASS = 'pass', 'Pass'
        FAIL = 'fail', 'Fail'
        WARN = 'warn', 'Warn'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='design_system_stories',
    )
    theme_token = models.ForeignKey(
        'tenancy.TenantThemeToken',
        on_delete=models.CASCADE,
        related_name='design_system_stories',
    )
    component_id = models.CharField(max_length=128)
    story_id = models.CharField(max_length=128)
    tags = models.JSONField(default=list, blank=True)
    coverage_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
    )
    axe_status = models.CharField(max_length=8, choices=AxeStatus.choices)
    axe_results = models.JSONField(default=dict, blank=True)
    chromatic_build = models.CharField(max_length=128)
    storybook_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'design_system_stories'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['component_id', 'story_id', 'tenant', 'chromatic_build'],
                name='unique_story_per_build_tenant',
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - representação auxiliar
        return f'DesignSystemStory<{self.component_id}:{self.story_id}>'
