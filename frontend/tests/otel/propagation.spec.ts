import { beforeEach, describe, expect, it, vi } from 'vitest';

const registerInstrumentationsMock = vi.fn();

vi.mock(
  '@opentelemetry/instrumentation',
  () => ({
    registerInstrumentations: registerInstrumentationsMock,
  }),
  { virtual: true },
);

const createdFetchInstrumentations: FakeFetchInstrumentation[] = [];
class FakeFetchInstrumentation {
  instrumentationName = 'fetch';
  config?: Record<string, unknown>;

  constructor(config?: Record<string, unknown>) {
    this.config = config;
    createdFetchInstrumentations.push(this);
  }
}

vi.mock(
  '@opentelemetry/instrumentation-fetch',
  () => ({
    FetchInstrumentation: FakeFetchInstrumentation,
  }),
  { virtual: true },
);

const createdDocumentLoadInstrumentations: FakeDocumentLoadInstrumentation[] = [];
class FakeDocumentLoadInstrumentation {
  instrumentationName = 'document-load';

  constructor(config?: Record<string, unknown>) {
    this.config = config;
    createdDocumentLoadInstrumentations.push(this);
  }

  config?: Record<string, unknown>;
}

vi.mock(
  '@opentelemetry/instrumentation-document-load',
  () => ({
    DocumentLoadInstrumentation: FakeDocumentLoadInstrumentation,
  }),
  { virtual: true },
);

const createdUserInteractionInstrumentations: FakeUserInteractionInstrumentation[] = [];
class FakeUserInteractionInstrumentation {
  instrumentationName = 'user-interaction';
  config?: Record<string, unknown>;

  constructor(config?: Record<string, unknown>) {
    this.config = config;
    createdUserInteractionInstrumentations.push(this);
  }
}

vi.mock(
  '@opentelemetry/instrumentation-user-interaction',
  () => ({
    UserInteractionInstrumentation: FakeUserInteractionInstrumentation,
  }),
  { virtual: true },
);

const createdResources: FakeResource[] = [];
class FakeResource {
  attributes: Record<string, unknown>;

  constructor(attributes: Record<string, unknown>) {
    this.attributes = attributes;
    createdResources.push(this);
  }

  static default() {
    return new FakeResource({
      'telemetry.sdk.name': 'web',
      'telemetry.sdk.language': 'javascript',
    });
  }

  merge(other: FakeResource) {
    return new FakeResource({
      ...this.attributes,
      ...other.attributes,
    });
  }
}

vi.mock(
  '@opentelemetry/resources',
  () => ({
    Resource: FakeResource,
  }),
  { virtual: true },
);

const createdExporters: FakeOTLPTraceExporter[] = [];
class FakeOTLPTraceExporter {
  options: Record<string, unknown>;

  constructor(options: Record<string, unknown>) {
    this.options = options;
    createdExporters.push(this);
  }
}

vi.mock(
  '@opentelemetry/exporter-trace-otlp-http',
  () => ({
    OTLPTraceExporter: FakeOTLPTraceExporter,
  }),
  { virtual: true },
);

const createdSpanProcessors: FakeBatchSpanProcessor[] = [];
class FakeBatchSpanProcessor {
  exporter: unknown;

  constructor(exporter: unknown) {
    this.exporter = exporter;
    createdSpanProcessors.push(this);
  }
}

vi.mock(
  '@opentelemetry/sdk-trace-base',
  () => ({
    BatchSpanProcessor: FakeBatchSpanProcessor,
  }),
  { virtual: true },
);

const createdProviders: FakeWebTracerProvider[] = [];
class FakeWebTracerProvider {
  config?: Record<string, unknown>;
  addSpanProcessor = vi.fn();

  constructor(config?: Record<string, unknown>) {
    this.config = config;
    createdProviders.push(this);
  }

  register() {
    return undefined;
  }
}

vi.mock(
  '@opentelemetry/sdk-trace-web',
  () => ({
    WebTracerProvider: FakeWebTracerProvider,
  }),
  { virtual: true },
);

const setGlobalTracerProvider = vi.fn();

const spans: Array<ReturnType<typeof createMockSpan>> = [];
const createMockSpan = (name: string) => {
  const span = {
    name,
    setAttribute: vi.fn(),
    setAttributes: vi.fn(),
    addEvent: vi.fn(),
    end: vi.fn(),
  };
  spans.push(span);
  return span;
};

const startActiveSpanMock = vi.fn(
  (
    name: string,
    maybeOptions: unknown,
    maybeContext: unknown,
    maybeCallback: unknown,
  ) => {
    const callback =
      typeof maybeOptions === 'function'
        ? maybeOptions
        : typeof maybeContext === 'function'
          ? maybeContext
          : (maybeCallback as (span: ReturnType<typeof createMockSpan>) => unknown);

    const span = createMockSpan(name);
    const result = callback(span);
    span.end();
    return result;
  },
);

const getTracerMock = vi.fn().mockReturnValue({
  startActiveSpan: startActiveSpanMock,
});

const baggageCalls: Array<Record<string, { value: string }>> = [];
const createBaggageMock = vi.fn((entries: Record<string, { value: string }>) => {
  baggageCalls.push(entries);
  return { entries };
});

const setBaggageMock = vi.fn((contextValue: unknown, baggageValue: unknown) => {
  lastBaggage = baggageValue;
  return contextValue;
});

let lastBaggage: unknown = null;

const activeContextToken = Symbol('active-context');
const contextWithMock = vi.fn((contextValue: unknown, fn: () => unknown) => fn());
const contextActiveMock = vi.fn(() => activeContextToken);

const setGlobalPropagator = vi.fn();

class FakeCompositePropagator {
  propagators: unknown[];

  constructor(config: unknown) {
    if (Array.isArray(config)) {
      this.propagators = config;
      return;
    }

    if (
      config &&
      typeof config === 'object' &&
      Array.isArray((config as { propagators?: unknown[] }).propagators)
    ) {
      this.propagators = (config as { propagators: unknown[] }).propagators;
      return;
    }

    this.propagators = [];
  }
}

class FakeW3CBaggagePropagator {}

class FakeW3CTraceContextPropagator {}

vi.mock(
  '@opentelemetry/api',
  () => ({
    trace: {
      setGlobalTracerProvider,
      getTracer: getTracerMock,
    },
    context: {
      with: contextWithMock,
      active: contextActiveMock,
      setBaggage: setBaggageMock,
      getBaggage: vi.fn(() => lastBaggage),
    },
    propagation: {
      setGlobalPropagator,
      createBaggage: createBaggageMock,
      setBaggage: setBaggageMock,
    },
    diag: {
      setLogger: vi.fn(),
      setLogLevel: vi.fn(),
    },
  }),
  { virtual: true },
);

vi.mock(
  '@opentelemetry/core',
  () => ({
    CompositePropagator: FakeCompositePropagator,
    W3CBaggagePropagator: FakeW3CBaggagePropagator,
    W3CTraceContextPropagator: FakeW3CTraceContextPropagator,
  }),
  { virtual: true },
);

vi.mock('../../src/shared/config/env', () => ({
  env: {
    API_BASE_URL: 'https://api.iabank.test',
    TENANT_DEFAULT: 'tenant-alfa',
    OTEL_EXPORTER_OTLP_ENDPOINT: 'https://otel.iabank.test/v1/traces',
    OTEL_SERVICE_NAME: 'frontend-foundation',
    OTEL_RESOURCE_ATTRIBUTES: {
      'service.namespace': 'iabank',
      'service.version': '0.1.0',
    },
    CONFIGCAT_SDK_KEY: undefined,
    FOUNDATION_CSP_NONCE: 'nonce-dev',
    FOUNDATION_TRUSTED_TYPES_POLICY: 'foundation-ui',
    FOUNDATION_PGCRYPTO_KEY: 'pgcrypto-dev',
  },
}));

describe('OTEL client propagation', () => {
  beforeEach(() => {
    vi.resetModules();
    registerInstrumentationsMock.mockClear();
    createdProviders.length = 0;
    createdSpanProcessors.length = 0;
    createdExporters.length = 0;
    createdFetchInstrumentations.length = 0;
    createdDocumentLoadInstrumentations.length = 0;
    createdUserInteractionInstrumentations.length = 0;
    createdResources.length = 0;
    spans.length = 0;
    baggageCalls.length = 0;
    startActiveSpanMock.mockClear();
    getTracerMock.mockClear();
    setGlobalPropagator.mockClear();
    setGlobalTracerProvider.mockClear();
    contextWithMock.mockClear();
    contextActiveMock.mockClear();
    setBaggageMock.mockClear();
    createBaggageMock.mockClear();
    lastBaggage = null;
  });

  it('inicializa provider web com propagadores e instrumentações multi-tenant', async () => {
    const telemetryModule = (await import('../../src/app/providers/telemetry')) as Record<
      string,
      unknown
    >;

    const bootstrapTelemetry = telemetryModule.bootstrapTelemetry as (
      config: {
        endpoint: string;
        serviceName: string;
        resourceAttributes: Record<string, string>;
      },
    ) => unknown;

    expect(bootstrapTelemetry).toBeTypeOf('function');

    bootstrapTelemetry({
      endpoint: 'https://otel.iabank.test/v1/traces',
      serviceName: 'frontend-foundation',
      resourceAttributes: {
        'service.namespace': 'iabank',
        'service.version': '0.1.0',
      },
    });

    expect(createdProviders).toHaveLength(1);
    expect(setGlobalTracerProvider).toHaveBeenCalledWith(createdProviders[0]);

    const providerConfig = createdProviders[0]?.config;
    expect(providerConfig).toMatchObject({
      resource: expect.objectContaining({
        attributes: expect.objectContaining({
          'service.name': 'frontend-foundation',
          'service.namespace': 'iabank',
          'service.version': '0.1.0',
        }),
      }),
    });

    expect(createdSpanProcessors).toHaveLength(1);
    expect(createdExporters).toHaveLength(1);
    expect(createdExporters[0]?.options).toMatchObject({
      url: 'https://otel.iabank.test/v1/traces',
    });
    expect(createdResources.length).toBeGreaterThanOrEqual(2);
    expect(createdProviders[0]?.addSpanProcessor).toHaveBeenCalledWith(createdSpanProcessors[0]);

    expect(registerInstrumentationsMock).toHaveBeenCalledTimes(1);
    const instrumentationConfig = registerInstrumentationsMock.mock.calls[0][0];
    expect(Array.isArray(instrumentationConfig.instrumentations)).toBe(true);

    const instrumentationNames = instrumentationConfig.instrumentations.map(
      (instrumentation: { instrumentationName: string }) => instrumentation.instrumentationName,
    );
    expect(instrumentationNames).toEqual(
      expect.arrayContaining(['fetch', 'document-load', 'user-interaction']),
    );

    const userInteractionConfig = createdUserInteractionInstrumentations[0]?.config ?? {};
    expect(userInteractionConfig).toMatchObject({
      eventNames: expect.arrayContaining(['click', 'submit', 'keydown']),
    });
    expect(userInteractionConfig?.shouldPreventSpanCreation).toBeTypeOf('function');

    expect(setGlobalPropagator).toHaveBeenCalledTimes(1);
    const compositePropagatorInstance = setGlobalPropagator.mock.calls[0][0];
    expect(compositePropagatorInstance).toBeInstanceOf(FakeCompositePropagator);
    expect(
      (compositePropagatorInstance as FakeCompositePropagator).propagators.some(
        (propagator) => propagator instanceof FakeW3CBaggagePropagator,
      ),
    ).toBe(true);
  });

  it('expõe tracer de interação que injeta baggage com tenant e feature', async () => {
    const telemetryModule = (await import('../../src/app/providers/telemetry')) as Record<
      string,
      unknown
    >;

    const bootstrapTelemetry = telemetryModule.bootstrapTelemetry as (
      config: {
        endpoint: string;
        serviceName: string;
        resourceAttributes: Record<string, string>;
      },
    ) => unknown;

    expect(bootstrapTelemetry).toBeTypeOf('function');
    bootstrapTelemetry({
      endpoint: 'https://otel.iabank.test/v1/traces',
      serviceName: 'frontend-foundation',
      resourceAttributes: {
        'service.namespace': 'iabank',
        'service.version': '0.1.0',
      },
    });

    const createInteractionTracer = telemetryModule.createInteractionTracer as (
      input: {
        tenantId: string;
        featureSlug: string;
        interactionName: string;
      },
    ) => (operation: (span: { addEvent: (name: string, attrs?: Record<string, unknown>) => void }) => Promise<void> | void) => Promise<void>;

    expect(createInteractionTracer).toBeTypeOf('function');

    const tracer = createInteractionTracer({
      tenantId: 'tenant-alfa',
      featureSlug: 'loan-tracking',
      interactionName: 'submit-metrics-filter',
    });

    await tracer(async (span) => {
      span.addEvent('ui.click', { component: 'button.apply-filter' });
    });

    expect(getTracerMock).toHaveBeenCalledWith('frontend-foundation');
    expect(startActiveSpanMock).toHaveBeenCalledWith(
      'interaction.submit-metrics-filter',
      expect.any(Object),
      expect.anything(),
      expect.any(Function),
    );

    expect(createBaggageMock).toHaveBeenCalledWith({
      'tenant.id': { value: 'tenant-alfa' },
      'feature.slug': { value: 'loan-tracking' },
      'interaction.name': { value: 'submit-metrics-filter' },
    });

    expect(setBaggageMock).toHaveBeenCalledWith(activeContextToken, {
      entries: expect.any(Object),
    });

    const span = spans.at(-1);
    expect(span?.setAttributes).toHaveBeenCalledWith(
      expect.objectContaining({
        'app.tenant_id': 'tenant-alfa',
        'app.feature_slug': 'loan-tracking',
        'app.interaction': 'submit-metrics-filter',
      }),
    );
  });
});
