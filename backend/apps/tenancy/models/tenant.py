from __future__ import annotations

import uuid

from django.db import models


class Tenant(models.Model):
    class Status(models.TextChoices):
        PILOT = 'pilot', 'Piloto'
        PRODUCTION = 'production', 'Produção'
        DECOMMISSIONED = 'decommissioned', 'Descomissionado'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=32, unique=True)
    display_name = models.CharField(max_length=128)
    primary_domain = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PILOT)
    pii_policy_version = models.CharField(max_length=20)
    default_theme = models.ForeignKey(
        'tenancy.TenantThemeToken',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='default_for_tenants',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self) -> str:  # pragma: no cover - repr utilitário
        return f'Tenant<{self.slug}>'
