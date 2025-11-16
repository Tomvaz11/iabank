from __future__ import annotations

from django.db import models


class ApiContractArtifact(models.Model):
    class ArtifactType(models.TextChoices):
        OPENAPI = 'openapi', 'OpenAPI'
        PACT_CONSUMER = 'pact-consumer', 'Pact Consumer'
        PACT_PROVIDER = 'pact-provider', 'Pact Provider'

    type = models.CharField(max_length=32, choices=ArtifactType.choices)
    version = models.CharField(max_length=32)
    checksum = models.CharField(max_length=128)
    path = models.CharField(max_length=255)
    breaking_change = models.BooleanField(default=False)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('type', 'version', 'path')
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'{self.type}:{self.version} ({self.path})'


class ContractDiffReport(models.Model):
    class Tool(models.TextChoices):
        SPECTRAL = 'spectral', 'Spectral'
        OPENAPI_DIFF = 'openapi-diff', 'OpenAPI Diff'
        REDOCLY_CLI = 'redocly-cli', 'Redocly CLI'
        PACT_CLI = 'pact-cli', 'Pact CLI'

    class Status(models.TextChoices):
        PASSED = 'pass', 'Pass'
        WARNING = 'warn', 'Warning'
        FAILED = 'fail', 'Fail'

    artifact = models.ForeignKey(
        ApiContractArtifact,
        on_delete=models.CASCADE,
        related_name='diff_reports',
    )
    tool = models.CharField(max_length=32, choices=Tool.choices)
    status = models.CharField(max_length=16, choices=Status.choices)
    summary = models.TextField()
    logged_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-logged_at', '-created_at')

    def __str__(self) -> str:
        return f'{self.tool} [{self.status}] for {self.artifact}'
