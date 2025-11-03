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
    expect(defaults.gcTime).toBe(10 * 60 * 1000);
    expect(defaults.refetchOnWindowFocus).toBe(false);
    expect(defaults.refetchOnReconnect).toBe(true);
    expect(defaults.retry).toBe(2);
  });

  it('aplica políticas críticas quando meta.tags inclui critical', () => {
    const defaults = resolveQueryDefaults(['critical']);

    expect(defaults.staleTime).toBe(30 * 1000);
    expect(defaults.gcTime).toBeGreaterThanOrEqual(5 * 60 * 1000);
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
      gcTime: 10 * 60 * 1000,
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

    const options = query?.options as Record<string, unknown> | undefined;

    expect(options?.staleTime).toBe(30 * 1000);
    expect(options?.refetchOnWindowFocus).toBe(true);
    expect(options?.refetchOnReconnect).toBe('always');
    expect(options?.retry).toBe(3);

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

    const options = query?.options as Record<string, unknown> | undefined;

    expect(options?.staleTime).toBe(5 * 60 * 1000);
    expect(options?.refetchOnWindowFocus).toBe(false);
    expect(options?.refetchOnReconnect).toBe(true);
    expect(options?.retry).toBe(2);

    await resetOnTenantChange(client);
  });
});
