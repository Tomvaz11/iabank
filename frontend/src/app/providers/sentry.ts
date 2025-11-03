import * as Sentry from '@sentry/react';

const FILTERED_VALUE = '[Filtered]';
const SENSITIVE_KEYWORDS = [
  'password',
  'secret',
  'token',
  'key',
  'authorization',
  'cookie',
  'domain',
  'email',
  'cpf',
  'cnpj',
];

export type SentryConfig = {
  dsn?: string;
  environment: string;
  release?: string;
  tracesSampleRate: number;
  replaysSessionSampleRate: number;
  replaysOnErrorSampleRate: number;
};

const clampRate = (value: number): number => {
  if (Number.isNaN(value)) {
    return 0;
  }
  if (value < 0) {
    return 0;
  }
  if (value > 1) {
    return 1;
  }
  return value;
};

const shouldFilter = (key: unknown): key is string => {
  if (typeof key !== 'string') {
    return false;
  }
  const lowered = key.toLowerCase();
  if (lowered.startsWith('masked_')) {
    return false;
  }
  return SENSITIVE_KEYWORDS.some((keyword) => {
    if (keyword === 'token') {
      return lowered === 'token' || lowered.endsWith('_token') || lowered.endsWith('token_id');
    }
    return lowered.includes(keyword);
  });
};

const scrubUnknown = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map((item) => scrubUnknown(item));
  }

  if (value && typeof value === 'object') {
    const target = value as Record<string, unknown>;
    Object.entries(target).forEach(([innerKey, innerValue]) => {
      if (shouldFilter(innerKey)) {
        target[innerKey] = FILTERED_VALUE;
      } else {
        target[innerKey] = scrubUnknown(innerValue);
      }
    });
    return target;
  }

  return value;
};

const scrubEvent = <T>(event: T): T => {
  if (!event || typeof event !== 'object') {
    return event;
  }

  const target = event as unknown as Record<string, unknown>;
  Object.entries(target).forEach(([key, value]) => {
    if (shouldFilter(key)) {
      target[key] = FILTERED_VALUE;
    } else {
      target[key] = scrubUnknown(value);
    }
  });
  return event;
};

const scrubBreadcrumb = <T>(breadcrumb: T): T => {
  if (!breadcrumb || typeof breadcrumb !== 'object') {
    return breadcrumb;
  }

  const target = breadcrumb as unknown as Record<string, unknown>;
  Object.entries(target).forEach(([key, value]) => {
    if (shouldFilter(key)) {
      target[key] = FILTERED_VALUE;
    } else {
      target[key] = scrubUnknown(value);
    }
  });
  return breadcrumb;
};

export const initializeSentry = (config: SentryConfig) => {
  if (!config.dsn) {
    return;
  }

  Sentry.init({
    dsn: config.dsn,
    environment: config.environment,
    release: config.release,
    tracesSampleRate: clampRate(config.tracesSampleRate),
    replaysSessionSampleRate: clampRate(config.replaysSessionSampleRate),
    replaysOnErrorSampleRate: clampRate(config.replaysOnErrorSampleRate),
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    beforeSend: (event, _hint) => scrubEvent(event),
    beforeBreadcrumb: (breadcrumb) => scrubBreadcrumb(breadcrumb),
  });
};
