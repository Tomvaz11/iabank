import { create } from 'zustand';
import type { StoreApi, UseBoundStore } from 'zustand';

import { resetOnTenantChange, tenantQueryClient } from '../../shared/api/queryClient';

type TenantSlice = {
  id: string | null;
  previousId: string | null;
};

type ThemeSlice = {
  id: string | null;
  version: string | null;
  tokens: Record<string, string>;
  lastUpdatedAt: string | null;
};

type SessionSlice = {
  user: {
    id: string;
    name: string;
    roles: string[];
    email?: string;
  } | null;
  featureFlags: Record<string, boolean>;
};

type InitialSlices = {
  tenant: TenantSlice;
  theme: ThemeSlice;
  session: SessionSlice;
};

type SetSessionPayload = {
  user: NonNullable<SessionSlice['user']>;
  featureFlags: Record<string, boolean>;
};

export type AppStoreState = InitialSlices & {
  setTenant: (tenantId: string | null) => Promise<void>;
  setTheme: (theme: Partial<Omit<ThemeSlice, 'tokens'>> & { tokens: Record<string, string> }) => void;
  resetTheme: () => void;
  setSession: (session: SetSessionPayload) => void;
  setFeatureFlags: (flags: Record<string, boolean>) => void;
  clearSession: () => void;
  resetSensitiveState: () => void;
};

export type AppStore = UseBoundStore<StoreApi<AppStoreState>> & {
  getInitialSlices: () => InitialSlices;
};

const createInitialSlices = (): InitialSlices => ({
  tenant: {
    id: null,
    previousId: null,
  },
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

const cloneSlices = (slices: InitialSlices): InitialSlices => ({
  tenant: { ...slices.tenant },
  theme: {
    ...slices.theme,
    tokens: { ...slices.theme.tokens },
  },
  session: {
    ...slices.session,
    featureFlags: { ...slices.session.featureFlags },
  },
});

export const createAppStore = (
  queryClient = tenantQueryClient,
  baseState: InitialSlices = createInitialSlices(),
): AppStore => {
  const useBoundStore = create<AppStoreState>((set, get) => ({
    ...cloneSlices(baseState),
    setTenant: async (nextTenantId: string | null) => {
      const currentTenant = get().tenant.id;

      if (currentTenant === nextTenantId) {
        return;
      }

      await resetOnTenantChange(queryClient);

      set((state) => ({
        tenant: {
          id: nextTenantId,
          previousId: state.tenant.id,
        },
      }));

      get().resetSensitiveState();
    },
    setTheme: (theme) => {
      set({
        theme: {
          id: theme.id ?? get().theme.id,
          version: theme.version ?? get().theme.version,
          tokens: { ...theme.tokens },
          lastUpdatedAt: theme.lastUpdatedAt ?? null,
        },
      });
    },
    resetTheme: () => {
      set({
        theme: cloneSlices(baseState).theme,
      });
    },
    setSession: (session) => {
      set({
        session: {
          user: session.user,
          featureFlags: { ...session.featureFlags },
        },
      });
    },
    setFeatureFlags: (flags) => {
      set({
        session: {
          ...get().session,
          featureFlags: { ...flags },
        },
      });
    },
    clearSession: () => {
      set({
        session: cloneSlices(baseState).session,
      });
    },
    resetSensitiveState: () => {
      const initial = cloneSlices(baseState);
      set({
        session: initial.session,
        theme: initial.theme,
      });
    },
  }));

  const store = useBoundStore as AppStore;
  store.getInitialSlices = () => cloneSlices(baseState);

  return store;
};

export const useAppStore = createAppStore();
