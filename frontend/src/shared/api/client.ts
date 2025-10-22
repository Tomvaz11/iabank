export type TraceContext = {
  traceparent: string;
  tracestate?: string;
};

export type TenantHeaders = {
  tenantId: string;
};

export type GetTenantThemeParams = {
  tenantId: string;
  traceContext: TraceContext;
};

export type RegisterFeatureScaffoldParams = {
  tenantId: string;
  idempotencyKey: string;
  payload: Record<string, unknown>;
  traceContext: TraceContext;
};

export type ListTenantSuccessMetricsParams = {
  tenantId: string;
  page: number;
  pageSize: number;
  traceContext: TraceContext;
};

const notImplemented = (): never => {
  throw new Error('Client HTTP ainda não implementado');
};

export const getTenantTheme = async (_params: GetTenantThemeParams) => notImplemented();

export const registerFeatureScaffold = async (_params: RegisterFeatureScaffoldParams) =>
  notImplemented();

export const listTenantSuccessMetrics = async (_params: ListTenantSuccessMetricsParams) =>
  notImplemented();
