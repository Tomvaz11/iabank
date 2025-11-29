from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from backend.apps.tenancy.managers import TenantManager, use_tenant
from backend.apps.tenancy.models.tenant import Tenant


class Environment(models.TextChoices):
    DEV = "dev", "Dev"
    HOMOLOG = "homolog", "Homolog"
    STAGING = "staging", "Staging"
    PERF = "perf", "Perf"
    DR = "dr", "DR"
    PROD = "prod", "Prod"


class Mode(models.TextChoices):
    BASELINE = "baseline", "Baseline"
    CARGA = "carga", "Carga"
    DR = "dr", "DR"
    CANARY = "canary", "Canary"


class TenantScopedModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="%(class)ss")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):  # pragma: no cover - validação é exercitada por testes de migração
        if self.tenant_id:
            with use_tenant(self.tenant_id):
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)


class SeedProfile(TenantScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.CharField(max_length=16, choices=Environment.choices)
    profile = models.CharField(max_length=128)
    schema_version = models.CharField(max_length=16)
    version = models.CharField(max_length=32)
    mode = models.CharField(max_length=16, choices=Mode.choices)
    reference_datetime = models.DateTimeField()
    volumetry = models.JSONField(default=dict)
    rate_limit = models.JSONField(default=dict)
    backoff = models.JSONField(default=dict)
    budget = models.JSONField(default=dict)
    window_start_utc = models.TimeField()
    window_end_utc = models.TimeField()
    ttl_config = models.JSONField(default=dict)
    slo_p95_ms = models.PositiveIntegerField()
    slo_p99_ms = models.PositiveIntegerField()
    slo_throughput_rps = models.DecimalField(max_digits=10, decimal_places=3)
    integrity_hash = models.CharField(max_length=128)
    manifest_path = models.CharField(max_length=255)
    manifest_hash_sha256 = models.CharField(max_length=64)
    salt_version = models.CharField(max_length=64)
    canary_scope = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "tenancy_seed_profile"
        unique_together = (("tenant", "profile", "version"),)
        indexes = [
            models.Index(fields=["tenant", "profile"], name="seed_profile_profile_idx"),
            models.Index(fields=["tenant", "mode"], name="seed_profile_mode_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(window_start_utc=models.F("window_end_utc")),
                name="seed_profile_window_not_equal",
            ),
            models.CheckConstraint(
                check=models.Q(mode=Mode.CANARY, canary_scope__isnull=False)
                | ~models.Q(mode=Mode.CANARY),
                name="seed_profile_canary_scope_guard",
            ),
        ]


class SeedRun(TenantScopedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        ABORTED = "aborted", "Aborted"
        RETRY_SCHEDULED = "retry_scheduled", "Retry scheduled"
        BLOCKED = "blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seed_profile = models.ForeignKey(SeedProfile, on_delete=models.PROTECT, related_name="runs")
    environment = models.CharField(max_length=16, choices=Environment.choices)
    mode = models.CharField(max_length=16, choices=Mode.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    requested_by = models.CharField(max_length=255, null=True, blank=True)
    idempotency_key = models.CharField(max_length=255)
    manifest_path = models.CharField(max_length=255)
    manifest_hash_sha256 = models.CharField(max_length=64)
    reference_datetime = models.DateTimeField()
    trace_id = models.CharField(max_length=128, null=True, blank=True)
    span_id = models.CharField(max_length=64, null=True, blank=True)
    rate_limit_usage = models.JSONField(default=dict)
    error_budget_consumed = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    reason = models.JSONField(null=True, blank=True)
    profile_version = models.CharField(max_length=32)
    dry_run = models.BooleanField(default=False)
    offpeak_window = models.JSONField(null=True, blank=True)
    canary_scope_snapshot = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "tenancy_seed_run"
        unique_together = (("tenant", "seed_profile", "idempotency_key"),)
        indexes = [
            models.Index(fields=["tenant", "status"], name="seed_run_status_idx"),
            models.Index(fields=["tenant", "seed_profile"], name="seed_run_profile_idx"),
            models.Index(fields=["environment", "status"], name="seed_run_env_status_idx"),
        ]


class SeedBatch(TenantScopedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        DLQ = "dlq", "DLQ"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seed_run = models.ForeignKey(SeedRun, on_delete=models.CASCADE, related_name="batches")
    entity = models.CharField(max_length=64)
    batch_size = models.PositiveIntegerField()
    attempt = models.PositiveSmallIntegerField(default=0)
    dlq_attempts = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    caps_snapshot = models.JSONField(default=dict)

    class Meta:
        db_table = "tenancy_seed_batch"
        indexes = [
            models.Index(fields=["tenant", "seed_run", "entity"], name="seed_batch_entity_idx"),
            models.Index(fields=["tenant", "status"], name="seed_batch_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(batch_size__gt=0), name="seed_batch_size_positive"),
        ]


class SeedCheckpoint(TenantScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seed_run = models.ForeignKey(SeedRun, on_delete=models.CASCADE, related_name="checkpoints")
    entity = models.CharField(max_length=64)
    hash_estado = models.CharField(max_length=128)
    resume_token = models.BinaryField()
    percentual_concluido = models.DecimalField(max_digits=5, decimal_places=2)
    sealed = models.BooleanField(default=False)

    class Meta:
        db_table = "tenancy_seed_checkpoint"
        indexes = [
            models.Index(fields=["tenant", "seed_run", "entity"], name="seed_checkpoint_entity_idx"),
            models.Index(fields=["tenant", "created_at"], name="seed_checkpoint_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(percentual_concluido__gte=0) & models.Q(percentual_concluido__lte=100),
                name="seed_checkpoint_percentual_range",
            ),
        ]


class SeedQueue(TenantScopedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        STARTED = "started", "Started"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="seedqueues",
        null=True,
        blank=True,
    )
    environment = models.CharField(max_length=16, choices=Environment.choices)
    seed_run = models.ForeignKey(
        SeedRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queue_entries",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    enqueued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    lease_lock_key = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = "tenancy_seed_queue"
        indexes = [
            models.Index(fields=["environment", "status", "enqueued_at"], name="seed_queue_status_idx"),
            models.Index(fields=["tenant", "status"], name="seed_queue_tenant_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(expires_at__gt=models.F("enqueued_at")),
                name="seed_queue_ttl_positive",
            ),
        ]


class SeedDataset(TenantScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seed_run = models.ForeignKey(SeedRun, on_delete=models.CASCADE, related_name="datasets")
    entity = models.CharField(max_length=64)
    volumetria_prevista = models.PositiveIntegerField(default=0)
    volumetria_real = models.PositiveIntegerField(default=0)
    slo_target_p95 = models.PositiveIntegerField(default=0)
    slo_target_p99 = models.PositiveIntegerField(default=0)
    drift_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "tenancy_seed_dataset"
        indexes = [
            models.Index(fields=["tenant", "seed_run", "entity"], name="seed_dataset_entity_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(volumetria_real__gte=0) & models.Q(volumetria_prevista__gte=0),
                name="seed_dataset_volume_non_negative",
            ),
        ]


class SeedIdempotency(TenantScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.CharField(max_length=16, choices=Environment.choices)
    idempotency_key = models.CharField(max_length=255)
    manifest_hash_sha256 = models.CharField(max_length=64)
    mode = models.CharField(max_length=16, choices=Mode.choices)
    seed_run = models.ForeignKey(
        SeedRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_entries",
    )
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "tenancy_seed_idempotency"
        unique_together = (("tenant", "environment", "idempotency_key"),)
        indexes = [
            models.Index(fields=["tenant", "environment", "expires_at"], name="seed_idemp_exp_idx"),
            models.Index(fields=["manifest_hash_sha256"], name="seed_idempotency_manifest_idx"),
        ]


class SeedRBAC(TenantScopedModel):
    class Role(models.TextChoices):
        SEED_RUNNER = "seed-runner", "Seed runner"
        SEED_ADMIN = "seed-admin", "Seed admin"
        SEED_READ = "seed-read", "Seed read"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.CharField(max_length=16, choices=Environment.choices)
    subject = models.CharField(max_length=255)
    role = models.CharField(max_length=32, choices=Role.choices)
    policy_version = models.CharField(max_length=32)

    class Meta:
        db_table = "tenancy_seed_rbac"
        unique_together = (("tenant", "environment", "subject"),)
        indexes = [
            models.Index(fields=["tenant", "environment", "role"], name="seed_rbac_role_idx"),
            models.Index(fields=["tenant", "subject"], name="seed_rbac_subject_idx"),
        ]


class BudgetRateLimit(TenantScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seed_profile = models.ForeignKey(SeedProfile, on_delete=models.PROTECT, related_name="budget_limits")
    environment = models.CharField(max_length=16, choices=Environment.choices)
    rate_limit_limit = models.PositiveIntegerField()
    rate_limit_window_seconds = models.PositiveIntegerField()
    budget_cost_cap = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    budget_cost_estimated = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    budget_cost_actual = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    error_budget = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rate_limit_remaining = models.IntegerField(default=0)
    reset_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    throughput_target_rps = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    budget_alert_at_pct = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    cost_model_version = models.CharField(max_length=64, null=True, blank=True)
    cost_window_started_at = models.DateTimeField(null=True, blank=True)
    cost_window_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tenancy_seed_budget_ratelimit"
        indexes = [
            models.Index(fields=["tenant", "seed_profile"], name="seed_budget_profile_idx"),
            models.Index(fields=["tenant", "reset_at"], name="seed_budget_reset_idx"),
            models.Index(fields=["environment", "reset_at"], name="seed_budget_env_reset_idx"),
            models.Index(fields=["environment", "cost_window_ends_at"], name="seed_budget_cost_window_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(budget_cost_cap__gte=0)
                & models.Q(budget_cost_estimated__gte=0)
                & models.Q(budget_cost_actual__gte=0),
                name="seed_budget_cost_non_negative",
            ),
            models.CheckConstraint(
                check=models.Q(rate_limit_limit__gte=0) & models.Q(rate_limit_window_seconds__gte=0),
                name="seed_budget_ratelimit_non_negative",
            ),
        ]


class EvidenceWORM(TenantScopedModel):
    class IntegrityStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        STORED = "stored", "Stored"
        VERIFIED = "verified", "Verified"
        INVALID = "invalid", "Invalid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seed_run = models.OneToOneField(SeedRun, on_delete=models.CASCADE, related_name="evidence")
    report_url = models.CharField(max_length=512)
    signature_hash = models.CharField(max_length=128)
    signature_algo = models.CharField(max_length=32)
    key_id = models.CharField(max_length=128)
    key_version = models.CharField(max_length=32)
    worm_retention_days = models.PositiveIntegerField()
    integrity_status = models.CharField(
        max_length=16,
        choices=IntegrityStatus.choices,
        default=IntegrityStatus.PENDING,
    )
    integrity_verified_at = models.DateTimeField(null=True, blank=True)
    cost_model_version = models.CharField(max_length=64, null=True, blank=True)
    cost_estimated_brl = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cost_actual_brl = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "tenancy_seed_evidence"
        constraints = [
            models.CheckConstraint(
                check=models.Q(worm_retention_days__gte=0),
                name="seed_evidence_retention_positive",
            ),
            models.CheckConstraint(
                check=models.Q(cost_estimated_brl__gte=0) & models.Q(cost_actual_brl__gte=0),
                name="seed_evidence_costs_non_negative",
            ),
        ]
