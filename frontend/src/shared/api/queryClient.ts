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
const TENANT_KEY_PREFIX = 'tenant';

const validateTenantPartition = (key: QueryKey | undefined, requireKey = true): void => {
  if (!key) {
    if (requireKey) {
      throw new Error('Query key inválida: esperado array com tenant_id.');
    }
    return;
  }

  if (!Array.isArray(key)) {
    throw new Error('Query key inválida: esperado array com tenant_id.');
  }

  const [prefix, tenantId] = key;
  if (prefix !== TENANT_KEY_PREFIX || typeof tenantId !== 'string' || tenantId.trim().length === 0) {
    throw new Error('Query key deve incluir tenant_id na segunda posição. Use buildTenantQueryKey.');
  }
};

const extractQueryKey = (args: unknown[]): QueryKey | undefined => {
  const [first] = args;
  if (Array.isArray(first)) {
    return first as QueryKey;
  }
  if (first && typeof first === 'object' && 'queryKey' in (first as Record<string, unknown>)) {
    return (first as { queryKey?: QueryKey }).queryKey;
  }
  return undefined;
};

const extractFiltersQueryKey = (args: unknown[]): QueryKey | undefined => {
  const [filters] = args;
  if (!filters) {
    return undefined;
  }
  if (Array.isArray(filters)) {
    return filters as QueryKey;
  }
  if (typeof filters === 'object' && 'queryKey' in (filters as Record<string, unknown>)) {
    return (filters as { queryKey?: QueryKey }).queryKey;
  }
  return undefined;
};

const withTenantGuard =
  <TArgs extends unknown[], TResult>(
    fn: (...args: TArgs) => TResult,
    keyResolver: (args: TArgs) => QueryKey | undefined = extractQueryKey,
    requireKey = true,
  ) =>
  (...args: TArgs): TResult => {
    const queryKey = keyResolver(args);
    validateTenantPartition(queryKey, requireKey);
    return fn(...args);
  };

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

  client.fetchQuery = withTenantGuard(client.fetchQuery.bind(client)) as QueryClient['fetchQuery'];
  client.prefetchQuery = withTenantGuard(
    client.prefetchQuery.bind(client),
  ) as QueryClient['prefetchQuery'];
  client.ensureQueryData = withTenantGuard(
    client.ensureQueryData.bind(client),
  ) as QueryClient['ensureQueryData'];
  client.getQueryData = withTenantGuard(
    client.getQueryData.bind(client),
    (args) => args[0] as QueryKey,
  ) as QueryClient['getQueryData'];
  client.setQueryData = withTenantGuard(
    client.setQueryData.bind(client),
    (args) => args[0] as QueryKey,
  ) as QueryClient['setQueryData'];
  const baseSetQueriesData = client.setQueriesData.bind(client);
  client.setQueriesData = ((filters, updater) =>
    {
      if (filters?.queryKey) {
        validateTenantPartition(filters.queryKey as QueryKey, false);
      }
      return baseSetQueriesData(filters, (oldData, query) => {
        if (query?.queryKey) {
          validateTenantPartition(query.queryKey as QueryKey, false);
        }
        if (typeof updater === 'function') {
          const applyUpdater = updater as (data: unknown, context: { queryKey: QueryKey }) => unknown;
          return applyUpdater(oldData, query ?? { queryKey: [] });
        }
        return updater;
      });
    }) as QueryClient['setQueriesData'];
  client.invalidateQueries = withTenantGuard(
    client.invalidateQueries.bind(client),
    extractFiltersQueryKey,
    false,
  ) as QueryClient['invalidateQueries'];
  client.refetchQueries = withTenantGuard(
    client.refetchQueries.bind(client),
    extractFiltersQueryKey,
    false,
  ) as QueryClient['refetchQueries'];
  client.removeQueries = withTenantGuard(
    client.removeQueries.bind(client),
    extractFiltersQueryKey,
    false,
  ) as QueryClient['removeQueries'];
  client.cancelQueries = withTenantGuard(
    client.cancelQueries.bind(client),
    extractFiltersQueryKey,
    false,
  ) as QueryClient['cancelQueries'];
  client.resetQueries = withTenantGuard(
    client.resetQueries.bind(client),
    extractFiltersQueryKey,
    false,
  ) as QueryClient['resetQueries'];

  return client;
};

export const tenantQueryClient = createTenantQueryClient();

export const resetOnTenantChange = async (client: QueryClient): Promise<void> => {
  await client.cancelQueries();
  client.getQueryCache().clear();
  client.getMutationCache().clear();
  client.clear();
};
