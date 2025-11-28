import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.SEED_BASE_URL || 'http://localhost:8000';
const VALIDATE_URL = __ENV.SEED_VALIDATE_URL || `${BASE_URL}/api/v1/seed-profiles/validate`;
const RUNS_URL = __ENV.SEED_RUNS_URL || `${BASE_URL}/api/v1/seed-runs`;
const TENANT = __ENV.SEED_TENANT_ID || 'tenant-perf';
const ENVIRONMENT = __ENV.SEED_ENVIRONMENT || 'staging';
const SUBJECT = __ENV.SEED_SUBJECT || 'svc-k6-load';
const MODE = __ENV.SEED_MODE || 'carga';

const validateTrend = new Trend('seed_validate_duration', true);
const createTrend = new Trend('seed_create_duration', true);
const pollTrend = new Trend('seed_poll_duration', true);
const errorRate = new Rate('seed_error_rate');
const ratelimitRemaining = new Trend('seed_ratelimit_remaining', true);
const runsCreated = new Counter('seed_runs_created');

function manifestFromEnv() {
  const slo = {
    p95_target_ms: Number(__ENV.SEED_SLO_P95_MS || 5000),
    p99_target_ms: Number(__ENV.SEED_SLO_P99_MS || 7000),
    throughput_target_rps: Number(__ENV.SEED_SLO_RPS || 20),
  };

  const rateLimit = {
    limit: Number(__ENV.SEED_RATE_LIMIT || 1200),
    window_seconds: Number(__ENV.SEED_RATE_WINDOW || 60),
    burst: Number(__ENV.SEED_RATE_BURST || 2400),
  };

  const volumetry = {
    customers: { cap: Number(__ENV.SEED_CAP_CUSTOMERS || 500) },
    bank_accounts: { cap: Number(__ENV.SEED_CAP_BANK_ACCOUNTS || 600) },
    loans: { cap: Number(__ENV.SEED_CAP_LOANS || 1000) },
    installments: { cap: Number(__ENV.SEED_CAP_INSTALLMENTS || 10000) },
    financial_transactions: { cap: Number(__ENV.SEED_CAP_FINTRANS || 20000) },
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
    volumetry,
    rate_limit: rateLimit,
    backoff: {
      base_seconds: Number(__ENV.SEED_BACKOFF_BASE || 1),
      jitter_factor: Number(__ENV.SEED_BACKOFF_JITTER || 0.15),
      max_retries: Number(__ENV.SEED_BACKOFF_RETRIES || 5),
      max_interval_seconds: Number(__ENV.SEED_BACKOFF_MAX || 120),
    },
    budget: {
      cost_cap_brl: Number(__ENV.SEED_COST_CAP || 125),
      error_budget_pct: Number(__ENV.SEED_ERROR_BUDGET || 10),
    },
    ttl: {
      baseline_days: Number(__ENV.SEED_TTL_BASELINE || 1),
      carga_days: Number(__ENV.SEED_TTL_CARGA || 2),
      dr_days: Number(__ENV.SEED_TTL_DR || 2),
    },
    slo,
    integrity: {
      manifest_hash: __ENV.SEED_MANIFEST_HASH || 'load-hash',
    },
  };
}

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

const MANIFEST = manifestFromEnv();
const ERROR_RATE_CAP = Number(__ENV.SEED_ERROR_RATE || 0.05);

export const options = {
  scenarios: {
    load: {
      executor: 'ramping-arrival-rate',
      startRate: Number(__ENV.SEED_START_RPS || 5),
      timeUnit: '1s',
      preAllocatedVUs: Number(__ENV.SEED_VUS || 20),
      maxVUs: Number(__ENV.SEED_MAX_VUS || 100),
      stages: [
        { target: Number(__ENV.SEED_TARGET_RPS || 20), duration: __ENV.SEED_RAMP_DURATION || '2m' },
        { target: Number(__ENV.SEED_TARGET_RPS || 20), duration: __ENV.SEED_SUSTAIN_DURATION || '3m' },
        { target: 0, duration: '30s' },
      ],
    },
  },
  thresholds: {
    http_req_failed: [`rate<${ERROR_RATE_CAP}`],
    'seed_validate_duration{kind:validate}': [`p(95)<${MANIFEST.slo.p95_target_ms}`, `p(99)<${MANIFEST.slo.p99_target_ms}`],
    'seed_create_duration{kind:create}': [`p(95)<${MANIFEST.slo.p95_target_ms}`, `p(99)<${MANIFEST.slo.p99_target_ms}`],
    'seed_poll_duration{kind:poll}': [`p(95)<${MANIFEST.slo.p99_target_ms}`],
  },
  summaryTrendStats: ['avg', 'p(95)', 'p(99)', 'min', 'max'],
};

function recordError(success) {
  errorRate.add(success ? 0 : 1);
}

export default function () {
  const idempoKey = `${__ENV.SEED_IDEMPOTENCY_PREFIX || 'k6-load'}-${__ITER}-${Date.now()}`;

  const validateRes = http.post(
    VALIDATE_URL,
    JSON.stringify({ manifest: MANIFEST }),
    { headers: headers(`${idempoKey}-validate`), timeout: '15s' },
  );
  validateTrend.add(validateRes.timings.duration, { kind: 'validate' });
  const validateOk = check(validateRes, {
    'validate status accepted': (r) => [200, 422, 429].includes(r.status),
    'validate ratelimit headers': (r) => r.headers['RateLimit-Remaining'] !== undefined,
  });
  recordError(validateOk);

  const createBody = {
    manifest: MANIFEST,
    manifest_path: __ENV.SEED_MANIFEST_PATH || `configs/seed_profiles/${ENVIRONMENT}/${TENANT}.yaml`,
    mode: MODE,
    dry_run: __ENV.SEED_DRY_RUN === 'true',
  };
  const createRes = http.post(RUNS_URL, JSON.stringify(createBody), {
    headers: headers(idempoKey),
    timeout: '15s',
  });
  createTrend.add(createRes.timings.duration, { kind: 'create' });

  const acceptedStatuses = [201, 409, 422, 429];
  const createOk = check(createRes, {
    'create status accepted': (r) => acceptedStatuses.includes(r.status),
    'create returned etag or retry': (r) => r.headers['ETag'] !== undefined || r.headers['Retry-After'] !== undefined,
  });
  recordError(createOk);

  const seedRunId = createRes.json('seed_run_id');
  if (createRes.status === 201 && seedRunId) {
    runsCreated.add(1);
    const pollRes = http.get(`${RUNS_URL}/${seedRunId}`, {
      headers: headers(`${idempoKey}-poll`, {
        'If-None-Match': createRes.headers['ETag'] || createRes.headers['Etag'] || '',
      }),
      timeout: '10s',
    });
    pollTrend.add(pollRes.timings.duration, { kind: 'poll' });

    const pollOk = check(pollRes, {
      'poll status ok': (r) => [200, 304, 429].includes(r.status),
      'poll has ratelimit': (r) => r.headers['RateLimit-Remaining'] !== undefined,
    });
    recordError(pollOk);

    const remaining = Number(pollRes.headers['RateLimit-Remaining'] || 0);
    ratelimitRemaining.add(remaining, { mode: MODE });
  } else {
    ratelimitRemaining.add(Number(createRes.headers['RateLimit-Remaining'] || 0), { mode: MODE });
  }

  const targetSleep = Number(__ENV.SEED_SLEEP || '0.3');
  sleep(targetSleep);
}
