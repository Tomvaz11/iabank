from __future__ import annotations

from django.test import TestCase
from django.utils import timezone
from backend.apps.contracts import signals


class ContractSignalsTest(TestCase):
    def test_contract_check_completed_signal_persists_report(self) -> None:
        results = signals.contract_check_completed.send(
            sender=self.__class__,
            artifact_type='openapi',
            version='1.2.3',
            path='contracts/api.yaml',
            checksum='sha256:abc',
            breaking_change=True,
            released_at=timezone.now(),
            tool='spectral',
            status='fail',
            summary='Lint errors detected',
        )

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        _, payload = results[0]
        self.assertIsNotNone(payload)

        from backend.apps.contracts.models import ApiContractArtifact, ContractDiffReport

        stored_artifact = ApiContractArtifact.objects.get(path='contracts/api.yaml', version='1.2.3')
        self.assertTrue(stored_artifact.breaking_change)
        self.assertIsNotNone(stored_artifact.released_at)

        report = ContractDiffReport.objects.get(artifact=stored_artifact)
        self.assertEqual(report.tool, 'spectral')
        self.assertEqual(report.status, 'fail')
        self.assertEqual(report.summary, 'Lint errors detected')
        self.assertIsNotNone(report.logged_at)

    def test_contract_diff_report_str_representation(self) -> None:
        from backend.apps.contracts.models import ContractDiffReport, ApiContractArtifact

        artifact = ApiContractArtifact.objects.create(
            type='openapi',
            version='0.1.0',
            path='contracts/api.yaml',
            checksum='sha256:def',
        )

        report = ContractDiffReport.objects.create(
            artifact=artifact,
            tool='openapi-diff',
            status='warn',
            summary='Non-breaking additions detected',
            logged_at=timezone.now(),
        )

        self.assertIn('openapi-diff', str(report))
        self.assertIn('warn', str(report))
