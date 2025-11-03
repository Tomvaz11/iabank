from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.utils.encoding import force_bytes

from base64 import b64decode, b64encode


def _get_pgcrypto_key() -> str:
    key = getattr(settings, 'PGCRYPTO_KEY', None)
    if not key:
        raise ImproperlyConfigured(
            'PGCRYPTO_KEY deve estar configurado nas settings para uso do EncryptedJSONField.',
        )
    return key


class EncryptedJSONField(models.BinaryField):
    description = 'JSON armazenado criptografado com pgcrypto (pgp_sym_encrypt)'

    def _encrypt(self, value: str) -> bytes:
        pgcrypto_key = _get_pgcrypto_key()
        if connection.vendor != 'postgresql':
            return b64encode(force_bytes(value))

        with connection.cursor() as cursor:
            cursor.execute("SELECT pgp_sym_encrypt(%s::text, %s)", [value, pgcrypto_key])
            encrypted = cursor.fetchone()[0]
        return bytes(encrypted)

    def _decrypt(self, value: bytes) -> str:
        pgcrypto_key = _get_pgcrypto_key()
        if connection.vendor != 'postgresql':
            return b64decode(bytes(value)).decode('utf-8')

        with connection.cursor() as cursor:
            cursor.execute("SELECT pgp_sym_decrypt(%s::bytea, %s)::text", [value, pgcrypto_key])
            decrypted = cursor.fetchone()[0]
        return decrypted

    def to_python(self, value: Any) -> Any:
        if value is None or isinstance(value, dict):
            return value

        if isinstance(value, (bytes, memoryview)):
            decrypted = self._decrypt(bytes(value))
            return json.loads(decrypted)

        if isinstance(value, str):
            return json.loads(value)

        return value

    def from_db_value(self, value: Any, expression, connection) -> Any:
        if value is None:
            return value
        return self.to_python(value)

    def get_prep_value(self, value: Any) -> Any:
        if value is None:
            return value

        if not isinstance(value, str):
            value = json.dumps(value)

        return self._encrypt(value)
