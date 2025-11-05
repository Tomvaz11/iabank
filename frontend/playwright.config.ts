import { defineConfig, devices } from '@playwright/test';

const PORT = Number(process.env.FRONTEND_PORT ?? 4173);
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: {
    timeout: 5_000
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }]
  ],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      testDir: './tests/e2e',
      testMatch: ['**/*.spec.ts'],
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      testDir: './tests/e2e',
      testMatch: ['**/*.spec.ts'],
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      testDir: './tests/e2e',
      testMatch: ['**/*.spec.ts'],
      use: { ...devices['Desktop Safari'] }
    },
    {
      name: 'lighthouse',
      testDir: './tests/performance',
      testMatch: ['**/*.spec.ts'],
      timeout: 180_000,
      retries: process.env.CI ? 1 : 0,
      use: {
        ...devices['Desktop Chrome'],
        video: 'off',
        trace: 'off',
        screenshot: 'off'
      }
    }
  ],
  webServer: {
    command: `pnpm preview --host 0.0.0.0 --port ${PORT} --strictPort`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
});
