import { useCallback, useEffect, useMemo, useState, type ChangeEvent } from 'react';

import { env } from '../../shared/config/env';
import { useAppStore } from '../store';

type LocationState = {
  pathname: string;
  searchParams: URLSearchParams;
};

const FALLBACK_TENANTS = ['tenant-alfa', 'tenant-beta'] as const;

const SUPPORTED_TENANTS = Array.from(
  new Set<string>([env.TENANT_DEFAULT, ...FALLBACK_TENANTS]),
);

const DEFAULT_FEATURE = 'foundation-scaffold';

const parseLocation = (): LocationState => {
  if (typeof window === 'undefined') {
    return {
      pathname: '/foundation/scaffold',
      searchParams: new URLSearchParams(),
    };
  }

  return {
    pathname: window.location.pathname,
    searchParams: new URLSearchParams(window.location.search),
  };
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

  const tenantId = ensureTenant(locationState.searchParams.get('tenant'));
  const featureSlug = ensureFeature(locationState.searchParams.get('feature'));

  useEffect(() => {
    const params = new URLSearchParams(locationState.searchParams);
    let mutated = false;

    if (params.get('tenant') !== tenantId) {
      params.set('tenant', tenantId);
      mutated = true;
    }

    if (params.get('feature') !== featureSlug) {
      params.set('feature', featureSlug);
      mutated = true;
    }

    if (mutated && typeof window !== 'undefined') {
      const queryString = params.toString();
      const nextUrl = `${locationState.pathname}${queryString ? `?${queryString}` : ''}`;
      window.history.replaceState(window.history.state, '', nextUrl);
      setLocationState({
        pathname: locationState.pathname,
        searchParams: params,
      });
    }
  }, [featureSlug, locationState.pathname, locationState.searchParams, tenantId]);

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
      params.set('tenant', ensureTenant(nextTenant));
      params.set('feature', featureSlug);

      if (typeof window !== 'undefined') {
        const queryString = params.toString();
        const nextUrl = `/foundation/scaffold${queryString ? `?${queryString}` : ''}`;
        window.history.replaceState(window.history.state, '', nextUrl);
      }

      setLocationState({
        pathname: '/foundation/scaffold',
        searchParams: params,
      });
    },
    [featureSlug, locationState.searchParams],
  );

  if (locationState.pathname !== '/foundation/scaffold') {
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
