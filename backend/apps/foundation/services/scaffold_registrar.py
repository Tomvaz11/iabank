from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import structlog

from backend.apps.foundation.metrics import record_scaffolding_duration
from backend.apps.foundation.models import FeatureTemplateRegistration
from backend.apps.tenancy.models import Tenant

logger = structlog.get_logger('backend.apps.foundation.scaffold')


def _normalize_slices(raw_slices: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for slice_entry in raw_slices:
        files = [
            {'path': file_entry['path'], 'checksum': file_entry['checksum']}
            for file_entry in slice_entry['files']
        ]
        normalized.append({'slice': slice_entry['slice'], 'files': files})
    return normalized


def _resolve_latest_slice(slices: Iterable[Dict[str, Any]]) -> str:
    order_map = FeatureTemplateRegistration.slice_order()
    latest_slice = FeatureTemplateRegistration.Slice.APP
    highest_order = -1

    for slice_entry in slices:
        slice_name = slice_entry['slice']
        position = order_map.get(slice_name, -1)
        if position > highest_order:
            highest_order = position
            latest_slice = slice_name

    return latest_slice


@dataclass(slots=True)
class ScaffoldRegistrar:
    tenant: Tenant

    def register(
        self,
        payload: Dict[str, Any],
        idempotency_key: str,
    ) -> Tuple[FeatureTemplateRegistration, bool]:
        normalized_slices = _normalize_slices(payload['slices'])
        latest_slice = _resolve_latest_slice(normalized_slices)
        duration_ms_raw = payload.get('durationMs')
        duration_minutes: float | None = None
        if duration_ms_raw is not None:
            try:
                duration_minutes = float(duration_ms_raw) / 60000.0
            except (TypeError, ValueError):
                duration_minutes = None

        metadata = copy.deepcopy(payload.get('metadata', {}))
        sc_refs = list(payload['scReferences'])
        created_by = payload['initiatedBy']
        if isinstance(created_by, str):
            created_by = uuid.UUID(created_by)

        manager = FeatureTemplateRegistration.objects

        existing_by_key = manager.acquire_by_idempotency(self.tenant.id, idempotency_key)
        if existing_by_key:
            logger.info(
                'scaffold_registration_idempotent_hit',
                tenant=str(self.tenant.id),
                feature_slug=existing_by_key.feature_slug,
            )
            return existing_by_key, False

        existing_by_slug = manager.acquire_by_feature(self.tenant.id, payload['featureSlug'])
        if existing_by_slug:
            logger.info(
                'scaffold_registration_reused',
                tenant=str(self.tenant.id),
                feature_slug=existing_by_slug.feature_slug,
            )
            return existing_by_slug, False

        defaults = {
            'slice': latest_slice,
            'scaffold_manifest': normalized_slices,
            'lint_commit_hash': payload['lintCommitHash'],
            'sc_references': sc_refs,
            'metadata': metadata,
            'created_by': created_by,
            'duration_ms': duration_ms_raw,
            'idempotency_key': idempotency_key,
        }

        registration, created = manager.register(
            tenant_id=self.tenant.id,
            feature_slug=payload['featureSlug'],
            defaults=defaults,
        )

        logger.info(
            'scaffold_registration_created',
            tenant=str(self.tenant.id),
            feature_slug=registration.feature_slug,
            latest_slice=registration.slice,
            duration_ms=duration_ms_raw,
            duration_minutes=duration_minutes,
        )

        if created and duration_minutes is not None:
            record_scaffolding_duration(
                tenant_slug=self.tenant.slug,
                feature_slug=registration.feature_slug,
                duration_minutes=duration_minutes,
            )

        return registration, created
