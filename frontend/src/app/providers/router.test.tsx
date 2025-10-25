import { describe, expect, it, beforeEach, vi } from 'vitest';
import { screen, within, fireEvent } from '../../tests/utils/test-utils';
import { renderWithProviders } from '../../tests/utils/test-utils';

// Garante que o módulo env use as variáveis definidas no teste
const setupEnv = () => {
  process.env.VITE_API_BASE_URL = 'https://api.iabank.test';
  process.env.VITE_TENANT_DEFAULT = 'tenant-alfa';
  process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT = 'https://otel.iabank.test';
  process.env.VITE_OTEL_SERVICE_NAME = 'frontend-foundation';
  process.env.VITE_OTEL_RESOURCE_ATTRIBUTES = 'service.namespace=iabank,service.version=0.1.0';
  process.env.VITE_FOUNDATION_CSP_NONCE = 'nonce-value';
  process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY = 'foundation-ui';
  process.env.VITE_FOUNDATION_PGCRYPTO_KEY = 'pgcrypto-key';
};

describe('RouterProvider (T034)', () => {
  beforeEach(() => {
    // Limpa cache de módulos para reavaliar env a cada teste
    vi.resetModules();
    setupEnv();
  });

  it('renderiza rota /foundation/scaffold com tenant e feature da query', async () => {
    window.history.pushState({}, '', '/foundation/scaffold?tenant=tenant-alfa&feature=loan-tracking');

    const { RouterProvider } = await import('./router');

    renderWithProviders(<RouterProvider />);

    const summary = await screen.findByTestId('scaffold-summary');
    expect(screen.getByText(/Feature:/)).toBeInTheDocument();
    expect(screen.getByText(/Tenant:/)).toBeInTheDocument();
    expect(screen.getByText('loan-tracking')).toBeInTheDocument();
    expect(within(summary).getByText('tenant-alfa')).toBeInTheDocument();
  });

  it('troca de tenant atualiza a URL sem recarregar a página', async () => {
    window.history.pushState({}, '', '/foundation/scaffold?tenant=tenant-alfa&feature=loan-tracking');

    const { RouterProvider } = await import('./router');

    renderWithProviders(<RouterProvider />);

    const select = (await screen.findByTestId('tenant-switcher')) as HTMLSelectElement;
    // Simula mudança de tenant
    fireEvent.change(select, { target: { value: 'tenant-beta' } });

    expect(window.location.pathname).toBe('/foundation/scaffold');
    expect(window.location.search).toContain('tenant=tenant-beta');
    expect(window.location.search).toContain('feature=loan-tracking');
  });

  it('rota desconhecida renderiza landing sem explodir', async () => {
    window.history.pushState({}, '', '/');
    const { RouterProvider } = await import('./router');
    renderWithProviders(<RouterProvider />);
    expect(screen.getByText('Fundação Frontend IABank')).toBeInTheDocument();
  });
});
