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
const throughputTrend = new Trend('foundation_api_throughput', true);
const DEFAULT_DURATION = '30s';
const DEFAULT_SERVICE_NAME = 'frontend-foundation';
const DEFAULT_OTEL_TIMEOUT_MS = 2000;
const otelServiceName = __ENV.OTEL_SERVICE_NAME || DEFAULT_SERVICE_NAME;
const otelEndpoint =
  (__ENV.FOUNDATION_OTEL_EXPORT_URL || __ENV.OTEL_EXPORTER_OTLP_ENDPOINT || '').replace(/\/$/, '');
const throughputCritical = Number(__ENV.FOUNDATION_PERF_THROUGHPUT_CRITICAL || 45);
const throughputWarning = Number(__ENV.FOUNDATION_PERF_THROUGHPUT_WARNING || throughputCritical * 0.9);

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

const getHeaderValue = (headers, headerName) => {
  const target = headerName.toLowerCase();
  for (const [key, value] of Object.entries(headers)) {
    if (key.toLowerCase() !== target) {
      continue;
    }
    if (Array.isArray(value)) {
      return value.join(',');
    }
    return value;
  }
  return undefined;
};

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: Number(__ENV.FOUNDATION_PERF_VUS || 5),
      duration: __ENV.FOUNDATION_PERF_DURATION || DEFAULT_DURATION,
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
      getHeaderValue(res.request.headers, 'traceparent') !== undefined &&
      getHeaderValue(res.request.headers, 'tracestate') !== undefined,
    'feature flags header propagated': (res) =>
      getHeaderValue(res.request.headers, 'X-Feature-Flags') === featureHeaders,
  });

  sleep(1);
}

const parseDurationToSeconds = (raw) => {
  if (!raw) {
    return 0;
  }
  if (typeof raw === 'number') {
    return raw;
  }
  const match = /^(\d+)(ms|s|m|h)?$/.exec(raw.trim());
  if (!match) {
    return 0;
  }
  const value = Number(match[1]);
  const unit = match[2] || 's';
  switch (unit) {
    case 'ms':
      return value / 1000;
    case 'm':
      return value * 60;
    case 'h':
      return value * 3600;
    default:
      return value;
  }
};

const publishFoundationThroughput = (value, attributes) => {
  if (!otelEndpoint) {
    console.warn('[foundation:throughput] OTEL endpoint ausente, métrica não será publicada.');
    return;
  }
  const url = `${otelEndpoint}/v1/metrics`;
  const now = Date.now() * 1e6;
  const tenantTag = attributes?.tenant || tenant;
  const payload = JSON.stringify({
    resourceMetrics: [
      {
        resource: {
          attributes: [
            { key: 'service.name', value: { stringValue: otelServiceName } },
            {
              key: 'deployment.environment',
              value: { stringValue: __ENV.OTEL_RESOURCE_ENV || 'local' },
            },
            { key: 'feature', value: { stringValue: baseTags.feature } },
          ],
        },
        scopeMetrics: [
          {
            scope: {
              name: 'tests/performance/frontend-smoke',
              version: '1.0.0',
            },
            metrics: [
              {
                name: 'foundation_api_throughput',
                description: 'Throughput medido via k6 smoke test',
                unit: 'requests/second',
                gauge: {
                  dataPoints: [
                    {
                      asDouble: Number(value),
                      timeUnixNano: `${now}`,
                      attributes: [
                        { key: 'tenant', value: { stringValue: tenantTag } },
                        { key: 'scenario', value: { stringValue: 'smoke' } },
                        { key: 'phase', value: { stringValue: baseTags.phase } },
                      ],
                    },
                  ],
                },
              },
            ],
          },
        ],
      },
    ],
  });
  const timeoutSeconds = Math.max(Number(__ENV.FOUNDATION_OTEL_TIMEOUT_MS || DEFAULT_OTEL_TIMEOUT_MS) / 1000, 1);
  try {
    const response = http.post(
      url,
      payload,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: `${timeoutSeconds}s`,
        tags: {
          ...baseTags,
          otel_export: 'foundation_api_throughput',
        },
      },
    );
    if (response.status >= 300) {
      console.error(
        `[foundation:throughput] Falha ao publicar foundation_api_throughput: status=${response.status} body=${response.body}`,
      );
    }
  } catch (error) {
    console.error(`[foundation:throughput] Erro ao publicar métrica: ${error.message}`);
  }
};

const extractCount = (metric) => {
  if (!metric) {
    return 0;
  }
  if (typeof metric.count === 'number') {
    return metric.count;
  }
  if (metric.values && typeof metric.values.count === 'number') {
    return metric.values.count;
  }
  if (typeof metric.total === 'number') {
    return metric.total;
  }
  return 0;
};

export function handleSummary(data) {
  const metrics = data?.metrics ?? {};
  const totalRequests =
    extractCount(metrics.http_reqs) ||
    extractCount(metrics.iterations);
  const scenarioDuration =
    options.scenarios?.smoke?.duration || __ENV.FOUNDATION_PERF_DURATION || DEFAULT_DURATION;
  const durationSeconds = parseDurationToSeconds(scenarioDuration);
  const throughput = durationSeconds > 0 ? totalRequests / durationSeconds : 0;

  throughputTrend.add(throughput, { tenant });
  publishFoundationThroughput(throughput, { tenant });

  const status =
    throughput >= throughputCritical
      ? 'ok'
      : throughput >= throughputWarning
        ? 'warning'
        : 'critical';

  const summary = {
    metric: 'foundation_api_throughput',
    throughput,
    totalRequests,
    durationSeconds,
    status,
    thresholds: {
      warning: throughputWarning,
      critical: throughputCritical,
    },
  };

  return {
    stdout: JSON.stringify(summary, null, 2),
    'artifacts/foundation-api-throughput.json': JSON.stringify(summary, null, 2),
  };
}
