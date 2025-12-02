import { afterEach, describe, expect, it, beforeEach, vi } from 'vitest';
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
  process.env.VITE_FOUNDATION_TRUSTED_TYPES_ROLLOUT_START = '2025-09-01T00:00:00.000Z';
  process.env.VITE_FOUNDATION_PGCRYPTO_KEY = 'pgcrypto-key';
};

const mockWindowLocation = (url: string) => {
  const parsed = new URL(url);
  const stubLocation: Partial<Location> & { assign?: (next: string) => void } = {
    href: parsed.href,
    protocol: parsed.protocol,
    host: parsed.host,
    hostname: parsed.hostname,
    pathname: parsed.pathname,
    search: parsed.search,
    hash: parsed.hash,
    origin: parsed.origin,
  };

  stubLocation.assign = (next: string) => {
    const nextUrl = new URL(next, parsed.origin);
    stubLocation.href = nextUrl.href;
    stubLocation.hostname = nextUrl.hostname;
    stubLocation.pathname = nextUrl.pathname;
    stubLocation.search = nextUrl.search;
    stubLocation.protocol = nextUrl.protocol;
    stubLocation.origin = nextUrl.origin;
  };

  Object.defineProperty(window, 'location', {
    value: stubLocation as Location,
    writable: true,
    configurable: true,
  });

  vi.spyOn(window.history, 'replaceState').mockImplementation((_data, _title, nextUrl) => {
    const next = typeof nextUrl === 'string' ? new URL(nextUrl, stubLocation.origin) : new URL(String(nextUrl), stubLocation.origin);
    stubLocation.href = next.href;
    stubLocation.pathname = next.pathname;
    stubLocation.search = next.search;
  });

  vi.spyOn(window.history, 'pushState').mockImplementation((_data, _title, nextUrl) => {
    const next = typeof nextUrl === 'string' ? new URL(nextUrl, stubLocation.origin) : new URL(String(nextUrl), stubLocation.origin);
    stubLocation.href = next.href;
    stubLocation.pathname = next.pathname;
    stubLocation.search = next.search;
  });

  return stubLocation;
};

describe('RouterProvider (T034)', () => {
  beforeEach(() => {
    // Limpa cache de módulos para reavaliar env a cada teste
    vi.resetModules();
    setupEnv();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('resolve tenant a partir do prefixo /t/:tenant em ambiente local', async () => {
    mockWindowLocation('http://localhost:4173/t/tenant-alfa/foundation/scaffold?feature=loan-tracking');

    const { RouterProvider } = await import('./router');

    renderWithProviders(<RouterProvider />);

    const summary = await screen.findByTestId('scaffold-summary');
    expect(screen.getByText(/Feature:/)).toBeInTheDocument();
    expect(screen.getByText(/Tenant:/)).toBeInTheDocument();
    expect(screen.getByText('loan-tracking')).toBeInTheDocument();
    expect(within(summary).getByText('tenant-alfa')).toBeInTheDocument();
    expect(window.location.pathname).toBe('/t/tenant-alfa/foundation/scaffold');
    expect(window.location.search).not.toContain('tenant=');
  });

  it('resolve tenant pelo subdomínio em produção sem depender de query string', async () => {
    mockWindowLocation('https://tenant-beta.iabank.test/foundation/scaffold?feature=loan-tracking');

    const { RouterProvider } = await import('./router');

    renderWithProviders(<RouterProvider />);

    const summary = await screen.findByTestId('scaffold-summary');
    expect(within(summary).getByText('tenant-beta')).toBeInTheDocument();
    expect(window.location.pathname).toBe('/foundation/scaffold');
    expect(window.location.search).toContain('feature=loan-tracking');
    expect(window.location.search).not.toContain('tenant=');
  });

  it('troca de tenant atualiza o prefixo sem usar query param', async () => {
    mockWindowLocation('http://127.0.0.1:4173/t/tenant-alfa/foundation/scaffold?feature=loan-tracking');

    const { RouterProvider } = await import('./router');

    renderWithProviders(<RouterProvider />);

    const select = (await screen.findByTestId('tenant-switcher')) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'tenant-beta' } });

    expect(window.location.pathname).toBe('/t/tenant-beta/foundation/scaffold');
    expect(window.location.search).toContain('feature=loan-tracking');
    expect(window.location.search).not.toContain('tenant=');
  });

  it('mantém fallback no tenant padrão ao receber rota inválida e limpa data-tenant ao desmontar', async () => {
    mockWindowLocation('http://localhost:4173/t/tenant-desconhecido/foundation/scaffold');
    const { RouterProvider } = await import('./router');

    const { unmount } = renderWithProviders(<RouterProvider />);

    const summary = await screen.findByTestId('scaffold-summary');
    expect(within(summary).getByText('tenant-alfa')).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute('data-tenant', 'tenant-alfa');

    unmount();
    expect(document.documentElement).not.toHaveAttribute('data-tenant');
  });

  it('em produção, troca de tenant usa subdomínio e navega via assign', async () => {
    const location = mockWindowLocation(
      'https://tenant-alfa.iabank.test/foundation/scaffold?feature=foundation-scaffold',
    ) as Location & { assign?: ReturnType<typeof vi.fn> };
    const assignSpy = vi.spyOn(location, 'assign' as never).mockImplementation(() => {});

    const { RouterProvider } = await import('./router');
    renderWithProviders(<RouterProvider />);

    const select = (await screen.findByTestId('tenant-switcher')) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'tenant-beta' } });

    expect(assignSpy).toHaveBeenCalledWith(
      'https://tenant-beta.iabank.test/foundation/scaffold?feature=foundation-scaffold',
    );
  });

  it('usa tenant padrão quando host não contém subdomínio', async () => {
    mockWindowLocation('https://www.iabank.test/foundation/scaffold?feature=foundation-scaffold');

    const { RouterProvider } = await import('./router');
    renderWithProviders(<RouterProvider />);

    const summary = await screen.findByTestId('scaffold-summary');
    expect(within(summary).getByText('tenant-alfa')).toBeInTheDocument();
  });

  it('em localhost sem prefixo /t, aplica fallback do tenant padrão', async () => {
    mockWindowLocation('http://localhost:4173/foundation/scaffold?feature=foundation-scaffold');

    const { RouterProvider } = await import('./router');
    renderWithProviders(<RouterProvider />);

    const summary = await screen.findByTestId('scaffold-summary');
    expect(within(summary).getByText('tenant-alfa')).toBeInTheDocument();
  });

  it('rota desconhecida renderiza landing sem explodir', async () => {
    mockWindowLocation('http://localhost:4173/');
    const { RouterProvider } = await import('./router');
    renderWithProviders(<RouterProvider />);
    expect(screen.getByText('Fundação Frontend IABank')).toBeInTheDocument();
  });
});
