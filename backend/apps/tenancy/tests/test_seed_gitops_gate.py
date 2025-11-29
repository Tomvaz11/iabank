from __future__ import annotations

from http import HTTPStatus

from django.test import SimpleTestCase

from backend.apps.tenancy.services.seed_runs import ProblemDetail, SeedRunService


class SeedGitOpsGateTest(SimpleTestCase):
    def test_blocks_manifest_outside_gitops_tree(self) -> None:
        service = SeedRunService()

        problem = service.ensure_manifest_gitops_alignment(
            manifest_path='configs/other/tenant-a.yaml',
            environment='staging',
        )

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.CONFLICT)
        self.assertIn('gitops', problem.title)

        allowed = service.ensure_manifest_gitops_alignment(
            manifest_path='configs/seed_profiles/staging/tenant-a.yaml',
            environment='staging',
        )
        self.assertIsNone(allowed)
