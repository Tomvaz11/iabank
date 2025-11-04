import { afterEach, describe, expect, it, vi } from 'vitest';

describe('createFeatureFlagClient com ConfigCat', () => {
  afterEach(() => {
    vi.resetModules();
    vi.doUnmock('configcat-js');
    vi.doUnmock('./env');
    vi.clearAllMocks();
  });

  it('utiliza client remoto e aplica fallback em erros', async () => {
    const listeners = new Set<() => void>();

    const getValueAsync = vi.fn(async () => {
      throw new Error('ConfigCat indisponível');
    }) as unknown as ((...args: unknown[]) => Promise<unknown>) & {
      mockImplementationOnce: (impl: (...args: unknown[]) => unknown | Promise<unknown>) => unknown;
    };
    getValueAsync.mockImplementationOnce(async () => 'valor-inválido');

    const on = vi.fn((event: string, handler: () => void) => {
      if (event === 'configChanged') {
        listeners.add(handler);
      }
    });

    const off = vi.fn((event: string, handler: () => void) => {
      if (event === 'configChanged') {
        listeners.delete(handler);
      }
    });

    const dispose = vi.fn();

    vi.doMock('configcat-js', () => ({
      getClient: vi.fn(() => ({
        getValueAsync,
        on,
        off,
        dispose,
      })),
      PollingMode: { AutoPoll: 'AutoPoll' },
    }));

    vi.doMock('./env', () => ({
      env: {
        CONFIGCAT_SDK_KEY: 'sdk-local-test',
      },
    }));

    const mod = await import('./flags');
    const client = mod.createFeatureFlagClient();

    const snapshot = await client.getSnapshot('tenant-beta');

    expect(snapshot).toEqual({
      'foundation.fsd': false,
      'design-system.theming': false,
    });

    const listener = vi.fn();
    const unsubscribe = client.subscribe(listener);

    listeners.forEach((handler) => handler());
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    await client.dispose();

    expect(dispose).toHaveBeenCalled();
    expect(on).toHaveBeenCalledWith('configChanged', expect.any(Function));
    expect(off).toHaveBeenCalledWith('configChanged', expect.any(Function));

    mod.resetFeatureFlagClientFactory();
  });
});
