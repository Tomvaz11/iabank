import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.SEED_VALIDATE_URL || 'http://localhost:8000/api/v1/seed-profiles/validate';
const TENANT = __ENV.SEED_TENANT_ID || 'tenant-a';
const ENVIRONMENT = __ENV.SEED_ENVIRONMENT || 'staging';
const IDEMPOTENCY_KEY = __ENV.SEED_IDEMPOTENCY_KEY || `k6-${Date.now()}`;

const SLO_P95_MS = Number(__ENV.SEED_SLO_P95_MS || 5000);
const SLO_P99_MS = Number(__ENV.SEED_SLO_P99_MS || 7000);
const ERROR_RATE = Number(__ENV.SEED_ERROR_RATE || 0.02);

export const options = {
  vus: Number(__ENV.SEED_VUS || 1),
  duration: __ENV.SEED_DURATION || '1m',
  thresholds: {
    http_req_duration: [`p(95)<${SLO_P95_MS}`, `p(99)<${SLO_P99_MS}`],
    http_req_failed: [`rate<${ERROR_RATE}`],
  },
  summaryTrendStats: ['avg', 'p(95)', 'p(99)', 'min', 'max'],
};

function buildPayload() {
  return {
    mode: __ENV.SEED_MODE || 'baseline',
    tenant: TENANT,
    environment: ENVIRONMENT,
    manifest_version: __ENV.SEED_MANIFEST_VERSION || 'v1.0.0',
    reference_datetime: __ENV.SEED_REFERENCE_DATETIME || '2025-01-01T00:00:00Z',
    slo: {
      p95_target_ms: SLO_P95_MS,
      p99_target_ms: SLO_P99_MS,
      throughput_target_rps: Number(__ENV.SEED_SLO_RPS || 5),
    },
    rate_limit: {
      limit: Number(__ENV.SEED_RATE_LIMIT || 960),
      window_seconds: Number(__ENV.SEED_RATE_WINDOW || 60),
    },
    integrity: {
      manifest_hash: __ENV.SEED_MANIFEST_HASH || 'dev-hash',
      schema_version: __ENV.SEED_SCHEMA_VERSION || 'v1',
    },
  };
}

export default function () {
  const payload = JSON.stringify(buildPayload());
  const res = http.post(BASE_URL, payload, {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': TENANT,
      'X-Environment': ENVIRONMENT,
      'Idempotency-Key': IDEMPOTENCY_KEY,
    },
    timeout: '10s',
  });

  check(res, {
    'status is allowed': (r) => [200, 422, 429].includes(r.status),
    'ratelimit headers present': (r) => r.headers['RateLimit-Remaining'] !== undefined,
    'retry-after for throttling': (r) => r.status !== 429 || Boolean(r.headers['Retry-After']),
  });

  sleep(Number(__ENV.SEED_SLEEP || '1'));
}
