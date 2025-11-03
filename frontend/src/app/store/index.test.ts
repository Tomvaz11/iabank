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

  it('atualiza feature flags preservando usuário ativo', () => {
    const store = createAppStore();

    act(() => {
      store.getState().setSession({
        user: { id: 'user-1', name: 'Usuário', roles: ['admin'] },
        featureFlags: { 'foundation.fsd': false },
      });

      store.getState().setFeatureFlags({ 'foundation.fsd': true });
    });

    const state = store.getState();
    expect(state.session.user?.id).toBe('user-1');
    expect(state.session.featureFlags).toEqual({ 'foundation.fsd': true });
  });

  it('resetTheme restaura valores iniciais do slice de tema', () => {
    const baseState = {
      tenant: { id: null, previousId: null },
      theme: {
        id: 'theme-base',
        version: '1.0.0',
        tokens: { primary: '#111' },
        lastUpdatedAt: '2025-10-10T00:00:00Z',
      },
      session: { user: null, featureFlags: {} },
    } as const;

    const store = createAppStore(undefined, baseState);

    act(() => {
      store.getState().setTheme({
        id: 'theme-diff',
        version: '1.1.0',
        tokens: { primary: '#222' },
        lastUpdatedAt: '2025-10-11T00:00:00Z',
      });
    });

    act(() => {
      store.getState().resetTheme();
    });

    expect(store.getState().theme).toEqual(baseState.theme);
  });

  it('clearSession e resetSensitiveState utilizam slices iniciais', () => {
    const baseState = {
      tenant: { id: 'tenant-base', previousId: null },
      theme: {
        id: 'theme-base',
        version: '1.0.0',
        tokens: { primary: '#111' },
        lastUpdatedAt: '2025-10-10T00:00:00Z',
      },
      session: {
        user: { id: 'analyst', name: 'Analista', roles: ['analyst'] },
        featureFlags: { 'design-system.theming': true },
      },
    } as const;

    const store = createAppStore(undefined, baseState);
    const initialSnapshot = store.getInitialSlices();

    act(() => {
      store.getState().clearSession();
    });

    expect(store.getState().session).toEqual(initialSnapshot.session);

    act(() => {
      store.getState().resetSensitiveState();
    });

    expect(store.getState().session).toEqual(initialSnapshot.session);
    expect(store.getState().theme).toEqual(initialSnapshot.theme);
  });
});
