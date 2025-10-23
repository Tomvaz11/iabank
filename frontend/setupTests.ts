import '@testing-library/jest-dom';

process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL ?? 'https://api.iabank.test';
process.env.VITE_TENANT_DEFAULT = process.env.VITE_TENANT_DEFAULT ?? 'tenant-default';
process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT = process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318';
process.env.VITE_OTEL_SERVICE_NAME = process.env.VITE_OTEL_SERVICE_NAME ?? 'frontend-foundation';
process.env.VITE_OTEL_RESOURCE_ATTRIBUTES = process.env.VITE_OTEL_RESOURCE_ATTRIBUTES ?? 'service.namespace=iabank,service.version=0.0.1';
process.env.VITE_FOUNDATION_CSP_NONCE = process.env.VITE_FOUNDATION_CSP_NONCE ?? 'nonce-dev-fallback';
process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY =
  process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY ?? 'foundation-ui-dev';
process.env.VITE_FOUNDATION_PGCRYPTO_KEY =
  process.env.VITE_FOUNDATION_PGCRYPTO_KEY ?? 'dev-only-pgcrypto-key';
