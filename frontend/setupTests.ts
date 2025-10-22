import '@testing-library/jest-dom';

process.env.VITE_API_BASE_URL = process.env.VITE_API_BASE_URL ?? 'https://api.iabank.test';
process.env.VITE_TENANT_DEFAULT = process.env.VITE_TENANT_DEFAULT ?? 'tenant-default';
process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT = process.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT ?? 'http://localhost:4318';
process.env.VITE_OTEL_SERVICE_NAME = process.env.VITE_OTEL_SERVICE_NAME ?? 'frontend-foundation';
process.env.VITE_OTEL_RESOURCE_ATTRIBUTES = process.env.VITE_OTEL_RESOURCE_ATTRIBUTES ?? 'service.namespace=iabank,service.version=0.0.1';
