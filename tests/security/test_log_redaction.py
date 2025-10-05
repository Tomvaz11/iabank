import pytest

from scripts.observability.check_structlog import (
    RedactionError,
    SENSITIVE_KEYS,
    validate_entry,
)


def test_validate_entry_accepts_masked_values():
    data = {
        "cpf": "***",
        "email": "[REDACTED]",
        "document": "redacted:hash",
        "action": "ok",
    }
    validate_entry(data)


@pytest.mark.parametrize(
    "key,value",
    [
        ("cpf", "12345678901"),
        ("email", "user@example.com"),
        ("password", "secret"),
    ],
)
def test_validate_entry_rejects_cleartext_values(key, value):
    data = {key: value}
    with pytest.raises(RedactionError):
        validate_entry(data, sensitive_keys=[key])


def test_sensitive_keys_catalog_is_non_empty():
    assert SENSITIVE_KEYS, "sensitive key catalog should not be empty"
