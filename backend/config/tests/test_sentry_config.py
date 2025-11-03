from __future__ import annotations

from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove variáveis relevantes antes de cada teste."""
    monkeypatch.delenv('FOUNDATION_SENTRY_DSN', raising=False)
    monkeypatch.delenv('FOUNDATION_SENTRY_ENVIRONMENT', raising=False)
    monkeypatch.delenv('FOUNDATION_SENTRY_RELEASE', raising=False)
    monkeypatch.delenv('FOUNDATION_SENTRY_TRACES_SAMPLE_RATE', raising=False)
    monkeypatch.delenv('FOUNDATION_SENTRY_PROFILES_SAMPLE_RATE', raising=False)


def test_init_sentry_disabled_without_dsn() -> None:
    import backend.config.sentry as sentry  # import adiado para aplicar fixture

    with mock.patch('sentry_sdk.init') as init_mock:
        assert sentry.init_sentry() is False
        init_mock.assert_not_called()


def test_init_sentry_configures_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.config.sentry as sentry

    monkeypatch.setenv('FOUNDATION_SENTRY_DSN', 'https://public@sentry.invalid/1')
    monkeypatch.setenv('FOUNDATION_SENTRY_ENVIRONMENT', 'test')
    monkeypatch.setenv('FOUNDATION_SENTRY_RELEASE', '1.0.0-test')
    monkeypatch.setenv('FOUNDATION_SENTRY_TRACES_SAMPLE_RATE', '0.7')
    monkeypatch.setenv('FOUNDATION_SENTRY_PROFILES_SAMPLE_RATE', '0.2')

    with mock.patch('sentry_sdk.init') as init_mock:
        sentry.init_sentry()

    init_mock.assert_called_once()
    kwargs = init_mock.call_args.kwargs
    assert kwargs['dsn'] == 'https://public@sentry.invalid/1'
    assert kwargs['environment'] == 'test'
    assert kwargs['release'] == '1.0.0-test'
    assert pytest.approx(kwargs['traces_sample_rate']) == 0.7
    assert pytest.approx(kwargs['profiles_sample_rate']) == 0.2
    assert callable(kwargs['before_send'])
    assert callable(kwargs['before_breadcrumb'])

    event = {
        'request': {
            'headers': {
                'Authorization': 'Bearer secret-token',
            },
            'data': {
                'email': 'user@example.com',
                'primary_domain': 'tenant-alfa.iabank.test',
            },
        },
        'extra': {
            'tenant': 'tenant-alfa',
            'tenant_id': '123',
        },
    }
    scrubbed = kwargs['before_send'](event, None)
    assert scrubbed['request']['headers']['Authorization'] == '[Filtered]'
    assert scrubbed['request']['data']['email'] == '[Filtered]'
    assert scrubbed['request']['data']['primary_domain'] == '[Filtered]'
    assert scrubbed['extra']['tenant'] == 'tenant-alfa'
    assert scrubbed['extra']['tenant_id'] == '123'

    breadcrumb = {
        'category': 'request',
        'data': {
            'url': 'https://api.iabank.test',
            'headers': {
                'Authorization': 'Bearer abc',
            },
        },
    }
    scrubbed_breadcrumb = kwargs['before_breadcrumb'](breadcrumb, None)
    assert scrubbed_breadcrumb['data']['headers']['Authorization'] == '[Filtered]'
