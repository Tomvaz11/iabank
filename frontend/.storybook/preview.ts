import type { Decorator, Preview } from '@storybook/react';

import '../src/styles.css';

import type { TenantAlias } from '../src/shared/config/theme/tenants';
import { applyTenantTheme } from '../src/shared/config/theme/registry';
import { tenantTokens } from '../src/shared/config/theme/tenants';

const DEFAULT_TENANT: TenantAlias = 'tenant-default';
const AVAILABLE_TENANTS = Object.keys(tenantTokens) as TenantAlias[];

const formatTenantLabel = (tenant: TenantAlias): string =>
  tenant.replace('tenant-', '').replace(/\b\w/g, (char) => char.toUpperCase());

const withTenant: Decorator = (Story, context) => {
  const tenant = (context.parameters.tenant ?? context.globals.tenant ?? DEFAULT_TENANT) as TenantAlias;
  const categories = tenantTokens[tenant] ?? tenantTokens[DEFAULT_TENANT];

  applyTenantTheme({
    tenantId: tenant,
    version: 'storybook-preview',
    categories,
  });

  return Story();
};

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    layout: 'fullscreen',
  },
  globalTypes: {
    tenant: {
      name: 'Tenant',
      description: 'Seleciona o tenant aplicado ao canvas do Storybook.',
      defaultValue: DEFAULT_TENANT,
      toolbar: {
        icon: 'globe',
        dynamicTitle: true,
        items: AVAILABLE_TENANTS.map((tenant) => ({
          value: tenant,
          title: formatTenantLabel(tenant),
        })),
      },
    },
  },
  decorators: [withTenant],
};

export default preview;
