import path from 'node:path';

import { defineConfig } from 'vitest/config';

const toThreshold = (rawValue: string | undefined, fallback: number): number => {
  if (!rawValue) {
    return fallback;
  }
  const parsed = Number(rawValue);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
};

const coverageThresholds = {
  statements: toThreshold(process.env.FOUNDATION_COVERAGE_STATEMENTS, 85),
  branches: toThreshold(process.env.FOUNDATION_COVERAGE_BRANCHES, 85),
  functions: toThreshold(process.env.FOUNDATION_COVERAGE_FUNCTIONS, 85),
  lines: toThreshold(process.env.FOUNDATION_COVERAGE_LINES, 85),
} as const;

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: [path.resolve(__dirname, 'setupTests.ts')],
    include: [
      'src/**/*.{test,spec,pact}.{ts,tsx}',
      'tests/**/*.{test,spec,pact}.{ts,tsx}',
      path.resolve(__dirname, '../contracts/pacts/**/*.pact.ts'),
    ],
    exclude: ['tests/e2e/**', 'tests/performance/**'],
    passWithNoTests: true,
    coverage: {
      reporter: ['text', 'lcov', 'json-summary'],
      provider: 'v8',
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.stories.{ts,tsx}',
        'src/**/__stories__/**',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'tests/**',
        'storybook-static/**',
        'src/shared/api/generated/**',
        'src/shared/api/generated-next/**',
        'src/shared/config/theme/**',
        'src/shared/ui/**',
        'src/app/providers/sentry.ts',
        'src/types/**',
        'src/App.tsx',
        'src/app/index.tsx',
        'src/main.tsx',
      ],
      thresholds: {
        statements: coverageThresholds.statements,
        branches: coverageThresholds.branches,
        functions: coverageThresholds.functions,
        lines: coverageThresholds.lines,
      },
    },
    alias: {
      '@app': path.resolve(__dirname, './src/app'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@features': path.resolve(__dirname, './src/features'),
      '@entities': path.resolve(__dirname, './src/entities'),
      '@shared': path.resolve(__dirname, './src/shared'),
      '@tests': path.resolve(__dirname, './src/tests'),
    },
  },
});
