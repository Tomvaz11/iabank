import { QueryClient, type QueryClientConfig, type QueryKey } from '@tanstack/react-query';

type QueryDefaults = {
  staleTime: number;
  gcTime: number;
  refetchOnWindowFocus: boolean;
  refetchOnReconnect: boolean | 'always';
  retry: number;
  retryDelay: (attempt: number) => number;
};

const CRITICAL_TAG = 'critical';

const BASE_QUERY_DEFAULTS: QueryDefaults = {
  staleTime: 5 * 60 * 1000,
  gcTime: 10 * 60 * 1000,
  refetchOnWindowFocus: false,
  refetchOnReconnect: true,
  retry: 2,
  retryDelay: (attempt: number) => Math.min(1000 * 2 ** attempt, 30_000),
};

const CRITICAL_QUERY_DEFAULTS: QueryDefaults = {
  staleTime: 30 * 1000,
  gcTime: 10 * 60 * 1000,
  refetchOnWindowFocus: true,
  refetchOnReconnect: 'always',
  retry: 3,
  retryDelay: (attempt: number) => Math.min(2000 * 2 ** attempt, 60_000),
};

export type TenantQueryKey = QueryKey;

export const buildTenantQueryKey = (tenantId: string, ...parts: unknown[]): TenantQueryKey => [
  'tenant',
  tenantId,
  ...parts,
];

export const resolveQueryDefaults = (tags?: string[]): QueryDefaults => {
  if (tags?.includes(CRITICAL_TAG)) {
    return CRITICAL_QUERY_DEFAULTS;
  }

  return BASE_QUERY_DEFAULTS;
};

type QueryOptionsWithMeta = Parameters<QueryClient['defaultQueryOptions']>[0];

const applyPoliciesToOptions = (options: QueryOptionsWithMeta): QueryOptionsWithMeta => {
  const tags = (options.meta?.tags ?? []) as string[];
  const defaults = resolveQueryDefaults(tags);
  const isCritical = tags.includes(CRITICAL_TAG);

  const next = { ...options } as QueryOptionsWithMeta & Partial<QueryDefaults>;
  const target = next as unknown as Record<string, unknown>;

  const apply = <K extends keyof QueryDefaults>(key: K) => {
    const current = target[key as string];
    if (isCritical || typeof current === 'undefined') {
      target[key as string] = defaults[key];
    }
  };

  apply('staleTime');
  apply('gcTime');
  apply('refetchOnWindowFocus');
  apply('refetchOnReconnect');
  apply('retry');
  apply('retryDelay');

  return next;
};

const createConfig = (defaults: QueryDefaults): QueryClientConfig => ({
  defaultOptions: {
    queries: {
      staleTime: defaults.staleTime,
      gcTime: defaults.gcTime,
      retry: defaults.retry,
      retryDelay: defaults.retryDelay,
      refetchOnWindowFocus: defaults.refetchOnWindowFocus,
      refetchOnReconnect: defaults.refetchOnReconnect,
      refetchOnMount: false,
      networkMode: 'always',
      structuralSharing: true,
    },
    mutations: {
      gcTime: 5 * 60 * 1000,
      retry: 1,
      retryDelay: defaults.retryDelay,
      networkMode: 'always',
    },
  },
});

export const createTenantQueryClient = (): QueryClient => {
  const defaults = resolveQueryDefaults();
  const client = new QueryClient(createConfig(defaults));
  const baseDefaultQueryOptions = client.defaultQueryOptions.bind(client);

  client.defaultQueryOptions = ((options: QueryOptionsWithMeta) =>
    applyPoliciesToOptions(
      baseDefaultQueryOptions(options) as unknown as QueryOptionsWithMeta,
    )) as unknown as QueryClient['defaultQueryOptions'];

  return client;
};

export const tenantQueryClient = createTenantQueryClient();

export const resetOnTenantChange = async (client: QueryClient): Promise<void> => {
  await client.cancelQueries();
  client.getQueryCache().clear();
  client.getMutationCache().clear();
  client.clear();
};
