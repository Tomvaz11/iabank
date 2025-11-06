import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../shared/config/env', () => ({
  env: {
    API_BASE_URL: 'https://api.iabank.test',
    TENANT_DEFAULT: 'tenant-alfa',
    OTEL_EXPORTER_OTLP_ENDPOINT: 'http://localhost:4318',
    OTEL_SERVICE_NAME: 'frontend-foundation',
    OTEL_RESOURCE_ATTRIBUTES: {
      'service.namespace': 'iabank',
      'service.version': '0.1.0',
    },
    FOUNDATION_CSP_NONCE: 'nonce-dev',
    FOUNDATION_TRUSTED_TYPES_POLICY: 'foundation-ui',
    FOUNDATION_PGCRYPTO_KEY: 'dev-only',
  },
}));

// Evita efeitos colaterais de inicialização real do Sentry durante estes testes
vi.mock('./sentry', () => ({ initializeSentry: vi.fn() }));

describe('TelemetryProvider', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('inicializa o bootstrap configurado e executa shutdown ao desmontar', async () => {
    const shutdown = vi.fn();
    const telemetryModule = await import('./telemetry');
    const bootstrapSpy = vi.fn().mockReturnValue({ shutdown });
    telemetryModule.setTelemetryBootstrap(bootstrapSpy);

    const { unmount } = render(
      <telemetryModule.TelemetryProvider>
        <span>child</span>
      </telemetryModule.TelemetryProvider>,
    );

    expect(screen.getByText('child')).toBeInTheDocument();
    expect(bootstrapSpy).toHaveBeenCalledWith({
      endpoint: 'http://localhost:4318',
      serviceName: 'frontend-foundation',
      resourceAttributes: {
        'service.namespace': 'iabank',
        'service.version': '0.1.0',
      },
    });

    unmount();
    await waitFor(() => expect(shutdown).toHaveBeenCalled());
    telemetryModule.resetTelemetryBootstrap();
  }, 10000);

  // Nota: o branch assíncrono via import dinâmico é exercitado em testes de integração de performance.
  it('segue sem telemetria quando o bootstrap lança erro e registra aviso', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const telemetryModule = await import('./telemetry');
    const boom = new Error('boom');
    telemetryModule.setTelemetryBootstrap(() => {
      throw boom;
    });

    const { unmount } = render(
      <telemetryModule.TelemetryProvider>
        <span>child</span>
      </telemetryModule.TelemetryProvider>,
    );

    expect(screen.getByText('child')).toBeInTheDocument();
    await waitFor(() => expect(warnSpy).toHaveBeenCalled());
    expect(warnSpy.mock.calls[0][0]).toContain(
      '[telemetry] Falha ao iniciar coleta OTEL; execução seguirá sem telemetria.',
    );

    unmount();
    telemetryModule.resetTelemetryBootstrap();
    warnSpy.mockRestore();
  });

  it('não tenta shutdown quando o client não expõe método', async () => {
    const telemetryModule = await import('./telemetry');
    const bootstrapSpy = vi.fn().mockReturnValue({});
    telemetryModule.setTelemetryBootstrap(bootstrapSpy);

    const { unmount } = render(
      <telemetryModule.TelemetryProvider>
        <span>child</span>
      </telemetryModule.TelemetryProvider>,
    );
    expect(screen.getByText('child')).toBeInTheDocument();

    // Desmonta sem lançar exceções apesar da ausência de shutdown
    expect(() => unmount()).not.toThrow();

    telemetryModule.resetTelemetryBootstrap();
  });
});
