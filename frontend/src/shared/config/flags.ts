// Evita incluir o SDK de flags no bundle inicial; carregamos sob demanda
type IConfigCatClient = {
  getValueAsync<T>(key: string, defaultValue: T, user?: unknown): Promise<T>;
  on(event: 'configChanged', listener: () => void): void;
  off(event: 'configChanged', listener: () => void): void;
  dispose(): void;
};

import { env } from './env';

export const FEATURE_FLAG_KEYS = ['foundation.fsd', 'design-system.theming'] as const;

export type FeatureFlagKey = (typeof FEATURE_FLAG_KEYS)[number];

export type FeatureFlagSnapshot = Record<FeatureFlagKey, boolean>;

type TenantRollout = {
  default: boolean;
  tenants?: Record<string, boolean>;
};

export const DEFAULT_FLAG_ROLLOUTS: Record<FeatureFlagKey, TenantRollout> = {
  'foundation.fsd': {
    default: false,
    tenants: {
      'tenant-alfa': true,
    },
  },
  'design-system.theming': {
    default: false,
    tenants: {
      'tenant-alfa': true,
    },
  },
};

export type FeatureFlagClient = {
  getSnapshot: (tenantId: string | null) => Promise<FeatureFlagSnapshot>;
  subscribe: (listener: () => void) => () => void;
  dispose: () => Promise<void> | void;
};

type ClientFactory = () => FeatureFlagClient;

const resolveTenantRollout = (rollout: TenantRollout, tenantId: string | null): boolean => {
  if (!tenantId) {
    return rollout.default;
  }

  const overrides = rollout.tenants ?? {};
  if (tenantId in overrides) {
    return overrides[tenantId];
  }

  return rollout.default;
};

const buildFallbackSnapshot = (tenantId: string | null): FeatureFlagSnapshot =>
  FEATURE_FLAG_KEYS.reduce<FeatureFlagSnapshot>((snapshot, key) => {
    snapshot[key] = resolveTenantRollout(DEFAULT_FLAG_ROLLOUTS[key], tenantId);
    return snapshot;
  }, {} as FeatureFlagSnapshot);

const createFallbackClient = (): FeatureFlagClient => ({
  getSnapshot: async (tenantId) => buildFallbackSnapshot(tenantId),
  subscribe: () => () => undefined,
  dispose: async () => undefined,
});

const evaluateWithClient = async (
  client: IConfigCatClient,
  tenantId: string | null,
): Promise<FeatureFlagSnapshot> => {
  const snapshot: FeatureFlagSnapshot = {} as FeatureFlagSnapshot;
  const defaultSnapshot = buildFallbackSnapshot(tenantId);
  const user =
    tenantId !== null
      ? {
          identifier: tenantId,
          custom: {
            tenant: tenantId,
          },
        }
      : undefined;

  await Promise.all(
    FEATURE_FLAG_KEYS.map(async (key) => {
      const defaultValue = defaultSnapshot[key];

      try {
        const value = await client.getValueAsync<boolean>(key, defaultValue, user);
        snapshot[key] = typeof value === 'boolean' ? value : defaultValue;
      } catch (error) {
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.warn('[flags] fallback aplicado ao resolver flag', { key, error });
        }
        snapshot[key] = defaultValue;
      }
    }),
  );

  return snapshot;
};

const createConfigCatClient = (sdkKey: string): FeatureFlagClient => {
  // Nota: import dinâmico para permitir code-splitting
  // O módulo só é carregado quando há SDK key configurada
  let clientPromise: Promise<IConfigCatClient> | null = null;
  const getClientInstance = async (): Promise<IConfigCatClient> => {
    if (!clientPromise) {
      clientPromise = import('configcat-js').then((mod) => {
        const { getClient, PollingMode } = mod as unknown as {
          getClient: (
            key: string,
            mode: unknown,
            opts: { pollIntervalSeconds: number },
          ) => IConfigCatClient;
          PollingMode: { AutoPoll: unknown };
        };
        return getClient(sdkKey, PollingMode.AutoPoll, { pollIntervalSeconds: 60 });
      });
    }
    return clientPromise;
  };

  const listeners = new Set<() => void>();

  const notify = () => {
    listeners.forEach((listener) => {
      try {
        listener();
      } catch (error) {
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.warn('[flags] listener execution falhou', error);
        }
      }
    });
  };

  const onConfigChanged = () => {
    notify();
  };

  void getClientInstance().then((client) => client.on('configChanged', onConfigChanged));

  return {
    getSnapshot: async (tenantId) => evaluateWithClient(await getClientInstance(), tenantId),
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    dispose: async () => {
      listeners.clear();
      const client = await getClientInstance().catch(() => null);
      if (client) {
        client.off('configChanged', onConfigChanged);
        client.dispose();
      }
    },
  };
};

const resolveDefaultFactory = (): FeatureFlagClient => {
  if (!env.CONFIGCAT_SDK_KEY) {
    return createFallbackClient();
  }

  return createConfigCatClient(env.CONFIGCAT_SDK_KEY);
};

let activeFactory: ClientFactory = resolveDefaultFactory;

export const setFeatureFlagClientFactory = (factory: ClientFactory) => {
  activeFactory = factory;
};

export const resetFeatureFlagClientFactory = () => {
  activeFactory = resolveDefaultFactory;
};

export const createFeatureFlagClient = (): FeatureFlagClient => {
  return activeFactory();
};
