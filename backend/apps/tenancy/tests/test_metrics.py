from django.test import TestCase


class PrometheusMetricsTest(TestCase):
    databases = {"default"}

    def test_metrics_endpoint_available(self) -> None:
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'# HELP', response.content)
