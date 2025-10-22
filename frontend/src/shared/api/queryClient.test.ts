import { describe, expect, it } from 'vitest';

import {
  buildTenantQueryKey,
  createTenantQueryClient,
  resolveQueryDefaults,
  resetOnTenantChange,
} from './queryClient';

const buildQueryOptions = (tenantId: string) => ({
  queryKey: buildTenantQueryKey(tenantId, 'themes'),
  queryFn: async () => ({ data: 'value' }),
});

describe('queryClient', () => {
  it('gera chaves de consulta com particionamento por tenant', () => {
    const key = buildTenantQueryKey('tenant-alfa', 'themes', { version: '1.0.0' });

    expect(key).toEqual(['tenant', 'tenant-alfa', 'themes', { version: '1.0.0' }]);
  });

  it('aplica políticas padrão para queries regulares', () => {
    const defaults = resolveQueryDefaults();

    expect(defaults.staleTime).toBe(5 * 60 * 1000);
    expect(defaults.cacheTime).toBe(10 * 60 * 1000);
    expect(defaults.refetchOnWindowFocus).toBe(false);
    expect(defaults.refetchOnReconnect).toBe(true);
    expect(defaults.retry).toBe(2);
  });

  it('aplica políticas críticas quando meta.tags inclui critical', () => {
    const defaults = resolveQueryDefaults(['critical']);

    expect(defaults.staleTime).toBe(30 * 1000);
    expect(defaults.cacheTime).toBeGreaterThanOrEqual(5 * 60 * 1000);
    expect(defaults.refetchOnWindowFocus).toBe(true);
    expect(defaults.refetchOnReconnect).toBe('always');
    expect(defaults.retry).toBe(3);
  });

  it('limpa o cache ao trocar de tenant', async () => {
    const client = createTenantQueryClient();
    client.setQueryData(buildTenantQueryKey('tenant-alfa', 'themes'), { data: 'any' });

    await resetOnTenantChange(client);

    expect(client.getQueryData(buildTenantQueryKey('tenant-alfa', 'themes'))).toBeUndefined();
  });

  it('configura valores padrão coerentes para queries regulares', () => {
    const client = createTenantQueryClient();

    expect(client.getDefaultOptions().queries).toMatchObject({
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: 2,
    });
  });

  it('aplica políticas críticas quando meta.tags inclui critical', async () => {
    const client = createTenantQueryClient();

    await client.fetchQuery({
      ...buildQueryOptions('tenant-alfa'),
      meta: { tags: ['critical'] },
    });

    const query = client
      .getQueryCache()
      .find({ queryKey: buildTenantQueryKey('tenant-alfa', 'themes') });

    expect(query?.options.staleTime).toBe(30 * 1000);
    expect(query?.options.refetchOnWindowFocus).toBe(true);
    expect(query?.options.refetchOnReconnect).toBe('always');
    expect(query?.options.retry).toBe(3);

    await resetOnTenantChange(client);
  });

  it('mantém políticas padrão quando meta.tags não inclui critical', async () => {
    const client = createTenantQueryClient();

    await client.fetchQuery({
      ...buildQueryOptions('tenant-beta'),
    });

    const query = client
      .getQueryCache()
      .find({ queryKey: buildTenantQueryKey('tenant-beta', 'themes') });

    expect(query?.options.staleTime).toBe(5 * 60 * 1000);
    expect(query?.options.refetchOnWindowFocus).toBe(false);
    expect(query?.options.refetchOnReconnect).toBe(true);
    expect(query?.options.retry).toBe(2);

    await resetOnTenantChange(client);
  });
});
