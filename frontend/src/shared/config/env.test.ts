import { describe, expect, it } from 'vitest';

describe('config/env', () => {
  it('normaliza atributos do OTEL e retorna objeto tipado', async () => {
    process.env.VITE_API_BASE_URL = 'https://api.iabank.test';
    process.env.VITE_TENANT_DEFAULT = 'tenant-alfa';
    process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT = 'https://otel.iabank.test';
    process.env.VITE_OTEL_SERVICE_NAME = 'frontend-foundation';
    process.env.VITE_OTEL_RESOURCE_ATTRIBUTES = 'service.namespace=iabank,service.version=0.1.0';
    process.env.VITE_FOUNDATION_CSP_NONCE = 'nonce-value';
    process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY = 'foundation-ui';
    process.env.VITE_FOUNDATION_PGCRYPTO_KEY = 'pgcrypto-key';

    const { createEnv } = await import('./env');
    const env = createEnv({
      VITE_API_BASE_URL: 'https://api.iabank.test',
      VITE_TENANT_DEFAULT: 'tenant-alfa',
      VITE_OTEL_EXPORTER_OTLP_ENDPOINT: 'https://otel.iabank.test',
      VITE_OTEL_SERVICE_NAME: 'frontend-foundation',
      VITE_OTEL_RESOURCE_ATTRIBUTES: 'service.namespace=iabank,service.version=0.1.0',
      VITE_FOUNDATION_CSP_NONCE: 'nonce-value',
      VITE_FOUNDATION_TRUSTED_TYPES_POLICY: 'foundation-ui',
      VITE_FOUNDATION_PGCRYPTO_KEY: 'pgcrypto-key',
    });

    expect(env.API_BASE_URL).toBe('https://api.iabank.test');
    expect(env.TENANT_DEFAULT).toBe('tenant-alfa');
    expect(env.OTEL_RESOURCE_ATTRIBUTES).toEqual({
      'service.namespace': 'iabank',
      'service.version': '0.1.0',
    });
    expect(env.FOUNDATION_CSP_NONCE).toBe('nonce-value');
    expect(env.FOUNDATION_TRUSTED_TYPES_POLICY).toBe('foundation-ui');
    expect(env.FOUNDATION_PGCRYPTO_KEY).toBe('pgcrypto-key');
  });

  it('lança erro quando variáveis obrigatórias estão ausentes', async () => {
    process.env.VITE_API_BASE_URL = '';
    process.env.VITE_TENANT_DEFAULT = 'tenant-alfa';
    process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT = 'http://localhost:4318';
    process.env.VITE_OTEL_SERVICE_NAME = 'frontend-foundation';
    process.env.VITE_OTEL_RESOURCE_ATTRIBUTES = '';
    process.env.VITE_FOUNDATION_CSP_NONCE = 'nonce';
    process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY = 'policy';
    process.env.VITE_FOUNDATION_PGCRYPTO_KEY = 'key';

    const { createEnv } = await import('./env');
    expect(() =>
      createEnv({
        VITE_API_BASE_URL: '',
        VITE_TENANT_DEFAULT: 'tenant-alfa',
        VITE_OTEL_EXPORTER_OTLP_ENDPOINT: 'http://localhost:4318',
        VITE_OTEL_SERVICE_NAME: 'frontend-foundation',
        VITE_OTEL_RESOURCE_ATTRIBUTES: '',
        VITE_FOUNDATION_CSP_NONCE: 'nonce',
        VITE_FOUNDATION_TRUSTED_TYPES_POLICY: 'policy',
        VITE_FOUNDATION_PGCRYPTO_KEY: 'key',
      }),
    ).toThrow(/VITE_API_BASE_URL/);
  });
});
