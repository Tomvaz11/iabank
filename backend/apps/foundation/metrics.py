from __future__ import annotations

from typing import Optional

from prometheus_client import Histogram
from prometheus_client.registry import REGISTRY

_SC_001_BUCKETS = (
    1,
    2,
    3,
    5,
    8,
    13,
    21,
    30,
    45,
    60,
    90,
    120,
    240,
    480,
    720,
    1440,
)


def _build_histogram() -> Histogram:
    try:
        return Histogram(
            'sc_001_scaffolding_minutes',
            'Tempo de scaffolding FSD em minutos (SC-001)',
            ('tenant_slug', 'feature_slug'),
            buckets=_SC_001_BUCKETS,
        )
    except ValueError:
        existing = REGISTRY._names_to_collectors.get('sc_001_scaffolding_minutes')
        if existing is None:
            raise
        return existing


SC_001_SCAFFOLDING_MINUTES = _build_histogram()


def record_scaffolding_duration(
    tenant_slug: str, feature_slug: str, duration_minutes: Optional[float]
) -> None:
    if duration_minutes is None:
        return

    try:
        value = float(duration_minutes)
    except (TypeError, ValueError):
        return

    if value < 0:
        return

    SC_001_SCAFFOLDING_MINUTES.labels(
        tenant_slug=str(tenant_slug),
        feature_slug=str(feature_slug),
    ).observe(value)
