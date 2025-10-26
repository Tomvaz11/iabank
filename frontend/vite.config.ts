import react from '@vitejs/plugin-react';
import path from 'node:path';
import { defineConfig } from 'vite';

import { createFoundationCspPlugin } from './vite.csp.middleware';

const trustedTypesPolicy = process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY ?? 'foundation-ui';
const nonce = process.env.VITE_FOUNDATION_CSP_NONCE ?? 'nonce-dev-fallback';
const reportUri = process.env.VITE_FOUNDATION_CSP_REPORT_URI ?? 'https://csp-report.iabank.com';
const apiBaseUrl = process.env.VITE_API_BASE_URL ?? 'https://api.iabank.test';

export default defineConfig({
  plugins: [
    react(),
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
      '@tests': path.resolve(__dirname, './src/tests')
    }
  },
  server: {
    port: 5173,
    open: false
  },
  preview: {
    port: 4173
  }
});
