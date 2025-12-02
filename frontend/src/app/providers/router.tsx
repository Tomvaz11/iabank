import { useCallback, useEffect, useMemo, useState, type ChangeEvent } from 'react';

import { env } from '../../shared/config/env';
import { supportedTenants as resolveSupportedTenants } from '../../shared/config/theme/registry';
import { useAppStore } from '../store';

const SUPPORTED_TENANTS = resolveSupportedTenants(env.TENANT_DEFAULT);

const DEFAULT_FEATURE = 'foundation-scaffold';

type TenantResolution = 'hostname' | 'path' | 'fallback';

type LocationState = {
  routePathname: string;
  searchParams: URLSearchParams;
  tenantId: string;
  tenantResolution: TenantResolution;
  hostname: string;
  isLocal: boolean;
  pathTenantId: string | null;
};

const ensureTenant = (value: string | null): string => {
  if (value && SUPPORTED_TENANTS.includes(value)) {
    return value;
  }
  return env.TENANT_DEFAULT;
};

const ensureFeature = (value: string | null): string => {
  if (value && /^[a-z0-9-]+$/.test(value)) {
    return value;
  }
  return DEFAULT_FEATURE;
};

const normalizeRoutePathname = (value: string): string => {
  if (!value) return '/';
  return value.startsWith('/') ? value : `/${value}`;
};

const isLocalHost = (hostname: string): boolean =>
  hostname === 'localhost' ||
  hostname === '127.0.0.1' ||
  hostname === '::1' ||
  hostname.endsWith('.local');

const extractTenantFromHostname = (hostname: string): string | null => {
  const parts = hostname.split('.');
  if (parts.length < 2) {
    return null;
  }

  const [maybeTenant] = parts;
  return maybeTenant || null;
};

const extractTenantFromPath = (
  pathname: string,
): { tenantId: string; routePathname: string } | null => {
  const match = pathname.match(/^\/t\/([^/]+)(\/.*)?$/);
  if (!match) {
    return null;
  }

  const [, tenantId, rest] = match;
  return {
    tenantId,
    routePathname: normalizeRoutePathname(rest ?? '/'),
  };
};

const parseLocation = (): LocationState => {
  if (typeof window === 'undefined') {
    return {
      routePathname: '/foundation/scaffold',
      searchParams: new URLSearchParams(),
      tenantId: env.TENANT_DEFAULT,
      tenantResolution: 'fallback',
      hostname: 'localhost',
      isLocal: true,
      pathTenantId: null,
    };
  }

  const { pathname, search, hostname } = window.location;
  const searchParams = new URLSearchParams(search);
  const pathTenant = extractTenantFromPath(pathname);
  const tenantFromHost = extractTenantFromHostname(hostname);
  const isLocal = isLocalHost(hostname);

  let tenantId = env.TENANT_DEFAULT;
  let tenantResolution: TenantResolution = 'fallback';

  if (!isLocal && tenantFromHost) {
    tenantId = ensureTenant(tenantFromHost);
    tenantResolution = 'hostname';
  } else if (isLocal && pathTenant?.tenantId) {
    tenantId = ensureTenant(pathTenant.tenantId);
    tenantResolution = 'path';
  }

  const routePathname = normalizeRoutePathname(
    pathTenant?.routePathname ?? pathname ?? '/foundation/scaffold',
  );

  return {
    routePathname,
    searchParams,
    tenantId,
    tenantResolution,
    hostname,
    isLocal,
    pathTenantId: pathTenant?.tenantId ?? null,
  };
};

const formatFeatureTitle = (slug: string): string =>
  slug
    .split(/[-_]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

type ScaffoldRouteProps = {
  tenantId: string;
  featureSlug: string;
  onTenantChange: (tenantId: string) => void;
};

const ScaffoldRoute = ({ tenantId, featureSlug, onTenantChange }: ScaffoldRouteProps) => {
  const featureTitle = useMemo(() => formatFeatureTitle(featureSlug), [featureSlug]);
  const summaryItems = useMemo(
    () => [
      { label: 'Feature', value: featureSlug },
      { label: 'Tenant', value: tenantId },
    ],
    [featureSlug, tenantId],
  );

  const handleTenantChange = useCallback(
    (event: ChangeEvent<HTMLSelectElement>) => {
      onTenantChange(event.target.value);
    },
    [onTenantChange],
  );

  return (
    <main className="scaffold-shell">
      <header className="scaffold-header">
        <h1>{featureTitle}</h1>
        <div className="scaffold-tenant-selector">
          <label htmlFor="tenant-switcher">Tenant</label>
          <select
            id="tenant-switcher"
            data-testid="tenant-switcher"
            value={tenantId}
            onChange={handleTenantChange}
          >
            {SUPPORTED_TENANTS.map((tenant) => (
              <option key={tenant} value={tenant}>
                {tenant}
              </option>
            ))}
          </select>
        </div>
      </header>

      <section className="scaffold-summary" data-testid="scaffold-summary">
        {summaryItems.map((item) => (
          <p key={item.label}>
            <strong>{item.label}:</strong> {item.value}
          </p>
        ))}
      </section>
    </main>
  );
};

const LandingRoute = () => (
  <main className="scaffold-shell">
    <header className="scaffold-header">
      <h1>Fundação Frontend IABank</h1>
      <p>Escolha uma rota para iniciar o scaffolding multi-tenant.</p>
    </header>
  </main>
);

export const RouterProvider = (): JSX.Element => {
  const [locationState, setLocationState] = useState<LocationState>(() => parseLocation());
  const setTenant = useAppStore((state) => state.setTenant);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const handlePopState = () => {
      setLocationState(parseLocation());
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const tenantId = ensureTenant(locationState.tenantId);
  const featureSlug = ensureFeature(locationState.searchParams.get('feature'));

  const buildTenantAwarePathname = useCallback(
    (tenant: string) => {
      if (locationState.isLocal) {
        return `/t/${tenant}${normalizeRoutePathname(locationState.routePathname)}`;
      }
      return normalizeRoutePathname(locationState.routePathname);
    },
    [locationState.isLocal, locationState.routePathname],
  );

  useEffect(() => {
    const params = new URLSearchParams(locationState.searchParams);
    let mutated = false;

    if (params.get('feature') !== featureSlug) {
      params.set('feature', featureSlug);
      mutated = true;
    }

    if (params.has('tenant')) {
      params.delete('tenant');
      mutated = true;
    }

    const nextPathname = buildTenantAwarePathname(tenantId);

    const currentUrl =
      typeof window !== 'undefined'
        ? `${window.location.pathname}${window.location.search}`
        : '';
    const nextQueryString = params.toString();
    const nextUrl = `${nextPathname}${nextQueryString ? `?${nextQueryString}` : ''}`;

    if ((mutated || nextUrl !== currentUrl) && typeof window !== 'undefined') {
      window.history.replaceState(window.history.state, '', nextUrl);
      setLocationState(parseLocation());
    }
  }, [buildTenantAwarePathname, featureSlug, locationState.searchParams, tenantId]);

  useEffect(() => {
    void setTenant(tenantId);
  }, [setTenant, tenantId]);

  useEffect(() => {
    if (typeof document === 'undefined') {
      return;
    }
    document.documentElement.setAttribute('data-tenant', tenantId);
    return () => {
      document.documentElement.removeAttribute('data-tenant');
    };
  }, [tenantId]);

  const handleTenantChange = useCallback(
    (nextTenant: string) => {
      const params = new URLSearchParams(locationState.searchParams);
      params.delete('tenant');
      params.set('feature', featureSlug);
      const nextTenantId = ensureTenant(nextTenant);
      const queryString = params.toString();

      if (typeof window !== 'undefined') {
        const tenantPath = buildTenantAwarePathname(nextTenantId);
        if (!locationState.isLocal && locationState.hostname.includes('.')) {
          const [, ...rest] = locationState.hostname.split('.');
          if (rest.length > 0) {
            const domain = rest.join('.');
            const nextHost = `${nextTenantId}.${domain}`;
            const nextUrl = `${window.location.protocol}//${nextHost}${tenantPath}${queryString ? `?${queryString}` : ''}`;
            window.location.assign(nextUrl);
            return;
          }
        }

        const nextUrl = `${tenantPath}${queryString ? `?${queryString}` : ''}`;
        window.history.replaceState(window.history.state, '', nextUrl);
      }

      setLocationState(parseLocation());
    },
    [
      buildTenantAwarePathname,
      featureSlug,
      locationState.hostname,
      locationState.isLocal,
      locationState.searchParams,
    ],
  );

  if (locationState.routePathname !== '/foundation/scaffold') {
    return <LandingRoute />;
  }

  return (
    <ScaffoldRoute
      tenantId={tenantId}
      featureSlug={featureSlug}
      onTenantChange={handleTenantChange}
    />
  );
};
