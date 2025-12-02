import { render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../shared/config/env', () => ({
  env: {
    TENANT_DEFAULT: 'tenant-default',
    API_BASE_URL: 'https://api.iabank.test',
    OTEL_EXPORTER_OTLP_ENDPOINT: 'http://localhost:4318',
    OTEL_SERVICE_NAME: 'frontend-foundation',
    OTEL_RESOURCE_ATTRIBUTES: {},
    FOUNDATION_CSP_NONCE: 'nonce',
    FOUNDATION_TRUSTED_TYPES_POLICY: 'foundation-ui',
    FOUNDATION_TRUSTED_TYPES_ROLLOUT_START: '2025-09-01T00:00:00.000Z',
    FOUNDATION_PGCRYPTO_KEY: 'dev-only',
  },
}));

const mocks = vi.hoisted(() => ({
  loadTenantTheme: vi.fn(),
  applyTenantTheme: vi.fn(),
}));

vi.mock('../../shared/config/theme/registry', () => ({
  loadTenantTheme: mocks.loadTenantTheme,
  applyTenantTheme: mocks.applyTenantTheme,
}));

vi.mock('../store', () => ({
  useAppStore:
    (selector: (state: { tenant: { id: string | null } }) => unknown) =>
      selector({ tenant: { id: 'tenant-alfa' } }),
}));

import * as registry from '../../shared/config/theme/registry';
import { ThemeProvider } from './theme';

describe('ThemeProvider', () => {
  afterEach(() => {
    mocks.loadTenantTheme.mockReset();
    mocks.applyTenantTheme.mockReset();
    vi.restoreAllMocks();
  });

  it('carrega tokens do tenant atual e aplica variáveis CSS', async () => {
    mocks.loadTenantTheme.mockResolvedValue({
      tenantId: 'tenant-alfa',
      version: '1.0.0',
      categories: {
        foundation: { 'color.brand.primary': '#123456' },
        semantic: {},
        component: {},
      },
    });

    render(
      <ThemeProvider>
        <div>child</div>
      </ThemeProvider>,
    );

    await waitFor(() =>
      expect(registry.applyTenantTheme).toHaveBeenCalledWith(
        expect.objectContaining({ tenantId: 'tenant-alfa' }),
      ),
    );
  });

  it('aplica fallback seguro quando carregamento do tenant falha', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    mocks.loadTenantTheme
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce({
        tenantId: 'tenant-default',
        version: '1.0.0',
        categories: {
          foundation: { 'color.brand.primary': '#abcdef' },
          semantic: {},
          component: {},
        },
      });

    render(
      <ThemeProvider>
        <div>child</div>
      </ThemeProvider>,
    );

    await waitFor(() =>
      expect(registry.applyTenantTheme).toHaveBeenLastCalledWith(
        expect.objectContaining({ tenantId: 'tenant-default' }),
      ),
    );
  });
});
