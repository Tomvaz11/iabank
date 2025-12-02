import type { TestRunnerConfig } from '@storybook/test-runner';
import { injectAxe, checkA11y } from 'axe-playwright';

const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];
const TRUSTED_TYPES_POLICY = process.env.VITE_FOUNDATION_TRUSTED_TYPES_POLICY ?? 'foundation-ui';

const config: TestRunnerConfig = {
  async preVisit(page) {
    page.on('console', (msg) => {
      // Ajuda a depurar timeouts do runner (CSP/TT)
      // eslint-disable-next-line no-console
      console.log(`[storybook:console:${msg.type()}] ${msg.text()}`);
    });
    page.on('pageerror', (err) => {
      // eslint-disable-next-line no-console
      console.error(`[storybook:pageerror] ${err.message}`);
    });

    await page.addInitScript((policyName) => {
      const tt = (window as unknown as { trustedTypes?: TrustedTypePolicyFactory }).trustedTypes;
      if (!tt) return;
      try {
        if (!tt.getPolicyNames().includes(policyName)) {
          tt.createPolicy(policyName, {
            createScript: (input) => input,
            createScriptURL: (input) => input,
          });
        }
      } catch (_err) {
        // ignore policy creation errors in the runner context
      }
    }, TRUSTED_TYPES_POLICY);

    await injectAxe(page);
  },
  async postVisit(page, _context) {
    await checkA11y(page, '#storybook-root', {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
      axeOptions: {
        runOnly: {
          type: 'tag',
          values: WCAG_TAGS,
        },
        reporter: 'v2',
      },
    });
  },
};

export default config;
