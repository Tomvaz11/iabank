from __future__ import annotations

from rest_framework import serializers

from backend.apps.tenancy.models import SeedRun


class SeedRunCreateSerializer(serializers.Serializer):
    manifest = serializers.DictField()
    manifest_path = serializers.CharField(required=False, allow_blank=True)
    dry_run = serializers.BooleanField(default=False)
    mode = serializers.CharField(required=False, allow_blank=True)
    requested_by = serializers.CharField(required=False, allow_blank=True)


class SeedRunSerializer(serializers.ModelSerializer):
    manifest_hash = serializers.CharField(source='manifest_hash_sha256', read_only=True)

    class Meta:
        model = SeedRun
        fields = [
            'id',
            'status',
            'mode',
            'environment',
            'manifest_hash',
            'reference_datetime',
            'dry_run',
            'profile_version',
        ]
        read_only_fields = fields
