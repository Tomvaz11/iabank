/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_TENANT_DEFAULT: string;
  readonly VITE_OTEL_EXPORTER_OTLP_ENDPOINT: string;
  readonly VITE_OTEL_SERVICE_NAME: string;
  readonly VITE_OTEL_RESOURCE_ATTRIBUTES: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
