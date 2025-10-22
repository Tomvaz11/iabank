import { z } from 'zod';

const schema = z.object({
  VITE_API_BASE_URL: z.string().url(),
  VITE_TENANT_DEFAULT: z.string().min(1),
  VITE_OTEL_EXPORTER_OTLP_ENDPOINT: z.string().url(),
  VITE_OTEL_SERVICE_NAME: z.string().min(1),
  VITE_OTEL_RESOURCE_ATTRIBUTES: z.string().min(1),
});

type RawEnv = z.input<typeof schema>;

export type AppEnv = {
  API_BASE_URL: string;
  TENANT_DEFAULT: string;
  OTEL_EXPORTER_OTLP_ENDPOINT: string;
  OTEL_SERVICE_NAME: string;
  OTEL_RESOURCE_ATTRIBUTES: Record<string, string>;
};

const parseResourceAttributes = (value: string): Record<string, string> =>
  value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((attributes, entry) => {
      const [key, rawValue] = entry.split('=');
      if (key && rawValue) {
        attributes[key.trim()] = rawValue.trim();
      }
      return attributes;
    }, {});

const normalizeBaseUrl = (value: string): string => value.replace(/\/+$/, '');

const formatIssues = (issues: z.ZodIssue[]): string =>
  issues.map((issue) => issue.path.join('.') || issue.message).join(', ');

export const createEnv = (raw: Partial<Record<keyof RawEnv, unknown>>): AppEnv => {
  const result = schema.safeParse(raw);

  if (!result.success) {
    throw new Error(`Variáveis de ambiente inválidas: ${formatIssues(result.error.issues)}`);
  }

  return {
    API_BASE_URL: normalizeBaseUrl(result.data.VITE_API_BASE_URL),
    TENANT_DEFAULT: result.data.VITE_TENANT_DEFAULT,
    OTEL_EXPORTER_OTLP_ENDPOINT: normalizeBaseUrl(result.data.VITE_OTEL_EXPORTER_OTLP_ENDPOINT),
    OTEL_SERVICE_NAME: result.data.VITE_OTEL_SERVICE_NAME,
    OTEL_RESOURCE_ATTRIBUTES: parseResourceAttributes(result.data.VITE_OTEL_RESOURCE_ATTRIBUTES),
  };
};

const resolveRuntimeEnv = (): Partial<Record<keyof RawEnv, unknown>> => {
  const metaEnv =
    typeof import.meta !== 'undefined' && (import.meta as unknown as { env?: unknown }).env
      ? ((import.meta as unknown as { env: unknown }).env as Partial<Record<keyof RawEnv, unknown>>)
      : undefined;

  if (metaEnv) {
    try {
      createEnv(metaEnv);
      return metaEnv;
    } catch (error) {
      if (typeof process !== 'undefined') {
        return process.env as Partial<Record<keyof RawEnv, unknown>>;
      }
      throw error;
    }
  }

  if (typeof process !== 'undefined') {
    return process.env as Partial<Record<keyof RawEnv, unknown>>;
  }

  return {};
};

export const env = createEnv(resolveRuntimeEnv());
