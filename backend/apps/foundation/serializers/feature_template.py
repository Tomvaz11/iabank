from __future__ import annotations

from typing import Any, Dict, List

from rest_framework import serializers

from backend.apps.foundation.models import FeatureTemplateRegistration


class FeatureScaffoldFileSerializer(serializers.Serializer):
    path = serializers.CharField(max_length=512)
    checksum = serializers.RegexField(regex=r'^[0-9a-f]{64}$')


class FeatureScaffoldSliceSerializer(serializers.Serializer):
    slice = serializers.ChoiceField(choices=FeatureTemplateRegistration.Slice.choices)
    files = FeatureScaffoldFileSerializer(many=True, allow_empty=False)


class FeatureScaffoldRequestSerializer(serializers.Serializer):
    featureSlug = serializers.RegexField(regex=r'^[a-z0-9-]+$', max_length=64)
    initiatedBy = serializers.UUIDField()
    slices = FeatureScaffoldSliceSerializer(many=True, allow_empty=False)
    lintCommitHash = serializers.RegexField(regex=r'^[0-9a-f]{40}$')
    scReferences = serializers.ListSerializer(
        child=serializers.RegexField(regex=r'^@SC-00[1-5]$'),
        allow_empty=False,
    )
    durationMs = serializers.IntegerField(required=False, min_value=0)
    metadata = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
        default=dict,
    )


class FeatureTemplateRegistrationSerializer(serializers.ModelSerializer):
    scaffoldId = serializers.UUIDField(source='id', read_only=True)
    tenantId = serializers.UUIDField(source='tenant_id', read_only=True)
    recordedAt = serializers.DateTimeField(source='created_at', read_only=True)
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = FeatureTemplateRegistration
        fields = ('scaffoldId', 'tenantId', 'status', 'recordedAt', 'metrics')
        read_only_fields = fields

    def get_metrics(self, obj: FeatureTemplateRegistration) -> List[Dict[str, Any]]:
        # Métricas serão implementadas em tarefas futuras (SC-001/SC-003).
        return []
