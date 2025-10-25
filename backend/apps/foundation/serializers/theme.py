from __future__ import annotations

from collections import defaultdict
import re
from typing import Iterable

from rest_framework import serializers

from backend.apps.tenancy.models import TenantThemeToken


REQUIRED_CATEGORIES: tuple[str, str, str] = (
    TenantThemeToken.Category.FOUNDATION,
    TenantThemeToken.Category.SEMANTIC,
    TenantThemeToken.Category.COMPONENT,
)

TOKEN_KEY_PATTERN = re.compile(r'^[a-z0-9]+(?:[.-][a-z0-9]+)*$', re.IGNORECASE)


def _validate_categories(categories: dict[str, dict[str, str]]) -> None:
    errors: list[str] = []

    for category in categories.keys():
        if category not in REQUIRED_CATEGORIES:
            errors.append(f'{category}: categoria desconhecida')

    for category in REQUIRED_CATEGORIES:
        tokens = categories.get(category)
        if tokens is None:
            errors.append(f'{category}: categoria ausente no TokenSchema')
            continue

        if not isinstance(tokens, dict):
            errors.append(f'{category}: estrutura inválida')
            continue

        for token_name, token_value in tokens.items():
            if not isinstance(token_name, str) or not TOKEN_KEY_PATTERN.fullmatch(token_name):
                errors.append(f'{category}.{token_name}: chave fora do padrão permitido')
            if not isinstance(token_value, str) or len(token_value) == 0:
                errors.append(f'{category}.{token_name}: valor deve ser string não vazia')

    if errors:
        joined = '; '.join(errors)
        raise serializers.ValidationError(
            {'categories': [f'TokenSchema inválido: {joined}']},
        )


class TenantThemeSerializer(serializers.Serializer):
    tenantId = serializers.UUIDField(format='hex_verbose')
    version = serializers.RegexField(regex=r'^\d+\.\d+\.\d+$')
    generatedAt = serializers.DateTimeField()
    categories = serializers.DictField(child=serializers.DictField(child=serializers.JSONField()))
    wcagReport = serializers.DictField(child=serializers.DictField(child=serializers.JSONField()), required=False)

    def to_representation(self, instance: dict) -> dict:
        tenant = instance['tenant']
        tokens: Iterable[TenantThemeToken] = instance['tokens']

        categories: dict[str, dict[str, str]] = {category: {} for category in REQUIRED_CATEGORIES}
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

        _validate_categories(categories)

        payload: dict[str, object] = {
            'tenantId': tenant.id,
            'version': version or '0.0.0',
            'generatedAt': generated_at or tenant.updated_at,
            'categories': categories,
        }

        if wcag_report:
            payload['wcagReport'] = dict(wcag_report)

        return super().to_representation(payload)
