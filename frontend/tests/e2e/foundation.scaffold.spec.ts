import { expect, test } from '@playwright/test';

const PII_PATTERNS = [
  /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/, // CPF
  /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i, // email
  /\b\d{2}\s?\d{5}-\d{4}\b/, // telefone BR
];

const MAX_DURATION_MS = 5 * 60 * 1000;

test.describe('@SC-001 @SC-005 Fluxo E2E de scaffolding multi-tenant', () => {
  test('encaminha roteamento multi-tenant sem expor PII', async ({ page }) => {
    const requestedUrls: string[] = [];
    page.on('request', (request) => {
      requestedUrls.push(request.url());
    });

    const startedAt = Date.now();

    await page.goto('/t/tenant-alfa/foundation/scaffold?feature=loan-tracking');

    await expect(page.getByRole('heading', { name: /loan tracking/i })).toBeVisible();
    await expect(page.getByTestId('scaffold-summary')).toContainText('loan-tracking');

    const duration = Date.now() - startedAt;
    expect(duration).toBeLessThan(MAX_DURATION_MS);

    await expect(page.locator('html')).toHaveAttribute('data-tenant', 'tenant-alfa');

    await page.getByTestId('tenant-switcher').selectOption('tenant-beta');
    await expect(page.locator('html')).toHaveAttribute('data-tenant', 'tenant-beta');
    await expect(page).toHaveURL(/\/t\/tenant-beta\/foundation\/scaffold/);

    const currentUrl = page.url();
    PII_PATTERNS.forEach((pattern) => {
      expect(currentUrl).not.toMatch(pattern);
      requestedUrls.forEach((url) => expect(url).not.toMatch(pattern));
    });

    const traces = await page.evaluate(() =>
      window.performance
        .getEntriesByType('navigation')
        .map((entry) => (entry as PerformanceNavigationTiming).duration),
    );

    traces.forEach((value) => expect(value).toBeLessThan(MAX_DURATION_MS));
  });
});
