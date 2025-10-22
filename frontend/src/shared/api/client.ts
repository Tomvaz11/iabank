import { env } from '../config/env';

export type TraceContext = {
  traceparent: string;
  tracestate?: string;
};

type HttpMethod = 'GET' | 'POST';

type RequestConfig = {
  path: string;
  method: HttpMethod;
  tenantId: string;
  traceContext: TraceContext;
  query?: Record<string, string | number | undefined>;
  body?: Record<string, unknown>;
  idempotencyKey?: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly payload: unknown,
  ) {
    super(`Request failed with status ${status}: ${statusText}`);
  }
}

const buildUrl = (path: string, query?: RequestConfig['query']): string => {
  const url = new URL(`${env.API_BASE_URL}${path}`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
};

const request = async <TResponse>({
  path,
  method,
  tenantId,
  traceContext,
  body,
  query,
  idempotencyKey,
}: RequestConfig): Promise<TResponse> => {
  const url = buildUrl(path, query);

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Tenant-Id': tenantId,
    traceparent: traceContext.traceparent,
  };

  if (traceContext.tracestate) {
    headers.tracestate = traceContext.tracestate;
  }

  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
    mode: 'cors',
  });

  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      payload = await response.text();
    }

    throw new ApiError(response.status, response.statusText ?? 'Error', payload);
  }

  return response.json() as Promise<TResponse>;
};

export type GetTenantThemeParams = {
  tenantId: string;
  traceContext: TraceContext;
};

export const getTenantTheme = async <TResponse = unknown>({
  tenantId,
  traceContext,
}: GetTenantThemeParams): Promise<TResponse> =>
  request<TResponse>({
    method: 'GET',
    path: `/api/v1/tenants/${tenantId}/themes/current`,
    tenantId,
    traceContext,
  });

export type RegisterFeatureScaffoldParams = {
  tenantId: string;
  idempotencyKey: string;
  payload: Record<string, unknown>;
  traceContext: TraceContext;
};

export const registerFeatureScaffold = async <TResponse = unknown>({
  tenantId,
  idempotencyKey,
  payload,
  traceContext,
}: RegisterFeatureScaffoldParams): Promise<TResponse> =>
  request<TResponse>({
    method: 'POST',
    path: `/api/v1/tenants/${tenantId}/features/scaffold`,
    tenantId,
    traceContext,
    idempotencyKey,
    body: payload,
  });

export type ListTenantSuccessMetricsParams = {
  tenantId: string;
  page: number;
  pageSize: number;
  traceContext: TraceContext;
};

export const listTenantSuccessMetrics = async <TResponse = unknown>({
  tenantId,
  page,
  pageSize,
  traceContext,
}: ListTenantSuccessMetricsParams): Promise<TResponse> =>
  request<TResponse>({
    method: 'GET',
    path: `/api/v1/tenant-metrics/${tenantId}/sc`,
    tenantId,
    traceContext,
    query: {
      page,
      page_size: pageSize,
    },
  });
