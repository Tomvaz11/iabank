from __future__ import annotations

import pytest
from django.test import Client


@pytest.mark.django_db
def test_metrics_endpoint_exposes_prometheus_data(client: Client) -> None:
    response = client.get('/metrics')

    assert response.status_code == 200
    assert response.headers['Content-Type'].startswith('text/plain')
    body = response.content.decode('utf-8')
    assert 'django_http_requests_total' in body
