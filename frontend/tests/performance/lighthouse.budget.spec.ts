import { expect, test } from '@playwright/test';
import { enforceLighthouseBudgets } from './support/lighthouse';

test.describe('@SC-004 Orçamento Lighthouse', () => {
  test('home respeita budgets críticos de UX', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Lighthouse roda apenas em Chromium');

    const targetUrl = process.env.LIGHTHOUSE_TARGET_URL ?? '/';
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('main, #root, [data-app-ready]', { timeout: 60_000 }).catch(() => {
      // tolera apps sem esses seletores, mas registra espera mínima
      return page.waitForTimeout(1500);
    });

    const { passed } = await enforceLighthouseBudgets(page);

    expect(passed).toBe(true);
  });
});
