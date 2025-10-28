import { expect, test } from '@playwright/test';
import { enforceLighthouseBudgets } from './support/lighthouse';

test.describe('@SC-004 Orçamento Lighthouse', () => {
  test('home respeita budgets críticos de UX', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Lighthouse roda apenas em Chromium');

    await page.goto('/');

    const { passed } = await enforceLighthouseBudgets(page);

    expect(passed).toBe(true);
  });
});
