import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  FeatureFlagKey,
  createFeatureFlagClient,
  resetFeatureFlagClientFactory,
  setFeatureFlagClientFactory,
} from './flags';

type StubSnapshot = Partial<Record<FeatureFlagKey, boolean>>;

const createStubClient = (snapshot: StubSnapshot) => ({
  getSnapshot: vi.fn(async (_tenantId: string | null) => ({
    'foundation.fsd': snapshot['foundation.fsd'] ?? false,
    'design-system.theming': snapshot['design-system.theming'] ?? false,
  })),
  subscribe: vi.fn(() => () => undefined),
  dispose: vi.fn(),
});

describe('createFeatureFlagClient', () => {
  beforeEach(() => {
    resetFeatureFlagClientFactory();
  });

  it('retorna fallback por tenant quando nenhum client remoto é configurado', async () => {
    const client = createFeatureFlagClient();

    const fallbackAlfa = await client.getSnapshot('tenant-alfa');
    expect(fallbackAlfa['foundation.fsd']).toBe(true);
    expect(fallbackAlfa['design-system.theming']).toBe(true);

    const fallbackBeta = await client.getSnapshot('tenant-beta');
    expect(fallbackBeta['foundation.fsd']).toBe(false);
    expect(fallbackBeta['design-system.theming']).toBe(false);

    const fallbackNull = await client.getSnapshot(null);
    expect(fallbackNull['foundation.fsd']).toBe(false);
    expect(fallbackNull['design-system.theming']).toBe(false);
  });

  it('permite injetar client customizado para leitura de flags', async () => {
    const stub = createStubClient({
      'foundation.fsd': true,
      'design-system.theming': false,
    });

    setFeatureFlagClientFactory(() => stub);

    const client = createFeatureFlagClient();
    const snapshot = await client.getSnapshot('tenant-beta');

    expect(stub.getSnapshot).toHaveBeenCalledWith('tenant-beta');
    expect(snapshot).toEqual({
      'foundation.fsd': true,
      'design-system.theming': false,
    });

    await client.dispose();
    expect(stub.dispose).toHaveBeenCalled();
  });
});
