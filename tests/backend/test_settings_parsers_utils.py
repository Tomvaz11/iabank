import pytest

from backend.config import settings


@pytest.mark.django_db(False)
def test_parse_csp_list_defaults_and_values():
    assert settings._parse_csp_list(None, ["'self'"]) == ["'self'"]
    assert settings._parse_csp_list('', ["'self'"]) == ["'self'"]
    assert settings._parse_csp_list(' a, b , ,', ['x']) == ['a', 'b']


@pytest.mark.django_db(False)
def test_parse_csp_exceptions_various_inputs():
    assert settings._parse_csp_exceptions(None) == []
    assert settings._parse_csp_exceptions('not-json') == []
    assert settings._parse_csp_exceptions('[]') == []

    raw = (
        '[{"directive":"script-src","value":"https://x","expires_at":"2099-01-01"},'
        '{"directive":"","value":"x","expires_at":"y"},'
        '{"directive":"img-src","value":"data:","expires_at":"2099-01-01","note":" tmp "}]'
    )
    result = settings._parse_csp_exceptions(raw)
    assert result[0]['directive'] == 'script-src'
    assert result[0]['value'] == 'https://x'
    assert result[0]['expires_at'] == '2099-01-01'
    # note is optional and trimmed
    assert result[1:]  # at least one valid entry remains

