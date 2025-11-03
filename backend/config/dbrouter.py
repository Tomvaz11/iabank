from __future__ import annotations

from django.db import connections


class PostgresOnlyRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):  # type: ignore[override]
        target_db = hints.get('target_db')
        if target_db != 'postgresql':
            return None

        vendor = connections[db].vendor
        return vendor == 'postgresql'
