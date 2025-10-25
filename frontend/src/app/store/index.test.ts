import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { resetOnTenantChange } from '../../shared/api/queryClient';
import { createAppStore, useAppStore } from './index';

vi.mock('../../shared/api/queryClient', () => ({
  tenantQueryClient: { clear: vi.fn() },
  resetOnTenantChange: vi.fn(async () => Promise.resolve()),
}));

const resetOnTenantChangeMock = vi.mocked(resetOnTenantChange);

describe('store global (Zustand)', () => {
  beforeEach(() => {
    act(() => {
      useAppStore.setState(useAppStore.getInitialSlices());
    });
    vi.clearAllMocks();
  });

  it('mantém slices de tenant, tema e sessão com valores padrão', () => {
    const { result } = renderHook(() => useAppStore());

    expect(result.current.tenant.id).toBeNull();
    expect(result.current.theme.tokens).toEqual({});
    expect(result.current.session.user).toBeNull();
    expect(result.current.session.featureFlags).toEqual({});
  });

  it('reseta estado sensível e cache ao trocar de tenant', async () => {
    const store = createAppStore();

    act(() => {
      store.getState().setTenant('tenant-alfa');
      store.getState().setSession({
        user: { id: 'user-1', name: 'Usuário', roles: ['admin'] },
        featureFlags: { 'foundation.fsd': true },
      });
      store.getState().setTheme({
        id: 'theme-alfa',
        version: '1.0.0',
        tokens: { primary: '#000' },
        lastUpdatedAt: '2025-10-01T00:00:00Z',
      });
    });

    await act(async () => {
      await store.getState().setTenant('tenant-beta');
    });

    const state = store.getState();
    expect(state.tenant.id).toBe('tenant-beta');
    expect(state.tenant.previousId).toBe('tenant-alfa');
    expect(state.session.user).toBeNull();
    expect(state.session.featureFlags).toEqual({});
    expect(state.theme.tokens).toEqual({});
    expect(resetOnTenantChangeMock).toHaveBeenCalled();
  });

  it('não executa reset quando o tenant permanece igual', async () => {
    const store = createAppStore();

    await act(async () => {
      await store.getState().setTenant('tenant-alfa');
    });

    await act(async () => {
      await store.getState().setTenant('tenant-alfa');
    });

    expect(resetOnTenantChangeMock).toHaveBeenCalledTimes(1);
    expect(store.getState().tenant.previousId).toBeNull();
  });
});
