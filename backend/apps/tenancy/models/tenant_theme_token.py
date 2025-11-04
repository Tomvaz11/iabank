from __future__ import annotations

import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models

from ..fields import EncryptedJSONField
from ..managers import TenantManager, use_tenant
from .tenant import Tenant


SEMVER_PATTERN = re.compile(r'^\d+\.\d+\.\d+$')


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

    def _validate_version(self, errors: dict[str, list[str]]) -> None:
        if self.version and not SEMVER_PATTERN.match(self.version):
            errors.setdefault('version', []).append('Versão deve seguir o formato SemVer (ex.: 1.2.3).')

    def _validate_wcag_presence_and_type(self, errors: dict[str, list[str]]) -> dict[str, object] | None:
        if self.category != self.Category.FOUNDATION and not self.wcag_report:
            errors.setdefault('wcag_report', []).append(
                'Tokens semânticos e de componentes exigem relatório WCAG associado.',
            )
        if self.wcag_report and not isinstance(self.wcag_report, dict):
            errors.setdefault('wcag_report', []).append('Relatório WCAG deve ser um objeto JSON.')
        return self.wcag_report if isinstance(self.wcag_report, dict) else None

    def _validate_default_wcag(self, wcag_data: dict[str, object] | None, errors: dict[str, list[str]]) -> None:
        if self.category == self.Category.FOUNDATION or not self.is_default:
            return
        if not wcag_data:
            errors.setdefault('wcag_report', []).append(
                'Auditoria WCAG válida é obrigatória para marcar tokens padrão.',
            )
            return

        status_value = str(wcag_data.get('status', '')).lower()
        if status_value != 'pass':
            errors.setdefault('wcag_report', []).append(
                'Somente tokens com status WCAG "pass" podem ser definidos como padrão.',
            )

        violations = wcag_data.get('violations', [])
        if violations is None:
            wcag_data['violations'] = []
        elif isinstance(violations, list):
            if len(violations) > 0:
                errors.setdefault('wcag_report', []).append(
                    'Resolva violações WCAG antes de marcar o token como padrão.',
                )
        else:
            errors.setdefault('wcag_report', []).append('Campo "violations" deve ser uma lista.')

        if status_value == 'pass':
            self.wcag_report = {
                **wcag_data,
                'status': 'pass',
                'violations': wcag_data.get('violations', []),
            }

    def clean(self) -> None:  # pragma: no cover - executado via save/full_clean
        errors: dict[str, list[str]] = {}

        self._validate_version(errors)
        wcag_data = self._validate_wcag_presence_and_type(errors)
        self._validate_default_wcag(wcag_data, errors)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        tenant_id = self.tenant_id or getattr(self.tenant, 'id', None)
        if tenant_id is not None:
            with use_tenant(tenant_id):
                self.full_clean()
        else:
            self.full_clean()
        return super().save(*args, **kwargs)
