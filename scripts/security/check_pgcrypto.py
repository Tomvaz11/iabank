#!/usr/bin/env python
from __future__ import annotations

import os
import sys

import django


def main() -> int:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
    django.setup()

    from backend.apps.tenancy.fields import EncryptedJSONField
    from backend.apps.tenancy.models import TenantThemeToken

    field = TenantThemeToken._meta.get_field('json_payload')
    if not isinstance(field, EncryptedJSONField):
        print('json_payload não está protegido por EncryptedJSONField', file=sys.stderr)
        return 1

    print('json_payload protegido com pgcrypto.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
