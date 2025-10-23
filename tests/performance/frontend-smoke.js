import http from 'k6/http';
import { Trend } from 'k6/metrics';
import { check, sleep } from 'k6';

const DEFAULT_BASE_URL = 'http://localhost:4173';
const DEFAULT_TENANT = 'tenant-alfa';

const baseUrl = __ENV.FOUNDATION_PERF_BASE_URL || DEFAULT_BASE_URL;
const tenant = __ENV.FOUNDATION_PERF_TENANT || DEFAULT_TENANT;

const featureRollout = {
  'foundation.fsd': __ENV.FOUNDATION_FLAG_FOUNDATION_FSD || 'canary',
  'design-system.theming': __ENV.FOUNDATION_FLAG_DESIGN_SYSTEM_THEMING || 'canary',
};

const frontendResponseTrend = new Trend('foundation_frontend_response_ms', true);

const randomHex = (length) => {
  let output = '';
  for (let index = 0; index < length; index += 1) {
    output += Math.floor(Math.random() * 16)
      .toString(16)
      .toLowerCase();
  }
  return output;
};

const buildTraceHeaders = (tenantId) => {
  const traceId = randomHex(32);
  const spanId = randomHex(16);
  return {
    traceparent: `00-${traceId}-${spanId}-01`,
    tracestate: `tenant-id=${tenantId}`,
  };
};

const buildFeatureHeader = (rollout) =>
  Object.entries(rollout)
    .map(([flag, status]) => `${flag}:${status}`)
    .join(',');

const baseTags = Object.entries(featureRollout).reduce(
  (acc, [flag, status]) => ({
    ...acc,
    [`flag_${flag.replace('.', '_')}`]: status,
  }),
  {
    feature: 'foundation',
    phase: 'fase-2',
    tenant,
  },
);

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: Number(__ENV.FOUNDATION_PERF_VUS || 5),
      duration: __ENV.FOUNDATION_PERF_DURATION || '30s',
      gracefulStop: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
    foundation_frontend_response_ms: ['p(95)<300'],
  },
  tags: baseTags,
};

export default function foundationSmoke() {
  const traceHeaders = buildTraceHeaders(tenant);
  const featureHeaders = buildFeatureHeader(featureRollout);

  const response = http.get(baseUrl, {
    headers: {
      'X-Tenant-Id': tenant,
      'X-Feature-Flags': featureHeaders,
      ...traceHeaders,
    },
    tags: {
      ...baseTags,
      endpoint: 'root',
    },
  });

  frontendResponseTrend.add(response.timings.duration, { tenant });

  check(response, {
    'status is 200': (res) => res.status === 200,
    'trace headers present': (res) =>
      res.request.headers.traceparent !== undefined &&
      res.request.headers.tracestate !== undefined,
    'feature flags header propagated': (res) =>
      (res.request.headers['X-Feature-Flags'] || res.request.headers['x-feature-flags']) ===
      featureHeaders,
  });

  sleep(1);
}
