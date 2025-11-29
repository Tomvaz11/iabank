from __future__ import annotations

import uuid
from pathlib import Path

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
RLS_SQL_FILE = SQL_DIR / "rls_policies.sql"

if not RLS_SQL_FILE.exists():
    raise RuntimeError("Arquivo de políticas RLS não encontrado.")

RLS_SQL = RLS_SQL_FILE.read_text(encoding="utf-8")


class Migration(migrations.Migration):
    dependencies = [
        ("tenancy", "0027_alter_tenant_options_alter_tenantthemetoken_managers"),
    ]

    operations = [
        migrations.CreateModel(
            name="SeedProfile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("environment", models.CharField(choices=[("dev", "Dev"), ("homolog", "Homolog"), ("staging", "Staging"), ("perf", "Perf"), ("dr", "DR"), ("prod", "Prod")], max_length=16)),
                ("profile", models.CharField(max_length=128)),
                ("schema_version", models.CharField(max_length=16)),
                ("version", models.CharField(max_length=32)),
                ("mode", models.CharField(choices=[("baseline", "Baseline"), ("carga", "Carga"), ("dr", "DR"), ("canary", "Canary")], max_length=16)),
                ("reference_datetime", models.DateTimeField()),
                ("volumetry", models.JSONField(default=dict)),
                ("rate_limit", models.JSONField(default=dict)),
                ("backoff", models.JSONField(default=dict)),
                ("budget", models.JSONField(default=dict)),
                ("window_start_utc", models.TimeField()),
                ("window_end_utc", models.TimeField()),
                ("ttl_config", models.JSONField(default=dict)),
                ("slo_p95_ms", models.PositiveIntegerField()),
                ("slo_p99_ms", models.PositiveIntegerField()),
                ("slo_throughput_rps", models.DecimalField(decimal_places=3, max_digits=10)),
                ("integrity_hash", models.CharField(max_length=128)),
                ("manifest_path", models.CharField(max_length=255)),
                ("manifest_hash_sha256", models.CharField(max_length=64)),
                ("salt_version", models.CharField(max_length=64)),
                ("canary_scope", models.JSONField(blank=True, null=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seedprofiles", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_profile",
                "unique_together": {("tenant", "profile", "version")},
            },
        ),
        migrations.CreateModel(
            name="SeedRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("environment", models.CharField(choices=[("dev", "Dev"), ("homolog", "Homolog"), ("staging", "Staging"), ("perf", "Perf"), ("dr", "DR"), ("prod", "Prod")], max_length=16)),
                ("mode", models.CharField(choices=[("baseline", "Baseline"), ("carga", "Carga"), ("dr", "DR"), ("canary", "Canary")], max_length=16)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("running", "Running"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("aborted", "Aborted"), ("retry_scheduled", "Retry scheduled"), ("blocked", "Blocked")], default="queued", max_length=32)),
                ("requested_by", models.CharField(blank=True, max_length=255, null=True)),
                ("idempotency_key", models.CharField(max_length=255)),
                ("manifest_path", models.CharField(max_length=255)),
                ("manifest_hash_sha256", models.CharField(max_length=64)),
                ("reference_datetime", models.DateTimeField()),
                ("trace_id", models.CharField(blank=True, max_length=128, null=True)),
                ("span_id", models.CharField(blank=True, max_length=64, null=True)),
                ("rate_limit_usage", models.JSONField(default=dict)),
                ("error_budget_consumed", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("reason", models.JSONField(blank=True, null=True)),
                ("profile_version", models.CharField(max_length=32)),
                ("dry_run", models.BooleanField(default=False)),
                ("offpeak_window", models.JSONField(blank=True, null=True)),
                ("canary_scope_snapshot", models.JSONField(blank=True, null=True)),
                ("seed_profile", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="runs", to="tenancy.seedprofile")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seedruns", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_run",
                "unique_together": {("tenant", "seed_profile", "idempotency_key")},
            },
        ),
        migrations.CreateModel(
            name="SeedBatch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entity", models.CharField(max_length=64)),
                ("batch_size", models.PositiveIntegerField()),
                ("attempt", models.PositiveSmallIntegerField(default=0)),
                ("dlq_attempts", models.PositiveSmallIntegerField(default=0)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed"), ("dlq", "DLQ")], default="pending", max_length=16)),
                ("last_retry_at", models.DateTimeField(blank=True, null=True)),
                ("next_retry_at", models.DateTimeField(blank=True, null=True)),
                ("caps_snapshot", models.JSONField(default=dict)),
                ("seed_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="tenancy.seedrun")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seedbatchs", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_batch",
            },
        ),
        migrations.CreateModel(
            name="SeedCheckpoint",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entity", models.CharField(max_length=64)),
                ("hash_estado", models.CharField(max_length=128)),
                ("resume_token", models.BinaryField()),
                ("percentual_concluido", models.DecimalField(decimal_places=2, max_digits=5)),
                ("sealed", models.BooleanField(default=False)),
                ("seed_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="checkpoints", to="tenancy.seedrun")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seedcheckpoints", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_checkpoint",
            },
        ),
        migrations.CreateModel(
            name="SeedQueue",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("environment", models.CharField(choices=[("dev", "Dev"), ("homolog", "Homolog"), ("staging", "Staging"), ("perf", "Perf"), ("dr", "DR"), ("prod", "Prod")], max_length=16)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("started", "Started"), ("expired", "Expired")], default="pending", max_length=16)),
                ("enqueued_at", models.DateTimeField(default=timezone.now)),
                ("expires_at", models.DateTimeField()),
                ("lease_lock_key", models.BigIntegerField(blank=True, null=True)),
                ("seed_run", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="queue_entries", to="tenancy.seedrun")),
                ("tenant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="seedqueues", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_queue",
            },
        ),
        migrations.CreateModel(
            name="SeedDataset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("entity", models.CharField(max_length=64)),
                ("volumetria_prevista", models.PositiveIntegerField(default=0)),
                ("volumetria_real", models.PositiveIntegerField(default=0)),
                ("slo_target_p95", models.PositiveIntegerField(default=0)),
                ("slo_target_p99", models.PositiveIntegerField(default=0)),
                ("drift_percentual", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("seed_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="datasets", to="tenancy.seedrun")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seeddatasets", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_dataset",
            },
        ),
        migrations.CreateModel(
            name="SeedIdempotency",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("environment", models.CharField(choices=[("dev", "Dev"), ("homolog", "Homolog"), ("staging", "Staging"), ("perf", "Perf"), ("dr", "DR"), ("prod", "Prod")], max_length=16)),
                ("idempotency_key", models.CharField(max_length=255)),
                ("manifest_hash_sha256", models.CharField(max_length=64)),
                ("mode", models.CharField(choices=[("baseline", "Baseline"), ("carga", "Carga"), ("dr", "DR"), ("canary", "Canary")], max_length=16)),
                ("expires_at", models.DateTimeField()),
                ("seed_run", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="idempotency_entries", to="tenancy.seedrun")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seedidempotencys", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_idempotency",
                "unique_together": {("tenant", "environment", "idempotency_key")},
            },
        ),
        migrations.CreateModel(
            name="SeedRBAC",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("environment", models.CharField(choices=[("dev", "Dev"), ("homolog", "Homolog"), ("staging", "Staging"), ("perf", "Perf"), ("dr", "DR"), ("prod", "Prod")], max_length=16)),
                ("subject", models.CharField(max_length=255)),
                ("role", models.CharField(choices=[("seed-runner", "Seed runner"), ("seed-admin", "Seed admin"), ("seed-read", "Seed read")], max_length=32)),
                ("policy_version", models.CharField(max_length=32)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seedrbacs", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_rbac",
                "unique_together": {("tenant", "environment", "subject")},
            },
        ),
        migrations.CreateModel(
            name="BudgetRateLimit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("environment", models.CharField(choices=[("dev", "Dev"), ("homolog", "Homolog"), ("staging", "Staging"), ("perf", "Perf"), ("dr", "DR"), ("prod", "Prod")], max_length=16)),
                ("rate_limit_limit", models.PositiveIntegerField()),
                ("rate_limit_window_seconds", models.PositiveIntegerField()),
                ("budget_cost_cap", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("budget_cost_estimated", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("budget_cost_actual", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("error_budget", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("rate_limit_remaining", models.IntegerField(default=0)),
                ("reset_at", models.DateTimeField(blank=True, null=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("throughput_target_rps", models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ("budget_alert_at_pct", models.DecimalField(decimal_places=2, default=80.0, max_digits=5)),
                ("cost_model_version", models.CharField(blank=True, max_length=64, null=True)),
                ("cost_window_started_at", models.DateTimeField(blank=True, null=True)),
                ("cost_window_ends_at", models.DateTimeField(blank=True, null=True)),
                ("seed_profile", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="budget_limits", to="tenancy.seedprofile")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="budgetratelimits", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_budget_ratelimit",
            },
        ),
        migrations.CreateModel(
            name="EvidenceWORM",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("report_url", models.CharField(max_length=512)),
                ("signature_hash", models.CharField(max_length=128)),
                ("signature_algo", models.CharField(max_length=32)),
                ("key_id", models.CharField(max_length=128)),
                ("key_version", models.CharField(max_length=32)),
                ("worm_retention_days", models.PositiveIntegerField()),
                ("integrity_status", models.CharField(choices=[("pending", "Pending"), ("stored", "Stored"), ("verified", "Verified"), ("invalid", "Invalid")], default="pending", max_length=16)),
                ("integrity_verified_at", models.DateTimeField(blank=True, null=True)),
                ("cost_model_version", models.CharField(blank=True, max_length=64, null=True)),
                ("cost_estimated_brl", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("cost_actual_brl", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("seed_run", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="tenancy.seedrun")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seed_evidences", to="tenancy.tenant")),
            ],
            options={
                "db_table": "tenancy_seed_evidence",
            },
        ),
        migrations.AddConstraint(
            model_name="seedprofile",
            constraint=models.CheckConstraint(check=~models.Q(window_start_utc=models.F("window_end_utc")), name="seed_profile_window_not_equal"),
        ),
        migrations.AddConstraint(
            model_name="seedprofile",
            constraint=models.CheckConstraint(
                check=models.Q(mode="canary", canary_scope__isnull=False) | ~models.Q(mode="canary"),
                name="seed_profile_canary_scope_guard",
            ),
        ),
        migrations.AddConstraint(
            model_name="seedbatch",
            constraint=models.CheckConstraint(check=models.Q(batch_size__gt=0), name="seed_batch_size_positive"),
        ),
        migrations.AddConstraint(
            model_name="seedcheckpoint",
            constraint=models.CheckConstraint(
                check=models.Q(percentual_concluido__gte=0) & models.Q(percentual_concluido__lte=100),
                name="seed_checkpoint_percentual_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="seedqueue",
            constraint=models.CheckConstraint(check=models.Q(expires_at__gt=models.F("enqueued_at")), name="seed_queue_ttl_positive"),
        ),
        migrations.AddConstraint(
            model_name="seeddataset",
            constraint=models.CheckConstraint(
                check=models.Q(volumetria_real__gte=0) & models.Q(volumetria_prevista__gte=0),
                name="seed_dataset_volume_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="budgetratelimit",
            constraint=models.CheckConstraint(
                check=models.Q(budget_cost_cap__gte=0)
                & models.Q(budget_cost_estimated__gte=0)
                & models.Q(budget_cost_actual__gte=0),
                name="seed_budget_cost_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="budgetratelimit",
            constraint=models.CheckConstraint(
                check=models.Q(rate_limit_limit__gte=0) & models.Q(rate_limit_window_seconds__gte=0),
                name="seed_budget_ratelimit_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="evidenceworm",
            constraint=models.CheckConstraint(
                check=models.Q(worm_retention_days__gte=0),
                name="seed_evidence_retention_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="evidenceworm",
            constraint=models.CheckConstraint(
                check=models.Q(cost_estimated_brl__gte=0) & models.Q(cost_actual_brl__gte=0),
                name="seed_evidence_costs_non_negative",
            ),
        ),
        migrations.AddIndex(
            model_name="seedprofile",
            index=models.Index(fields=["tenant", "profile"], name="seed_profile_profile_idx"),
        ),
        migrations.AddIndex(
            model_name="seedprofile",
            index=models.Index(fields=["tenant", "mode"], name="seed_profile_mode_idx"),
        ),
        migrations.AddIndex(
            model_name="seedrun",
            index=models.Index(fields=["tenant", "status"], name="seed_run_status_idx"),
        ),
        migrations.AddIndex(
            model_name="seedrun",
            index=models.Index(fields=["tenant", "seed_profile"], name="seed_run_profile_idx"),
        ),
        migrations.AddIndex(
            model_name="seedrun",
            index=models.Index(fields=["environment", "status"], name="seed_run_env_status_idx"),
        ),
        migrations.AddIndex(
            model_name="seedbatch",
            index=models.Index(fields=["tenant", "seed_run", "entity"], name="seed_batch_entity_idx"),
        ),
        migrations.AddIndex(
            model_name="seedbatch",
            index=models.Index(fields=["tenant", "status"], name="seed_batch_status_idx"),
        ),
        migrations.AddIndex(
            model_name="seedcheckpoint",
            index=models.Index(fields=["tenant", "seed_run", "entity"], name="seed_checkpoint_entity_idx"),
        ),
        migrations.AddIndex(
            model_name="seedcheckpoint",
            index=models.Index(fields=["tenant", "created_at"], name="seed_checkpoint_created_idx"),
        ),
        migrations.AddIndex(
            model_name="seedqueue",
            index=models.Index(fields=["environment", "status", "enqueued_at"], name="seed_queue_status_idx"),
        ),
        migrations.AddIndex(
            model_name="seedqueue",
            index=models.Index(fields=["tenant", "status"], name="seed_queue_tenant_status_idx"),
        ),
        migrations.AddIndex(
            model_name="seeddataset",
            index=models.Index(fields=["tenant", "seed_run", "entity"], name="seed_dataset_entity_idx"),
        ),
        migrations.AddIndex(
            model_name="seedidempotency",
            index=models.Index(fields=["tenant", "environment", "expires_at"], name="seed_idemp_exp_idx"),
        ),
        migrations.AddIndex(
            model_name="seedidempotency",
            index=models.Index(fields=["manifest_hash_sha256"], name="seed_idempotency_manifest_idx"),
        ),
        migrations.AddIndex(
            model_name="seedrbac",
            index=models.Index(fields=["tenant", "environment", "role"], name="seed_rbac_role_idx"),
        ),
        migrations.AddIndex(
            model_name="seedrbac",
            index=models.Index(fields=["tenant", "subject"], name="seed_rbac_subject_idx"),
        ),
        migrations.AddIndex(
            model_name="budgetratelimit",
            index=models.Index(fields=["tenant", "seed_profile"], name="seed_budget_profile_idx"),
        ),
        migrations.AddIndex(
            model_name="budgetratelimit",
            index=models.Index(fields=["tenant", "reset_at"], name="seed_budget_reset_idx"),
        ),
        migrations.AddIndex(
            model_name="budgetratelimit",
            index=models.Index(fields=["environment", "reset_at"], name="seed_budget_env_reset_idx"),
        ),
        migrations.AddIndex(
            model_name="budgetratelimit",
            index=models.Index(fields=["environment", "cost_window_ends_at"], name="seed_budget_cost_window_idx"),
        ),
        migrations.RunSQL(
            sql=RLS_SQL,
            reverse_sql="""
                DROP FUNCTION IF EXISTS iabank.apply_tenant_rls_policies();
                DROP FUNCTION IF EXISTS iabank.revert_tenant_rls_policies();
            """,
        ),
        migrations.RunSQL(
            sql="SELECT iabank.apply_tenant_rls_policies();",
            reverse_sql="SELECT iabank.revert_tenant_rls_policies();",
        ),
    ]
