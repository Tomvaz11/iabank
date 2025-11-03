from __future__ import annotations

from typing import Tuple
from uuid import UUID

from django.db import models, transaction


class FeatureTemplateRegistrationQuerySet(models.QuerySet):
    def for_tenant(self, tenant_id: UUID | str) -> 'FeatureTemplateRegistrationQuerySet':
        return self.filter(tenant_id=str(tenant_id))


class FeatureTemplateRegistrationManager(
    models.Manager.from_queryset(FeatureTemplateRegistrationQuerySet),
):
    def for_tenant(self, tenant_id: UUID | str) -> FeatureTemplateRegistrationQuerySet:
        return self.get_queryset().for_tenant(tenant_id)

    def acquire_by_idempotency(
        self,
        tenant_id: UUID | str,
        idempotency_key: str,
    ):
        return self.for_tenant(tenant_id).filter(idempotency_key=idempotency_key).first()

    def acquire_by_feature(
        self,
        tenant_id: UUID | str,
        feature_slug: str,
    ):
        return self.for_tenant(tenant_id).filter(feature_slug=feature_slug).first()

    def register(
        self,
        tenant_id: UUID | str,
        feature_slug: str,
        defaults: dict,
    ) -> Tuple[models.Model, bool]:
        with transaction.atomic():
            scoped_qs = self.for_tenant(tenant_id).select_for_update()

            existing = scoped_qs.filter(feature_slug=feature_slug).first()
            if existing:
                return existing, False

            instance = self.create(
                tenant_id=tenant_id,
                feature_slug=feature_slug,
                **defaults,
            )
            return instance, True
