const ALLOWED_KEYS = new Set([
  'tenant_id',
  'tenantId',
  'feature_slug',
  'featureSlug',
  'metric_code',
  'metricCode',
]);

const PII_PATTERNS: RegExp[] = [
  /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/, // CPF
  /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i, // Email
  /\+?\d{1,3}\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b/, // Phone (Brazil)
];

const REDACTED_TOKEN = '[PII]';

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const shouldMaskString = (key: string, value: string): boolean => {
  if (ALLOWED_KEYS.has(key)) {
    return false;
  }

  if (value === REDACTED_TOKEN) {
    return false;
  }

  return PII_PATTERNS.some((pattern) => pattern.test(value));
};

const sanitizeValue = (key: string, value: unknown): unknown => {
  if (typeof value === 'string') {
    return shouldMaskString(key, value) ? REDACTED_TOKEN : value;
  }

  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(key, item));
  }

  if (isPlainObject(value)) {
    return sanitizeTelemetryAttributes(value);
  }

  return value;
};

export const sanitizeTelemetryAttributes = (
  attributes: Record<string, unknown>,
): Record<string, unknown> => {
  return Object.entries(attributes).reduce<Record<string, unknown>>((acc, [key, value]) => {
    acc[key] = sanitizeValue(key, value);
    return acc;
  }, {});
};

export const piiRedactionToken = REDACTED_TOKEN;
