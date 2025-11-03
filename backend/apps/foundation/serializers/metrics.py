from __future__ import annotations

from rest_framework import serializers

from backend.apps.foundation.models import FeatureTemplateMetric


class SuccessMetricSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='metric_code', read_only=True)
    collectedAt = serializers.DateTimeField(source='collected_at', read_only=True)
    value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureTemplateMetric
        fields = ('code', 'value', 'collectedAt', 'source')
        read_only_fields = fields

    def get_value(self, obj: FeatureTemplateMetric) -> float:
        return float(obj.value)
