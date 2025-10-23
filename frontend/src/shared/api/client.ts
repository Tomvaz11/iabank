import { env } from '../config/env';
import type { FeatureScaffoldRequest } from './generated/models/FeatureScaffoldRequest';
import type { FeatureScaffoldResponse } from './generated/models/FeatureScaffoldResponse';
import type { TenantMetricPage } from './generated/models/TenantMetricPage';
import type { TenantThemeResponse } from './generated/models/TenantThemeResponse';
import { ApiError } from './generated/core/ApiError';
import type { ApiRequestOptions } from './generated/core/ApiRequestOptions';
import { OpenAPI } from './generated/core/OpenAPI';
import { request as openApiRequest } from './generated/core/request';

export type TraceContext = {
  traceparent: string;
  tracestate?: string;
};

OpenAPI.CREDENTIALS = 'include';
OpenAPI.WITH_CREDENTIALS = true;

type HeadersRecord = Record<string, string | undefined>;

const buildHeaders = (
  tenantId: string,
  traceContext: TraceContext,
  extraHeaders?: HeadersRecord,
): Record<string, string> => {
  const headers: Record<string, string> = {
    'X-Tenant-Id': tenantId,
    traceparent: traceContext.traceparent,
  };

  if (traceContext.tracestate) {
    headers.tracestate = traceContext.tracestate;
  }

  if (extraHeaders) {
    Object.entries(extraHeaders).forEach(([key, value]) => {
      if (value) {
        headers[key] = value;
      }
    });
  }

  return headers;
};

const execute = <T>(options: ApiRequestOptions) => {
  OpenAPI.BASE = env.API_BASE_URL;
  return openApiRequest<T>(OpenAPI, options);
};

export type GetTenantThemeParams = {
  tenantId: string;
  traceContext: TraceContext;
};

export const getTenantTheme = ({
  tenantId,
  traceContext,
}: GetTenantThemeParams): Promise<TenantThemeResponse> =>
  execute<TenantThemeResponse>({
    method: 'GET',
    url: '/api/v1/tenants/{tenantId}/themes/current',
    path: { tenantId },
    headers: buildHeaders(tenantId, traceContext),
  });

export type RegisterFeatureScaffoldParams = {
  tenantId: string;
  idempotencyKey: string;
  payload: FeatureScaffoldRequest;
  traceContext: TraceContext;
};

export const registerFeatureScaffold = ({
  tenantId,
  idempotencyKey,
  payload,
  traceContext,
}: RegisterFeatureScaffoldParams): Promise<FeatureScaffoldResponse | unknown> =>
  execute({
    method: 'POST',
    url: '/api/v1/tenants/{tenantId}/features/scaffold',
    path: { tenantId },
    headers: buildHeaders(tenantId, traceContext, {
      'Idempotency-Key': idempotencyKey,
      'Content-Type': 'application/json',
    }),
    body: payload,
    mediaType: 'application/json',
  });

export type ListTenantSuccessMetricsParams = {
  tenantId: string;
  page: number;
  pageSize: number;
  traceContext: TraceContext;
};

export const listTenantSuccessMetrics = ({
  tenantId,
  page,
  pageSize,
  traceContext,
}: ListTenantSuccessMetricsParams): Promise<TenantMetricPage> =>
  execute<TenantMetricPage>({
    method: 'GET',
    url: '/api/v1/tenant-metrics/{tenantId}/sc',
    path: { tenantId },
    headers: buildHeaders(tenantId, traceContext),
    query: {
      page,
      page_size: pageSize,
    },
  });

export { ApiError };
