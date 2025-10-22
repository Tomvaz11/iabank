import {
  QueryClient,
  type QueryClientConfig,
  type QueryKey,
  type QueryOptions,
} from '@tanstack/react-query';

type QueryDefaults = {
  staleTime: number;
  cacheTime: number;
  refetchOnWindowFocus: boolean;
  refetchOnReconnect: boolean | 'always';
  retry: number;
  retryDelay: (attempt: number) => number;
};

const CRITICAL_TAG = 'critical';

const BASE_QUERY_DEFAULTS: QueryDefaults = {
  staleTime: 5 * 60 * 1000,
  cacheTime: 10 * 60 * 1000,
  refetchOnWindowFocus: false,
  refetchOnReconnect: true,
  retry: 2,
  retryDelay: (attempt: number) => Math.min(1000 * 2 ** attempt, 30_000),
};

const CRITICAL_QUERY_DEFAULTS: QueryDefaults = {
  staleTime: 30 * 1000,
  cacheTime: 10 * 60 * 1000,
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

type QueryOptionsWithMeta = QueryOptions<unknown, unknown, unknown, QueryKey>;

const applyPoliciesToOptions = <T extends QueryOptionsWithMeta>(options: T): T => {
  const tags = (options.meta?.tags ?? []) as string[];
  const defaults = resolveQueryDefaults(tags);
  const isCritical = tags.includes(CRITICAL_TAG);

  const resolveValue = <K extends keyof QueryDefaults>(
    key: K,
    current: T[K],
  ): T[K] => {
    if (isCritical) {
      return defaults[key] as T[K];
    }

    return (typeof current === 'undefined' ? defaults[key] : current) as T[K];
  };

  return {
    ...options,
    staleTime: resolveValue('staleTime', options.staleTime),
    cacheTime: resolveValue('cacheTime', options.cacheTime),
    refetchOnWindowFocus: resolveValue(
      'refetchOnWindowFocus',
      options.refetchOnWindowFocus as T['refetchOnWindowFocus'],
    ),
    refetchOnReconnect: resolveValue(
      'refetchOnReconnect',
      options.refetchOnReconnect as T['refetchOnReconnect'],
    ),
    retry: resolveValue('retry', options.retry as T['retry']),
    retryDelay: resolveValue('retryDelay', options.retryDelay as T['retryDelay']),
  } as T;
};

const createConfig = (defaults: QueryDefaults): QueryClientConfig => ({
  defaultOptions: {
    queries: {
      staleTime: defaults.staleTime,
      cacheTime: defaults.cacheTime,
      retry: defaults.retry,
      retryDelay: defaults.retryDelay,
      refetchOnWindowFocus: defaults.refetchOnWindowFocus,
      refetchOnReconnect: defaults.refetchOnReconnect,
      refetchOnMount: false,
      networkMode: 'always',
      structuralSharing: true,
    },
    mutations: {
      cacheTime: 5 * 60 * 1000,
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

  client.defaultQueryOptions = ((options) =>
    applyPoliciesToOptions(baseDefaultQueryOptions(options))) as QueryClient['defaultQueryOptions'];

  return client;
};

export const tenantQueryClient = createTenantQueryClient();

export const resetOnTenantChange = async (client: QueryClient): Promise<void> => {
  await client.cancelQueries();
  client.getQueryCache().clear();
  client.getMutationCache().clear();
  client.clear();
};
