import { useEffect, useMemo, useRef } from 'react';

import type { AppStore } from '../store';
import { useAppStore } from '../store';
import {
  createFeatureFlagClient,
  resetFeatureFlagClientFactory,
  setFeatureFlagClientFactory,
  type FeatureFlagClient,
  type FeatureFlagSnapshot,
} from '../../shared/config/flags';
import { env } from '../../shared/config/env';

type Props = {
  children: React.ReactNode;
  store?: AppStore;
};

const useResolvedTenantId = (store: AppStore): string => {
  const tenantId = store((state) => state.tenant.id);
  return useMemo(() => tenantId ?? env.TENANT_DEFAULT, [tenantId]);
};

export const FlagsProvider = ({ children, store = useAppStore }: Props) => {
  const resolvedTenantId = useResolvedTenantId(store);
  const setFeatureFlags = store((state) => state.setFeatureFlags);
  const clientRef = useRef<FeatureFlagClient | null>(null);

  useEffect(() => {
    const client = createFeatureFlagClient();
    clientRef.current = client;

    return () => {
      const current = clientRef.current;
      clientRef.current = null;

      if (current) {
        void current.dispose();
      }
    };
  }, []);

  useEffect(() => {
    const client = clientRef.current;
    if (!client) {
      return undefined;
    }

    let cancelled = false;

    const applySnapshot = (snapshot: FeatureFlagSnapshot) => {
      if (!cancelled) {
        setFeatureFlags(snapshot);
      }
    };

    const refresh = async () => {
      const snapshot = await client.getSnapshot(resolvedTenantId);
      applySnapshot(snapshot);
    };

    void refresh();

    const unsubscribe = client.subscribe(() => {
      void refresh();
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [resolvedTenantId, setFeatureFlags]);

  return <>{children}</>;
};

export { createFeatureFlagClient, setFeatureFlagClientFactory, resetFeatureFlagClientFactory };
