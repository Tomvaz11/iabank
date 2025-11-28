from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedDataset, Tenant
from backend.apps.tenancy.services.seed_dataset_gc import SeedDatasetGC
from backend.apps.tenancy.services.seed_runs import SeedRunService
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


class SeedDatasetGCTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-dataset',
            display_name='Tenant Dataset',
            primary_domain='tenant-dataset.iabank.local',
            pii_policy_version='v1',
        )
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging', mode='carga')
        creation = SeedRunService().create_seed_run(
            tenant_id=self.tenant.id,
            environment='staging',
            manifest=manifest,
            manifest_path='configs/seed_profiles/staging/tenant-dataset.yaml',
            idempotency_key='dataset-1',
            requested_by='svc-dataset',
            dry_run=False,
            mode='carga',
        )
        self.seed_run = creation.seed_run
        self.gc = SeedDatasetGC()

    def test_cleanup_removes_existing_datasets_for_mode(self) -> None:
        with use_tenant(self.tenant.id):
            SeedDataset.objects.create(
                seed_run=self.seed_run,
                tenant=self.seed_run.tenant,
                entity='customers',
                volumetria_prevista=10,
                volumetria_real=10,
            )

        removed = self.gc.cleanup_for_mode(
            tenant_id=self.tenant.id,
            environment='staging',
            mode='carga',
        )

        self.assertGreaterEqual(removed, 1)
        with use_tenant(self.tenant.id):
            self.assertEqual(SeedDataset.objects.filter(seed_run=self.seed_run).count(), 0)

    def test_expire_by_ttl_removes_old_records_only(self) -> None:
        with use_tenant(self.tenant.id):
            recent = SeedDataset.objects.create(
                seed_run=self.seed_run,
                tenant=self.seed_run.tenant,
                entity='addresses',
                volumetria_prevista=5,
                volumetria_real=5,
            )
            old = SeedDataset.objects.create(
                seed_run=self.seed_run,
                tenant=self.seed_run.tenant,
                entity='loans',
                volumetria_prevista=2,
                volumetria_real=1,
            )
            SeedDataset.objects.filter(id=old.id).update(created_at=timezone.now() - timedelta(days=10))

        removed = self.gc.expire_by_ttl(
            tenant_id=self.tenant.id,
            days=5,
            environment='staging',
        )

        self.assertGreaterEqual(removed, 1)
        with use_tenant(self.tenant.id):
            remaining = SeedDataset.objects.filter(tenant=self.tenant, entity='addresses').count()
            self.assertEqual(remaining, 1)
            self.assertEqual(SeedDataset.objects.filter(id=recent.id).count(), 1)
