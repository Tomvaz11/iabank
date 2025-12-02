export type TenantThemeCategories = {
  foundation: Record<string, string>;
  semantic: Record<string, string>;
  component: Record<string, string>;
};

export type TenantTheme = {
  tenantId: string;
  version: string;
  categories: TenantThemeCategories;
};

type TenantLoader = () => Promise<unknown>;

const tenantLoaders: Record<string, TenantLoader> = {
  'tenant-default': () => import('./tokens/tenant-default.json'),
  'tenant-alfa': () => import('./tokens/tenant-alfa.json'),
  'tenant-beta': () => import('./tokens/tenant-beta.json'),
};

export const ACTIVE_TENANTS = ['tenant-alfa', 'tenant-beta'] as const;

const DEFAULT_TENANT_FALLBACK = import.meta.env.VITE_TENANT_DEFAULT || 'tenant-default';

export const supportedTenants = (tenantDefault: string): string[] =>
  Array.from(new Set([tenantDefault, ...Object.keys(tenantLoaders)]));

const toRecord = (value: unknown): Record<string, string> => {
  if (!value || typeof value !== 'object') {
    return {};
  }
  return { ...(value as Record<string, string>) };
};

const normalizeTheme = (input: unknown, tenantAlias: string): TenantTheme => {
  const root = (input as { default?: unknown })?.default ?? input;
  const payload = (root as { payload?: unknown })?.payload ?? root;
  const maybe = payload as Partial<TenantTheme> & {
    categories?: Partial<TenantThemeCategories>;
  };

  if (!maybe || typeof maybe !== 'object' || !maybe.categories) {
    throw new Error(`Tokens de tema inválidos para ${tenantAlias}`);
  }

  return {
    tenantId: maybe.tenantId ?? tenantAlias,
    version: maybe.version ?? '0.0.0',
    categories: {
      foundation: toRecord(maybe.categories.foundation),
      semantic: toRecord(maybe.categories.semantic),
      component: toRecord(maybe.categories.component),
    },
  };
};

export const loadTenantTheme = async (
  tenantAlias: string,
  fallbackTenant: string = DEFAULT_TENANT_FALLBACK,
): Promise<TenantTheme> => {
  const loader =
    tenantLoaders[tenantAlias] ??
    tenantLoaders[fallbackTenant] ??
    tenantLoaders['tenant-default'];

  const module = await loader();
  return normalizeTheme(module, tenantAlias);
};

const toCssVarName = (token: string): string => `--${token.replace(/\./g, '-')}`;

const flattenTokens = (theme: TenantTheme): Record<string, string> =>
  Object.values(theme.categories).reduce<Record<string, string>>((acc, category) => {
    Object.entries(category).forEach(([token, value]) => {
      acc[token] = value;
    });
    return acc;
  }, {});

let appliedVars: string[] = [];

export const applyTenantTheme = (theme: TenantTheme): void => {
  if (typeof document === 'undefined') {
    return;
  }

  const root = document.documentElement;
  appliedVars.forEach((name) => root.style.removeProperty(name));

  const tokens = flattenTokens(theme);
  appliedVars = Object.entries(tokens).map(([token, value]) => {
    const varName = toCssVarName(token);
    root.style.setProperty(varName, value);
    return varName;
  });

  root.setAttribute('data-tenant', theme.tenantId);
};
