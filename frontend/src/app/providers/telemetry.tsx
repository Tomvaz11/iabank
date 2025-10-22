import { useEffect, useRef } from 'react';

import { env } from '../../shared/config/env';

export type TelemetryBootstrapConfig = {
  endpoint: string;
  serviceName: string;
  resourceAttributes: Record<string, string>;
};

export type TelemetryClient = {
  shutdown: () => Promise<void> | void;
};

export const bootstrapTelemetry = (
  config: TelemetryBootstrapConfig,
): TelemetryClient => {
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.info('[telemetry] Inicialização do stub OTEL', config);
  }

  return {
    shutdown: async () => undefined,
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
