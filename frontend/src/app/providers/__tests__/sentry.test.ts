import { afterEach, describe, expect, test, vi } from 'vitest';

const initMock = vi.fn();
const browserTracingIntegrationMock = vi.fn(() => ({ name: 'browserTracing' }));
const replayIntegrationMock = vi.fn(() => ({ name: 'replay' }));

vi.mock('@sentry/react', () => ({
  init: initMock,
  browserTracingIntegration: browserTracingIntegrationMock,
  replayIntegration: replayIntegrationMock,
}));

afterEach(() => {
  initMock.mockClear();
  browserTracingIntegrationMock.mockClear();
  replayIntegrationMock.mockClear();
});

describe('initializeSentry', () => {
  test('não inicializa quando DSN está ausente', async () => {
    const { initializeSentry } = await import('../sentry');

    await initializeSentry({
      dsn: undefined,
      environment: 'test',
      release: '1.0.0',
      tracesSampleRate: 0.5,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
    });

    expect(initMock).not.toHaveBeenCalled();
  });

  test('configura Sentry com scrubbing de PII', async () => {
    const { initializeSentry } = await import('../sentry');

    await initializeSentry({
      dsn: 'https://public@sentry.invalid/1',
      environment: 'test',
      release: '1.0.0',
      tracesSampleRate: 0.5,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
    });

    expect(initMock).toHaveBeenCalledTimes(1);
    const options = initMock.mock.calls[0][0];

    expect(options.dsn).toBe('https://public@sentry.invalid/1');
    expect(options.environment).toBe('test');
    expect(options.release).toBe('1.0.0');
    expect(options.tracesSampleRate).toBe(0.5);
    expect(options.integrations).toEqual([
      browserTracingIntegrationMock.mock.results[0].value,
      replayIntegrationMock.mock.results[0].value,
    ]);

    const event = {
      request: {
        headers: {
          Authorization: 'Bearer secret',
        },
        data: {
          email: 'user@example.com',
        },
      },
    };
    const scrubbedEvent = options.beforeSend(event);
    expect(scrubbedEvent.request.headers.Authorization).toBe('[Filtered]');
    expect(scrubbedEvent.request.data.email).toBe('[Filtered]');

    const breadcrumb = {
      data: {
        headers: {
          Authorization: 'Bearer secret',
        },
      },
    };

    const scrubbedBreadcrumb = options.beforeBreadcrumb(breadcrumb);
    expect(scrubbedBreadcrumb.data.headers.Authorization).toBe('[Filtered]');
  });
});
