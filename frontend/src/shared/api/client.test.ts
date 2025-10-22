import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  getTenantTheme,
  listTenantSuccessMetrics,
  registerFeatureScaffold,
  TraceContext,
} from './client';

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
      json: () => Promise.resolve({ theme: {} }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await getTenantTheme({ tenantId: 'tenant-alfa', traceContext });

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.local.test/api/v1/tenants/tenant-alfa/themes/current',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'X-Tenant-Id': 'tenant-alfa',
          traceparent: traceContext.traceparent,
          tracestate: traceContext.tracestate,
        }),
      }),
    );
  });

  it('propaga idempotency-key e payload ao registrar scaffolding', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ok: true }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await registerFeatureScaffold({
      tenantId: 'tenant-beta',
      idempotencyKey: 'uuid-123',
      payload: { slice: 'app' },
      traceContext,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.local.test/api/v1/tenants/tenant-beta/features/scaffold',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'Idempotency-Key': 'uuid-123',
        }),
        body: JSON.stringify({ slice: 'app' }),
      }),
    );
  });

  it('anexa paginação padrão ao listar métricas de sucesso', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: [] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await listTenantSuccessMetrics({
      tenantId: 'tenant-gamma',
      page: 2,
      pageSize: 50,
      traceContext,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.local.test/api/v1/tenant-metrics/tenant-gamma/sc?page=2&page_size=50',
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-Tenant-Id': 'tenant-gamma',
        }),
      }),
    );
  });

  it('lança erro quando a resposta não é bem sucedida', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      json: () => Promise.resolve({ detail: 'blocked' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      getTenantTheme({
        tenantId: 'tenant-alfa',
        traceContext,
      }),
    ).rejects.toThrow(/403/);
  });
});
