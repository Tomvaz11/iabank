import http from 'k6/http';
import { check, sleep } from 'k6';

const VALIDATE_URL = __ENV.SEED_VALIDATE_URL || 'http://localhost:8000/api/v1/seed-profiles/validate';
const RUNS_URL = __ENV.SEED_RUNS_URL || 'http://localhost:8000/api/v1/seed-runs';
const TENANT = __ENV.SEED_TENANT_ID || 'tenant-a';
const ENVIRONMENT = __ENV.SEED_ENVIRONMENT || 'staging';
const SUBJECT = __ENV.SEED_SUBJECT || 'svc-k6';
const IDEMPOTENCY_KEY = __ENV.SEED_IDEMPOTENCY_KEY || `k6-${Date.now()}`;
const MODE = __ENV.SEED_MODE || 'baseline';

function manifestFromEnv() {
  const slo = {
    p95_target_ms: Number(__ENV.SEED_SLO_P95_MS || 5000),
    p99_target_ms: Number(__ENV.SEED_SLO_P99_MS || 7000),
    throughput_target_rps: Number(__ENV.SEED_SLO_RPS || 5),
  };

  const rateLimit = {
    limit: Number(__ENV.SEED_RATE_LIMIT || 120),
    window_seconds: Number(__ENV.SEED_RATE_WINDOW || 60),
  };

  return {
    metadata: {
      tenant: TENANT,
      environment: ENVIRONMENT,
      profile: __ENV.SEED_PROFILE || 'default',
      version: __ENV.SEED_MANIFEST_VERSION || '1.0.0',
      schema_version: __ENV.SEED_SCHEMA_VERSION || 'v1',
      salt_version: __ENV.SEED_SALT_VERSION || 'v1',
    },
    mode: MODE,
    reference_datetime: __ENV.SEED_REFERENCE_DATETIME || '2025-01-01T00:00:00Z',
    window: {
      start_utc: __ENV.SEED_WINDOW_START || '00:00',
      end_utc: __ENV.SEED_WINDOW_END || '06:00',
    },
    volumetry: {
      customers: { cap: Number(__ENV.SEED_CAP_CUSTOMERS || 25) },
    },
    rate_limit: rateLimit,
    backoff: {
      base_seconds: Number(__ENV.SEED_BACKOFF_BASE || 1),
      jitter_factor: Number(__ENV.SEED_BACKOFF_JITTER || 0.1),
      max_retries: Number(__ENV.SEED_BACKOFF_RETRIES || 3),
      max_interval_seconds: Number(__ENV.SEED_BACKOFF_MAX || 60),
    },
    budget: {
      cost_cap_brl: Number(__ENV.SEED_COST_CAP || 50),
      error_budget_pct: Number(__ENV.SEED_ERROR_BUDGET || 10),
    },
    ttl: {
      baseline_days: Number(__ENV.SEED_TTL_BASELINE || 1),
    },
    slo,
    integrity: {
      manifest_hash: __ENV.SEED_MANIFEST_HASH || 'dev-hash',
    },
  };
}

const MANIFEST = manifestFromEnv();

export const options = {
  vus: Number(__ENV.SEED_VUS || 1),
  duration: __ENV.SEED_DURATION || '1m',
  thresholds: {
    http_req_duration: [`p(95)<${MANIFEST.slo.p95_target_ms}`, `p(99)<${MANIFEST.slo.p99_target_ms}`],
    http_req_failed: [`rate<${Number(__ENV.SEED_ERROR_RATE || 0.05)}`],
  },
  summaryTrendStats: ['avg', 'p(95)', 'p(99)', 'min', 'max'],
};

function headers(idempotencyKey, extra = {}) {
  return {
    'Content-Type': 'application/json',
    'X-Tenant-ID': TENANT,
    'X-Environment': ENVIRONMENT,
    'Idempotency-Key': idempotencyKey,
    'X-Seed-Subject': SUBJECT,
    ...extra,
  };
}

export default function () {
  const validateRes = http.post(VALIDATE_URL, JSON.stringify({ manifest: MANIFEST }), {
    headers: headers(`${IDEMPOTENCY_KEY}-validate`),
    timeout: '10s',
  });

  check(validateRes, {
    'validate status ok': (r) => [200, 422, 429].includes(r.status),
    'validate ratelimit headers': (r) => r.headers['RateLimit-Remaining'] !== undefined,
  });

  const createBody = {
    manifest: MANIFEST,
    manifest_path: __ENV.SEED_MANIFEST_PATH || `configs/seed_profiles/${ENVIRONMENT}/${TENANT}.yaml`,
    mode: MODE,
    dry_run: __ENV.SEED_DRY_RUN === 'true',
  };

  const createRes = http.post(RUNS_URL, JSON.stringify(createBody), {
    headers: headers(IDEMPOTENCY_KEY),
    timeout: '10s',
  });

  check(createRes, {
    'create status ok': (r) => [201, 409, 422, 429].includes(r.status),
    'create ratelimit headers': (r) => r.headers['RateLimit-Remaining'] !== undefined,
    'etag returned': (r) => r.headers['ETag'] !== undefined || r.headers['Etag'] !== undefined,
  });

  const etag = createRes.headers['ETag'] || createRes.headers['Etag'];
  const seedRunId = createRes.json('seed_run_id');
  if (createRes.status === 201 && seedRunId) {
    const pollRes = http.get(`${RUNS_URL}/${seedRunId}`, {
      headers: headers(`${IDEMPOTENCY_KEY}-poll`, etag ? { 'If-None-Match': etag } : {}),
      timeout: '10s',
    });

    check(pollRes, {
      'poll status ok': (r) => [200, 304, 429].includes(r.status),
      'poll ratelimit headers': (r) => r.headers['RateLimit-Remaining'] !== undefined,
    });
  }

  sleep(Number(__ENV.SEED_SLEEP || '1'));
}
