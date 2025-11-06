import react from '@vitejs/plugin-react';
import path from 'node:path';
import autoprefixer from 'autoprefixer';
import tailwindcss from 'tailwindcss';
import { defineConfig, splitVendorChunkPlugin } from 'vite';

import { createFoundationCspPlugin } from './vite.csp.middleware';

const trustedTypesPolicy = process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY ?? 'foundation-ui';
const nonce = process.env.VITE_FOUNDATION_CSP_NONCE ?? 'nonce-dev-fallback';
const reportUri = process.env.VITE_FOUNDATION_CSP_REPORT_URI ?? 'https://csp-report.iabank.com';
const apiBaseUrl = process.env.VITE_API_BASE_URL ?? 'https://api.iabank.test';
const previewHost = process.env.FOUNDATION_PERF_HOST ?? '127.0.0.1';
const previewPort = Number(process.env.FOUNDATION_PERF_PORT ?? '4173');

export default defineConfig({
  plugins: [
    react(),
    // Melhora code-splitting de dependências de terceiros
    splitVendorChunkPlugin(),
    createFoundationCspPlugin({
      nonce,
      trustedTypesPolicy,
      reportUri,
      connectSrc: ["'self'", apiBaseUrl].filter(Boolean),
    }),
  ],
  resolve: {
    alias: {
      '@app': path.resolve(__dirname, './src/app'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@features': path.resolve(__dirname, './src/features'),
      '@entities': path.resolve(__dirname, './src/entities'),
      '@shared': path.resolve(__dirname, './src/shared'),
      '@tests': path.resolve(__dirname, './src/tests'),
    },
  },
  server: {
    port: 5173,
    open: false,
  },
  preview: {
    host: previewHost,
    port: Number.isNaN(previewPort) ? 4173 : previewPort,
    strictPort: true,
  },
  build: {
    chunkSizeWarningLimit: 1024,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('@opentelemetry')) return 'vendor-otel';
            if (id.includes('@sentry')) return 'vendor-sentry';
            if (id.includes('react')) return 'vendor-react';
          }
        },
      },
    },
  },
  css: {
    postcss: {
      plugins: [tailwindcss(), autoprefixer()],
    },
  },
});
