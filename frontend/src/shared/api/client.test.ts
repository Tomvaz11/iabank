import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  getTenantTheme,
  listTenantSuccessMetrics,
  registerFeatureScaffold,
  type TraceContext,
} from './client';
import type { FeatureScaffoldRequest } from './generated/models/FeatureScaffoldRequest';

vi.mock('../config/env', () => ({
  env: {
    API_BASE_URL: 'https://api.local.test',
    TENANT_DEFAULT: 'tenant-default',
    OTEL_EXPORTER_OTLP_ENDPOINT: 'http://localhost:4318',
    OTEL_SERVICE_NAME: 'frontend-foundation',
    OTEL_RESOURCE_ATTRIBUTES: {
      'service.namespace': 'iabank',
      'service.version': '0.1.0',
    },
  },
}));

const traceContext: TraceContext = {
  traceparent: '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
  tracestate: 'tenant=tenant-alfa',
};

describe('client HTTP multi-tenant', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('envia cabeçalhos obrigatórios ao buscar temas do tenant', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({ theme: {} }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await getTenantTheme({ tenantId: 'tenant-alfa', traceContext });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('https://api.local.test/api/v1/tenants/tenant-alfa/themes/current');
    expect(init?.method).toBe('GET');

    const headers = new Headers(init?.headers as HeadersInit);
    expect(headers.get('X-Tenant-Id')).toBe('tenant-alfa');
    expect(headers.get('traceparent')).toBe(traceContext.traceparent);
    expect(headers.get('tracestate')).toBe(traceContext.tracestate);
  });

  it('propaga idempotency-key e payload ao registrar scaffolding', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({ ok: true }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const payload: FeatureScaffoldRequest = {
      featureSlug: 'loan-tracking',
      initiatedBy: 'tester',
      slices: [
        {
          slice: 'app',
          files: [
            {
              path: 'app/index.ts',
              checksum: 'sha256-abc',
            },
          ],
        },
      ],
      lintCommitHash: 'sha1-hash',
      scReferences: ['@SC-001'],
      durationMs: 1200,
      metadata: { cliVersion: '0.1.0' },
    };

    await registerFeatureScaffold({
      tenantId: 'tenant-beta',
      idempotencyKey: 'uuid-123',
      payload,
      traceContext,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('https://api.local.test/api/v1/tenants/tenant-beta/features/scaffold');
    expect(init?.method).toBe('POST');
    expect(init?.body).toBe(JSON.stringify(payload));

    const headers = new Headers(init?.headers as HeadersInit);
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('Idempotency-Key')).toBe('uuid-123');
  });

  it('anexa paginação padrão ao listar métricas de sucesso', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers(),
      json: () => Promise.resolve({ results: [] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await listTenantSuccessMetrics({
      tenantId: 'tenant-gamma',
      page: 2,
      pageSize: 50,
      traceContext,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('https://api.local.test/api/v1/tenant-metrics/tenant-gamma/sc?page=2&page_size=50');

    const headers = new Headers(init?.headers as HeadersInit);
    expect(headers.get('X-Tenant-Id')).toBe('tenant-gamma');
  });

  it('lança erro quando a resposta não é bem sucedida', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: () => Promise.resolve({ detail: 'blocked' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      getTenantTheme({
        tenantId: 'tenant-alfa',
        traceContext,
      }),
    ).rejects.toMatchObject({ status: 403 });
  });
});
