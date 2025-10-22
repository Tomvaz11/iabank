import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 5,
      duration: '30s',
      gracefulStop: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
  tags: {
    feature: 'foundation',
    phase: 'fase-0',
  },
};

export default function foundationSmoke() {
  const response = http.get('http://localhost:4173/');

  check(response, {
    'status is 200': (res) => res.status === 200,
    'trace headers present': (res) =>
      res.request.headers['traceparent'] !== undefined &&
      res.request.headers['tracestate'] !== undefined,
  });

  sleep(1);
}
