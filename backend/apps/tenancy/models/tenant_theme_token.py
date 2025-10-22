from __future__ import annotations

import uuid

from django.db import models

from ..fields import EncryptedJSONField
from ..managers import TenantManager
from .tenant import Tenant


class TenantThemeToken(models.Model):
    class Category(models.TextChoices):
        FOUNDATION = 'foundation', 'Fundacional'
        SEMANTIC = 'semantic', 'Semântico'
        COMPONENT = 'component', 'Componente'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='theme_tokens')
    version = models.CharField(max_length=32)
    category = models.CharField(max_length=16, choices=Category.choices)
    json_payload = EncryptedJSONField()
    wcag_report = models.JSONField(null=True, blank=True)
    chromatic_snapshot_id = models.CharField(max_length=128, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        db_table = 'tenant_theme_tokens'
        unique_together = ('tenant', 'version', 'category')
        ordering = ['-created_at']

    def __str__(self) -> str:  # pragma: no cover - repr utilitário
        return f'TenantThemeToken<{self.tenant_id}:{self.version}>'
