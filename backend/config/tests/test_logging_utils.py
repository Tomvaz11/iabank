from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reload_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('PYTHONHASHSEED', '0')


def test_sanitize_event_dict_masks_sensitive_fields() -> None:
    import backend.config.logging_utils as logging_utils

    event = {
        'message': 'user update request',
        'password': 'super-secret',
        'metadata': {
            'primary_domain': 'tenant-alfa.iabank.test',
            'tokens': [
                {'cpf': '123.456.789-00'},
                {'email': 'user@example.com'},
            ],
        },
        'headers': {
            'Authorization': 'Bearer abc',
        },
    }

    sanitized = logging_utils.sanitize_event_dict(event)

    assert sanitized['password'] == logging_utils.FILTERED_VALUE
    assert sanitized['metadata']['primary_domain'] == logging_utils.FILTERED_VALUE
    assert sanitized['metadata']['tokens'][0]['cpf'] == logging_utils.FILTERED_VALUE
    assert sanitized['metadata']['tokens'][1]['email'] == logging_utils.FILTERED_VALUE
    assert sanitized['headers']['Authorization'] == logging_utils.FILTERED_VALUE
    assert sanitized['message'] == 'user update request'


def test_sanitize_event_dict_handles_non_dict_values() -> None:
    import backend.config.logging_utils as logging_utils

    event = {
        'count': 1,
        'items': ['abc', 'def'],
        'nested': ('tuple', {'secret': 'value'}),
    }

    sanitized = logging_utils.sanitize_event_dict(event)

    assert sanitized['count'] == 1
    assert sanitized['items'] == ['abc', 'def']
    assert sanitized['nested'][1]['secret'] == logging_utils.FILTERED_VALUE
