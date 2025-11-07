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


let activeBootstrap: ((config: TelemetryBootstrapConfig) => Promise<TelemetryClient> | TelemetryClient) | null = null;

export const setTelemetryBootstrap = (
  impl: (config: TelemetryBootstrapConfig) => Promise<TelemetryClient> | TelemetryClient,
) => {
  activeBootstrap = impl;
};

export const resetTelemetryBootstrap = () => {
  activeBootstrap = null;
};

type Props = {
  children: React.ReactNode;
};

const TELEMETRY_FAILURE_WARNING =
  '[telemetry] Falha ao iniciar coleta OTEL; execução seguirá sem telemetria.';

export const TelemetryProvider = ({ children }: Props) => {
  const clientRef = useRef<TelemetryClient | null>(null);

  useEffect(() => {
    const handleBootstrapFailure = (error: unknown) => {
      // eslint-disable-next-line no-console
      console.warn(TELEMETRY_FAILURE_WARNING, error);
      clientRef.current = null;
    };

    const queue = (cb: () => void) => {
      if (typeof window !== 'undefined') {
        const win = window as Window & {
          requestIdleCallback?: (cb: IdleRequestCallback, opts?: IdleRequestOptions) => number;
        };
        if (typeof win.requestIdleCallback === 'function') {
          win.requestIdleCallback(cb, { timeout: 2000 });
          return;
        }
      }
      setTimeout(cb, 0);
    };

    // Se um bootstrap customizado foi definido (ex.: nos testes), executa-o imediatamente
    // para permitir asserções síncronas.
    if (activeBootstrap) {
      try {
        const maybe = activeBootstrap({
          endpoint: env.OTEL_EXPORTER_OTLP_ENDPOINT,
          serviceName: env.OTEL_SERVICE_NAME,
          resourceAttributes: env.OTEL_RESOURCE_ATTRIBUTES,
        });
        if (maybe && typeof (maybe as unknown as { then?: unknown }).then === 'function') {
          Promise.resolve(maybe).then(
            (client) => {
              clientRef.current = client;
            },
            handleBootstrapFailure,
          );
        } else {
          clientRef.current = maybe as TelemetryClient;
        }
      } catch (error) {
        handleBootstrapFailure(error);
      }
    } else {
      // Carrega a pilha pesada de telemetria de forma assíncrona (code-splitting)
      queue(() => {
        void import('./telemetry.impl')
          .then(async (mod) => {
            try {
              const client = await mod.initializeTelemetryStack({
                endpoint: env.OTEL_EXPORTER_OTLP_ENDPOINT,
                serviceName: env.OTEL_SERVICE_NAME,
                resourceAttributes: env.OTEL_RESOURCE_ATTRIBUTES,
              });
              clientRef.current = client;
            } catch (error) {
              handleBootstrapFailure(error);
            }
          })
          .catch(() => {
            // eslint-disable-next-line no-console
            console.warn('[telemetry] Módulo de telemetria não carregado.');
          });
      });
    }

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

// Reexporta helpers utilizados diretamente pelos testes e por código legado
export { bootstrapTelemetry, createInteractionTracer } from './telemetry.impl';
