from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from rest_framework import serializers

from backend.apps.tenancy.models import TenantThemeToken


class TenantThemeSerializer(serializers.Serializer):
    tenantId = serializers.UUIDField(format='hex_verbose')
    version = serializers.RegexField(regex=r'^\d+\.\d+\.\d+$')
    generatedAt = serializers.DateTimeField()
    categories = serializers.DictField(child=serializers.DictField(child=serializers.JSONField()))
    wcagReport = serializers.DictField(child=serializers.DictField(child=serializers.JSONField()), required=False)

    def to_representation(self, instance: dict) -> dict:
        tenant = instance['tenant']
        tokens: Iterable[TenantThemeToken] = instance['tokens']

        categories: dict[str, dict[str, str]] = {}
        wcag_report: dict[str, dict[str, object]] = defaultdict(dict)

        version: str | None = None
        generated_at = None

        for token in tokens:
            if version is None:
                version = token.version
            categories[token.category] = dict(token.json_payload or {})
            if token.wcag_report:
                wcag_report[token.category] = dict(token.wcag_report)
            if generated_at is None or token.updated_at > generated_at:
                generated_at = token.updated_at

        payload: dict[str, object] = {
            'tenantId': tenant.id,
            'version': version or '0.0.0',
            'generatedAt': generated_at or tenant.updated_at,
            'categories': categories,
        }

        if wcag_report:
            payload['wcagReport'] = dict(wcag_report)

        return super().to_representation(payload)
