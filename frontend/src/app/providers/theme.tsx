import { useEffect } from 'react';

import { env } from '../../shared/config/env';
import { applyTenantTheme, loadTenantTheme } from '../../shared/config/theme/registry';
import { useAppStore } from '../store';

type Props = {
  children: React.ReactNode;
};

const THEME_FALLBACK_WARNING =
  '[theming] Falha ao carregar tokens do tenant; aplicando fallback seguro para o tenant padrão.';

export const ThemeProvider = ({ children }: Props): JSX.Element => {
  const tenantId = useAppStore((state) => state.tenant.id);

  useEffect(() => {
    let cancelled = false;
    const targetTenant = tenantId ?? env.TENANT_DEFAULT;

    const applyTheme = async (tenant: string) => {
      try {
        const theme = await loadTenantTheme(tenant, env.TENANT_DEFAULT);
        if (!cancelled) {
          applyTenantTheme({ ...theme, tenantId: tenant });
        }
      } catch (error) {
        if (!cancelled) {
          // eslint-disable-next-line no-console
          console.warn(THEME_FALLBACK_WARNING, error);
        }
        if (tenant !== env.TENANT_DEFAULT) {
          const fallback = await loadTenantTheme(env.TENANT_DEFAULT, env.TENANT_DEFAULT);
          if (!cancelled) {
            applyTenantTheme({ ...fallback, tenantId: env.TENANT_DEFAULT });
          }
        }
      }
    };

    void applyTheme(targetTenant);
    return () => {
      cancelled = true;
    };
  }, [tenantId]);

  return <>{children}</>;
};
