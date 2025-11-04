import pytest

from backend.apps.foundation.metrics import record_scaffolding_duration


@pytest.mark.django_db(False)
def test_record_scaffolding_duration_handles_none_and_invalid_values():
    # None -> early return
    record_scaffolding_duration('tenant', 'feature', None)
    # Non-numeric -> early return
    record_scaffolding_duration('tenant', 'feature', 'abc')  # type: ignore[arg-type]
    # Negative -> early return
    record_scaffolding_duration('tenant', 'feature', -5)


@pytest.mark.django_db(False)
def test_record_scaffolding_duration_observes_valid_value():
    # Should not raise when recording a valid value
    record_scaffolding_duration('tenant', 'feature', 10)

