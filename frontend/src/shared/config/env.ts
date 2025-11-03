import { z } from 'zod';

const schema = z.object({
  VITE_API_BASE_URL: z.string().url(),
  VITE_TENANT_DEFAULT: z.string().min(1),
  VITE_OTEL_EXPORTER_OTLP_ENDPOINT: z.string().url(),
  VITE_OTEL_SERVICE_NAME: z.string().min(1),
  VITE_OTEL_RESOURCE_ATTRIBUTES: z.string().min(1),
  VITE_CONFIGCAT_SDK_KEY: z.string().optional(),
  VITE_FOUNDATION_CSP_NONCE: z.string().min(1),
  VITE_FOUNDATION_TRUSTED_TYPES_POLICY: z.string().min(1),
  VITE_FOUNDATION_PGCRYPTO_KEY: z.string().min(1),
  VITE_SENTRY_DSN: z.union([z.string().url(), z.literal('')]).optional(),
  VITE_SENTRY_ENVIRONMENT: z.string().min(1).default('local'),
  VITE_SENTRY_RELEASE: z.string().optional(),
  VITE_SENTRY_TRACES_SAMPLE_RATE: z.string().optional(),
  VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE: z.string().optional(),
  VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE: z.string().optional(),
});

type RawEnv = z.input<typeof schema>;

export type AppEnv = {
  API_BASE_URL: string;
  TENANT_DEFAULT: string;
  OTEL_EXPORTER_OTLP_ENDPOINT: string;
  OTEL_SERVICE_NAME: string;
  OTEL_RESOURCE_ATTRIBUTES: Record<string, string>;
  CONFIGCAT_SDK_KEY?: string;
  FOUNDATION_CSP_NONCE: string;
  FOUNDATION_TRUSTED_TYPES_POLICY: string;
  FOUNDATION_PGCRYPTO_KEY: string;
  SENTRY_DSN?: string;
  SENTRY_ENVIRONMENT: string;
  SENTRY_RELEASE?: string;
  SENTRY_TRACES_SAMPLE_RATE: number;
  SENTRY_REPLAYS_SESSION_SAMPLE_RATE: number;
  SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE: number;
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

const clampRate = (value: number, fallback: number): number => {
  if (Number.isNaN(value)) {
    return fallback;
  }
  if (value < 0) {
    return 0;
  }
  if (value > 1) {
    return 1;
  }
  return value;
};

const parseSampleRate = (raw: string | undefined, fallback: number): number => {
  if (!raw) {
    return fallback;
  }
  const parsed = Number(raw);
  return clampRate(parsed, fallback);
};

const sanitizeOptional = (value: string | undefined): string | undefined => {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
};

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
    CONFIGCAT_SDK_KEY: result.data.VITE_CONFIGCAT_SDK_KEY?.trim() || undefined,
    FOUNDATION_CSP_NONCE: result.data.VITE_FOUNDATION_CSP_NONCE.trim(),
    FOUNDATION_TRUSTED_TYPES_POLICY: result.data.VITE_FOUNDATION_TRUSTED_TYPES_POLICY.trim(),
    FOUNDATION_PGCRYPTO_KEY: result.data.VITE_FOUNDATION_PGCRYPTO_KEY.trim(),
    SENTRY_DSN: sanitizeOptional(result.data.VITE_SENTRY_DSN),
    SENTRY_ENVIRONMENT: result.data.VITE_SENTRY_ENVIRONMENT,
    SENTRY_RELEASE: sanitizeOptional(result.data.VITE_SENTRY_RELEASE),
    SENTRY_TRACES_SAMPLE_RATE: parseSampleRate(result.data.VITE_SENTRY_TRACES_SAMPLE_RATE, 0.2),
    SENTRY_REPLAYS_SESSION_SAMPLE_RATE: parseSampleRate(
      result.data.VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE,
      0,
    ),
    SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE: parseSampleRate(
      result.data.VITE_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE,
      1,
    ),
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
