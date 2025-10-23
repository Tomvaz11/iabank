from __future__ import annotations

from typing import Any, List, Tuple

from django.db import migrations


LEGACY_TABLE_CANDIDATES: Tuple[str, ...] = (
    'foundation_feature_template_registrations_legacy',
    'foundation_feature_template_registration',
    'feature_template_registrations_legacy',
)


def _table_exists(schema_editor, table_name: str) -> bool:
    return table_name in schema_editor.connection.introspection.table_names()


def _resolve_source_table(schema_editor) -> str | None:
    for table_name in LEGACY_TABLE_CANDIDATES:
        if _table_exists(schema_editor, table_name):
            return table_name
    return None


def _fetch_legacy_rows(schema_editor, table_name: str) -> List[Tuple[Any, ...]]:
    columns = (
        'tenant_id',
        'feature_slug',
        'slice',
        'scaffold_manifest',
        'lint_commit_hash',
        'sc_references',
        'metadata',
        'created_by',
        'duration_ms',
        'idempotency_key',
        'status',
    )
    selected_columns = ', '.join(columns)

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f'SELECT {selected_columns} FROM {table_name}')
        return cursor.fetchall()


def forwards(apps, schema_editor) -> None:
    table_name = _resolve_source_table(schema_editor)
    if table_name is None:
        return

    FeatureTemplateRegistration = apps.get_model('foundation', 'FeatureTemplateRegistration')

    legacy_rows = _fetch_legacy_rows(schema_editor, table_name)

    manager = FeatureTemplateRegistration.objects
    for row in legacy_rows:
        (
            tenant_id,
            feature_slug,
            slice_value,
            scaffold_manifest,
            lint_commit_hash,
            sc_references,
            metadata,
            created_by,
            duration_ms,
            idempotency_key,
            status_value,
        ) = row

        defaults = {
            'slice': slice_value or FeatureTemplateRegistration.Slice.APP,
            'scaffold_manifest': scaffold_manifest or [],
            'lint_commit_hash': lint_commit_hash,
            'sc_references': sc_references or [],
            'metadata': metadata or {},
            'created_by': created_by,
            'duration_ms': duration_ms,
            'idempotency_key': idempotency_key or f'legacy-{feature_slug}',
            'status': status_value or FeatureTemplateRegistration.Status.INITIATED,
        }

        manager.update_or_create(
            tenant_id=tenant_id,
            feature_slug=feature_slug,
            defaults=defaults,
        )


def backwards(apps, schema_editor) -> None:
    FeatureTemplateRegistration = apps.get_model('foundation', 'FeatureTemplateRegistration')
    manager = FeatureTemplateRegistration.objects
    manager.filter(idempotency_key__startswith='legacy-').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('foundation', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
