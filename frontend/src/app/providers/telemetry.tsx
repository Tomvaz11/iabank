import { useEffect, useRef } from 'react';

import { trace, context, propagation } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import {
  CompositePropagator,
  W3CTraceContextPropagator,
  W3CBaggagePropagator,
} from '@opentelemetry/core';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { Resource } from '@opentelemetry/resources';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

import { env } from '../../shared/config/env';
import { initializeSentry } from './sentry';

export type TelemetryBootstrapConfig = {
  endpoint: string;
  serviceName: string;
  resourceAttributes: Record<string, string>;
};

export type TelemetryClient = {
  shutdown: () => Promise<void> | void;
};

const createInstrumentations = () => [
  new FetchInstrumentation({
    propagateTraceHeaderCorsUrls: [env.API_BASE_URL],
  }),
  new DocumentLoadInstrumentation(),
  new UserInteractionInstrumentation({
    eventNames: ['click', 'submit', 'keydown'],
    shouldPreventSpanCreation: () => false,
  }),
];

let currentServiceName = env.OTEL_SERVICE_NAME;

export const bootstrapTelemetry = (
  config: TelemetryBootstrapConfig,
): TelemetryClient => {
  currentServiceName = config.serviceName;

  const baseResource = Resource.default();
  const serviceResource = new Resource({
    ...config.resourceAttributes,
    [SemanticResourceAttributes.SERVICE_NAME]: config.serviceName,
  });
  const resource = baseResource.merge(serviceResource);

  const provider = new WebTracerProvider({ resource });
  const exporter = new OTLPTraceExporter({ url: config.endpoint });
  const spanProcessor = new BatchSpanProcessor(exporter);
  provider.addSpanProcessor(spanProcessor);

  const propagator = new CompositePropagator({
    propagators: [new W3CTraceContextPropagator(), new W3CBaggagePropagator()],
  });

  provider.register({
    contextManager: new ZoneContextManager(),
    propagator,
  });

  trace.setGlobalTracerProvider(provider);
  propagation.setGlobalPropagator(propagator);

  registerInstrumentations({
    tracerProvider: provider,
    instrumentations: createInstrumentations(),
  });

  return {
    shutdown: () => provider.shutdown(),
  };
};

export const createInteractionTracer = ({
  tenantId,
  featureSlug,
  interactionName,
}: {
  tenantId: string;
  featureSlug: string;
  interactionName: string;
}) => {
  return async (operation: (span: Span) => Promise<void> | void) => {
    const tracer = trace.getTracer(currentServiceName);
    const activeContext = context.active();
    const baggageValue = propagation.createBaggage({
      'tenant.id': { value: tenantId },
      'feature.slug': { value: featureSlug },
      'interaction.name': { value: interactionName },
    });
    const contextWithBaggage = propagation.setBaggage(activeContext, baggageValue);

    return context.with(contextWithBaggage, async () =>
      tracer.startActiveSpan(
        `interaction.${interactionName}`,
        {
          attributes: {
            'app.tenant_id': tenantId,
            'app.feature_slug': featureSlug,
            'app.interaction': interactionName,
          },
        },
        contextWithBaggage,
        async (span: Span) => {
          try {
            span.setAttributes({
              'app.tenant_id': tenantId,
              'app.feature_slug': featureSlug,
              'app.interaction': interactionName,
            });
            await operation(span);
          } finally {
            span.end();
          }
        },
      ),
    );
  };
};

let activeBootstrap = bootstrapTelemetry;

export const setTelemetryBootstrap = (impl: typeof bootstrapTelemetry) => {
  activeBootstrap = impl;
};

export const resetTelemetryBootstrap = () => {
  activeBootstrap = bootstrapTelemetry;
};

type Props = {
  children: React.ReactNode;
};

export const TelemetryProvider = ({ children }: Props) => {
  const clientRef = useRef<TelemetryClient | null>(null);

  useEffect(() => {
    initializeSentry({
      dsn: env.SENTRY_DSN,
      environment: env.SENTRY_ENVIRONMENT,
      release: env.SENTRY_RELEASE,
      tracesSampleRate: env.SENTRY_TRACES_SAMPLE_RATE,
      replaysSessionSampleRate: env.SENTRY_REPLAYS_SESSION_SAMPLE_RATE,
      replaysOnErrorSampleRate: env.SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE,
    });

    clientRef.current = activeBootstrap({
      endpoint: env.OTEL_EXPORTER_OTLP_ENDPOINT,
      serviceName: env.OTEL_SERVICE_NAME,
      resourceAttributes: env.OTEL_RESOURCE_ATTRIBUTES,
    });

    return () => {
      const client = clientRef.current;
      if (client?.shutdown) {
        void client.shutdown();
      }

      clientRef.current = null;
    };
  }, []);

  return <>{children}</>;
};
