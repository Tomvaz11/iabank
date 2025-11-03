from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from backend.apps.foundation.models import DesignSystemStory


class DesignSystemStorySerializer(serializers.ModelSerializer):
    tenantId = serializers.SerializerMethodField()
    componentId = serializers.CharField(source='component_id')
    storyId = serializers.CharField(source='story_id')
    tags = serializers.SerializerMethodField()
    coveragePercent = serializers.SerializerMethodField()
    axeStatus = serializers.CharField(source='axe_status')
    chromaticBuild = serializers.CharField(source='chromatic_build')
    storybookUrl = serializers.CharField(source='storybook_url')
    updatedAt = serializers.DateTimeField(source='updated_at')

    class Meta:
        model = DesignSystemStory
        fields = (
            'id',
            'tenantId',
            'componentId',
            'storyId',
            'tags',
            'coveragePercent',
            'axeStatus',
            'chromaticBuild',
            'storybookUrl',
            'updatedAt',
        )
        read_only_fields = fields

    def get_tenantId(self, instance: DesignSystemStory) -> str | None:
        tenant_id = instance.tenant_id or getattr(instance.tenant, 'id', None)
        return str(tenant_id) if tenant_id else None

    def get_tags(self, instance: DesignSystemStory) -> list[str]:
        tags = instance.tags or []
        if isinstance(tags, (list, tuple)):
            return [str(tag) for tag in tags]
        return []

    def get_coveragePercent(self, instance: DesignSystemStory) -> float:
        value: Decimal | float = instance.coverage_percent
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
