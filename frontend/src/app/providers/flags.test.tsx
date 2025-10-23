import { act, render } from '@testing-library/react';
import { waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { createAppStore } from '../store';
import type { AppStore } from '../store';
import { FlagsProvider, resetFeatureFlagClientFactory, setFeatureFlagClientFactory } from './flags';

type StubClient = ReturnType<typeof createStubClient>;

const createStubClient = (snapshots: Record<string, Record<string, boolean>>) => {
  const listeners = new Set<() => void>();

  return {
    getSnapshot: vi.fn(async (tenantId: string | null) => {
      const key = tenantId ?? 'default';
      return snapshots[key] ?? snapshots.default ?? {};
    }),
    subscribe: vi.fn((callback: () => void) => {
      listeners.add(callback);
      return () => listeners.delete(callback);
    }),
    dispose: vi.fn(async () => undefined),
    emitChange: () => {
      listeners.forEach((listener) => listener());
    },
    updateSnapshot: (tenantId: string | null, snapshot: Record<string, boolean>) => {
      snapshots[tenantId ?? 'default'] = snapshot;
    },
  };
};

const renderWithProvider = (store: AppStore, client: StubClient) => {
  setFeatureFlagClientFactory(() => client);

  render(
    <FlagsProvider store={store}>
      <span>flags</span>
    </FlagsProvider>,
  );
};

describe('FlagsProvider', () => {
  afterEach(() => {
    resetFeatureFlagClientFactory();
  });

  it('carrega flags iniciais para o tenant corrente', async () => {
    const store = createAppStore(undefined, {
      tenant: { id: 'tenant-alfa', previousId: null },
      theme: {
        id: null,
        version: null,
        tokens: {},
        lastUpdatedAt: null,
      },
      session: {
        user: null,
        featureFlags: {},
      },
    });

    const client = createStubClient({
      'tenant-alfa': {
        'foundation.fsd': true,
        'design-system.theming': false,
      },
      default: {
        'foundation.fsd': false,
        'design-system.theming': false,
      },
    });

    renderWithProvider(store, client);

    await waitFor(() => {
      expect(store.getState().session.featureFlags).toEqual({
        'foundation.fsd': true,
        'design-system.theming': false,
      });
    });
  });

  it('recarrega flags ao trocar de tenant', async () => {
    const store = createAppStore(undefined, {
      tenant: { id: 'tenant-alfa', previousId: null },
      theme: {
        id: null,
        version: null,
        tokens: {},
        lastUpdatedAt: null,
      },
      session: {
        user: null,
        featureFlags: {},
      },
    });

    const client = createStubClient({
      'tenant-alfa': {
        'foundation.fsd': true,
        'design-system.theming': true,
      },
      'tenant-beta': {
        'foundation.fsd': false,
        'design-system.theming': true,
      },
    });

    renderWithProvider(store, client);

    await waitFor(() => {
      expect(client.getSnapshot).toHaveBeenCalledWith('tenant-alfa');
    });

    act(() => {
      void store.getState().setTenant('tenant-beta');
    });

    await waitFor(() => {
      expect(client.getSnapshot).toHaveBeenLastCalledWith('tenant-beta');
    });

    await waitFor(() => {
      expect(store.getState().session.featureFlags).toEqual({
        'foundation.fsd': false,
        'design-system.theming': true,
      });
    });
  });

  it('encerra o client ao desmontar', async () => {
    const store = createAppStore();
    const client = createStubClient({
      default: {
        'foundation.fsd': false,
        'design-system.theming': false,
      },
    });

    setFeatureFlagClientFactory(() => client);

    const { unmount } = render(
      <FlagsProvider store={store}>
        <span>flags</span>
      </FlagsProvider>,
    );

    await waitFor(() => {
      expect(client.getSnapshot).toHaveBeenCalled();
    });

    unmount();

    expect(client.dispose).toHaveBeenCalled();
  });
});
