from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.db import transaction
from django.dispatch import Signal, receiver
from django.utils import timezone

from .models import ApiContractArtifact, ContractDiffReport

contract_check_completed = Signal()


@receiver(contract_check_completed)
def persist_contract_check(
    sender,
    *,
    artifact_type: str,
    version: str,
    path: str,
    checksum: str,
    tool: str,
    status: str,
    summary: str,
    breaking_change: bool = False,
    released_at: Optional[datetime] = None,
    logged_at: Optional[datetime] = None,
    **kwargs,
):
    """Persistir resultados de Spectral/oasdiff em ContractDiffReport."""
    with transaction.atomic():
        artifact, _ = ApiContractArtifact.objects.get_or_create(
            type=artifact_type,
            version=version,
            path=path,
            defaults={
                'checksum': checksum,
                'breaking_change': breaking_change,
                'released_at': released_at,
            },
        )

        updated = False

        if artifact.checksum != checksum:
            artifact.checksum = checksum
            updated = True

        if artifact.breaking_change != breaking_change:
            artifact.breaking_change = breaking_change
            updated = True

        if released_at and artifact.released_at != released_at:
            artifact.released_at = released_at
            updated = True

        if updated:
            artifact.save(update_fields=['checksum', 'breaking_change', 'released_at', 'updated_at'])

        report = ContractDiffReport.objects.create(
            artifact=artifact,
            tool=tool,
            status=status,
            summary=summary,
            logged_at=logged_at or timezone.now(),
        )

    return artifact, report
