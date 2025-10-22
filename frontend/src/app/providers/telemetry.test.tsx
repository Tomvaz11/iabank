import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

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
  },
}));
describe('TelemetryProvider', () => {
  it('inicializa o cliente OTEL ao montar e executa shutdown ao desmontar', async () => {
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
    expect(shutdown).toHaveBeenCalled();
    telemetryModule.resetTelemetryBootstrap();
  });
});
